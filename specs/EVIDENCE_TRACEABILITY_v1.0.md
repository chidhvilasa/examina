# EXAMINA Evidence Traceability Specification

Specification Version: 1.0.0
Status: FROZEN

Constitution Principle 2 requires every conclusion in a Digital Evidence
Report to be traceable to the specific underlying signal that produced it.
This document defines the mechanics of that traceability: the full chain
from a report sentence down to PRISM's own reasoning output, the
`TraceableString` type's contract, the implementation rule every
report-generating module must follow, and the security implication of
carrying trace data through the system.

## The Full Traceability Chain

```
ExaminaReport
  └─ Section (Assessment / EvidenceSection / HistorySection / ConfidenceSection)
       └─ TraceableString.trace_ids
            └─ BridgeFact.fact_id | BridgeContradiction.contradiction_id
               | BridgeHypothesis.hypothesis_id
                 └─ (bridge translation, BRIDGE_SPEC_v1.0.md)
                    └─ PRISM Fact.id | Contradiction rule_id | Hypothesis
                       (PRISM-internal, never exposed directly to EXAMINA
                        callers — see BRIDGE_SPEC_v1.0.md's one-way boundary
                        rules)
```

A trace ID is meaningful at every link in this chain: given a
`trace_id` from a rendered report, EXAMINA can always resolve it back to
the exact `BridgeFact`/`BridgeContradiction`/`BridgeHypothesis` that
produced it, and from there (internally, never exposed to the end user) to
the PRISM-side identifier the bridge translated it from.

Report → Family → Signal → BridgeFact → PRISM, concretely:

1. **Report** — the top-level `ExaminaReport`, identified by `report_id`.
2. **Family** — an `EvidenceFamily` within `EvidenceSection` (see
   `EVIDENCE_CLUSTERING_v1.0.md`), one of the six fixed families.
3. **Signal** — a single `Signal` within that family, whose
   `description: TraceableString` carries the trace.
4. **BridgeFact** — one or more `BridgeFact` (or `BridgeContradiction` /
   `BridgeHypothesis`) records identified by the `Signal`'s `trace_ids`.
5. **PRISM** — the original PRISM-side Fact/Contradiction/Hypothesis the
   bridge translated, resolvable only internally (via the bridge's own
   bookkeeping), never surfaced as a raw PRISM identifier to an EXAMINA API
   consumer.

## TraceableString Type Definition

Restated from `REPORT_SCHEMA_v1.0.md` for completeness:

```
TraceableString:
  text: str                  # the plain-language sentence shown to the user
  trace_ids: list[str]       # non-empty for any TraceableString that
                              # asserts a finding
```

`trace_ids` values are EXAMINA-side bridge identifiers (`BridgeFact.
fact_id`, `BridgeContradiction.contradiction_id`,
`BridgeHypothesis.hypothesis_id`) — never PRISM-internal UUIDs exposed
directly, and never derived from or containing file content.

## Implementation Rule

Every function in `src/examina/report/` (Phase 2) that constructs a
`TraceableString` intended for `EvidenceSection` or `HistorySection` must
supply at least one `trace_id`. This is enforced in two layers:

1. **Type-level convention** — a `TraceableString` constructor helper
   (introduced in Phase 2) that raises rather than silently accepting an
   empty `trace_ids` list for sections where traceability is mandatory.
2. **Test-level enforcement** — Phase 2's test suite includes an explicit
   check, run against every generated report fixture, that no
   `EvidenceSection`/`HistorySection` `TraceableString` has an empty
   `trace_ids` list.

`Assessment.headline_caveats` (plain `list[str]`, not `TraceableString`)
and the fixed `disclaimer` text are exempt from this rule by design — they
are qualifiers and boilerplate, not findings, and do not assert anything
that needs a trace.

## Security Implication

Trace IDs exist to make findings auditable, not to leak information about
the uploaded file's content.

- A `trace_id` is an opaque identifier (e.g. a UUID or short hash of an
  internal bridge record), never a substring of file content, never a
  filename, and never a value from which file content could be
  reconstructed.
- Resolving a `trace_id` back to its underlying `BridgeFact` detail is
  available within the report itself (e.g. an expandable detail view) —
  it is not a mechanism for reaching further into PRISM or the original
  file than the report already discloses.
- Because trace IDs are opaque and scoped to a single `report_id`, they
  carry no information across reports and cannot be used to correlate two
  different users' uploads.
