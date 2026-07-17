# EXAMINA Bridge Specification

Specification Version: 1.1.0
Status: FROZEN
Supersedes: BRIDGE_SPEC_v1.0.md (left unmodified per SPEC_VERSION.md policy)
Amendment Record: docs/adr/ADR-0001-bridge-type-schema-amendment.md

The bridge is the single, one-way boundary between EXAMINA and PRISM
(Constitution Principle 10). This document defines the complete interface
contract implemented in Phase 1 (`src/examina/bridge/`). No other EXAMINA
module may talk to PRISM except through the types and client interface
defined here. This version replaces the field-level contract in
`BRIDGE_SPEC_v1.0.md` in full; see ADR-0001 for why the field set changed.

## Boundary Statement

EXAMINA depends on PRISM. PRISM does not depend on EXAMINA, does not know
EXAMINA exists, and is never modified to accommodate EXAMINA's needs — any
gap is closed on the EXAMINA side of the bridge, in translation code, never
by reaching into PRISM internals.

EXAMINA never imports a PRISM internal module directly outside the bridge
package. Every PRISM concept that crosses into EXAMINA is represented by
an EXAMINA-native `Bridge*` type defined below — never by PRISM's own
Fact/Evidence/Contradiction/Hypothesis schema names.

## Types (Pydantic v2 models, `src/examina/bridge/types.py`)

```
BridgeRequest:
  file_bytes: bytes
  file_hash: str                 # exactly 64 lowercase hex chars, ^[0-9a-f]{64}$
  file_type: Literal["JPEG", "PNG", "WEBP", "PDF"]
  request_id: UUID               # auto-generated, EXAMINA-side correlation ID
  clamav_mode: Literal["enforce", "skip"] = "skip"
  examina_version: str

BridgeFact:
  fact_id: str                   # non-empty, EXAMINA-stable bridge identifier;
                                  # target of TraceableString.trace_ids
                                  # (EVIDENCE_TRACEABILITY_v1.0.md)
  statement: str                 # non-empty
  fact_type: Literal["STRUCTURAL", "TEMPORAL", "STATISTICAL",
                      "SEMANTIC", "PROVENANCE"]
  provenance_source_type: Literal["declared", "observed", "derived", "inferred"]
  extractor: str                 # non-empty, format "name:version"
  extraction_confidence: float   # [0.0, 1.0]
  source_reliability: float      # [0.0, 1.0]
  raw_value: dict[str, Any]

BridgeContradiction:
  contradiction_id: str          # non-empty, EXAMINA-stable bridge identifier
  severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
  explanation: str                # non-empty, plain-language, never a raw rule_id
  confidence_impact: float        # [-1.0, 0.0], always <= 0
  top_resolution: str              # non-empty

BridgeHypothesis:
  hypothesis_id: str              # non-empty, EXAMINA-stable bridge identifier
  description: str                # non-empty
  confidence: float               # [0.0, 1.0]
  rank: int                       # >= 1; rank 1 = highest confidence

BridgeTimelineEvent:
  sequence: int                   # >= 1
  description: str                # non-empty
  confidence: float                # [0.0, 1.0]

BridgeConfidence:
  overall: float                            # [0.0, 1.0]
  penalty_from_contradictions: float         # [0.0, 1.0]
  unresolved_contradictions: int             # >= 0
  active_hypotheses: int                     # >= 0

BridgeResult:
  request_id: UUID                # matches BridgeRequest.request_id
  bridge_version: str              # non-empty, format "bridge:X.Y"
  prism_version: str                # non-empty
  rule_set_version: str              # non-empty
  extractor_versions: dict[str, str]
  processing_time_ms: int            # >= 0
  facts: list[BridgeFact] = []
  contradictions: list[BridgeContradiction] = []
  hypotheses: list[BridgeHypothesis] = []
  timeline: list[BridgeTimelineEvent] = []
  reconstruction_confidence: BridgeConfidence
  errors: list[str] = []
  partial_analysis: bool = False
  partial_reason: str | None = None
  # partial_analysis == True  <=> partial_reason is a non-empty string
  # hypotheses must be sorted by rank ascending (rank 1 first)

BridgeError(Exception):
  code: Literal["BRIDGE_UNAVAILABLE", "VERSION_MISMATCH", "ANALYSIS_TIMEOUT",
                "PRISM_ERROR", "INVALID_RESPONSE"]
  message: str                     # never raw PRISM internal error text
  request_id: UUID | None
```

## Traceability

`BridgeFact.fact_id`, `BridgeContradiction.contradiction_id`, and
`BridgeHypothesis.hypothesis_id` are the identifiers
`TraceableString.trace_ids` (Phase 2, `REPORT_SCHEMA_v1.0.md`,
`EVIDENCE_TRACEABILITY_v1.0.md`) reference. They are opaque EXAMINA-side
bridge identifiers — never a PRISM-internal UUID exposed directly, never
derived from or containing file content (Constitution Principle 2,
`EVIDENCE_TRACEABILITY_v1.0.md`'s security section).

## Versioning Policy

- `bridge_version` follows semantic versioning independently of both
  EXAMINA's own version and PRISM's version.
- A further breaking change to any `Bridge*` type requires a
  `bridge_version` major bump and a corresponding `BRIDGE_SPEC_v1.2.md` (or
  v2.0.0) plus an ADR — never a silent edit to this file.
- Every `BridgeResult` embeds the `bridge_version` that produced it so a
  stored `ExaminaReport` remains interpretable even after the bridge
  contract evolves (Constitution Principle 9).

## Error Handling

- `BridgeClient.analyze` never raises an unhandled exception for an
  expected failure mode (PRISM unreachable, PRISM timeout, PRISM returning
  a malformed result, a bridge version mismatch). Each such case is caught
  at the bridge boundary and re-raised as `BridgeError` with the matching
  `code`.
- Genuinely unexpected errors (a bug) are logged internally with full
  detail and still surfaced to the caller as `BridgeError(code="PRISM_ERROR")`
  with a generic, non-leaking `message` — never a raw stack trace or PRISM
  internal error string (Constitution Principle 6).
- No bare `except:` or `except Exception: pass`. Every catch clause names
  the exception type(s) it expects and either translates them into a
  `BridgeError` or re-raises after logging.

## BridgeClient Interface

```
class BridgeClient(abc.ABC):
    @abstractmethod
    async def analyze(self, request: BridgeRequest) -> BridgeResult: ...
    @abstractmethod
    async def health_check(self) -> bool: ...
    @abstractmethod
    def get_bridge_version(self) -> str: ...
    def validate_result(self, result: BridgeResult) -> None: ...  # concrete
```

Two implementations satisfy this interface, both introduced in Phase 1:

- **`LocalBridgeClient`** — in development, a stub returning placeholder
  data (Phase 1); replaced with a real in-process/subprocess call into
  PRISM's public entry point no earlier than Phase 2.
- **`RemoteBridgeClient`** — in production, a stub raising
  `BridgeError(code="BRIDGE_UNAVAILABLE")` (Phase 1); replaced with a real
  HTTP call to `PRISM_BRIDGE_URL`, authenticated with `PRISM_BRIDGE_TOKEN`,
  no earlier than the phase that needs a live remote PRISM deployment.

Both implementations return the exact same `BridgeResult` shape. Calling
code (report generation, Phase 2) never branches on which client
implementation is in use.

## One-Way Boundary Enforcement Rules

- PRISM never receives a callback, webhook, or any other channel to push
  data into EXAMINA. All communication is EXAMINA calling PRISM and PRISM
  returning a result to that call.
- PRISM is never configured, extended, or instructed by EXAMINA to change
  its own behavior per-request beyond the contents of `BridgeRequest`.
- Any EXAMINA capability that would require PRISM to change its public
  interface is treated as a PRISM feature request, tracked outside this
  repository, never worked around inside the bridge package.
