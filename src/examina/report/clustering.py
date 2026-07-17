"""
Evidence clustering — groups BridgeFacts into the six fixed evidence
families defined in specs/EVIDENCE_CLUSTERING_v1.0.md.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from examina.bridge.types import BridgeFact
from examina.report.schema import EvidenceFamily, Signal, TraceableString

logger = logging.getLogger(__name__)

# Assignment priority order (highest first). A fact is assigned to the
# first family, in this order, whose membership predicate it satisfies.
_ASSIGNMENT_ORDER: list[str] = [
    "embedded",
    "provenance",
    "metadata",
    "compression",
    "frequency",
    "structure",
]

# Display/output order (fixed per EVIDENCE_CLUSTERING_v1.0.md's Family
# Ordering section), independent of assignment priority.
_DISPLAY_ORDER: list[str] = [
    "metadata",
    "compression",
    "frequency",
    "provenance",
    "structure",
    "embedded",
]

_FAMILY_NAMES: dict[str, str] = {
    "metadata": "File Metadata",
    "compression": "Compression History",
    "frequency": "Frequency Analysis",
    "provenance": "Provenance and Origin",
    "structure": "Document Structure",
    "embedded": "Embedded Content",
}

_FAMILY_CORRELATED: dict[str, bool] = {
    "metadata": True,
    "compression": True,
    "frequency": True,
    "provenance": False,
    "structure": True,
    "embedded": False,
}

_COMPRESSION_KEYWORDS = ("compression", "encoding", "recompressed", "quantization")
_STRUCTURE_ANOMALY_KEYWORDS = ("anomaly", "inconsistent", "hidden", "redaction", "macro")


def _matches_embedded(fact: BridgeFact) -> bool:
    statement = fact.statement.lower()
    return fact.provenance_source_type == "derived" and (
        "embedded" in statement or "cross-modal" in statement
    )


def _matches_provenance(fact: BridgeFact) -> bool:
    return fact.fact_type == "PROVENANCE" and fact.provenance_source_type in (
        "observed",
        "derived",
    )


def _matches_metadata(fact: BridgeFact) -> bool:
    return fact.fact_type == "PROVENANCE" and fact.provenance_source_type == "declared"


def _matches_compression(fact: BridgeFact) -> bool:
    if fact.fact_type != "STRUCTURAL":
        return False
    statement = fact.statement.lower()
    return any(keyword in statement for keyword in _COMPRESSION_KEYWORDS)


def _matches_frequency(fact: BridgeFact) -> bool:
    return fact.fact_type == "STATISTICAL"


def _matches_structure(fact: BridgeFact) -> bool:
    return fact.fact_type == "STRUCTURAL"


_PREDICATES: dict[str, Callable[[BridgeFact], bool]] = {
    "embedded": _matches_embedded,
    "provenance": _matches_provenance,
    "metadata": _matches_metadata,
    "compression": _matches_compression,
    "frequency": _matches_frequency,
    "structure": _matches_structure,
}


def _assign_facts(facts: list[BridgeFact]) -> dict[str, list[BridgeFact]]:
    buckets: dict[str, list[BridgeFact]] = {family_id: [] for family_id in _DISPLAY_ORDER}
    for fact in facts:
        assigned = False
        for family_id in _ASSIGNMENT_ORDER:
            if _PREDICATES[family_id](fact):
                buckets[family_id].append(fact)
                assigned = True
                break
        if not assigned:
            logger.warning(
                "Fact %s (fact_type=%s, provenance_source_type=%s) did not match "
                "any evidence family and was dropped.",
                fact.fact_id,
                fact.fact_type,
                fact.provenance_source_type,
            )
    return buckets


def _metadata_finding(facts: list[BridgeFact]) -> str | None:
    if not facts:
        return None
    if any("metadata" in f.statement.lower() or "claims" in f.statement.lower() for f in facts):
        return "File contains declared metadata establishing claimed origin."
    return "File contains declared metadata, though it does not explicitly state origin claims."


def _compression_finding(facts: list[BridgeFact]) -> str | None:
    if not facts:
        return None
    if any("double" in f.statement.lower() or "re-encod" in f.statement.lower() for f in facts):
        return "File shows evidence of re-encoding after initial creation."
    return "Compression characteristics appear consistent with single-pass encoding."


def _frequency_finding(facts: list[BridgeFact]) -> str | None:
    if not facts:
        return None
    if any("flat" in f.statement.lower() or "generative" in f.statement.lower() for f in facts):
        finding = (
            "Frequency distribution shows characteristics inconsistent "
            "with typical camera-captured content."
        )
    else:
        finding = "Frequency characteristics are consistent with camera capture."
    return (
        finding
        + " Note: frequency analysis has limited reliability and should not be "
        "the sole basis for any conclusion."
    )


def _provenance_finding(facts: list[BridgeFact]) -> str | None:
    if not facts:
        return None
    if any("c2pa" in f.statement.lower() or "credential" in f.statement.lower() for f in facts):
        return "File carries provenance credentials."
    if any("camera" in f.statement.lower() or "captured" in f.statement.lower() for f in facts):
        return "File claims camera capture origin — not cryptographically verified."
    return "No verifiable origin credentials detected."


def _structure_finding(facts: list[BridgeFact]) -> str | None:
    if not facts:
        return None
    statement_text = " ".join(f.statement.lower() for f in facts)
    if any(keyword in statement_text for keyword in _STRUCTURE_ANOMALY_KEYWORDS):
        return "Document structure contains signals that warrant attention."
    return "Document structure shows no anomalies."


def _embedded_finding(facts: list[BridgeFact]) -> str | None:
    if not facts:
        return None
    if any("conflict" in f.statement.lower() or "contradict" in f.statement.lower() for f in facts):
        return "The document container and its embedded content contain conflicting signals."
    return "Embedded content is consistent with document-level signals."


_FINDING_BUILDERS: dict[str, Callable[[list[BridgeFact]], str | None]] = {
    "metadata": _metadata_finding,
    "compression": _compression_finding,
    "frequency": _frequency_finding,
    "provenance": _provenance_finding,
    "structure": _structure_finding,
    "embedded": _embedded_finding,
}


def _build_signal(family_id: str, index: int, fact: BridgeFact) -> Signal:
    statement = TraceableString(
        text=fact.statement,
        trace_ids=[fact.fact_id],
        generated=False,
    ).checked()
    return Signal(
        signal_id=f"{family_id}_{index:03d}",
        statement=statement,
        direction="NEUTRAL",
        extraction_confidence=fact.extraction_confidence,
        source_reliability=fact.source_reliability,
        produced_by=fact.extractor,
        affected_region=None,
        raw_value=fact.raw_value,
    )


def cluster_facts(facts: list[BridgeFact]) -> list[EvidenceFamily]:
    buckets = _assign_facts(facts)
    families: list[EvidenceFamily] = []

    for family_id in _DISPLAY_ORDER:
        family_facts = buckets[family_id]
        finding_text = _FINDING_BUILDERS[family_id](family_facts)
        if finding_text is None or not family_facts:
            continue

        signals = [
            _build_signal(family_id, index, fact) for index, fact in enumerate(family_facts)
        ]
        family_finding = TraceableString(
            text=finding_text,
            trace_ids=[fact.fact_id for fact in family_facts],
            generated=True,
        ).checked()

        families.append(
            EvidenceFamily(
                family_id=family_id,
                family_name=_FAMILY_NAMES[family_id],
                family_finding=family_finding,
                signals=signals,
                correlated=_FAMILY_CORRELATED[family_id],
            )
        )

    return families
