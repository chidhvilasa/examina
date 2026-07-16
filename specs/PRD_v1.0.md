# EXAMINA Product Requirements Document

Specification Version: 1.0.0
Status: FROZEN

## Mission

Give journalists and photo editors a fast, honest, evidence-based read on a
digital file's likely processing history — without requiring them to become
forensic analysts, and without ever telling them what to publish.

EXAMINA exists because newsroom verification decisions currently happen
under two bad conditions at once: severe time pressure, and no accessible
tooling that explains *why* a file looks suspicious in language a
non-specialist can act on. EXAMINA is the interface between PRISM's
forensic reasoning engine and that newsroom deadline.

## Primary User

**Journalists and photo editors at mid-sized newsrooms** — not national
wire services with in-house forensic teams, and not individual citizens
doing casual reverse-image searches. The primary user:

- Receives user-submitted media (tips, leaked documents, social media
  screenshots) as a routine part of their job.
- Has general digital literacy but no forensic training — they do not know
  what a quantization table is and should never need to.
- Operates under real deadline pressure: the decision to publish or hold a
  piece of media is often made in minutes, not days.
- Needs a second opinion they can defend to an editor, not a black-box
  verdict they must take on faith.

## The Problem

A photo editor receives a JPEG over Signal at 11:40pm. The story is due at
1:00am. The image purports to show something newsworthy and time-sensitive.
There is no chain of custody, no metadata anyone trusts, and no accessible
tool that explains what actually can and cannot be determined about the
file in the next 90 minutes.

Today's options are all inadequate for this moment:

- Manual EXIF/metadata inspection requires expertise most newsrooms don't
  have on shift at midnight.
- General-purpose "AI detector" web tools produce an unexplained percentage
  score with no evidence trail — useless in an editorial meeting where the
  editor will ask "how do you know?"
- Waiting for a forensic lab is not compatible with the news cycle.

EXAMINA closes this gap: upload the file, get a structured, evidence-backed
report in the time it takes to make a decision — not instead of a human
decision, but in support of one.

## What EXAMINA Produces

For every analyzed file, EXAMINA produces a single **Digital Evidence
Report** (`ExaminaReport`, see `REPORT_SCHEMA_v1.0.md`): a structured,
traceable, plain-language document translating PRISM's forensic
reconstruction into something a journalist can read, question, and act on
in minutes.

A report is not a verdict to be published as-is. It is evidence a human
editor uses to make their own call, exactly as they would use any other
source — with the added benefit that every claim in it can be traced back
to a concrete signal.

## The Four Report Sections

1. **Assessment** — the headline: a plain-language verdict drawn from one
   of a fixed, non-accusatory set of categories (see
   `DECISION_MODEL_v1.0.md`), the overall confidence label, and a short
   summary a photo editor can read in fifteen seconds.
2. **Evidence** — the "why": every signal PRISM extracted, grouped into
   the six evidence families (see `EVIDENCE_CLUSTERING_v1.0.md`), each with
   a plain-language description and a trace back to its source.
3. **History** — the "what happened to this file": a reconstructed,
   chronological narrative of the file's likely processing history
   (captured → edited → recompressed → forwarded, etc.), translated from
   PRISM's hypothesis and timeline output.
4. **Confidence** — the "how sure is EXAMINA": the full confidence
   breakdown, translated into the five plain-language dimensions defined in
   `CONFIDENCE_TRANSLATION_v1.0.md`, plus the mandatory disclaimer.

## Success Metrics

EXAMINA v1 is successful if, for a supported file type:

- **Four minutes total**: from upload to a fully rendered report, in the
  common case, on a typical newsroom connection.
- **No jargon**: a journalist with no forensic background can read the
  Assessment and Evidence sections and understand what they mean without
  looking anything up.
- **Traceable**: every claim in the report can be traced, on request
  (e.g. via an inline trace ID or an expandable detail view), back to the
  specific signal that produced it.
- **Says "insufficient" when it means it**: when the evidence does not
  support a confident read, the report says so plainly rather than forcing
  a verdict — this is treated as a successful outcome, not a failure of the
  tool.

## Competitive Position

EXAMINA is not competing to be the most sensitive AI-detection classifier.
It is competing to be the tool a newsroom trusts because it *shows its
work*.

- **vs. FauxLens** — FauxLens-style consumer detectors return a bare
  authenticity percentage with no evidence trail. EXAMINA always shows the
  underlying signals and lets the reader judge them.
- **vs. AP Verify** and similar wire-service internal tooling — those
  tools assume institutional scale and in-house forensic staff. EXAMINA is
  built for the mid-sized newsroom that has neither, and for a
  90-minute deadline rather than a multi-day review process.
- **vs. Reality Defender** and similar enterprise deepfake-detection
  platforms — those tools optimize for classifier accuracy at scale for
  platform trust & safety teams. EXAMINA optimizes for a single editor's
  ability to explain and defend a publish/hold decision, with traceability
  and plain language as first-class requirements rather than an
  afterthought.

## Explicit Out-of-Scope for v1

The following are deliberately not part of v1. Building any of them
requires a new PRD version and explicit approval, not an in-flight
addition to this one:

- Video and audio analysis (image and document formats only in v1; see
  `BRIDGE_SPEC_v1.0.md` for the file types PRISM currently supports).
- Any form of automated publish/hold decisioning, or integration that acts
  on a report without a human in the loop (Constitution Principle 1).
- User accounts, multi-newsroom organizational structures, or role-based
  access control beyond a single shared invite-code gate.
- Bulk/batch analysis of large media archives.
- Any feature that requires retaining uploaded file content beyond the
  minimum needed to produce a single report (Constitution Principle 7).
- Integrations with social platforms, CMS systems, or third-party
  publishing tools.
