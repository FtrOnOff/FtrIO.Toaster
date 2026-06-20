<p align="center">
  <img src="app/static/FtrIOToaster.png" alt="FtrIO Toaster" width="600"/>
</p>

# FtrIO Toaster

A lightweight Docker-hosted web UI for managing [FtrIO](https://github.com/TheScottBot/FtrIO) feature toggles. View, edit, add, and delete toggles in your `appsettings.json` without touching a file.

## Why Toaster?

Toast is binary — it's either toasted or it's not. Much like a feature toggle.

It's also a nod to the Dungeon Master who runs our D&D sessions. Every good campaign needs someone deciding what's enabled and what isn't.

## Features

- **Boolean** on/off toggles
- **Percentage rollout** — slider and number input in sync
- **Blue/Green** deployment switching
- Change toggle type at any time
- Add and delete toggles
- Implements FtrIO's buffer logic — changes are staged in memory and flushed atomically to `appsettings.json` on the `FlushInterval` defined in your config, exactly as a native FtrIO provider would

## Getting Started

```bash
git clone https://github.com/TheScottBot/FtrIO.Toaster
cd FtrIO.Toaster
docker compose up -d
```

Open `http://localhost:8000`.

## Configuration

Before running, update `docker-compose.yml` to point at the directory containing
the `appsettings.json` of the app you have FtrIO installed in:

```yaml
volumes:
  - type: bind
    source: /path/to/your/ftrio/app
    target: /data
```

Two env vars control behaviour:

| Variable | Default | Description |
|---|---|---|
| `APPSETTINGS_PATH` | `/data/appsettings.json` | Full path to the config file inside the container |
| `APP_NAME` | *(empty)* | Display name shown in the UI header — useful when running multiple Toaster instances for different products |

If the app runs on a different machine, mount the directory over a network share
first, then point the volume at the mount point. The file will be created
automatically if it doesn't exist yet.

## appsettings.json Format

```json
{
  "Toggles": {
    "MyBoolToggle":       true,
    "MyPercentToggle":    "20%",
    "MyBlueGreenToggle":  "blue"
  }
}
```

All other keys in the file (`FtrIO`, `Logging`, etc.) are left untouched.
