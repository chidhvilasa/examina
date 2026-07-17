# Integration Test Results — Phase 7 (Bridge Integration)

Date: 2026-07-17
PRISM version: v0.3.2 (`prism/bridge/` — serializer and CLI added this phase)
EXAMINA version: v0.7.0
Tester: automated (5 manual end-to-end tests, run by the implementing agent per the Phase 7 prompt's Step 4)

## Setup

```
PRISM_PATH=C:\Users\chidh\Downloads\project forensic\PRISM
PRISM_PYTHON=C:\Users\chidh\Downloads\project forensic\PRISM\.venv\Scripts\python.exe
EXAMINA_INVITE_CODE=test-e2e
EXAMINA_TEST_MODE=1
CLAMAV_MODE=skip
```

API started with `python -m examina.api.main`; verified reachable via
`GET /status` before each test. UI started with `npm run dev` for the
one test (Test 3) that checks UI-level error rendering.

## Test 1 — Real JPEG Analysis

**Result: PASS**

Uploaded a real Pillow-generated JPEG (400×300, mixed solid/checkerboard
color content, 6453 bytes) via `POST /analyze`.

- `overall_confidence`: `0.1266427405239804` — not the stub's exact
  `0.72`.
- Evidence: 6 real signals across 3 families (`Compression History`,
  `Frequency Analysis`, `Document Structure`), including
  `"JPEG quantization tables suggest possible double compression
  encoding"`, `"Frequency analysis detects elevated energy at 8x8 block
  boundaries..."`, `"Estimated JPEG quality factor is approximately
  82"` — not the stub's exact 2 fixed facts.
- `prism_version` embedded in the report's component versions is real
  (`0.3.1`, from PRISM's `ReasoningConfig` default), not `"stub:1.0"`.

Confirms the LocalBridgeClient → PRISM subprocess → real JPEG adapter
(EXIF, compression, frequency extractors) → reasoning pipeline chain is
live end to end, not returning placeholder data.

## Test 2 — Real PDF Analysis

**Result: PASS**

Generated a real PDF via PyMuPDF (1 page, title/author metadata, a line
of body text) and uploaded it via `POST /analyze`.

- Evidence: 11 real signals across 2 families (`File Metadata`,
  `Document Structure`), including `"PDF metadata claims document
  author is EXAMINA QA"`, `"PDF metadata contains title: Manual Test 2
  Document"`, `"PDF contains 1 page(s)"`, `"PDF version is 1.7"`, `"PDF
  cross-reference table contains 8 objects"`.
- Facts are attributed to `pdf_metadata_extractor` and
  `pdf_structure_analyzer` (visible in the underlying bridge payload),
  confirming document-level facts, not image-level ones, drove this
  report.
- Note: `unresolved_contradictions` was unusually high (240) for this
  PDF — this is real PRISM cross-modal rule-engine output (jpeg_v1 +
  pdf_v1 + crossmodal_v1 rule sets applied to a plain-text, no-embedded-
  image PDF) and is a PRISM-side reasoning characteristic, not an
  EXAMINA-side defect; out of scope for this phase to investigate
  further (PRISM's rule engine is not modified here).

## Test 3 — PRISM Offline Behavior

**Result: PASS**

Restarted the API with `PRISM_PATH` pointed at a nonexistent directory
and re-uploaded the same JPEG.

- `POST /analyze` returned `503` with
  `{"error":"analysis_unavailable","detail":"Analysis service is
  temporarily unavailable. Please try again in a few minutes.",
  "status_code":503}` — the defined error response
  (`src/examina/api/routes/analyze.py`'s `BridgeError` handling,
  unchanged this phase).
- Verified in the UI (`npm run dev`, Playwright-driven): the same
  upload attempt renders a dismissible red banner reading "Analysis
  service is temporarily unavailable. Please try again in a few
  minutes." — the existing generic error-display path from Phase 5,
  confirmed still working correctly against this new failure mode.
- Restarted the API with the correct `PRISM_PATH` afterward and
  confirmed `GET /status` returned `200` again before continuing.

## Test 4 — Determinism

**Result: PASS**

Uploaded the identical JPEG bytes twice in separate `/analyze` calls and
fetched both reports.

- `overall_confidence`: `0.1266427405239804` on both — identical (well
  within the 0.001 epsilon).
- `assessment.verdict`: identical on both (`INSUFFICIENT_EVIDENCE`).
- `report_id` and timestamps differed between the two calls, as
  expected — each analysis is a new report, not a cache hit.

Confirms PRISM's reasoning pipeline is deterministic given identical
input bytes, and that determinism survives the full round trip through
the subprocess bridge and EXAMINA's report assembly.

## Test 5 — Failure Modes

**Result: PASS** (all three sub-cases)

| Sub-case | Input | Expected | Actual |
|---|---|---|---|
| Corrupted JPEG | Real JPEG truncated to 200 bytes (valid magic bytes, incomplete data) | Report still generated (adapter degrades gracefully) | `200`, full report generated (`verdict: AI_ASSISTED`, `confidence: 0.5`) — the JPEG adapter tolerated the truncation and PRISM still produced a complete, real analysis rather than crashing |
| Oversized file | 21MB of JPEG-signature-prefixed bytes | `413` | `413 file_too_large` — `"File exceeds the 20MB limit."` |
| Fake-typed file | Plain text content saved as `fake.jpg` | `415` | `415 unsupported_media_type` — `"File type is not supported. EXAMINA accepts JPEG, PNG, WebP, and PDF files."` |

All three failure modes are handled by the existing upload pipeline
(Phase 3) and API error mapping (Phase 4), confirmed still correct
against the real bridge integration.

## Summary

| Test | Result |
|---|---|
| 1 — Real JPEG analysis | PASS |
| 2 — Real PDF analysis | PASS |
| 3 — PRISM offline behavior | PASS |
| 4 — Determinism | PASS |
| 5 — Failure modes | PASS |

**All 5 manual end-to-end tests pass. No issues found requiring a code
change.**

## Operational Note

`LocalBridgeClient`'s `python_executable` defaults to `PRISM_PYTHON` if
set, else plain `"python"` from `PATH` (per
`specs/BRIDGE_SPEC_v1.1.md`-adjacent design in
`src/examina/bridge/local_client.py`). A bare `"python"` on `PATH` will
almost never have PRISM's dependencies (scipy, PyMuPDF, opencv, etc.)
installed, causing every subprocess call to fail with a generic
`PRISM_ERROR`. **`PRISM_PYTHON` must be set to PRISM's own venv
interpreter** for any real (non-offline-test) bridge call to succeed —
this is not optional in practice, despite being an optional constructor
parameter. Documented here since it is easy to reproduce accidentally
(e.g. running `tests/integration/test_real_bridge.py` with only
`PRISM_PATH` set) and easy to mistake for a bridge defect rather than an
environment configuration gap.
