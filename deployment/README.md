# EXAMINA Deployment Guide

This guide covers deploying EXAMINA (API + UI) to a single production
host, per `specs/DEPLOYMENT_SPEC_v1.0.md`'s environment-tier and
firewall model. It assumes PRISM is deployed independently, per its own
deployment documentation (Constitution Principle 10 — the bridge is
one-way; EXAMINA and PRISM are recovered and redeployed independently).

## Prerequisites

- Ubuntu 22.04 or Debian 12
- Python 3.11+
- Node.js 20+ (for the UI build)
- Caddy or Nginx
- Optional: ClamAV (for malware scanning in production — recommended)

## Server Setup (Hetzner CX32)

1. Create a server in the Hetzner console (CX32 or larger).
2. SSH in as `root`.
3. Create the `examina` user:
   ```
   adduser --system --group --home /opt/examina examina
   ```
4. Install Python 3.11, pip, and git:
   ```
   apt-get update
   apt-get install -y python3.11 python3.11-venv python3-pip git
   ```
5. Clone the repository into `/opt/examina`:
   ```
   git clone https://github.com/chidhvilasa/examina.git /opt/examina
   chown -R examina:examina /opt/examina
   ```
6. Create the virtual environment:
   ```
   su - examina -s /bin/bash
   cd /opt/examina
   python3.11 -m venv .venv
   ```
7. Install dependencies (the frozen, reproducible set from Phase 6):
   ```
   .venv/bin/pip install -r requirements/frozen_v060.txt
   .venv/bin/pip install -e .
   ```
8. Build the UI:
   ```
   cd src/examina/ui
   npm ci
   npm run build
   cd /opt/examina
   ```
9. Serve the UI build. The `dist/` output of the UI build
   (`src/examina/ui/dist/`) is static files — either serve them directly
   from Nginx/Caddy (recommended, add a `root`/`file_server` directive
   pointing at that path alongside the API `location`/`reverse_proxy`
   blocks in `deployment/nginx.conf` / `deployment/caddy/Caddyfile`), or
   copy them to whatever static-file directory your edge server is
   already configured to serve.

## Environment Variables

Copy `.env.example` to `/opt/examina/.env` and fill in real values.
**Never commit `.env` with real values** — it is git-ignored, and the
`secret-scan` CI job (TruffleHog) exists specifically to catch an
accidental commit of a secret.

| Variable | Purpose | Sensitivity |
|---|---|---|
| `EXAMINA_INVITE_CODE` | Gates access to the application for early-access users | Secret |
| `EXAMINA_ADMIN_TOKEN` | Gates the admin/research surfaces | Secret |
| `DATABASE_URL` | Database connection string | Secret (may embed credentials) |
| `PRISM_BRIDGE_URL` | Address of the PRISM bridge endpoint | Not secret, but not publicly documented |
| `PRISM_BRIDGE_TOKEN` | Authenticates EXAMINA to PRISM's bridge | Secret |
| `CLAMAV_MODE` | `enforce` or `skip` — upload pipeline antivirus scanning mode | Not secret |
| `CLAMAV_SOCKET` | Local ClamAV daemon socket path | Not secret |
| `EXAMINA_ALLOWED_ORIGINS` | Comma-separated list of browser origins allowed by CORS | Not secret |
| `EXAMINA_VERSION` | Reported application version | Not secret |
| `LOG_LEVEL` | Logging verbosity | Not secret |
| `EXAMINA_ENV` | `development` \| `staging` \| `production` | Not secret |

See `.env.example` for the canonical, versioned list with placeholder
values, and `specs/DEPLOYMENT_SPEC_v1.0.md` for the full secret
management rules (rotation, never baking secrets into a build artifact).

## Firewall (UFW)

```
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

Per `specs/DEPLOYMENT_SPEC_v1.0.md`'s firewall table: only the edge
server (Nginx/Caddy) is reachable from the public internet on 80/443;
the EXAMINA API itself listens on `127.0.0.1:8000` only and is never
directly exposed. SSH (22) should additionally be restricted to an admin
IP allowlist where your provider's firewall supports it.

## TLS with Caddy

1. Install Caddy: https://caddyserver.com/docs/install
2. Copy `deployment/caddy/Caddyfile` to `/etc/caddy/Caddyfile`.
3. Replace `your-domain.com` and `your-email@domain.com` with real values.
4. Enable and start:
   ```
   systemctl enable caddy && systemctl start caddy
   ```

Caddy obtains and renews a Let's Encrypt certificate automatically — no
manual certificate management. If you prefer Nginx instead, see
`deployment/nginx.conf`, which requires you to provision and renew TLS
certificates yourself (e.g. via `certbot`).

## Start EXAMINA

```
cp deployment/examina.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable examina
systemctl start examina
```

## Verify Deployment

```
curl https://your-domain.com/status
curl https://your-domain.com/health
```

`/status` should return `{"status":"ok",...}`. `/health` should return
`200` with `"status":"ok"` (or `"degraded"` if disk/memory headroom is
low — see `src/examina/api/routes/health.py`); a `503` there indicates a
database connectivity problem and should be investigated before
directing beta traffic to the deployment.

## ClamAV (Optional but Recommended)

```
sudo apt-get install clamav clamav-daemon
sudo freshclam
sudo systemctl start clamav-daemon
```

Set `CLAMAV_MODE=enforce` in `.env`. `CLAMAV_MODE=skip` (the default) is
a development-only bypass — every skipped scan is logged loudly
(`scan_for_malware()`, `src/examina/pipeline/steps/clamav_scan.py`) so it
can never be mistaken for a passed scan, but it must not be used in
production per Constitution Principle 8 (security before features).

## Rate Limiting

In-memory rate limiting (slowapi) is active by default and is
per-process. For a multi-worker production deployment (multiple
`uvicorn` workers or horizontally scaled instances), configure a shared
Redis backend so limits are enforced across workers rather than reset
per-process. See `specs/TECH_DEBT.md` TD-010 for details. A single-worker
deployment (the default `python -m examina.api.main` invocation, and
what `deployment/examina.service` runs) does not need this.

## Monitoring

Set up an external uptime monitor (e.g. UptimeRobot) against
`GET /health`. Alert on a non-200 response or a response time greater
than 10 seconds. See `specs/DEPLOYMENT_SPEC_v1.0.md`'s Monitoring and
Alerting section for the full internal-logging-based alerting model
(ERROR-severity log entries, WARNING-severity security events) that
complements this external check.

## CORS Configuration

CORS **must** be configured before deployment — the default
(`EXAMINA_ALLOWED_ORIGINS` unset) only allows `http://localhost:5173`
(the Vite dev server), which is correct for local development but wrong
for production. Set it to the actual UI origin:

```
EXAMINA_ALLOWED_ORIGINS=https://examina.yourdomain.com
```

Multiple origins may be comma-separated
(`EXAMINA_ALLOWED_ORIGINS=https://a.example.com,https://b.example.com`).
See `specs/TECH_DEBT.md` TD-012 for why the UI's own default (same-origin
requests via a dev proxy) does not, by itself, need CORS in local
development, and why a split-origin production deployment does.
