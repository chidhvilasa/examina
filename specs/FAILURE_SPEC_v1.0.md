# EXAMINA Failure Specification

Specification Version: 1.0.0
Status: FROZEN

This document implements Constitution Principle 6 (no silent failures). It
enumerates every failure category EXAMINA must handle explicitly, the
trigger condition for each, the exact user-facing message class, the
report impact, and the required internal action. Every failure path in
every future phase (upload pipeline in Phase 3, bridge client in Phase 1,
API layer in Phase 4) must map onto one of these nine categories — a new,
unclassified failure mode is itself a specification gap requiring an ADR
before the code that produces it ships.

## The No-Silent-Failure Rule

No failure, of any severity, is ever swallowed without both:

1. A plain-language message shown to the user, explaining what happened
   and what it means for the report they are about to receive (or why they
   are receiving none).
2. An internal log entry with enough detail (exception type, stage,
   correlation/request ID — never file content, never the original
   filename) for a developer to diagnose the failure after the fact.

No code path anywhere in EXAMINA uses a bare `except:` or an
`except Exception: pass`/`except Exception: continue` with no logging.
Every `except` clause names the specific exception type(s) it expects.

## The Nine Failure Categories

### 1. Malformed / Corrupted Upload

- **Trigger:** The uploaded file cannot be parsed as a valid instance of
  its declared or detected file type (truncated JPEG, corrupt PDF xref
  table, invalid DOCX ZIP container).
- **User message:** "This file could not be read as a valid [file type].
  It may be corrupted or incomplete. Please try re-exporting or
  re-uploading the original file."
- **Report impact:** No report is generated. The user is returned to the
  upload step, not shown a partial or empty report.
- **Internal action:** Logged at INFO level (expected, user-facing,
  not a defect) with file type, byte size, and the specific parse error —
  never file content.

### 2. Unsupported File Type

- **Trigger:** The uploaded file's detected MIME type is not one EXAMINA
  currently routes to PRISM (see `BRIDGE_SPEC_v1.0.md` and the PRD's
  out-of-scope section for video/audio).
- **User message:** "EXAMINA currently supports [supported types]. This
  file's type ([detected type]) is not yet supported."
- **Report impact:** No report is generated.
- **Internal action:** Logged at INFO level with the detected MIME type,
  for future prioritization of format support — never file content.

### 3. Oversized Upload

- **Trigger:** The uploaded file exceeds the configured maximum size
  before or during the upload pipeline's processing.
- **User message:** "This file exceeds EXAMINA's maximum size of [limit].
  Please upload a smaller file."
- **Report impact:** No report is generated. The upload is rejected before
  any analysis begins.
- **Internal action:** Logged at INFO level with the declared/observed
  size and the configured limit.

### 4. Malicious Upload Pattern Detected

- **Trigger:** The upload pipeline detects a known-malicious pattern
  (zip-slip path traversal attempt, decompression-bomb ratio, a byte
  signature mismatched against the declared extension in a way consistent
  with an exploit attempt).
- **User message:** "This file could not be processed. If you believe
  this is an error, please try a different export of the same file."
  (Deliberately generic: EXAMINA never tells a potential attacker exactly
  which detection fired.)
- **Report impact:** No report is generated. The file is never passed to
  PRISM.
- **Internal action:** Logged at WARNING level with the specific detection
  that fired (e.g. "zip-slip path traversal in DOCX container"), the
  request's correlation ID, and timestamp — treated as a security event
  for monitoring purposes, per Constitution Principle 11's threat model
  (the malicious uploader).

### 5. PRISM Bridge Unreachable

- **Trigger:** The configured `BridgeClient` (local or remote) cannot be
  reached at all — connection refused, DNS failure, process not running.
- **User message:** "EXAMINA's analysis engine is temporarily unavailable.
  Please try again in a few minutes."
- **Report impact:** No report is generated.
- **Internal action:** Logged at ERROR level (this is an operational
  defect, not user error) with the bridge client type and the underlying
  connection error. Feeds into the health-check monitoring described in
  `DEPLOYMENT_SPEC_v1.0.md`.

### 6. PRISM Bridge Timeout

- **Trigger:** The bridge call is reachable but does not return within the
  configured timeout (e.g. an unusually large or complex file).
- **User message:** "Analysis is taking longer than expected for this
  file. Please try again — very large or complex files may need a second
  attempt."
- **Report impact:** No report is generated for this attempt.
- **Internal action:** Logged at WARNING level with file size, type, and
  elapsed time, to distinguish a systemic performance issue from an
  isolated slow file.

### 7. Partial PRISM Analysis

- **Trigger:** PRISM returns `BridgeStatus.PARTIAL` — analysis completed
  but one or more sections were degraded or omitted (e.g. OCR unavailable,
  a byte-budget limit truncated embedded-image analysis, a page-count
  limit left some pages unanalyzed).
- **User message:** Rendered inline in the report itself, using the
  three-part Limitation Statement Format from `LANGUAGE_SPEC_v1.0.md" —
  never a separate error message, since a report is still produced.
- **Report impact:** The report is generated with the affected
  section(s) explicitly noting the limitation. `Assessment.
  headline_caveats` includes a short pointer to the limitation for
  visibility at the top of the report.
- **Internal action:** Logged at INFO level with which specific limit or
  unavailable capability caused the partial result.

### 8. Language Enforcement Rejection

- **Trigger:** A generated report string, at serialization time, is found
  to contain forbidden vocabulary (`LANGUAGE_SPEC_v1.0.md`) — indicating a
  defect in report-generation logic, not a PRISM or user issue.
- **User message:** "EXAMINA could not produce a report for this file due
  to an internal issue. This has been logged for review; please try
  again later."
- **Report impact:** No report is shown to the user. A report containing
  forbidden language is never released, even partially, even with a
  caveat (Constitution Principle 4 is absolute).
- **Internal action:** Logged at ERROR level with the offending field
  path and the specific forbidden term matched — treated as a
  release-blocking defect, escalated above ordinary bugs.

### 9. Internal / Unexpected Exception

- **Trigger:** Any exception not covered by categories 1-8 — a genuine
  bug anywhere in the request path.
- **User message:** "Something went wrong while processing this file.
  This has been logged; please try again, and contact support if the
  problem continues."
- **Report impact:** No report is generated.
- **Internal action:** Logged at ERROR level with full exception detail
  (type, message, stack trace) and correlation ID — never file content or
  filename. This is the only category where the specific internal detail
  is expected to require developer investigation rather than being a
  known, already-understood condition.

## Cross-Cutting Rules

- Categories 1-4 and 6 are user-input-shaped: expected, common, and never
  logged above INFO/WARNING severity, since they do not indicate a defect
  in EXAMINA itself.
- Categories 5, 8, and 9 are operational-shaped: they indicate something
  EXAMINA-side needs attention, logged at ERROR severity, and feed into
  the monitoring/alerting described in `DEPLOYMENT_SPEC_v1.0.md`.
- Category 7 is the only category that still produces a report — every
  other category produces no report at all, consistent with Principle 6:
  it is better to clearly say "no report" than to show a silently
  incomplete one that looks complete.
- No user-facing message in any category ever includes a raw stack trace,
  raw PRISM internal error text, file content, or the original filename.
