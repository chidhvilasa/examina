# EXAMINA Deployment Specification

Specification Version: 1.0.0
Status: FROZEN

This document defines the deployment architecture EXAMINA targets from
Phase 4 (API) onward. Phase 0 introduces no deployable application code;
this specification exists now so every later phase's infrastructure
decisions (CI/CD, environment variables, secrets) are built against a
single frozen target rather than improvised per-phase.

## Environment Tiers

| Tier | Purpose | Data sensitivity | Access |
|---|---|---|---|
| **Development** | Local development, `sqlite:///./examina_dev.db`, `LocalBridgeClient` against a locally-running PRISM checkout. | Synthetic/test files only — never real journalist-submitted material. | Individual developer machine only. |
| **Staging** | Pre-release verification of a full release candidate against production-like configuration (real `RemoteBridgeClient`, hardened upload pipeline, real rate limits). | Synthetic/test files only. | Restricted to maintainers; not publicly reachable without the invite code. |
| **Production** | The deployment journalists actually use. | Real, potentially sensitive user-submitted files, held only transiently per Constitution Principle 7. | Gated by `EXAMINA_INVITE_CODE`; admin surfaces additionally gated by `EXAMINA_ADMIN_TOKEN`. |

## Server Architecture

```
                     Internet
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Edge server (reverse proxy)  │
        │   Nginx or Caddy               │
        │   - TLS termination            │
        │   - Rate limiting (edge layer) │
        │   - Security headers           │
        └───────────────┬────────────────┘
                        │  127.0.0.1 only
                        ▼
        ┌───────────────────────────────┐
        │   Application server           │
        │   - EXAMINA API (FastAPI/uvicorn, Phase 4) │
        │   - EXAMINA UI static build (Phase 5)       │
        │   - SQLite (or managed Postgres later)      │
        └───────────────┬────────────────┘
                        │  PRISM_BRIDGE_URL (internal network
                        │  or same-host, per RemoteBridgeClient)
                        ▼
        ┌───────────────────────────────┐
        │   PRISM server (separate host  │
        │   or process)                  │
        │   - Independently deployed and │
        │     versioned per PRISM's own  │
        │     deployment docs             │
        └───────────────────────────────┘
```

Two independently deployable units: the EXAMINA application server, and
the PRISM server it talks to via the bridge (Constitution Principle 10).
They may run on the same host in a small deployment, or be split across
hosts as load requires — the bridge abstraction (`BRIDGE_SPEC_v1.0.md`)
makes this a deployment decision, not a code change.

## Firewall Rules

**Edge server:**

| Port | Direction | Source | Purpose |
|---|---|---|---|
| 443 | Inbound | Any | HTTPS (public traffic) |
| 80 | Inbound | Any | HTTP → HTTPS redirect only |
| 22 | Inbound | Admin IP allowlist only | SSH |
| all other | Inbound | Denied | Default deny |

**Application server:**

| Port | Direction | Source | Purpose |
|---|---|---|---|
| 8000 (or configured) | Inbound | Edge server only (private network / localhost) | EXAMINA API |
| 22 | Inbound | Admin IP allowlist only | SSH |
| PRISM_BRIDGE port | Outbound | PRISM server only | Bridge calls |
| all other | Inbound | Denied | Default deny |

**PRISM server** (when split from the application server): follows
PRISM's own deployment specification for its own inbound rules; accepts
inbound bridge traffic only from the EXAMINA application server's address.

## Environment Variables

The complete set (see `.env.example` for the canonical, versioned list):

| Variable | Purpose | Sensitivity |
|---|---|---|
| `EXAMINA_INVITE_CODE` | Gates access to the application for early-access users | Secret |
| `EXAMINA_ADMIN_TOKEN` | Gates the admin/research surfaces | Secret |
| `DATABASE_URL` | Database connection string | Secret (may embed credentials in production) |
| `PRISM_BRIDGE_URL` | Address of the PRISM bridge endpoint | Not secret, but not publicly documented |
| `PRISM_BRIDGE_TOKEN` | Authenticates EXAMINA to PRISM's bridge | Secret |
| `CLAMAV_MODE` | Upload pipeline antivirus scanning mode | Not secret |
| `CLAMAV_SOCKET` | Local ClamAV daemon socket path | Not secret |
| `EXAMINA_VERSION` | Reported application version | Not secret |
| `LOG_LEVEL` | Logging verbosity | Not secret |
| `EXAMINA_ENV` | `development` \| `staging` \| `production` | Not secret |

## Secret Management Rules

- No secret value is ever committed to the repository, in any file, at
  any commit — `.env` is git-ignored, `.env.example` contains only
  placeholder values, and this rule is enforced by the `secret-scan` CI
  job (TruffleHog) introduced this phase.
- Secrets are provided to each environment via that environment's own
  secret store (systemd environment file, host-level environment
  variables, or a secrets manager) — never baked into a container image
  or committed configuration file.
- Rotating a secret (invite code, admin token, bridge token) never
  requires a code change — only an environment variable update and a
  process restart.
- Any secret suspected of exposure (accidental commit, log leak) is
  rotated immediately; the exposed value is treated as compromised even
  after the exposing artifact is removed from history.

## CI/CD Pipeline

Defined in `.github/workflows/ci.yml` (introduced this phase), with four
required jobs on every push and pull request against `main`:

1. **`lint`** — `ruff check src/ tests/`.
2. **`type-check`** — `mypy src/ --strict --ignore-missing-imports`.
3. **`unit-tests`** — `pytest tests/unit/ -v --tb=short`.
4. **`secret-scan`** — TruffleHog scan of the diff against `main`.

Branch protection on `main` (configured in Phase -1) requires `lint`,
`type-check`, and `unit-tests` to pass before a merge is accepted (see
`docs/GITHUB_SETUP.md` for the exact configuration and its current
limitations). `secret-scan` runs on every push/PR as a further defense
layer even though it is not (yet) a required status check.

Deployment itself (build → staging → production promotion) is out of
scope for Phase 0; it is introduced when Phase 4/5 produce a deployable
application, following this same environment-tier and firewall model.

## Monitoring and Alerting

- **Health check:** the application server exposes an unauthenticated,
  unrate-limited health endpoint (introduced in Phase 4) reporting
  database connectivity, bridge reachability, and basic resource
  headroom — modeled on PRISM's own `GET /health` design.
- **Error-rate alerting:** ERROR-severity log entries (Failure
  Specification categories 5, 8, 9) are the primary signal for
  operational alerting once a monitoring stack is introduced; a spike in
  any of these three categories is treated as an incident, not routine
  noise.
- **Security-event alerting:** WARNING-severity entries from Failure
  Specification category 4 (malicious upload pattern detected) are
  reviewed as security signals per Constitution Principle 11's threat
  model, independent of ordinary error-rate monitoring.

## Backup Policy

- The database (report metadata, feedback, consent records — never raw
  file content, which is never stored per Constitution Principle 7) is
  backed up on a regular schedule appropriate to its size and change
  rate, with backups encrypted at rest.
- Given the 24-hour-style report expiry pattern established for PRISM and
  expected to carry into EXAMINA's own report retention policy (defined
  precisely when Phase 2's report engine ships), backups are treated as a
  disaster-recovery safety net, not a mechanism for extending retention
  beyond the documented expiry window.
- Backup restoration is tested periodically, not assumed to work because
  a backup job "succeeded."

## Disaster Recovery

- **RPO (Recovery Point Objective):** bounded by the backup interval —
  data since the last successful backup may be lost in a full-loss
  scenario.
- **RTO (Recovery Time Objective):** re-provisioning the application
  server from infrastructure-as-config (the deployment scripts introduced
  alongside Phase 4/5) and restoring the most recent database backup.
- PRISM and EXAMINA are recovered independently, consistent with their
  independent deployability — an EXAMINA-side disaster does not imply a
  PRISM-side one, and vice versa.

## Rollback Procedure

- Every release is tagged (as this phase establishes with `v0.0.1`).
  Rolling back means redeploying the previous tag's build artifact, not
  reverting commits on `main`.
- Because reports embed their producing versions (Constitution Principle
  9 — `examina_version`, `bridge_version`, `specification_version`), a
  rollback never needs to "fix up" previously generated reports; they
  remain self-describing and valid under the version that produced them.
- A rollback is followed by a root-cause fix on `main` and a new,
  forward-only release — `main` is never force-pushed or rewritten to
  erase a bad release (Constitution-adjacent operational norm, consistent
  with branch protection disallowing force pushes).
