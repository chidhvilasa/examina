# EXAMINA Constitution

Specification Version: 1.0.0
Status: FROZEN

This document defines the immutable principles that govern every line of
code, every user-facing string, and every architectural decision in
EXAMINA. Where any other specification conflicts with this document, this
document wins. Where this document is silent, the most conservative reading
(more human oversight, more disclosure, less certainty) wins.

No implementation detail described elsewhere may weaken a principle stated
here. An ADR may propose changing how a principle is satisfied; no ADR may
propose removing a principle.

---

## PRINCIPLE 1 — THE HUMAN DECIDES

EXAMINA produces evidence and analysis. It does not produce verdicts that a
journalist is expected to publish unexamined. Every report exists to help a
human editor make their own decision faster and with better information —
never to make the decision for them.

- No report field, UI element, or API response may present EXAMINA's
  output as a final determination of authenticity.
- Every report must make clear, in its own text, that the responsibility
  for any editorial or publication decision rests with the human reader.
- EXAMINA never auto-publishes, auto-flags to third parties, or takes any
  action on a file beyond producing a report for the user who submitted it.

## PRINCIPLE 2 — EVERY CONCLUSION IS TRACEABLE

Nothing in a Digital Evidence Report may assert something that cannot be
traced back to a specific underlying signal produced by PRISM.

- Every sentence in `EvidenceSection` and `HistorySection` that states a
  finding must carry one or more `trace_ids` linking it to the `BridgeFact`
  or `BridgeContradiction` records that support it (see
  `EVIDENCE_TRACEABILITY_v1.0.md`).
- A conclusion with no traceable origin is a defect, not a feature. It must
  be removed before release, not shipped with a caveat.
- Traceability exists so a skeptical journalist, editor, or opposing party
  can always ask "how do you know that?" and receive a concrete, inspectable
  answer.

## PRINCIPLE 3 — UNCERTAINTY IS MANDATORY

EXAMINA reasons over incomplete, adversarial, and sometimes corrupted
signals. Certainty is nearly always false confidence.

- Every report includes a `ConfidenceSection` with explicit, numeric,
  human-readable confidence information — never a bare verdict with no
  accompanying uncertainty.
- Low or insufficient confidence must be stated as plainly as high
  confidence. A report is never permitted to omit or soften a low-confidence
  result to appear more useful.
- When evidence is contradictory, insufficient, or inconclusive, the
  report says so directly rather than forcing a verdict.

## PRINCIPLE 4 — FORBIDDEN LANGUAGE IS ABSOLUTE

The following words and their close variants never appear in any
EXAMINA-generated output shown to a user, under any circumstance, at any
confidence level: **fake, forgery, fraud, definitely, guaranteed,
confirmed, proof, proven.**

- This is not a style preference. It is a legal and epistemic boundary:
  these words assert certainty and intent that a structural/metadata
  analysis tool can never actually establish.
- This rule applies to every code path that renders text for a human,
  including error messages, tooltips, exported PDFs, and API responses
  intended for display. It does not apply to internal log messages that
  are never shown to an end user.
- See `LANGUAGE_SPEC_v1.0.md` for the complete forbidden vocabulary and
  approved alternatives. That specification implements this Principle; it
  does not define its own, narrower scope.

## PRINCIPLE 5 — PRISM IS THE ONLY REASONING ENGINE

EXAMINA does not reimplement forensic analysis. All extraction of Facts,
detection of Contradictions, generation of Hypotheses, and computation of
confidence happens inside PRISM. EXAMINA's job is translation, packaging,
and presentation — never independent forensic judgment.

- No EXAMINA module may implement its own signal extraction, contradiction
  detection, or confidence scoring that duplicates or second-guesses PRISM.
- If PRISM does not have a signal, EXAMINA does not invent one to fill the
  gap. A missing signal is reported as missing.
- Any perceived gap in PRISM's reasoning is addressed by a PRISM
  enhancement request, never by an EXAMINA-side workaround.

## PRINCIPLE 6 — NO SILENT FAILURES

Every failure mode — a corrupted upload, a PRISM bridge timeout, an
unsupported file type, an internal exception — must be visible to the user
in plain language and logged internally with enough detail to debug.

- A report is never generated that silently omits a section because of an
  internal error. If a section cannot be produced, the report says so.
- No `except Exception: pass` or equivalent silent-swallow pattern is
  permitted anywhere in the codebase.
- See `FAILURE_SPEC_v1.0.md` for the complete catalogue of failure
  categories and their required user-facing and internal behavior.

## PRINCIPLE 7 — PRIVACY BEFORE CONVENIENCE

A journalist's source material is often sensitive, sometimes dangerous to
its subject if disclosed. EXAMINA treats every uploaded file as
confidential by default.

- Uploaded file content and original filenames are never logged, and are
  never retained longer than the minimum needed to produce the report.
- No file content or derived report is ever transmitted to a third party
  (analytics vendor, error-tracking service, etc.) without the uploading
  user's explicit, informed action.
- Convenience features (e.g. "email me my report," social sharing,
  cross-device sync) are never implemented in a way that requires relaxing
  this default. If a feature cannot be built without weakening privacy, the
  feature is not built.

## PRINCIPLE 8 — SECURITY BEFORE FEATURES

No feature, however valuable, ships ahead of the security control it
depends on. Foundation before functionality.

- Application dependencies are added only when a phase actually needs
  them, and every addition is justified in the commit that introduces it.
- Untrusted input (an uploaded file, above all) is treated as
  potentially malicious until the security pipeline has validated it — see
  `FAILURE_SPEC_v1.0.md` and the upload pipeline specification introduced
  in Phase 3.
- When a security requirement and a feature deadline conflict, the
  security requirement wins and the feature slips.

## PRINCIPLE 9 — REPORTS ARE IMMUTABLE

Once a Digital Evidence Report is generated and returned to a user, its
content never silently changes.

- A report is never regenerated in place with different content under the
  same report ID. If the underlying PRISM analysis changes (e.g. a bridge
  version bump), a new report ID is issued.
- Report expiry (deletion after a retention window) is permitted and
  disclosed; silent mutation of a still-live report is not.
- Every report embeds the versions of every component that produced it
  (PRISM bridge version, EXAMINA version, specification version) so that a
  report is self-describing even after the software has moved on.

## PRINCIPLE 10 — THE BRIDGE IS ONE-WAY

EXAMINA consumes PRISM's output. It never instructs, configures, or
reaches into PRISM's internals, and PRISM never depends on EXAMINA.

- EXAMINA code never imports a PRISM-internal module directly. All
  interaction happens through the typed contract defined in
  `BRIDGE_SPEC_v1.0.md`.
- The bridge boundary exists so PRISM can be improved, replaced, or
  operated independently (including as a hosted service, per
  `RemoteBridgeClient`) without EXAMINA's application code changing.
- PRISM internals (its Fact/Evidence/Contradiction/Hypothesis schemas,
  its reasoning stages) never leak into an EXAMINA-facing type. Every type
  that crosses the boundary is an EXAMINA-native translation.

## PRINCIPLE 11 — SECURITY THREAT MODEL

EXAMINA is built assuming it will be targeted. The threat actor categories
below are treated as the standing baseline for every security decision,
not a hypothetical to revisit later.

1. **The malicious uploader** — someone who submits a crafted file
   (malformed image/PDF/DOCX, zip-slip payload, decompression bomb,
   oversized file) intending to crash, exploit, or exfiltrate from the
   analysis pipeline.
2. **The curious/hostile third party** — someone who did not upload the
   file but wants to read another user's report, enumerate report IDs, or
   otherwise access data they have no right to.
3. **The scraper/abuser** — someone using automated requests to exhaust
   rate limits, brute-force an invite code, or extract the corpus of
   reports at scale.
4. **The subject of the investigation** — a person whose manipulated or
   AI-generated content is the object of the report, who may have a strong
   incentive to discredit, suppress, or tamper with the analysis pipeline
   itself if given the chance.
5. **The insider/operator error** — a misconfiguration, leaked credential,
   or over-broad log statement that exposes user data even with no external
   attacker involved.
6. **The supply chain** — a compromised or vulnerable dependency
   introduced transitively through `pip`/`npm`.

Every new feature is reviewed against this list before it ships: which of
these actors could abuse it, and what stops them?

## PRINCIPLE 12 — EXPLAINABILITY BEFORE BREVITY

A report that is short but unclear fails its purpose. Where a choice must
be made between a terser report and a more explainable one, EXAMINA chooses
explainability.

- Technical terms are translated into plain language (see
  `CONFIDENCE_TRANSLATION_v1.0.md`), never left as raw PRISM jargon.
- Every section explains not just *what* was found but *why it matters*
  and *how confident EXAMINA is* in that finding.
- Brevity is still a goal (see the PRD's four-minute success metric) —
  but never at the cost of a reader being unable to understand or
  challenge a conclusion.

## PRINCIPLE 13 — EXAMINA DOES NOT ACCUSE

EXAMINA describes evidence about a file. It never describes intent,
culpability, or wrongdoing on the part of any person.

- Verdicts describe the *artifact* ("this image shows signs consistent
  with AI generation"), never a *person* ("the sender fabricated this").
- EXAMINA has no concept of a suspect, a perpetrator, or a victim. It has
  facts, evidence, hypotheses about processing history, and confidence.
- Any output that could be read as a statement about a specific person's
  honesty or intent is a Principle 13 violation and must be rewritten
  before release, regardless of how well-supported the underlying evidence
  is.

## PRINCIPLE 14 — RESEARCH INTEGRITY

EXAMINA is a research-grounded tool, not a marketing product dressed up in
scientific language.

- Claims about EXAMINA's accuracy, capability, or comparative performance
  are made only when backed by documented evaluation, never by assertion.
- Limitations (see `FAILURE_SPEC_v1.0.md` and `docs/BETA_GUIDE.md`-style
  documentation introduced in later phases) are disclosed as prominently as
  capabilities.
- The specification-first process itself — frozen specs, ADRs for
  deviations, ruthless traceability — exists in service of this principle:
  a tool that reasons about evidence must itself be built with an evidence
  trail.

---

THIS DOCUMENT IS FROZEN.
