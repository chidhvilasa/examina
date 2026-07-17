"""
Report package — Digital Evidence Report generation.
See specs/REPORT_SCHEMA_v1.0.md for the complete schema.
"""

from examina.report.assembler import assemble_report, build_evidence_section
from examina.report.clustering import cluster_facts
from examina.report.confidence import translate_confidence
from examina.report.decision import determine_verdict, generate_assessment
from examina.report.history import build_history
from examina.report.schema import (
    EXAMINA_DISCLAIMER,
    Assessment,
    CertaintyEnum,
    ConfidenceDimension,
    ConfidenceLabelEnum,
    ConfidenceSection,
    EvidenceFamily,
    EvidenceSection,
    ExaminaReport,
    HistoryEvent,
    HistorySection,
    Signal,
    TraceableString,
    VerdictEnum,
)

__all__ = [
    "EXAMINA_DISCLAIMER",
    "Assessment",
    "CertaintyEnum",
    "ConfidenceDimension",
    "ConfidenceLabelEnum",
    "ConfidenceSection",
    "EvidenceFamily",
    "EvidenceSection",
    "ExaminaReport",
    "HistoryEvent",
    "HistorySection",
    "Signal",
    "TraceableString",
    "VerdictEnum",
    "assemble_report",
    "build_evidence_section",
    "build_history",
    "cluster_facts",
    "determine_verdict",
    "generate_assessment",
    "translate_confidence",
]
