# EXAMINA Project Status

## Current State
Current Phase: Phase 1 Complete
Current Version: 0.1.0
Specification Version: 1.0.0 (FROZEN), BRIDGE_SPEC amended to 1.1.0 (see ADR-0001)
Architecture: FROZEN (bridge field-level contract amended via ADR-0001)
Implementation: BRIDGE INTERFACE COMPLETE

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

## Active Phase
None — awaiting Phase 2 prompt

## Next Phase
Phase 2: Report Engine

## Test Count
68 passing, 0 failing

## Coverage
100% on src/examina/bridge/ and src/examina/language/

## Known Blockers
None blocking Phase 2. One standing workflow characteristic to be aware
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
stubs, to be replaced in Phase 2) and TD-004 (BRIDGE_SPEC v1.0→v1.1
amendment record) newly added this phase.
