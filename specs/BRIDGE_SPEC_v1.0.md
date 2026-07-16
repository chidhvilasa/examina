# EXAMINA Bridge Specification

Specification Version: 1.0.0
Status: FROZEN

The bridge is the single, one-way boundary between EXAMINA and PRISM
(Constitution Principle 10). This document defines the complete interface
contract implemented in Phase 1 (`src/examina/bridge/`). No other EXAMINA
module may talk to PRISM except through the types and client interface
defined here.

## Boundary Statement

EXAMINA depends on PRISM. PRISM does not depend on EXAMINA, does not know
EXAMINA exists, and is never modified to accommodate EXAMINA's needs — any
gap is closed on the EXAMINA side of the bridge, in translation code, never
by reaching into PRISM internals.

EXAMINA never imports a `prism.*` internal module directly outside the
bridge package. Every PRISM concept that crosses into EXAMINA is
represented by an EXAMINA-native `Bridge*` type defined below — never by
PRISM's own `Fact`/`Evidence`/`Contradiction`/`Hypothesis`/`PRISMReport`
Pydantic models.

## BridgeRequest (input contract)

What EXAMINA sends to PRISM to request an analysis.

```
BridgeRequest:
  file_bytes: bytes             # the uploaded file, held in memory only
  declared_mime_type: str       # as detected by EXAMINA's upload pipeline
                                 # (Phase 3), not trusted blindly by PRISM
  request_id: str               # EXAMINA-side correlation ID, never derived
                                 # from file content
```

`BridgeRequest` is constructed only after EXAMINA's own upload security
pipeline (Phase 3, see `FAILURE_SPEC_v1.0.md`) has validated the file.
The bridge does not re-implement upload security; it assumes its caller
already enforced it.

## BridgeResult (output contract)

What PRISM (via the bridge client) returns to EXAMINA.

```
BridgeStatus (enum):
  COMPLETE
  PARTIAL              # analysis completed with some sections degraded
                        # or omitted (see FAILURE_SPEC_v1.0.md)
  FAILED               # analysis could not be completed at all

BridgeResult:
  status: BridgeStatus
  request_id: str
  file_hash: str
  facts: list[BridgeFact]
  contradictions: list[BridgeContradiction]
  hypotheses: list[BridgeHypothesis]
  timeline: list[BridgeTimelineEvent]
  confidence: BridgeConfidence
  bridge_version: str
  error_detail: str | None            # populated when status != COMPLETE;
                                       # plain-language, never raw stack traces
```

## Translated Types

Every type below is an EXAMINA-native structure populated by translating
the corresponding PRISM output (`Fact`, `Contradiction`, `Hypothesis`,
`TimelineEvent`, `ReconstructionConfidence`) at the bridge boundary. Field
names intentionally diverge from PRISM's own schema names where doing so
makes the EXAMINA-side contract clearer and more stable against PRISM's
internal schema evolving.

```
BridgeFact:
  fact_id: str                  # EXAMINA-stable ID, derived from PRISM's
                                 # Fact.id but namespaced to the bridge
  statement: str                # plain restatement of the PRISM Fact
  category: str                 # coarse category used for evidence
                                 # clustering (see EVIDENCE_CLUSTERING_v1.0.md)
  extraction_confidence: float  # 0.0-1.0, copied from PRISM Fact
  source_reliability: float     # 0.0-1.0, copied from PRISM Fact

BridgeContradiction:
  contradiction_id: str
  fact_ids: tuple[str, str]     # the two BridgeFact ids in conflict
  severity: str                 # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  explanation: str               # plain-language, never the raw rule_id
  confidence_delta: float        # negative; how much this reduced confidence

BridgeHypothesis:
  hypothesis_id: str
  description: str
  confidence: float             # 0.0-1.0
  supporting_fact_ids: list[str]
  is_top_hypothesis: bool       # true for exactly one hypothesis per result,
                                 # unless hypotheses is empty

BridgeTimelineEvent:
  sequence_number: int
  description: str
  is_inferred: bool
  hypothesis_id: str | None
  confidence: float

BridgeConfidence:
  extraction_confidence: float   # averaged across BridgeFacts
  source_reliability: float      # averaged across BridgeFacts
  inference_confidence: float    # averaged across derived evidence
  hypothesis_confidence: float   # top hypothesis's confidence, 0.0 if none
  contradiction_penalty: float   # 0.0-1.0, from PRISM's reconstruction confidence
  overall: float                 # 0.0-1.0, final reconstruction confidence
```

## Versioning Policy

- `bridge_version` follows semantic versioning independently of both
  EXAMINA's own version and PRISM's version.
- A breaking change to any `Bridge*` type (removing a field, changing a
  field's meaning, changing an enum's values) requires a `bridge_version`
  major bump and a corresponding `BRIDGE_SPEC_v1.1.md` (or v2.0.0) —
  never a silent edit to this file.
- Every `BridgeResult` embeds the `bridge_version` that produced it so a
  stored `ExaminaReport` remains interpretable even after the bridge
  contract evolves (Constitution Principle 9).

## Error Handling

- The bridge client never raises an unhandled exception to its caller for
  an expected failure mode (PRISM unreachable, PRISM timeout, PRISM
  returning a malformed result). Each such case is caught at the bridge
  boundary and translated into a `BridgeResult` with `status=FAILED` and a
  plain-language `error_detail`.
- Genuinely unexpected errors (a bug) are logged with full detail
  internally and still surfaced to the caller as a `FAILED` result with a
  generic, non-leaking `error_detail` — never a raw stack trace or PRISM
  internal error string (Constitution Principle 6: no silent failures, but
  also never a raw internal leak to the user).
- No bare `except:` or `except Exception: pass`. Every catch clause names
  the exception type(s) it expects and either translates them into a
  `BridgeResult` or re-raises after logging.

## BridgeClient Interface

```
class BridgeClient(Protocol):
    def analyze(self, request: BridgeRequest) -> BridgeResult: ...
```

Two implementations satisfy this interface, both introduced in Phase 1:

- **`LocalBridgeClient`** — invokes PRISM's reasoning pipeline in-process
  (direct Python call into PRISM's public `run_pipeline`-style entry
  point, never into PRISM's internal stage modules). Used in development
  and in any deployment where PRISM runs in the same process/host as
  EXAMINA.
- **`RemoteBridgeClient`** — invokes PRISM over HTTP, against
  `PRISM_BRIDGE_URL` (see `.env.example`), authenticated with
  `PRISM_BRIDGE_TOKEN`. Used when PRISM is operated as an independently
  deployed service.

Both implementations return the exact same `BridgeResult` shape. Calling
code (report generation, Phase 2) never branches on which client
implementation is in use — that is the entire point of the abstraction.

## One-Way Boundary Enforcement Rules

- PRISM never receives a callback, webhook, or any other channel to push
  data into EXAMINA. All communication is EXAMINA calling PRISM and PRISM
  returning a result to that call.
- PRISM is never configured, extended, or instructed by EXAMINA to change
  its own behavior per-request beyond the contents of `BridgeRequest`
  (i.e. no "analysis mode" flags that reach into PRISM's rule sets or
  reasoning configuration from the EXAMINA side).
- Any EXAMINA capability that would require PRISM to change its public
  interface is treated as a PRISM feature request, tracked outside this
  repository, never worked around inside the bridge package.
