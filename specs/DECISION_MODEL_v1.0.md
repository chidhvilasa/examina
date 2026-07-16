# EXAMINA Decision Model Specification

Specification Version: 1.0.0
Status: FROZEN

This document defines how `Assessment.verdict` (a `VerdictLabel`, see
`REPORT_SCHEMA_v1.0.md`) is chosen from PRISM's top `BridgeHypothesis` and
overall confidence label (see `CONFIDENCE_TRANSLATION_v1.0.md`), and the
escalation rules that override the default choice when contradictions are
severe. Not every theoretical `VerdictLabel` × confidence-label pairing is
meaningful — this document defines the eight pairings that are actually
reachable, and the collapse rules that route every other combination into
one of them.

## The Decision Matrix

Each row is a reachable, frozen combination of top-hypothesis category and
overall confidence label, and the `VerdictLabel` it produces.

| # | Top hypothesis category | Overall confidence | Verdict | Rationale |
|---|---|---|---|---|
| 1 | Consistent with unedited capture | High | `LIKELY_AUTHENTIC` | Strong, non-contradicted signals across families support a single unedited capture. |
| 2 | Consistent with unedited capture | Medium | `LIKELY_AUTHENTIC` | Signals lean the same way but are fewer or individually weaker. |
| 3 | Consistent with conventional editing (crop/color/compression, no generative signal) | High | `LIKELY_MANIPULATED` | Strong signals support deliberate post-capture editing not attributable to routine transmission (e.g. messaging-app recompression alone). |
| 4 | Consistent with conventional editing | Medium | `LIKELY_MANIPULATED` | Editing signals present but individually weaker or fewer. |
| 5 | Consistent with generative/synthetic origin | High | `LIKELY_AI_GENERATED` | Strong frequency-domain and/or structural signals converge on synthetic origin. |
| 6 | Consistent with generative/synthetic origin | Medium | `LIKELY_AI_GENERATED` | Generative-origin signals present but not all families agree as strongly. |
| 7 | Consistent with AI-assisted editing of an otherwise real capture (e.g. localized generative retouching) | Medium | `AI_ASSISTED` | Signals distinguish "edited with AI tooling" from "wholly synthetic" — this is its own category, not a weaker `LIKELY_AI_GENERATED`. |
| 8 | Two or more top-ranked hypotheses within the alternative-hypothesis threshold (see PRISM's `_ALTERNATIVE_HYPOTHESIS_THRESHOLD`) that would otherwise produce different verdicts | Medium | `MIXED_SIGNALS` | The evidence genuinely supports more than one story about equally well; EXAMINA reports the tension rather than picking a winner. |

## Collapse and Escalation Rules

Every combination not listed above is routed as follows, checked in order:

1. **No usable hypothesis, or overall confidence label is `Insufficient`.**
   → `INSUFFICIENT_EVIDENCE`, regardless of what any single hypothesis
   suggests. This is the default fallback and takes priority over every
   other rule.
2. **Overall confidence label is `Low`, for any hypothesis category.**
   → `MIXED_SIGNALS` if two or more hypotheses are within the alternative
   threshold of each other; otherwise `INSUFFICIENT_EVIDENCE`. A `Low`
   confidence result is never rendered as a confident-sounding verdict
   like `LIKELY_MANIPULATED`.
3. **A row above matches at `High`/`Medium` but a `CRITICAL`-severity
   `BridgeContradiction` exists among the supporting facts.**
   → Escalate to `MIXED_SIGNALS` regardless of what row 1-8 would
   otherwise select. A critical contradiction means the report cannot
   respect its own supporting evidence enough to state a clean verdict.
4. **Any other combination not covered by 1-3** (e.g. a hypothesis
   category outside the six described in the matrix, which would indicate
   a new PRISM hypothesis type EXAMINA does not yet translate).
   → `INSUFFICIENT_EVIDENCE`, and the gap is logged internally as a defect
   (Constitution Principle 6: no silent failures) — the report never
   guesses at a verdict for a hypothesis shape it doesn't recognize.

## Escalation Logic for CRITICAL Contradictions

A `BridgeContradiction` with `severity == "CRITICAL"` always triggers
escalation rule 3 above, with no exception carved out for any verdict or
confidence level. This is intentional: a critical contradiction (e.g. a
declared capture timestamp that postdates an observed processing
timestamp) means EXAMINA's own evidence disagrees with itself badly enough
that presenting any single-story verdict would misrepresent the analysis.

`MIXED_SIGNALS` produced via escalation always includes, in
`Assessment.headline_caveats`, a plain-language note naming that a
critical contradiction — not just an evidentiary tie — is the reason no
single verdict is given.

## What EXAMINA Never Says

Regardless of matrix row or escalation outcome, the decision model never
produces or permits:

- A verdict naming or implying a specific person's intent, honesty, or
  culpability (Constitution Principle 13) — verdicts describe the
  artifact, never the sender/creator as a person.
- A verdict expressed with the forbidden vocabulary in
  `LANGUAGE_SPEC_v1.0.md` (e.g. no "confirmed fake," no "proven
  authentic").
- A `LIKELY_*` verdict at `Insufficient` confidence — `Insufficient`
  confidence always routes to `INSUFFICIENT_EVIDENCE` via rule 1, with no
  exception.
- Two different verdicts for the same `report_id` — once assigned, a
  report's verdict does not change (Constitution Principle 9); a changed
  underlying analysis produces a new report.
