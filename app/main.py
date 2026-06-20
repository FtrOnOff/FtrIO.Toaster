import json
import os
import tempfile
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

APPSETTINGS_PATH = Path(os.environ.get("APPSETTINGS_PATH", "/data/appsettings.json"))
APP_NAME = os.environ.get("APP_NAME", "")

_lock = threading.Lock()

# In-memory buffer — staged changes waiting for the next flush tick.
# Keys are toggle names; values are the staged toggle value (or a sentinel
# for deletes). Mirrors the ConcurrentDictionary in FtrIO's ToggleProviderBuffer.
_DELETED = object()
_buffer: dict = {}
_flush_timer: threading.Timer | None = None

app = FastAPI(title="FtrIO Toaster")


# ── File I/O ──────────────────────────────────────────────────────────────────

def read_file() -> dict:
    if not APPSETTINGS_PATH.exists():
        return {}
    with open(APPSETTINGS_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _atomic_write(data: dict) -> None:
    """Write to a temp file then atomically rename, matching FtrIO's buffer flush."""
    APPSETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=APPSETTINGS_PATH.parent,
        prefix=".appsettings_tmp_",
        suffix=".json",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, APPSETTINGS_PATH)  # atomic on same filesystem
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ── Buffer / flush ─────────────────────────────────────────────────────────────

def _flush_interval_seconds() -> float:
    """Read FlushInterval from the config file, defaulting to 5 (FtrIO's default)."""
    try:
        data = read_file()
        return float(data.get("FtrIO", {}).get("FlushInterval", 5))
    except Exception:
        return 5.0


def _flush() -> None:
    """Apply staged buffer to appsettings.json and schedule the next tick."""
    global _buffer, _flush_timer

    with _lock:
        staged = _buffer.copy()
        _buffer = {}

    if staged:
        try:
            with _lock:
                data = read_file()
            toggles = data.get("Toggles", {})
            for name, value in staged.items():
                if value is _DELETED:
                    toggles.pop(name, None)
                else:
                    toggles[name] = value
            data["Toggles"] = toggles
            _atomic_write(data)
        except Exception:
            # Re-stage on failure so values aren't lost
            with _lock:
                merged = staged.copy()
                merged.update(_buffer)
                _buffer = merged

    _schedule_flush()


def _schedule_flush() -> None:
    global _flush_timer
    interval = _flush_interval_seconds()
    _flush_timer = threading.Timer(interval, _flush)
    _flush_timer.daemon = True
    _flush_timer.start()


@app.on_event("startup")
def startup() -> None:
    _schedule_flush()


@app.on_event("shutdown")
def shutdown() -> None:
    if _flush_timer:
        _flush_timer.cancel()
    _flush()  # final flush on shutdown, matching buffer.Dispose()


# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/toggles")
def list_toggles():
    """Source of truth is always the file; merge staged buffer on top for live preview."""
    with _lock:
        data = read_file()
        staged = _buffer.copy()

    toggles = data.get("Toggles", {})
    for name, value in staged.items():
        if value is _DELETED:
            toggles.pop(name, None)
        else:
            toggles[name] = value
    return toggles


class ToggleValue(BaseModel):
    value: bool | str | int | float


@app.put("/api/toggles/{name}")
def upsert_toggle(name: str, body: ToggleValue):
    with _lock:
        _buffer[name] = body.value
    return {"ok": True}


@app.delete("/api/toggles/{name}")
def delete_toggle(name: str):
    with _lock:
        data = read_file()
        in_file = name in data.get("Toggles", {})
        in_buffer = name in _buffer and _buffer[name] is not _DELETED
        if not in_file and not in_buffer:
            raise HTTPException(status_code=404, detail="Toggle not found")
        _buffer[name] = _DELETED
    return {"ok": True}


@app.get("/api/health")
def health():
    return {
        "path": str(APPSETTINGS_PATH),
        "exists": APPSETTINGS_PATH.exists(),
        "app_name": APP_NAME,
        "flush_interval": _flush_interval_seconds(),
        "pending_changes": sum(1 for v in _buffer.values() if v is not _DELETED),
    }


# ── Static UI ─────────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
