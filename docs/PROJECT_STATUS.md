# EXAMINA Project Status

## Current State
Current Phase: Phase 4 Complete
Current Version: 0.4.0
Specification Version: 1.0.0 (FROZEN), BRIDGE_SPEC amended to 1.1.0 (see ADR-0001)
Architecture: FROZEN (bridge field-level contract amended via ADR-0001)
Implementation: API COMPLETE

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

## Active Phase
None — awaiting Phase 5 prompt

## Next Phase
Phase 5: UI

## Test Count
338 passing, 1 skipped (EICAR/ClamAV live-daemon test — see
specs/TECH_DEBT.md TD-006), 0 failing

## Coverage
100% on src/examina/api/, src/examina/pipeline/, src/examina/report/,
src/examina/bridge/, and src/examina/language/

## Known Blockers
None blocking Phase 5. One standing workflow characteristic to be aware
of: direct `git push` to `main` is permanently rejected by branch
protection (required status checks can't be evaluated for a commit GitHub
has never seen). All changes to `main` land via a short-lived branch + PR,
merged once CI reports green on the PR — see specs/TECH_DEBT.md TD-002.

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
is deprecated in favor of FastAPI's `lifespan` pattern) newly added this
phase.
