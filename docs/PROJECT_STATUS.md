# EXAMINA Project Status

## Current State
Current Phase: Phase 0 Complete
Current Version: 0.0.0
Specification Version: 1.0.0 (FROZEN)
Architecture: FROZEN
Implementation: FOUNDATION COMPLETE

## Completed Phases
- [x] Phase -1: GitHub Repository Setup
- [x] Phase 0: Repository Bootstrap

## Active Phase
None — awaiting Phase 1 prompt

## Next Phase
Phase 1: Bridge Interface
  Implement BridgeClient abstraction with LocalBridgeClient
  and RemoteBridgeClient. All bridge types defined.
  EXAMINA code never calls PRISM directly.

## Test Count
3 passing, 0 failing

## Coverage
N/A (placeholder tests only — real coverage begins Phase 1)

## Known Blockers
None blocking Phase 1. One standing workflow characteristic to be aware
of: direct `git push` to `main` is permanently rejected by branch
protection (required status checks can't be evaluated for a commit GitHub
has never seen). All changes to `main`, including this phase's own
bootstrap commit, land via a short-lived branch + PR, merged once CI
reports green on the PR. This was true when Phase 0 itself was pushed and
will be true for every future phase — see specs/TECH_DEBT.md TD-002.

## Technical Debt
See specs/TECH_DEBT.md — TD-001 resolved (CI workflow now exists and
reports on every PR). TD-002 newly documented: the PR-only workflow
implication of TD-001's fix, which is permanent by design, not a
bootstrap-only condition.
