# EXAMINA Load Test Results

Date: 2026-07-20
EXAMINA version: v0.7.0 (running from source; pre-alpha prep bumps to v0.8.0 in this same phase)
PRISM version: v0.3.2

## Setup

```
EXAMINA_INVITE_CODE=load-test-code
EXAMINA_TEST_MODE=1
CLAMAV_MODE=skip
PRISM_PATH=C:\Users\chidh\Downloads\project forensic\PRISM
PRISM_PYTHON=C:\Users\chidh\Downloads\project forensic\PRISM\.venv\Scripts\python.exe
```

API started with `python -m examina.api.main`; load test run from a
second terminal with `python scripts/load_test.py --url
http://localhost:8000 --invite-code load-test-code` (no `--jpeg` flag —
minimal inline JPEG bytes used, per the script's stdlib-only default).

## Results

### Scenario 1 — Sequential (10 requests, 5s delay, warmup + leak detection)

**Result: PASS**

- Response times: min 3.45s, max 3.56s, mean 3.50s
- Success rate: 100% (10/10 returned 200)
- Memory (`GET /health` `memory_free_mb`): start 3049.9 MB, end 3107.7 MB
  — free memory *increased* by ~57.8 MB over the run (no decrease, so no
  leak signal)

### Scenario 2 — Concurrent (5 simultaneous requests)

**Result: PASS**

- All 5 requests returned `200` with no errors.
- Response times clustered around 9.38s (concurrent requests compete
  for the same single-process bridge subprocess call — see
  `specs/TECH_DEBT.md` TD-014 — so per-request latency roughly triples
  under 5-way concurrency versus the ~3.5s sequential baseline; this is
  expected given the deliberately blocking, single-worker
  `LocalBridgeClient.analyze()` implementation, not a bug).

### Scenario 3 — Failure Paths

**Result: PASS**

| Case | Expected | Actual |
|---|---|---|
| Text file uploaded as `/analyze` | 415 | 415 |
| Wrong invite code | 401 | 401 |
| `GET /report/nonexistent-id` | 404 | 404 |

## Overall: PASS

All three scenarios passed. Full raw results:
`alpha-data/load_test_results.json` (gitignored — not committed).

## Issues Found and Resolution

**Issue:** The first run of Scenario 1 failed (`memory_diff = 853.8 MB`,
comparing `abs(memory_start - memory_end)` against a 50MB threshold).
Free memory actually *increased* by ~854 MB over the sequential run —
the opposite of a leak signature (a real leak shows free memory
*decreasing* as the process retains more).

**Root cause:** `scripts/load_test.py`'s original verdict logic used an
unsigned absolute difference, so a large *increase* in free memory
(caused by ordinary OS-level memory management — disk cache growth/
reclamation elsewhere on the machine, unrelated to this test — while
this dev machine had other applications running) was indistinguishable
from a large *decrease*, and both failed the same threshold check.

**Fix:** Changed the metric to a signed `memory_decrease_mb =
memory_start - memory_end` and only flag a failure when memory
*decreased* by 50MB or more (`memory_decrease_mb >= 50`), matching what
"memory growth" (i.e. free memory shrinking) actually means for leak
detection. An increase in free memory is never itself a leak signal,
regardless of magnitude. Re-ran the full load test after the fix — all
three scenarios passed (`memory_decrease_mb = -57.8`, i.e. free memory
increased, well outside the failure threshold in the safe direction).

No EXAMINA application code was changed to produce this result — this
was purely a bug in the load test script's own verdict logic, found and
fixed before the results above were recorded.
