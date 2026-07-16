# EXAMINA Project Status

## Current State
Current Phase: Phase 0 (not yet started)
Current Version: 0.0.0
Specification Version: 1.0.0 (FROZEN)
Architecture: FROZEN
Implementation: NOT STARTED

## Completed Phases
- [x] Phase -1: GitHub Repository Setup

## Active Phase
None — awaiting Phase 0 prompt

## Next Phase
Phase 0: Repository Bootstrap

## Known Blockers
- Branch protection status checks reference CI jobs (`lint`, `type-check`,
  `unit-tests`) that do not exist until Phase 0 adds the workflow file.
  Branch protection is active but those checks are advisory until Phase 0 CI
  is committed — GitHub will not block a merge/push on a check that has
  never reported for the repository.
- `enforce_admins` is `true`, so once Phase 0 CI contexts start reporting,
  even the repository owner will be blocked by a failing required check
  with no override. This is intentional per the Phase -1 spec but is worth
  remembering the first time a push is unexpectedly blocked.
- Pull request reviews are not required (single-developer repository). If a
  second contributor joins, `required_pull_request_reviews` should be
  revisited.
- CodeQL analysis is not yet enabled: it requires a `.github/workflows/`
  file, and Phase -1 is scoped to `docs/` only. Deferred to Phase 0. See
  docs/GITHUB_SETUP.md.

## Notes
- Dependabot alerts and Dependabot security updates were enabled
  programmatically via the GitHub API during Phase -1 (both accept a plain
  PUT with no body) — no manual step was actually required for either.
- Secret scanning and secret scanning push protection were already enabled
  by default for this repository (GitHub's current default for new public
  repositories) — verified via the API, no action needed.
- See docs/GITHUB_SETUP.md for the one remaining item that does require
  manual/Phase-0 action (CodeQL).
