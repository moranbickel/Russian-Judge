# Changelog

## Unreleased

- README.md - added a **Prior art** section engaging the LLM-as-judge literature (Zheng et al. 2023, HELM) and stating what RJ does and does not inherit from it.
- examples/disputed-finding-walkthrough.md - new worked example covering a disputed finding (the author believes the reviewer is wrong): the false-positive-vs-latent-fragility decomposition, why a Critical is not author-overridable, and cross-model dispatch as the dispute resolver.

## v1.1 - 2026-06-19

Refinements from continued production use: the Note class, the machine-checkable floor invariant, floor variants, the calibration-loop escalation tactic, and the optional verdict record. Additive and backward-compatible - a v1.0 verdict is a valid v1.1 verdict.

- PROTOCOL.md - **§3.6 Note (N)**: a fourth observation category for true-but-non-defect remarks (out-of-scope, no-action, future-improvement), with no score or floor impact. **§4.4 pass-assertion invariant**: when a verdict carries an explicit pass flag, it must equal the floor formula recomputed from the counts; a mismatch is malformed. **§4.5 floor variants**: the default floor plus the Minor-inclusive and relaxed-Minor variants, set per operator policy. **§10.8 calibration-loop tactic**: the weaker-reviewer praise-Minor loop and the escalate-the-terminal-round-to-a-stronger-model recovery move. **§13 Verdict Records**: the optional auditable-record metadata (verdict id, predecessor link, review scope, change binding, reviewer model, issued-at, pass assertion) that makes a stored verdict chainable, bindable, and attributable. Version bumped 1.0 → 1.1.
- schemas/verdict.schema.json - added the optional `findings.notes` array (`N-` ids) and the optional top-level `record` object (verdict_id, predecessor_verdict, review_scope, covers_range, reviewer_model, review_round, pass_asserted, issued_at). The five required core fields are unchanged, so existing verdicts still validate. Floor reconciliation (finding C-1): `pass_asserted` now encodes the DEFAULT floor (score >= 9.0 AND 0 Critical AND 0 Important; Minors permitted), matching the `verdict` enum and PROTOCOL.md §4.2; an optional `record.floor_variant` selects the Minor-inclusive or Relaxed-Minor variants (§4.5); the schema now enforces the matching floor for a `pass_asserted:true` record. Removed `score.multipleOf: 0.1`, which spuriously rejected exact one-decimal scores such as 9.1 and 9.2 under IEEE-754 float; one-decimal precision is now a documented convention.
- templates/verdict-template.md - documented the Note slot and the JSON `record` block (with a worked record-bearing example), the pass-assertion field rule, and the new anti-patterns the format catches (pass-assertion mismatch; no-action remark filed as Minor).
- templates/reviewer-prompt.md - added the Note class to the Code and Domain primings (instruction + a `NOTES (N)` verdict slot), and notes on the priming covering why the Note class exists, the calibration-loop escalation tactic, and programmatic / async dispatch (gate on the verdict's arrival, not on the dispatch call returning).

## v1.0 - 2026-05-03

Initial public release.

- README.md - overview, failure mode, worked example, adoption pointer.
- PROTOCOL.md - formal specification (§§1-12).
- Templates: reviewer-prompt, verdict-template, pre-check-gate.
- Docs: rationale, how-to-adopt, faq.
- Diagram: RJ flow (`diagram.svg`).
- Licensing: CC BY 4.0 for prose, MIT for templates.
