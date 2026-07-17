# EXAMINA Research Beta Guide

## What EXAMINA Is

EXAMINA reconstructs the probable processing history of digital files
using explainable forensic reasoning. It produces a Digital Evidence
Report — evidence and confidence, not a verdict a journalist is expected
to publish unexamined.

EXAMINA is not:
- An AI detector
- An authenticity certificate
- A final forensic conclusion
- Production-hardened software with a long operating history

## Who This Is For

EXAMINA is designed for journalists, photo editors, and visual
researchers who need a documented analysis of a file's provenance before
making publication decisions.

## Supported File Types

- JPEG images (.jpg, .jpeg) — up to 20MB
- PNG images (.png) — up to 20MB
- WebP images (.webp) — up to 20MB
- PDF documents (.pdf) — up to 20MB

## How to Read the Report

- **Assessment:** The answer to your question. Read this first.
- **What would change this:** Read this second. It tells you what
  additional evidence would alter the conclusion.
- **Processing History:** The probable sequence of events.
- **Evidence:** The forensic signals behind the conclusion.
- **Confidence:** How certain EXAMINA is, broken into five parts.

## Understanding Confidence

EXAMINA separates confidence into five dimensions because they measure
different things. A HIGH overall confidence means the signals are
consistent and the analyzers are reliable for this file type. A LOW
confidence means either the signals are contradictory or the analyzers
have limited reliability for this file type — the report states which,
explicitly, rather than presenting a single number without context.

## What EXAMINA Cannot Do

- EXAMINA does not establish a file's authenticity or manipulation with
  certainty — every report pairs its conclusion with an explicit
  confidence level, never a bare determination.
- EXAMINA does not analyze audio or video files.
- EXAMINA may not detect signs of manipulation from very recent
  generative models not represented in its analyzers' training data.
- EXAMINA's frequency-domain analysis has limited reliability for some
  file types. See the Confidence section's limitations for specifics on
  any given report.

## Privacy

- Your file is analyzed and immediately deleted. It is never retained
  beyond the minimum needed to produce the report.
- The report itself is stored for 24 hours, then permanently deleted.
- Download the JSON (the "Copy Report JSON" button) to keep a permanent
  copy of your report — EXAMINA does not keep one for you past expiry.
- No personally identifying information is retained.

## Feedback

Your feedback directly improves EXAMINA. The five-question form at the
bottom of every report takes about 30 seconds and helps us understand
what works and what needs improvement.

## Reporting Issues

If you believe an analysis produced incorrect results, use the "Report
Incorrect Analysis" button in the report header. This helps us improve
the system's accuracy over time. Your file is not stored as part of this
report.

## Citation

If you use EXAMINA in your work, please cite:

[Citation placeholder — to be updated after paper submission]
