# FtrIO.Toaster

A lightweight web UI for managing [FtrIO](https://github.com/FtrOnOff/FtrIO) feature toggles. View, edit, add, and delete toggles across multiple environments without touching a file.

## Quick Start

Create a `compose.yml` and paste in this snippet — no cloning required:

```yaml
services:
  toaster:
    image: thescottbot/ftrio:latest
    ports:
      - "8000:8000"
    environment:
      APP_NAME: "My Application"
      APPSETTINGS_PATH: /data/appsettings.json
      # AUTH_USERNAME: admin
      # AUTH_PASSWORD: secret
      # CHANGES_LOG_PATH: /log/changes.log
      # APPSETTINGS_PATH_STAGING: /env/staging/appsettings.json
    volumes:
      - type: bind
        source: /path/to/your/appsettings.json
        target: /data/appsettings.json
      - toaster-logs:/log
    restart: unless-stopped

volumes:
  toaster-logs:
```

```bash
docker compose up -d
```

Open `http://localhost:8000`.

## Features

- Boolean, percentage rollout, and blue/green toggle types
- Add, delete, and change toggle type in-place
- Multi-environment support — manage any number of environments from a single instance
- Implements FtrIO's buffer logic — changes are staged and flushed atomically on `FlushInterval`
- Audit log — every change recorded with timestamp, environment, key, old value, new value, and user
- 60-second polling detects external file changes
- HTTP Basic Auth and OAuth2 Proxy (SSO) support

## Multiple Environments

Register additional environments via `APPSETTINGS_PATH_<NAME>` — each points directly at its own `appsettings.json`:

```yaml
environment:
  APPSETTINGS_PATH:            /env/base/appsettings.json
  APPSETTINGS_PATH_STAGING:    /env/staging/appsettings.json
  APPSETTINGS_PATH_PRODUCTION: /env/production/appsettings.json

volumes:
  - { type: bind, source: /path/to/base,       target: /env/base }
  - { type: bind, source: /path/to/staging,     target: /env/staging }
  - { type: bind, source: /path/to/production,  target: /env/production }
```

## Authentication

### Basic Auth

```yaml
environment:
  AUTH_USERNAME: myuser
  AUTH_PASSWORD: mypassword
```

### SSO (Google, GitHub, Microsoft, GitLab, OIDC)

Use [OAuth2 Proxy](https://oauth2-proxy.github.io/oauth2-proxy/) as a sidecar. See the [full README](https://github.com/FtrOnOff/FtrIO.Toaster) for a ready-to-use `docker-compose.yml` with the proxy service block included.

## Audit Log

Every change is written to an append-only JSONL file. Mount a host directory to persist it across restarts:

```yaml
environment:
  CHANGES_LOG_PATH: /log/changes.log

volumes:
  - type: bind
    source: /path/to/your/log/dir
    target: /log
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APPSETTINGS_PATH` | `/data/appsettings.json` | Path to the base config file inside the container |
| `APP_NAME` | *(empty)* | Display name shown in the UI header |
| `AUTH_USERNAME` | *(empty)* | Basic auth username |
| `AUTH_PASSWORD` | *(empty)* | Basic auth password |
| `CHANGES_LOG_PATH` | `/log/changes.log` | Path where the audit log is written |
| `APPSETTINGS_LABEL` | *(empty)* | Display label for the base environment path badge |

## Links

- [GitHub Repository](https://github.com/FtrOnOff/FtrIO.Toaster)
- [FtrIO Core Library](https://github.com/FtrOnOff/FtrIO)
- [FtrIO.onetwo CLI](https://github.com/FtrOnOff/FtrIO.onetwo)
