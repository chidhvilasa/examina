# EXAMINA Report Schema Specification

Specification Version: 1.0.0
Status: FROZEN

This document defines the complete typed structure of a Digital Evidence
Report. It is the contract every future EXAMINA report-generation module
(`src/examina/report/`, implemented in Phase 2) must satisfy. Field types
below are given in Python-like pseudo-syntax; the actual Pydantic models
are implemented in Phase 2, not this phase.

Every field described here exists to satisfy a Constitution principle:
traceability (Principle 2), mandatory uncertainty (Principle 3), forbidden
language (Principle 4), immutability (Principle 9), and non-accusatory
language (Principle 13). Do not add a field that undermines any of these.

---

## TraceableString

The atomic unit of traceability. Any human-readable sentence in a report
that asserts a finding is a `TraceableString`, never a bare `str`.

```
TraceableString:
  text: str                  # the plain-language sentence shown to the user
  trace_ids: list[str]       # one or more IDs pointing to the BridgeFact(s),
                              # BridgeContradiction(s), or BridgeHypothesis
                              # that support `text` (see
                              # EVIDENCE_TRACEABILITY_v1.0.md)
```

Rule: `trace_ids` is never empty for a `TraceableString` that appears in
`EvidenceSection` or `HistorySection`. A sentence with nothing to trace to
is not evidence — it must not be represented as a `TraceableString`.

## ExaminaReport (top-level)

```
ExaminaReport:
  report_id: str                       # opaque, unguessable identifier
  file_hash: str                       # sha256 of the uploaded file
  created_at: datetime                 # UTC, ISO-8601
  expires_at: datetime                 # UTC, ISO-8601 (Principle 9: reports
                                        # are immutable, not permanent)
  examina_version: str
  specification_version: str           # matches SPEC_VERSION.md at generation time
  bridge_version: str                  # PRISM bridge contract version used

  assessment: Assessment
  evidence: EvidenceSection
  history: HistorySection
  confidence: ConfidenceSection

  disclaimer: str                      # fixed text, always present, always
                                        # identical (see CONFIDENCE_TRANSLATION_v1.0.md)
```

A report is immutable once created: no field above is ever updated in
place after `created_at`. A change in underlying analysis produces a new
`report_id`, never a mutation of an existing one.

## Assessment

The headline section. Read first, understood in fifteen seconds.

```
VerdictLabel (enum):
  LIKELY_AUTHENTIC
  LIKELY_MANIPULATED
  LIKELY_AI_GENERATED
  AI_ASSISTED
  INSUFFICIENT_EVIDENCE
  MIXED_SIGNALS

Assessment:
  verdict: VerdictLabel
  overall_confidence_label: str        # "High" | "Medium" | "Low" | "Insufficient"
                                        # (see CONFIDENCE_TRANSLATION_v1.0.md)
  summary: TraceableString             # one to three sentences, plain language
  headline_caveats: list[str]          # short, non-traceable qualifiers, e.g.
                                        # "Based on a single embedded image only"
```

`verdict` values describe the *artifact*, never a person (Constitution
Principle 13). See `DECISION_MODEL_v1.0.md` for the complete mapping from
PRISM's top hypothesis and confidence to a `VerdictLabel`.

## EvidenceSection, EvidenceFamily, Signal

```
Signal:
  label: str                           # plain-language name, e.g.
                                        # "Recompression detected"
  description: TraceableString         # what was found and why it matters
  strength: str                        # "Strong" | "Moderate" | "Weak"
                                        # (never a bare numeric score alone)

EvidenceFamily:
  family_name: str                     # one of the six families, see
                                        # EVIDENCE_CLUSTERING_v1.0.md
  signals: list[Signal]
  combined_finding: TraceableString | None
                                        # present only when 2+ signals in
                                        # this family are correlated per
                                        # EVIDENCE_CLUSTERING_v1.0.md

EvidenceSection:
  families: list[EvidenceFamily]       # only families with at least one
                                        # signal are included
```

## HistorySection, HistoryEvent

```
HistoryEvent:
  sequence_number: int
  description: TraceableString         # e.g. "Image was likely recompressed
                                        # by a messaging app"
  is_inferred: bool                    # True if reconstructed rather than
                                        # directly observed
  event_confidence_label: str          # "High" | "Medium" | "Low"

HistorySection:
  events: list[HistoryEvent]           # chronological order
  narrative_summary: TraceableString | None
                                        # present only when 2+ events form a
                                        # coherent enough sequence to summarize
```

## ConfidenceSection

Translated, plain-language confidence, always present regardless of
verdict (Constitution Principle 3). Field names below map directly onto
the five dimensions defined in `CONFIDENCE_TRANSLATION_v1.0.md`.

```
ConfidenceSection:
  extraction_confidence_label: str     # how reliable was reading the file itself
  source_reliability_label: str        # how reliable are the underlying signals
  inference_confidence_label: str       # how reliable is the evidence derived from signals
  hypothesis_confidence_label: str     # how reliable is the leading explanation
  contradiction_penalty_note: str | None
                                        # plain-language note if contradictions
                                        # reduced confidence; None if no
                                        # contradictions were found
  overall_confidence_label: str        # duplicated from Assessment for
                                        # section-local readability
  overall_confidence_explanation: TraceableString
```

---

## Cross-Cutting Rules

- No field anywhere in this schema may hold a value drawn from the
  forbidden vocabulary in `LANGUAGE_SPEC_v1.0.md`. This is enforced at
  serialization time by the language package (`src/examina/language/`,
  introduced this phase as a stub, implemented in Phase 2+).
- Every `TraceableString` in `EvidenceSection` and `HistorySection` carries
  at least one `trace_id`. `Assessment.summary` and
  `ConfidenceSection.overall_confidence_explanation` also carry
  `trace_ids` where they summarize specific evidence.
- No field stores raw file bytes, raw filenames, or file content of any
  kind (Constitution Principle 7). `file_hash` is a one-way digest, never
  reversible to content.
