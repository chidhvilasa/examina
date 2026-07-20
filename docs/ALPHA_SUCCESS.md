# EXAMINA Alpha Success Criteria

Version: EXAMINA v0.7.0 | PRISM v0.3.2 | Bridge v1.0
Alpha Period: 3 journalists, 1 week minimum
Written: before first user invite (pre-alpha)

## Purpose

These criteria are written BEFORE the alpha begins to prevent
hindsight bias when interpreting results. The alpha is considered
successful if ALL critical criteria and at least 5 of 8 total
criteria are met.

## Success Criteria

| Metric | Target | Critical |
|--------|--------|----------|
| Mean understandability score | >= 4.0 / 5 | Yes |
| Workflow adoption (Yes + Maybe) | >= 70% | Yes |
| Report changed assessment (Yes significantly + Yes somewhat) | >= 50% | No |
| Critical bugs reported | 0 | Yes |
| Server uptime | >= 99% | Yes |
| Analysis failures (500 errors / total requests) | < 2% | Yes |
| Mean analysis time | < 30 seconds | No |
| Memory growth after 20 repeated analyses | None detectable | No |

## Failure Actions

If ANY critical criterion fails:
  Pause expansion to 10 users.
  Diagnose and fix before proceeding.
  Re-run the alpha with the same 3 users for one more week.

If mean understandability < 3.5:
  The reports need significant revision before any expansion.
  Consult FeedbackCard question 2 and 3 to identify which
  sections are failing.

If analysis failure rate >= 5%:
  Do not expand. Debug the bridge integration.
  Check /admin/overview and server logs.

## Expansion Gate (Alpha → Closed Beta)

Only expand to 10 users after:
  [ ] All critical criteria met
  [ ] At least 5 of 8 total criteria met
  [ ] INTEGRATION_TEST_RESULTS.md shows no unresolved issues
  [ ] At least 10 analyses completed per alpha user
  [ ] At least 5 feedback submissions received

## Data Snapshot Schedule

At the end of each week, export alpha data snapshot:
  python scripts/export_alpha_snapshot.py --week N
Snapshots committed to alpha-data/weekN/ directory.
See scripts/export_alpha_snapshot.py for format.

## Paper Citation

All results reported in the research paper will be attributed to
specific EXAMINA and PRISM versions recorded in each snapshot.
No results will be reported without version provenance.
