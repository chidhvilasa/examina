"""
Report assembler — orchestrates clustering, confidence translation, the
decision model, and history reconstruction into a single ExaminaReport.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

from examina.bridge.types import BridgeResult
from examina.report.clustering import cluster_facts
from examina.report.confidence import translate_confidence
from examina.report.decision import determine_verdict, generate_assessment
from examina.report.history import build_history
from examina.report.schema import EvidenceFamily, EvidenceSection, ExaminaReport


def build_evidence_section(
    families: list[EvidenceFamily],
    bridge_result: BridgeResult,
) -> EvidenceSection:
    del bridge_result  # signal counts are derived entirely from clustered families

    total_signals = 0
    supporting = 0
    contradicting = 0
    neutral = 0
    for family in families:
        for signal in family.signals:
            total_signals += 1
            if signal.direction == "SUPPORTS":
                supporting += 1
            elif signal.direction == "CONTRADICTS":
                contradicting += 1
            else:
                neutral += 1

    return EvidenceSection(
        families=families,
        total_signals=total_signals,
        signals_supporting_verdict=supporting,
        signals_contradicting_verdict=contradicting,
        signals_neutral=neutral,
    )


def assemble_report(
    bridge_result: BridgeResult,
    file_hash: str,
    file_type: Literal["JPEG", "PNG", "WEBP", "PDF"],
    file_size_bytes: int,
    examina_version: str,
) -> ExaminaReport:
    families = cluster_facts(bridge_result.facts)
    evidence_section = build_evidence_section(families, bridge_result)

    top_hypothesis = next((h for h in bridge_result.hypotheses if h.rank == 1), None)
    top_hypothesis_confidence = top_hypothesis.confidence if top_hypothesis is not None else 0.0

    confidence_section = translate_confidence(
        bridge_result.reconstruction_confidence,
        bridge_result.facts,
        evidence_section,
        top_hypothesis_confidence,
    )

    verdict, confidence_label = determine_verdict(
        bridge_result.hypotheses,
        bridge_result.reconstruction_confidence.overall,
    )

    all_signal_ids = [signal.signal_id for family in families for signal in family.signals]

    assessment = generate_assessment(
        verdict,
        confidence_label,
        bridge_result.hypotheses,
        bridge_result.contradictions,
        all_signal_ids,
    )

    history = build_history(bridge_result.timeline, bridge_result.facts)

    if bridge_result.partial_analysis:
        confidence_section.limitations.append(
            f"Analysis is incomplete: {bridge_result.partial_reason}"
        )

    created_at = datetime.now(UTC)
    expires_at = created_at + timedelta(hours=24)

    return ExaminaReport(
        file_hash=file_hash,
        file_name_sanitized=str(uuid4()),
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        created_at=created_at,
        expires_at=expires_at,
        examina_version=examina_version,
        prism_version=bridge_result.prism_version,
        rule_set_version=bridge_result.rule_set_version,
        assessment=assessment,
        evidence=evidence_section,
        history=history,
        confidence=confidence_section,
    )
