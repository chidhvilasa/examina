# EXAMINA Project Status

## Current State
Current Phase: Phase 6 Complete
Current Version: 0.6.0
Specification Version: 1.0.0 (FROZEN), BRIDGE_SPEC amended to 1.1.0 (see ADR-0001)
Architecture: FROZEN
Implementation: API + UI COMPLETE
Status: BETA READY

## Completed Phases
- [x] Phase -1: GitHub Repository Setup
- [x] Phase 0: Repository Bootstrap
- [x] Phase 1: Bridge Interface
  Implemented `BridgeClient` abstraction (`src/examina/bridge/client.py`)
  with `LocalBridgeClient` (stub, placeholder data) and `RemoteBridgeClient`
  (stub, raises `BridgeError(code="BRIDGE_UNAVAILABLE")`). All Bridge*
  Pydantic v2 types defined in `src/examina/bridge/types.py` per
  `specs/BRIDGE_SPEC_v1.1.md`. `get_bridge_client()` factory added
  (`src/examina/bridge/factory.py`). Language guard foundation added
  (`src/examina/language/guard.py`) enforcing the 10-word forbidden
  vocabulary with whole-word matching. EXAMINA code never calls PRISM
  directly — no `prism.*` import anywhere in `src/examina/`.
- [x] Phase 2: Report Engine
  Implemented the full BridgeResult → ExaminaReport pipeline in
  `src/examina/report/`: `schema.py` (all Pydantic v2 report models,
  including `TraceableString.checked()` enforcing the language guard on
  every stored string), `clustering.py` (the six fixed evidence families
  per `specs/EVIDENCE_CLUSTERING_v1.0.md`), `confidence.py` (the five
  plain-language confidence dimensions per
  `specs/CONFIDENCE_TRANSLATION_v1.0.md`), `decision.py` (verdict
  determination and the fixed Assessment templates per
  `specs/DECISION_MODEL_v1.0.md`), `history.py` (timeline reconstruction),
  and `assembler.py` (`assemble_report()`, the single entry point
  orchestrating all of the above). No bridge/ or language/guard.py logic
  was modified.
- [x] Phase 3: Upload Pipeline
  Implemented the 7-step upload security pipeline in
  `src/examina/pipeline/`: `exceptions.py` (the `UploadSecurityError`
  hierarchy), `config.py` (`UploadConfig`), `steps/size_check.py`,
  `steps/mime_check.py` (byte-signature detection only — see
  `docs/adr/ADR-0002-mime-detection-signature-table.md` for why a
  dependency-free signature table replaces `python-magic`),
  `steps/filename_sanitize.py` (UUID4 identity, original filename never
  read), `steps/hash_file.py` (SHA-256 canonical identity),
  `steps/clamav_scan.py` (skip/enforce modes, temp file always deleted
  via try/finally), `steps/archive_check.py` (ZIP/gzip decompression-bomb
  detection via metadata inspection, never extraction), `pipeline.py`
  (`process_upload()`, the 7-step orchestrator), and `orchestrator.py`
  (`run_analysis()`, connecting the upload pipeline to the bridge and
  report engine). No bridge/ or report/ files were modified.
- [x] Phase 4: API
  Implemented the FastAPI application in `src/examina/api/`:
  `database.py` (SQLAlchemy `ReportRecord`/`FeedbackRecord`/
  `IncorrectAnalysisRecord`, in-memory SQLite in test mode via
  `EXAMINA_TEST_MODE=1`), `auth.py` (invite-code and admin-token
  verification via `hmac.compare_digest`), `models.py` (all
  request/response Pydantic models), `rate_limit.py` (slowapi, 5
  per-route limits), and `routes/{status,health,analyze,report,feedback,
  admin}.py`. `POST /analyze` composes the pipeline/bridge/report-engine
  steps directly (rather than calling `run_analysis()`) so it can surface
  `BridgeConfidence.active_hypotheses`/`unresolved_contradictions` in its
  response without modifying `pipeline/`/`report/` — see the module
  docstring in `src/examina/api/routes/analyze.py`. No `bridge/`,
  `report/`, or `pipeline/` files were modified. `python-magic-bin`'s
  Windows/macOS-only-wheel finding from Phase 3 (ADR-0002) also motivated
  keeping this phase's new dependencies (`fastapi`, `uvicorn`, `slowapi`,
  `sqlalchemy`, `psutil`, `python-multipart`) all pure-Python/cross-platform.
- [x] Phase 5: UI
  Implemented the React/TypeScript single-page UI in `src/examina/ui/`
  (Vite + React 19 + TypeScript, Tailwind v4, shadcn/ui): `lib/types.ts`
  (mirrors `src/examina/api/models.py`/`src/examina/report/schema.py`),
  `lib/api.ts` (`analyzeFile`, `fetchReport`, `deleteReport`,
  `submitFeedback`, `reportIncorrect`), `App.tsx` (two-view state machine,
  `useState` only, no routing/Redux), `components/UploadView.tsx`,
  `components/ReportView.tsx` composing all six report cards
  (`ReportHeader`, `ExpiryBanner`, `AssessmentCard`, `HistoryCard`,
  `EvidenceCard`, `ConfidenceCard`, `FeedbackCard`), and the
  `CopyButton`/`VerdictBadge`/`ConfidenceBar` primitives. No Python files
  were modified. Two implementation notes:
  (1) `AssessmentCard`'s large verdict display always renders
  `assessment.verdict_plain.text` (already language-checked server-side)
  for every verdict, rather than a UI-hardcoded string for
  `LIKELY_AUTHENTIC` — the prompt's own architecture-compliance checklist
  requires the UI never generate its own verdict language, and
  `decision.py`'s `_VERDICT_PLAIN[LIKELY_AUTHENTIC]` text already matches
  the prompt's example almost verbatim, so no information is lost.
  (2) `lib/api.ts`'s `API_BASE` defaults to an empty string (same-origin)
  instead of the literal `http://localhost:8000` fallback the prompt's
  Step 4 snippet showed — with that literal default, a real browser
  request from the Vite dev server (port 5173) to the API (port 8000) is
  cross-origin and fails CORS preflight, since the API has no CORS
  middleware and Phase 5 forbids adding one. Same-origin requests are
  forwarded by the Vite dev proxy (`vite.config.ts`, Step 10) instead,
  which is what Step 10 says the proxy is for. Confirmed working via a
  full Playwright-driven manual test (upload → analyze → report render →
  all six cards → copy-to-clipboard → feedback submit → back navigation),
  zero console errors. See `specs/TECH_DEBT.md` TD-012.
- [x] Phase 6: Hardening and Beta Preparation
  Zero new features — made what exists production-ready. Verified (and
  documented in `docs/SECURITY_NOTES.md`) that no EXAMINA code path
  extracts ZIP contents to disk, so no zip-slip fix was needed; added
  `tests/integration/test_pipeline_stress.py` (5 tests: a large
  Pillow-generated JPEG through the full pipeline, the 20MB size-check
  boundary from both sides, a PyMuPDF-generated PDF with large embedded
  images, and a central-directory-lying ZIP bomb rejected by the MIME
  allowlist before `archive_check.py` ever runs — defense-in-depth,
  demonstrated). Added `CORSMiddleware` (`EXAMINA_ALLOWED_ORIGINS` env
  var, comma-separated, defaults to the Vite dev server origin) and
  `SecurityHeadersMiddleware` (`X-Content-Type-Options`,
  `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`,
  `Cache-Control: no-store`) to `src/examina/api/app.py` — this closes
  TD-012 from Phase 5. Ran `pip-audit` against `requirements/dev.txt`:
  zero vulnerabilities found; wired into CI as the `dependency-audit`
  job. Captured `requirements/frozen_v060.txt` via `pip freeze` for
  environment reproducibility. Added `deployment/nginx.conf`,
  `deployment/caddy/Caddyfile`, `deployment/examina.service`, and a
  complete `deployment/README.md`. Added `docs/BETA_GUIDE.md` and
  rewrote `README.md` and `CHANGELOG.md`. Bumped
  `src/examina/__init__.py`/`pyproject.toml` from the stale 0.4.0 (never
  updated in Phase 5) to 0.6.0. No `bridge/`, `report/`, or UI files were
  modified; no new features or endpoints added.

## Active Phase
None — awaiting Phase 7 prompt

## Next Phase
None scheduled — beta operation. Deploy to Hetzner, distribute invite
codes, run the beta for 6-8 weeks, collect feedback, write the paper.

## Test Count
Python: 343 passing, 1 skipped (EICAR/ClamAV live-daemon test — see
specs/TECH_DEBT.md TD-006), 0 failing
UI: `tsc --noEmit` clean (0 errors), `npm run build` clean (0 errors)
Dependency audit: `pip-audit` clean (0 vulnerabilities)

## Coverage
100% on src/examina/api/, src/examina/pipeline/, src/examina/report/,
src/examina/bridge/, and src/examina/language/ (UI has no automated test
suite — out of scope per the Phase 5 prompt; the Phase 6 stress tests
live in tests/integration/ and are exercised by `pytest tests/` but not
by the CI `unit-tests` job, which scopes to tests/unit/ only)

## Beta Readiness Checklist
- [x] Security pipeline implemented (7 steps)
- [x] Forensic analysis via PRISM bridge
- [x] Report generation with full traceability
- [x] API with auth, rate limiting, persistence
- [x] React UI with all 6 report cards
- [x] Deployment documentation
- [x] Beta guide for journalists
- [x] CORS configured
- [x] Security headers configured
- [x] Dependency audit clean
- [x] Frozen requirements for reproducibility
- [ ] ClamAV enabled (requires a live clamd daemon on the deployment host)
- [ ] Domain configured
- [ ] TLS certificate issued
- [ ] Production .env configured

## Known Blockers
None blocking beta deployment from the codebase side. The four
unchecked items above are host-provisioning steps (domain, TLS,
production secrets, a live ClamAV daemon), not code — see
`deployment/README.md` for each. One standing workflow characteristic to
be aware of: direct `git push` to `main` is permanently rejected by
branch protection (required status checks can't be evaluated for a
commit GitHub has never seen). All changes to `main` land via a
short-lived branch + PR, merged once CI reports green on the PR — see
specs/TECH_DEBT.md TD-002.

## Specification Amendment (Phase 1)
`specs/BRIDGE_SPEC_v1.0.md`'s field-level contract for `BridgeRequest`/
`BridgeFact`/`BridgeContradiction`/`BridgeHypothesis`/`BridgeResult`
conflicted with the Phase 1 implementation prompt, and the prompt's
schema omitted the `fact_id`/`contradiction_id`/`hypothesis_id` fields
`EVIDENCE_TRACEABILITY_v1.0.md` requires for Principle 2 traceability.
Raised to and confirmed by the project owner before implementation; see
`docs/adr/ADR-0001-bridge-type-schema-amendment.md` and
`specs/BRIDGE_SPEC_v1.1.md` (supersedes v1.0, which is left unmodified
per the spec amendment policy).

## Technical Debt
See specs/TECH_DEBT.md — TD-001 resolved (CI workflow exists and reports
on every PR). TD-002 remains, permanent by design. TD-003 (bridge client
stubs) and TD-004 (BRIDGE_SPEC v1.0→v1.1 amendment record) added in
Phase 1. TD-005 (`HistoryEvent.supporting_signals` always empty pending
Phase 3 signal-ID wiring) added in Phase 2. TD-006 (EICAR/ClamAV test
skips without a live clamd daemon), TD-007 (tar/bzip2/7z archives
rejected immediately pending a vetted extraction library), and TD-008
(MIME detection via signature table instead of python-magic — see
ADR-0002) added in Phase 3. TD-009 (`GET /admin/rules` returns no real
data pending PRISM rule-health bridge integration), TD-010 (rate
limiting uses an in-memory, per-process backend — Redis recommended
before multi-worker production deployment), and TD-011 (`@app.on_event`
is deprecated in favor of FastAPI's `lifespan` pattern) added in Phase 4.
TD-012 (no CORS middleware on the API; the UI relies on the Vite dev
proxy / same-origin production deployment instead) added in Phase 5,
**resolved in Phase 6** (`CORSMiddleware` added to
`src/examina/api/app.py`, configured via `EXAMINA_ALLOWED_ORIGINS`).
