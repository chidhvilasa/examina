/**
 * Types mirroring the EXAMINA API response schemas.
 * Cross-referenced with src/examina/api/models.py and
 * src/examina/report/schema.py — keep in sync with both.
 */

export type VerdictType =
  | "LIKELY_AUTHENTIC"
  | "LIKELY_MANIPULATED"
  | "LIKELY_AI_GENERATED"
  | "AI_ASSISTED"
  | "INSUFFICIENT_EVIDENCE"
  | "MIXED_SIGNALS";

export type ConfidenceLabelType = "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT";
export type CertaintyType = "CONFIRMED" | "PROBABLE" | "INFERRED";
export type FactType = "STRUCTURAL" | "TEMPORAL" | "STATISTICAL" | "SEMANTIC" | "PROVENANCE";
export type SignalDirection = "SUPPORTS" | "CONTRADICTS" | "NEUTRAL";

export interface TraceableString {
  text: string;
  trace_ids: string[];
  generated: boolean;
}

export interface Signal {
  signal_id: string;
  statement: TraceableString;
  direction: SignalDirection;
  extraction_confidence: number;
  source_reliability: number;
  produced_by: string;
  affected_region: string | null;
  raw_value: Record<string, unknown>;
}

export interface EvidenceFamily {
  family_id: string;
  family_name: string;
  family_finding: TraceableString;
  signals: Signal[];
  correlated: boolean;
}

export interface EvidenceSection {
  families: EvidenceFamily[];
  total_signals: number;
  signals_supporting_verdict: number;
  signals_contradicting_verdict: number;
  signals_neutral: number;
}

export interface HistoryEvent {
  sequence: number;
  description: TraceableString;
  certainty: CertaintyType;
  certainty_note: TraceableString;
  supporting_signals: string[];
}

export interface HistorySection {
  events: HistoryEvent[];
  reconstruction_complete: boolean;
  unknown_gaps: string[];
}

export interface ConfidenceDimension {
  value: number;
  label: string;
  note: TraceableString;
}

export interface ConfidenceSection {
  overall: number;
  overall_label: ConfidenceLabelType;
  extraction: ConfidenceDimension;
  reliability: ConfidenceDimension;
  inference: ConfidenceDimension;
  hypothesis: ConfidenceDimension;
  penalty: ConfidenceDimension;
  limitations: string[];
  disclaimer: string;
}

export interface Assessment {
  verdict: VerdictType;
  verdict_plain: TraceableString;
  recommendation: TraceableString;
  what_would_change: TraceableString;
  confidence_label: ConfidenceLabelType;
}

export interface ExaminaReport {
  report_id: string;
  file_hash: string;
  file_name_sanitized: string;
  file_type: string;
  file_size_bytes: number;
  created_at: string;
  expires_at: string;
  examina_version: string;
  prism_version: string;
  rule_set_version: string;
  schema_version: string;
  assessment: Assessment;
  evidence: EvidenceSection;
  history: HistorySection;
  confidence: ConfidenceSection;
}

export interface AnalyzeResponse {
  report_id: string;
  file_hash: string;
  file_type: string;
  status: "complete" | "failed";
  verdict: VerdictType;
  confidence_label: ConfidenceLabelType;
  overall_confidence: number;
  active_hypotheses: number;
  unresolved_contradictions: number;
  natural_language_summary: string;
  recommendation: string;
  what_would_change: string;
  report_url: string;
  expires_at: string;
}

export interface ReportResponse {
  report_id: string;
  file_hash: string;
  file_type: string;
  analysis_timestamp: string;
  expires_at: string;
  report: ExaminaReport;
}

export interface ErrorResponse {
  error: string;
  detail: string;
  status_code: number;
}
