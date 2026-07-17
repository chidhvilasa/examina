# ADR-0001: Bridge type schema amendment (BridgeRequest/Result field set)

Status: ACCEPTED

## Context

`BRIDGE_SPEC_v1.0.md` (FROZEN) defines `BridgeRequest`, `BridgeResult`, and
the translated types (`BridgeFact`, `BridgeContradiction`, `BridgeHypothesis`,
`BridgeTimelineEvent`, `BridgeConfidence`) with one field set. The Phase 1
implementation prompt specifies a materially different field set for the
same types — different `BridgeRequest` fields (`file_hash`/`file_type`/
`clamav_mode`/`examina_version` instead of `declared_mime_type`), a
different `BridgeResult` shape (`partial_analysis`/`partial_reason`/
`errors: list[str]` instead of a `BridgeStatus` enum with `error_detail`),
and, critically, no id fields on `BridgeFact`, `BridgeContradiction`, or
`BridgeHypothesis`.

That last gap is not cosmetic. Constitution Principle 2 ("every conclusion
is traceable") and `EVIDENCE_TRACEABILITY_v1.0.md` build the entire trace
chain — `TraceableString.trace_ids` — on `BridgeFact.fact_id`,
`BridgeContradiction.contradiction_id`, and `BridgeHypothesis.hypothesis_id`.
Implementing the new field set with no id fields would make Phase 2 (report
engine) structurally unable to satisfy Principle 2: there would be nothing
for a `trace_id` to reference.

Per `SPEC_VERSION.md`'s amendment policy, a breaking change to a frozen
spec requires a version bump and an ADR before implementation proceeds,
not a silent edit to the v1.0 file. This ADR is that record; it was
raised to, and confirmed by, the project owner before `src/examina/bridge/`
was written (see Phase 1 session, 2026-07-17).

## Decision

Adopt the Phase 1 prompt's field set for `BridgeRequest`, `BridgeFact`,
`BridgeContradiction`, `BridgeHypothesis`, `BridgeTimelineEvent`,
`BridgeConfidence`, `BridgeResult`, and `BridgeError`, as implemented in
`src/examina/bridge/types.py`, with one addition on top of the literal
prompt: restore the three id fields required for traceability —

- `BridgeFact.fact_id: str` (non-empty)
- `BridgeContradiction.contradiction_id: str` (non-empty)
- `BridgeHypothesis.hypothesis_id: str` (non-empty)

`BRIDGE_SPEC_v1.1.md` supersedes `BRIDGE_SPEC_v1.0.md` as the authoritative
field-level contract. `BRIDGE_SPEC_v1.0.md` is left in place, unmodified,
per the "v1.0.md files are never modified" rule; `v1.1.md` documents the
supersession explicitly rather than editing history.

## Consequences

- `src/examina/bridge/types.py` and all Phase 1 tests are written against
  `BRIDGE_SPEC_v1.1.md`, not `v1.0.md`.
- Phase 2 (report engine) can populate `TraceableString.trace_ids` from
  the three id fields added here, preserving Principle 2 without further
  schema surgery.
- `BridgeResult`'s error signaling model changes from a `BridgeStatus`
  enum (`COMPLETE`/`PARTIAL`/`FAILED`) to two fields,
  `partial_analysis: bool` + `partial_reason: str | None`, plus
  `errors: list[str]`. Any future code that reasons about bridge outcome
  branches on `partial_analysis`/`errors`, not a status enum — this is a
  simpler, flatter model but loses the enum's exhaustiveness-checking at
  the type level. Accepted as a reasonable tradeoff; not revisited without
  a new ADR.
- No PRISM-internal identifier is exposed by this change — `fact_id`,
  `contradiction_id`, and `hypothesis_id` remain EXAMINA-side bridge
  identifiers, consistent with `EVIDENCE_TRACEABILITY_v1.0.md`'s security
  section.

## Specification Impact

- `specs/BRIDGE_SPEC_v1.1.md` created, superseding `BRIDGE_SPEC_v1.0.md`.
- `specs/BRIDGE_SPEC_v1.0.md` unchanged (frozen files are never edited).
- No Constitution or other spec file changed; Principle 2 traceability is
  preserved, not weakened, by this amendment.
