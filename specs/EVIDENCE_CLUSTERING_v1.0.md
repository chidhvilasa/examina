# EXAMINA Evidence Clustering Specification

Specification Version: 1.0.0
Status: FROZEN

PRISM produces a flat list of Facts, Evidence, and Contradictions. A
journalist reading a report one signal at a time, in extraction order,
cannot form a coherent picture. This document defines the six fixed
**evidence families** that `EvidenceSection` (see `REPORT_SCHEMA_v1.0.md`)
groups every `BridgeFact` into, and the rule for when multiple signals in a
family are presented as a single combined finding rather than a list of
unrelated bullet points.

Every `BridgeFact` is assigned to exactly one family by
`BridgeFact.category` (set at bridge translation time, see
`BRIDGE_SPEC_v1.0.md`). A family with zero assigned facts for a given file
is omitted from the report entirely — EXAMINA never shows an empty
section.

## The Six Evidence Families

### 1. File Metadata

- **Signals it contains:** EXIF data (camera make/model, timestamps, GPS),
  PDF document properties (author, creation/modification tool,
  timestamps), DOCX core/extended properties (author, application,
  revision count).
- **Correlated?** Yes — a creation timestamp, an editing-tool identifier,
  and a modification timestamp from the same metadata block are treated as
  one correlated group, not three independent facts.
- **Combined finding rule:** When two or more metadata signals agree on a
  consistent story (e.g. capture device + capture time + no editing-tool
  signature), state it as one finding ("Metadata is internally
  consistent with a single capture event"). When they disagree (e.g. an
  editing application recorded alongside a "camera original" marker),
  state the disagreement explicitly rather than picking one signal to
  report.

### 2. Compression History

- **Signals it contains:** JPEG quantization table analysis, recompression
  signatures, quality-level estimates, double-compression artifacts.
- **Correlated?** Yes — multiple recompression indicators from the same
  image are one story about how many times, and by what kind of software,
  the file was re-saved.
- **Combined finding rule:** Two or more compression signals that agree on
  a recompression count/lineage are combined into one finding describing
  the likely re-save history (e.g. "This image shows signs of having been
  compressed at least twice, consistent with being forwarded through a
  messaging app"). Signals that only weakly or ambiguously suggest
  recompression are listed individually with "Weak" strength rather than
  folded into a confident combined statement.

### 3. Frequency Analysis

- **Signals it contains:** Frequency-domain artifacts associated with
  resizing, resampling, or certain classes of AI generation/upscaling.
- **Correlated?** Sometimes — frequency-domain signals are combined with
  each other when they consistently point to the same operation (e.g.
  upscaling), but are evaluated independently from Compression History
  signals even though both are JPEG-derived, since they answer different
  questions (recompression vs. resampling/generation).
- **Combined finding rule:** Combine only when two or more frequency
  signals agree on the same underlying operation. A single ambiguous
  frequency-domain signal is never, by itself, escalated into a
  `LIKELY_AI_GENERATED` verdict contribution — see `DECISION_MODEL_v1.0.md`.

### 4. Provenance and Origin

- **Signals it contains:** Declared vs. observed vs. derived vs. inferred
  provenance markers (per PRISM's `produced_by` convention), embedded
  device/software identifiers, cross-modal provenance contradictions.
- **Correlated?** Yes — this family exists specifically to surface
  agreement or conflict between *what the file claims about its own
  origin* and *what EXAMINA can independently observe*.
- **Combined finding rule:** Any contradiction between a declared-origin
  signal and an observed/derived signal is always surfaced as a combined
  finding, never split across two unrelated bullet points — the
  disagreement itself is the finding.

### 5. Document Structure

- **Signals it contains:** PDF object/page structure, embedded fonts,
  annotations, hidden/overlapping text, DOCX package structure (macros,
  OLE objects), tracked-change statistics.
- **Correlated?** Yes, within a document — structural anomalies (e.g.
  hidden text plus an unusual object count) are combined when they point
  to the same kind of document manipulation (e.g. content added after
  initial creation).
- **Combined finding rule:** Combine when two or more structural signals
  are consistent with the same manipulation narrative. Isolated, singular
  structural quirks (e.g. one unusual but explainable font substitution)
  are listed individually as "Weak" signals.

### 6. Embedded Content

- **Signals it contains:** Embedded images within PDFs/DOCX files (and
  their own recursive Compression History / Frequency Analysis / File
  Metadata signals, analyzed via PRISM's JPEG adapter composition),
  OCR-derived text findings, hyperlink domain statistics.
- **Correlated?** Yes — an embedded image's own internal signals are
  grouped as a sub-finding within Embedded Content rather than merged into
  the top-level document's own Compression History/Frequency Analysis
  families, since they describe a distinct embedded object with its own
  provenance.
- **Combined finding rule:** An embedded image with multiple internal
  signals is summarized as one finding about that embedded image (e.g.
  "One embedded image shows signs of being a screenshot of another
  screen"), with the embedded image's own signals available in detail on
  request via their trace IDs.

## Family Ordering

When rendered, families appear in the fixed order listed above (1 through
6). This order is chosen so metadata (cheapest to understand) comes first
and embedded/recursive content (most complex) comes last. The order never
changes based on which family has the strongest signal — EXAMINA does not
"lead with the scariest finding."
