# EXAMINA Confidence Translation Specification

Specification Version: 1.0.0
Status: FROZEN

PRISM produces numeric confidence across five dimensions (see
`prism/core/reasoning/report.py`'s `ReconstructionConfidence` and the
bridge's `BridgeConfidence`, defined in `BRIDGE_SPEC_v1.0.md`). A
journalist should never have to read a raw float to understand how sure
EXAMINA is. This document defines the one, frozen translation from PRISM's
numeric confidence into the plain language shown in every
`ConfidenceSection` (see `REPORT_SCHEMA_v1.0.md`).

## The Five Dimension Mappings

Each PRISM/bridge confidence dimension maps to one plain-language field in
`ConfidenceSection`. The label thresholds below are shared across all five
dimensions unless otherwise noted.

| Bridge field | ConfidenceSection field | Plain-language question it answers |
|---|---|---|
| `extraction_confidence` | `extraction_confidence_label` | "How reliably could EXAMINA read the file's internal structure?" |
| `source_reliability` | `source_reliability_label` | "How trustworthy are the underlying signals themselves?" |
| `inference_confidence` | `inference_confidence_label` | "How reliable is the evidence EXAMINA derived from those signals?" |
| `hypothesis_confidence` | `hypothesis_confidence_label` | "How confident is EXAMINA in its leading explanation of what happened to this file?" |
| `contradiction_penalty` | `contradiction_penalty_note` | "Did conflicting signals reduce confidence, and by how much?" |

### Label Thresholds (Overall Confidence)

Applied to `BridgeConfidence.overall` to produce
`Assessment.overall_confidence_label` and
`ConfidenceSection.overall_confidence_label`:

| Range (inclusive lower bound) | Label |
|---|---|
| `>= 0.70` | High |
| `>= 0.40` | Medium |
| `>  0.00` | Low |
| `== 0.00` or no usable signal | Insufficient |

The same thresholds apply independently to each of the four per-dimension
labels (`extraction_confidence_label`, `source_reliability_label`,
`inference_confidence_label`, `hypothesis_confidence_label`), computed from
their respective `BridgeConfidence` field.

### Contradiction Penalty Note

`contradiction_penalty_note` is `None` when `BridgeConfidence.
contradiction_penalty == 0.0` (no contradictions detected). Otherwise it is
a `TraceableString`-style plain sentence naming how many contradictions
were found and their overall severity, e.g. "Two conflicting signals were
found, which lowered EXAMINA's confidence in this assessment." — never a
bare percentage.

## Verdict Translation from Top Hypothesis

`Assessment.verdict` (a `VerdictLabel`, see `REPORT_SCHEMA_v1.0.md`) is
derived from the top `BridgeHypothesis` and the overall confidence label.
The complete decision matrix lives in `DECISION_MODEL_v1.0.md`; this
document only fixes the *language* used once a `VerdictLabel` is chosen. No
verdict is ever rendered using a word from the forbidden vocabulary below.

## Hard Rules

- **No "fake."** A manipulated or AI-generated verdict never uses the word
  "fake" or any synonym implying deliberate deception by a person.
- **No "definitely."** No confidence level, however high, is ever described
  using "definitely," "certainly," or "without doubt." The highest
  available label is "High" confidence — a bounded, explicitly-not-100%
  concept.
- **No "proof" / "proven."** EXAMINA produces evidence and confidence, not
  proof. These words are never used in any direction (neither "proof of
  manipulation" nor "proof of authenticity").
- **No "guaranteed" / "confirmed."** Nothing about a probabilistic,
  signal-based reconstruction is ever described as guaranteed or confirmed.
- The complete forbidden vocabulary, including variants and near-synonyms
  caught by the language enforcement package, is defined in
  `LANGUAGE_SPEC_v1.0.md`. This document's "Hard Rules" section is a
  restatement of the subset most relevant to confidence language, not an
  independent or narrower list.

## Disclaimer Text

Every `ExaminaReport.disclaimer` field contains the exact same text,
verbatim, regardless of verdict or confidence level:

> "This report presents evidence-based analysis to support your own
> editorial judgment. It is not a definitive determination of
> authenticity, manipulation, or origin. Confidence levels reflect the
> strength of available signals, not certainty. Always apply your own
> editorial standards and, where warranted, seek additional verification
> before publication."

This text is never shortened, paraphrased, or omitted. It is rendered in
full on every report, at every confidence level, including
`INSUFFICIENT_EVIDENCE` and `LIKELY_AUTHENTIC` verdicts.
