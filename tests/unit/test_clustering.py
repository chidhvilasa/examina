"""Tests for src/examina/report/clustering.py — see specs/EVIDENCE_CLUSTERING_v1.0.md."""

from __future__ import annotations

from typing import Any

from examina.bridge.types import BridgeFact
from examina.language.guard import check_language
from examina.report.clustering import cluster_facts


def _fact(
    fact_id: str,
    statement: str,
    fact_type: str,
    provenance_source_type: str,
    extraction_confidence: float = 0.8,
    source_reliability: float = 0.8,
) -> BridgeFact:
    return BridgeFact(
        fact_id=fact_id,
        statement=statement,
        fact_type=fact_type,  # type: ignore[arg-type]
        provenance_source_type=provenance_source_type,  # type: ignore[arg-type]
        extractor="stub-extractor:1.0",
        extraction_confidence=extraction_confidence,
        source_reliability=source_reliability,
        raw_value={},
    )


METADATA_FACT = _fact(
    "fact-metadata",
    "This file declares creation metadata consistent with its format.",
    "PROVENANCE",
    "declared",
)
COMPRESSION_FACT = _fact(
    "fact-compression",
    "This file shows signs of double compression artifacts.",
    "STRUCTURAL",
    "observed",
)
FREQUENCY_FACT = _fact(
    "fact-frequency",
    "Frequency distribution appears flat across bands.",
    "STATISTICAL",
    "derived",
)
PROVENANCE_FACT = _fact(
    "fact-provenance",
    "File carries a C2PA credential naming the capture device.",
    "PROVENANCE",
    "observed",
)
STRUCTURE_FACT = _fact(
    "fact-structure",
    "Document object structure appears unremarkable.",
    "STRUCTURAL",
    "observed",
)
EMBEDDED_FACT = _fact(
    "fact-embedded",
    "An embedded image was found with conflicting cross-modal signals.",
    "STRUCTURAL",
    "derived",
)


def _families_by_id(facts: list[BridgeFact]) -> dict[str, Any]:
    return {family.family_id: family for family in cluster_facts(facts)}


class TestFamilyMembership:
    def test_provenance_declared_in_metadata_family(self) -> None:
        families = _families_by_id([METADATA_FACT])
        assert "metadata" in families
        assert families["metadata"].signals[0].statement.trace_ids == ["fact-metadata"]

    def test_structural_compression_keyword_in_compression_family(self) -> None:
        families = _families_by_id([COMPRESSION_FACT])
        assert "compression" in families

    def test_statistical_fact_in_frequency_family(self) -> None:
        families = _families_by_id([FREQUENCY_FACT])
        assert "frequency" in families

    def test_provenance_observed_in_provenance_family(self) -> None:
        families = _families_by_id([PROVENANCE_FACT])
        assert "provenance" in families

    def test_structural_non_compression_in_structure_family(self) -> None:
        families = _families_by_id([STRUCTURE_FACT])
        assert "structure" in families

    def test_derived_embedded_keyword_in_embedded_family(self) -> None:
        families = _families_by_id([EMBEDDED_FACT])
        assert "embedded" in families


class TestAssignment:
    def test_each_fact_assigned_to_exactly_one_family(self) -> None:
        facts = [
            METADATA_FACT,
            COMPRESSION_FACT,
            FREQUENCY_FACT,
            PROVENANCE_FACT,
            STRUCTURE_FACT,
            EMBEDDED_FACT,
        ]
        families = cluster_facts(facts)
        seen: dict[str, int] = {}
        for family in families:
            for signal in family.signals:
                fact_id = signal.statement.trace_ids[0]
                seen[fact_id] = seen.get(fact_id, 0) + 1
        for fact in facts:
            assert seen.get(fact.fact_id) == 1

    def test_empty_fact_list_returns_empty_family_list(self) -> None:
        assert cluster_facts([]) == []

    def test_family_with_no_facts_not_returned(self) -> None:
        families = _families_by_id([METADATA_FACT])
        assert "compression" not in families
        assert "frequency" not in families
        assert "provenance" not in families
        assert "structure" not in families
        assert "embedded" not in families

    def test_unmatched_fact_is_dropped(self) -> None:
        inferred_fact = _fact(
            "fact-inferred",
            "This provenance signal could not be classified.",
            "PROVENANCE",
            "inferred",
        )
        families = cluster_facts([inferred_fact])
        assert families == []


class TestFrequencyReliabilityNote:
    def test_frequency_family_always_appends_reliability_note(self) -> None:
        families = _families_by_id([FREQUENCY_FACT])
        assert "limited reliability" in families["frequency"].family_finding.text


class TestLanguageCompliance:
    def test_cluster_facts_output_passes_language_check(self) -> None:
        facts = [
            METADATA_FACT,
            COMPRESSION_FACT,
            FREQUENCY_FACT,
            PROVENANCE_FACT,
            STRUCTURE_FACT,
            EMBEDDED_FACT,
        ]
        families = cluster_facts(facts)
        for family in families:
            check_language(family.family_finding.text, context="test")
            for signal in family.signals:
                check_language(signal.statement.text, context="test")


class TestCorrelatedFlags:
    def test_correlated_true_families(self) -> None:
        families = _families_by_id(
            [METADATA_FACT, COMPRESSION_FACT, FREQUENCY_FACT, STRUCTURE_FACT]
        )
        assert families["metadata"].correlated is True
        assert families["compression"].correlated is True
        assert families["frequency"].correlated is True
        assert families["structure"].correlated is True

    def test_correlated_false_families(self) -> None:
        families = _families_by_id([PROVENANCE_FACT, EMBEDDED_FACT])
        assert families["provenance"].correlated is False
        assert families["embedded"].correlated is False


class TestFindingBranches:
    def test_metadata_without_keyword_uses_fallback_finding(self) -> None:
        fact = _fact(
            "fact-m2", "Origin details recorded by capture application.", "PROVENANCE", "declared"
        )
        families = _families_by_id([fact])
        assert "does not explicitly state" in families["metadata"].family_finding.text

    def test_compression_single_pass_finding(self) -> None:
        fact = _fact(
            "fact-c2",
            "Compression pattern matches a single encoding pass.",
            "STRUCTURAL",
            "observed",
        )
        families = _families_by_id([fact])
        assert "single-pass encoding" in families["compression"].family_finding.text

    def test_frequency_camera_consistent_finding(self) -> None:
        fact = _fact(
            "fact-f2", "Frequency pattern is typical of sensor noise.", "STATISTICAL", "observed"
        )
        families = _families_by_id([fact])
        assert "consistent with camera capture" in families["frequency"].family_finding.text

    def test_provenance_camera_claim_finding(self) -> None:
        fact = _fact(
            "fact-p2", "File claims it was captured on a camera device.", "PROVENANCE", "observed"
        )
        families = _families_by_id([fact])
        assert "not cryptographically verified" in families["provenance"].family_finding.text

    def test_provenance_no_credentials_finding(self) -> None:
        fact = _fact(
            "fact-p3", "No independent origin markers were located.", "PROVENANCE", "observed"
        )
        families = _families_by_id([fact])
        assert "No verifiable origin credentials" in families["provenance"].family_finding.text

    def test_structure_anomaly_finding(self) -> None:
        fact = _fact("fact-s2", "Document contains a hidden text layer.", "STRUCTURAL", "observed")
        families = _families_by_id([fact])
        assert "warrant attention" in families["structure"].family_finding.text

    def test_embedded_consistent_finding(self) -> None:
        fact = _fact(
            "fact-e2", "Embedded image signals align with the document.", "STRUCTURAL", "derived"
        )
        families = _families_by_id([fact])
        assert "consistent with document-level signals" in families["embedded"].family_finding.text
