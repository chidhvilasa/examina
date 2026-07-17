"""
Report schema — typed structure of a Digital Evidence Report.

See specs/REPORT_SCHEMA_v1.0.md for the frozen contract this module
implements. Field names below follow the Phase 2 implementation prompt,
which elaborates the spec's pseudo-syntax into concrete Pydantic v2
models.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from examina.language.guard import check_language

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

EXAMINA_DISCLAIMER: str = (
    "This report represents a probabilistic analysis, not a "
    "definitive forensic conclusion. Results should be evaluated "
    "alongside other verification methods."
)


class TraceableString(BaseModel):
    text: str = Field(min_length=1)
    trace_ids: list[str] = Field(default_factory=list)
    generated: bool

    def checked(self) -> TraceableString:
        check_language(self.text, context="report string")
        return self


class VerdictEnum(StrEnum):
    LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"
    LIKELY_MANIPULATED = "LIKELY_MANIPULATED"
    LIKELY_AI_GENERATED = "LIKELY_AI_GENERATED"
    AI_ASSISTED = "AI_ASSISTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    MIXED_SIGNALS = "MIXED_SIGNALS"


class ConfidenceLabelEnum(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class CertaintyEnum(StrEnum):
    CONFIRMED = "CONFIRMED"
    PROBABLE = "PROBABLE"
    INFERRED = "INFERRED"


class Signal(BaseModel):
    signal_id: str = Field(min_length=1)
    statement: TraceableString
    direction: Literal["SUPPORTS", "CONTRADICTS", "NEUTRAL"]
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    source_reliability: float = Field(ge=0.0, le=1.0)
    produced_by: str = Field(min_length=1)
    affected_region: str | None = None
    raw_value: dict[str, Any]


class EvidenceFamily(BaseModel):
    family_id: str = Field(min_length=1)
    family_name: str = Field(min_length=1)
    family_finding: TraceableString
    signals: list[Signal] = Field(min_length=1)
    correlated: bool


class EvidenceSection(BaseModel):
    families: list[EvidenceFamily]
    total_signals: int = Field(ge=0)
    signals_supporting_verdict: int = Field(ge=0)
    signals_contradicting_verdict: int = Field(ge=0)
    signals_neutral: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_signal_counts(self) -> EvidenceSection:
        expected = (
            self.signals_supporting_verdict
            + self.signals_contradicting_verdict
            + self.signals_neutral
        )
        if self.total_signals != expected:
            raise ValueError(
                "total_signals must equal signals_supporting_verdict + "
                "signals_contradicting_verdict + signals_neutral"
            )
        return self


class HistoryEvent(BaseModel):
    sequence: int = Field(ge=1)
    description: TraceableString
    certainty: CertaintyEnum
    certainty_note: TraceableString
    supporting_signals: list[str] = Field(default_factory=list)


class HistorySection(BaseModel):
    events: list[HistoryEvent]
    reconstruction_complete: bool
    unknown_gaps: list[str]

    @model_validator(mode="after")
    def _validate_event_sequence(self) -> HistorySection:
        sequences = [event.sequence for event in self.events]
        if len(set(sequences)) != len(sequences):
            raise ValueError("HistoryEvent sequence values must be unique")
        if sequences != sorted(sequences):
            raise ValueError("HistoryEvent events must be sorted by sequence ascending")
        return self


class ConfidenceDimension(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    label: str = Field(min_length=1)
    note: TraceableString


class ConfidenceSection(BaseModel):
    overall: float = Field(ge=0.0, le=1.0)
    overall_label: ConfidenceLabelEnum
    extraction: ConfidenceDimension
    reliability: ConfidenceDimension
    inference: ConfidenceDimension
    hypothesis: ConfidenceDimension
    penalty: ConfidenceDimension
    limitations: list[str] = Field(min_length=1)
    disclaimer: str

    @field_validator("disclaimer")
    @classmethod
    def _validate_disclaimer(cls, value: str) -> str:
        if value != EXAMINA_DISCLAIMER:
            raise ValueError("disclaimer must equal EXAMINA_DISCLAIMER exactly")
        return value


class Assessment(BaseModel):
    verdict: VerdictEnum
    verdict_plain: TraceableString
    recommendation: TraceableString
    what_would_change: TraceableString
    confidence_label: ConfidenceLabelEnum


class ExaminaReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    file_hash: str
    file_name_sanitized: str
    file_type: Literal["JPEG", "PNG", "WEBP", "PDF"]
    file_size_bytes: int = Field(ge=0)
    created_at: datetime
    expires_at: datetime
    examina_version: str = Field(min_length=1)
    prism_version: str = Field(min_length=1)
    rule_set_version: str = Field(min_length=1)
    schema_version: str = "1.0.0"
    assessment: Assessment
    evidence: EvidenceSection
    history: HistorySection
    confidence: ConfidenceSection

    @field_validator("file_hash")
    @classmethod
    def _validate_file_hash(cls, value: str) -> str:
        if not _HEX64_RE.match(value):
            raise ValueError("file_hash must be exactly 64 lowercase hex characters")
        return value

    @field_validator("file_name_sanitized")
    @classmethod
    def _validate_file_name_sanitized(cls, value: str) -> str:
        try:
            UUID(value)
        except ValueError as exc:
            raise ValueError("file_name_sanitized must be a valid UUID string") from exc
        return value

    @model_validator(mode="after")
    def _validate_expiry(self) -> ExaminaReport:
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        return self

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> ExaminaReport:
        return cls.model_validate(json.loads(json_str))
