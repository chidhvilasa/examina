# EXAMINA Specification Version

Specification Version: 1.0.0
Status: FROZEN
Frozen Date: July 2026

Specification Authority:
The EXAMINA Constitution supersedes every other specification
if a conflict exists between specifications.

Included Specifications:
  PRD_v1.0.md                      — Product Requirements Document
  REPORT_SCHEMA_v1.0.md            — Digital Evidence Report schema
  BRIDGE_SPEC_v1.0.md              — PRISM bridge interface
  CONFIDENCE_TRANSLATION_v1.0.md   — Confidence dimension translation
  EVIDENCE_CLUSTERING_v1.0.md      — Evidence family definitions
  DECISION_MODEL_v1.0.md           — Verdict and recommendation logic
  EVIDENCE_TRACEABILITY_v1.0.md    — Audit chain specification
  LANGUAGE_SPEC_v1.0.md            — Language policy
  FAILURE_SPEC_v1.0.md             — Failure mode definitions
  CONSTITUTION_v1.0.md             — Immutable principles
  DEPLOYMENT_SPEC_v1.0.md          — Deployment architecture

Amendment Policy:
  Specifications may be extended by creating v1.1.md alongside v1.0.md.
  v1.0.md files are NEVER modified after this commit.
  Claude Code reads the highest available version of each spec.
  Breaking changes require a major version bump and explicit approval.
  Any architectural change not covered by existing specs requires an ADR
  in docs/adr/ before implementation proceeds.
