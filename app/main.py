import json
import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

APPSETTINGS_PATH = Path(os.environ.get("APPSETTINGS_PATH", "/data/appsettings.json"))
APP_NAME = os.environ.get("APP_NAME", "")
_lock = threading.Lock()

app = FastAPI(title="FtrIO Toaster")


def read_file() -> dict:
    if not APPSETTINGS_PATH.exists():
        return {}
    with open(APPSETTINGS_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_file(data: dict) -> None:
    APPSETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(APPSETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_toggles(data: dict) -> dict:
    return data.get("Toggles", {})


def set_toggles(data: dict, toggles: dict) -> dict:
    data["Toggles"] = toggles
    return data


# ── API ──────────────────────────────────────────────────────────────────────

@app.get("/api/toggles")
def list_toggles():
    with _lock:
        data = read_file()
    return get_toggles(data)


class ToggleValue(BaseModel):
    value: bool | str | int | float


@app.put("/api/toggles/{name}")
def upsert_toggle(name: str, body: ToggleValue):
    with _lock:
        data = read_file()
        toggles = get_toggles(data)
        toggles[name] = body.value
        write_file(set_toggles(data, toggles))
    return {"ok": True}


@app.delete("/api/toggles/{name}")
def delete_toggle(name: str):
    with _lock:
        data = read_file()
        toggles = get_toggles(data)
        if name not in toggles:
            raise HTTPException(status_code=404, detail="Toggle not found")
        del toggles[name]
        write_file(set_toggles(data, toggles))
    return {"ok": True}


@app.get("/api/health")
def health():
    return {
        "path": str(APPSETTINGS_PATH),
        "exists": APPSETTINGS_PATH.exists(),
        "app_name": APP_NAME,
    }


# ── Static UI ─────────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
