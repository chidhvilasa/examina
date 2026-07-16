# GitHub Repository Manual Setup

Repository: https://github.com/chidhvilasa/examina

Most of the settings originally expected to require manual web UI action
were actually configurable via the GitHub API and were enabled
programmatically during Phase -1. The checklist below reflects the
**actual** verified state, not just the original assumption.

## Security Settings (Settings > Security)

- [x] Dependabot alerts: **Enabled** (via `PUT /repos/chidhvilasa/examina/vulnerability-alerts`)
- [x] Dependabot security updates: **Enabled** (via `PUT /repos/chidhvilasa/examina/automated-security-fixes`)
- [x] Secret scanning: **Enabled by default** for new public repositories (verified via API, no action needed)
- [x] Secret scanning push protection: **Enabled by default** for new public repositories (verified via API, no action needed)

## Code Security (Settings > Code security and analysis)

- [ ] CodeQL: **Not yet enabled.** This requires committing a
      `.github/workflows/codeql.yml` file, which is out of scope for Phase -1
      (GitHub setup only, no project structure beyond `docs/`). Enable this
      as part of Phase 0 when the CI workflow files (`lint`, `type-check`,
      `unit-tests`, and `codeql`) are added.

## Features (Settings > General > Features)

- [x] Issues: **Enabled** (via `PATCH /repos/chidhvilasa/examina` — `has_issues=true`)
- [x] Discussions: **Enabled** (via `PATCH /repos/chidhvilasa/examina` — `has_discussions=true`)

## Branch Protection (Settings > Branches)

- [x] `main` branch protection enabled: required status checks
      (`lint`, `type-check`, `unit-tests`, strict mode), `enforce_admins`,
      no required PR reviews (single-developer repo), no restrictions,
      force pushes disallowed, deletions disallowed.
- Note: because `enforce_admins` is `true` and the three required checks
  have never reported for this repository, protection briefly had to be
  removed and reapplied during Phase -1 itself to push
  `docs/PROJECT_STATUS.md` and this file — GitHub blocks *any* push
  (including the owner's) to a branch whose required checks have never run.
  Once Phase 0 adds the CI workflow producing `lint`/`type-check`/`unit-tests`
  contexts, this will resolve itself and future pushes/PRs will be gated
  normally.

## Remaining Manual Action

Only one item requires action, and it is deferred to Phase 0 by design:

- [ ] Add `.github/workflows/codeql.yml` (or enable "Default setup" for
      CodeQL under Settings > Code security and analysis) once Phase 0
      introduces the CI workflow directory.
