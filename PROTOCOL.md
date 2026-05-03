# Russian Judge — Protocol Specification

**Version:** 1.0
**Status:** Stable
**Author:** Moran Bickel

This document specifies the Russian Judge protocol formally. It is the canonical reference. The README is a friendly entry point; this is the source of truth.

---

## §1. Roles

The protocol involves three roles. They may be played by the same or different actors.

**§1.1 Author.** Produces the work product under review. Receives verdicts. Decides whether to address findings or escalate.

**§1.2 Reviewer.** Receives the work product and the priming. Returns a verdict. The reviewer is an LLM (or another reviewing actor) operating under an explicitly adversarial role. The reviewer does not negotiate, suggest collaboratively, or hedge — it returns a verdict in the specified format.

**§1.3 Operator.** Decides whether to invoke RJ for a given change (per §8 pre-check gate), which modality to use (per §9), and when to halt the review chain (per §5.5). In single-person workflows, the Operator and Author may be the same person.

---

## §2. Inputs

A review invocation requires:

- **Work product.** The artifact under review (code diff, full file, spec, prose, etc.). Must be self-contained or include sufficient context for evaluation.
- **Change scope.** A one-line description of what changed and why. Scopes review attention.
- **Modality.** One of: Code, Domain, Dual (per §9).
- **Round number.** R1, R2, R3, etc. Defaults to R1 on first invocation.
- **Prior verdict (R2+).** The verdict from the preceding round, included so the reviewer can verify findings have been addressed.

---

## §3. The C/I/M Defect Taxonomy

Every finding the reviewer surfaces must be classified into exactly one of three classes. A finding without a class is malformed and must be re-classified before the verdict is accepted.

**§3.1 Critical (C).**
A defect that, if shipped, would cause a serious failure: production breakage, data corruption, legal/regulatory violation, security vulnerability, or correctness failure in the work product's primary purpose. A Critical finding blocks shipping unconditionally. Any verdict with Critical findings cannot reach the pass floor regardless of score.

*Examples (across modalities):*
- Code: an unhandled exception path that will crash production.
- Domain: a legal claim that cites a repealed statute.
- Spec: a contract clause that contradicts a downstream consumer's documented expectations.

**§3.2 Important (I).**
A defect that meaningfully degrades the work product but does not unconditionally block shipping. Test coverage gaps, missing edge cases that are unlikely but plausible, ambiguous wording, missed cross-references. Important findings block shipping at the pass floor (≥ 9.0 + 0 C + 0 I) but may be deferred by explicit Operator decision when the Operator accepts the residual risk.

**§3.3 Minor (M).**
A defect that is real but cosmetic or low-impact. Naming, phrasing, ordering, formatting. Minors do not block shipping. Many ship-ready verdicts include Minor findings; the Operator addresses them or doesn't.

**§3.4 Anti-pattern: "Issue."**
The reviewer must not return findings as an undifferentiated "Issue" or "Concern." Every finding has a class. If the reviewer is uncertain about classification, the protocol mandates classifying upward (toward Critical), not downward.

**§3.5 Finding ID.**
Each finding receives an identifier of the form `<class-letter>-<index>`: `C-1`, `I-1`, `I-2`, `M-1`, etc. IDs are referenced when the Author addresses findings in R2.

---

## §4. The Score

The reviewer returns a single score in `[0.0, 10.0]` with one decimal of precision.

**§4.1 Anchored bands.**

| Band | Meaning | Action |
|------|---------|--------|
| 9.5–10.0 | Excellent. Nothing to add. | Ship; stop reviewing. |
| 9.0–9.4 | Production-ready. | Ship if 0 C and 0 I (pass floor). |
| 8.0–8.9 | Functional but flawed. | Address C/I, dispatch R2. |
| 7.0–7.9 | Significant gaps. | Likely needs rework, not just revisions. |
| < 7.0 | Not ready. | Rework before re-review. |

**§4.2 Scoring is an opinion, the floor is a contract.**
The score is the reviewer's holistic judgment. It is fallible. The pass floor is not the score alone — it is `score ≥ 9.0 AND C = 0 AND I = 0`. A score of 9.5 with one Critical finding does not pass. A score of 9.0 with three Minors does. The conjunction is non-negotiable.

**§4.3 No score inflation.**
The reviewer is primed to score conservatively. A reviewer that defaults to 9+ on every submission is broken. The operator should periodically audit verdicts for distribution; if scores cluster above 9.0 without corresponding empirical quality, re-prime the reviewer.

---

## §5. Round Protocol

**§5.1 R1 — Initial review.**
First dispatch. Reviewer receives the work product, scope, and modality. Returns a verdict in the §7 format.

**§5.2 Pass at R1.**
If `score ≥ 9.0 AND C = 0 AND I = 0`, the work product is ship-ready. Halt. Address Minors at Author discretion.

**§5.3 Fail at R1 — dispatch R2.**
If the floor is not met, the Author addresses Critical and Important findings. Each addressed finding is referenced by ID. The R2 dispatch includes the original work product, the modified work product, and the R1 verdict.

**§5.4 R2 — Verification round.**
Reviewer verifies that R1 findings have been addressed. May surface new findings if the changes introduced them. Returns verdict in the same format.

**§5.5 Halt conditions.**
The protocol halts when any of the following hold:

- **Pass.** Floor met (`score ≥ 9.0 AND C = 0 AND I = 0`).
- **Diminishing-returns halt.** After R2 (sometimes R3), if findings begin to be cosmetic preferences rather than substantive issues, the Operator halts and ships at the current verdict if the floor is met. The protocol assumes good-faith application of the floor — Operators do not run a fourth round looking for reassurance.
- **Escalation halt.** If R3 still fails the floor, the protocol escalates to either (a) a different reviewer (per §9 modalities), or (b) human review. Continuing to dispatch the same reviewer past R3 on the same work product wastes cycles.
- **Operator override.** The Operator may halt at any verdict that includes only Important findings if the Operator accepts the residual risk and documents the override. Critical findings are not subject to override.

**§5.6 Round-count discipline.**
Most work products converge in 1–2 rounds. A work product that requires more than 3 rounds is signaling that the underlying change is poorly scoped, not that it needs more review.

---

## §6. Reviewer-Role Priming

The reviewer is primed via system message to take an explicitly adversarial role. The exact priming is in [`templates/reviewer-prompt.md`](./templates/reviewer-prompt.md). The priming has three load-bearing properties:

**§6.1 Adversarial framing.**
The reviewer is told: *your job is to find what is wrong with this work, not to validate that it looks right.* Default LLM behavior is sycophantic; the priming inverts this.

**§6.2 Format constraint.**
The reviewer is told the verdict format is mandatory. No prose preamble, no commentary outside the format, no "I hope this helps." The format constraint forces structured output.

**§6.3 Classification mandate.**
The reviewer is told every finding must be classified C/I/M. Findings without a class are malformed.

The priming explicitly *does not* contain phrases like "be helpful," "give constructive feedback," or "be encouraging." These phrases are sycophancy primers and degrade adversarial review.

---

## §7. Verdict Format

The reviewer returns a verdict in the following format. The format is mandatory; deviations are treated as malformed responses.

```
SCORE: <number with one decimal>/10

CRITICAL (C):
  - C-1: <one-line description>. <one-line impact>.
  - C-2: ...
  (or "None")

IMPORTANT (I):
  - I-1: <one-line description>. <one-line impact>.
  - I-2: ...
  (or "None")

MINOR (M):
  - M-1: <one-line description>.
  - M-2: ...
  (or "None")

VERDICT: PASS | REVISE | REWORK
```

`PASS` requires `score ≥ 9.0 AND C = 0 AND I = 0`. `REVISE` is the default below the floor. `REWORK` is reserved for `score < 7.0` — signaling the work product needs structural rather than incremental change.

A JSON variant of the format is in [`templates/verdict-template.md`](./templates/verdict-template.md) for programmatic pipelines.

---

## §8. Pre-Check Gate

Before invoking RJ, the Operator applies the pre-check gate. The gate is a single test:

> **Can this change introduce a new failure mode?**

If yes, RJ. If no, ship.

**§8.1 Examples of YES (invoke RJ):**
- Code changes that touch a module contract.
- Spec changes that downstream code will consume.
- Domain content where a wrong fact, citation, or word is materially harmful.
- Refactors that change behavior boundaries.

**§8.2 Examples of NO (skip RJ):**
- Comment edits.
- Variable renames within a single function.
- Documentation typos.
- Style-only formatting changes.

**§8.3 The gate is not "is the change small?"**
A two-line change can drop a guard and zero out a downstream calculation. A two-hundred-line change that follows an established pattern can be safe. The axis is failure-mode-introduction, not size.

The full gate decision flow is in [`templates/pre-check-gate.md`](./templates/pre-check-gate.md).

---

## §9. Modalities

Three modalities, applied based on the nature of the work product.

**§9.1 Code RJ.**
Reviewer is primed for code-quality review: bugs, regressions, edge cases, missing tests, contract violations between modules, performance regressions. Code RJ is the default for code changes.

**§9.2 Domain RJ.**
Reviewer is primed for domain-content review: substantive correctness, factual accuracy, citation correctness, register, internal consistency. Domain RJ is the default for prose, specs, and any work product whose primary axis is content rather than code.

**§9.3 Dual RJ.**
Both Code RJ and Domain RJ run, independently, on the same work product. Used when a change touches both code and domain content (for example: a code change that modifies how legal text is generated). The two verdicts are evaluated independently against the floor; the work product passes only if both pass.

**§9.4 Cross-model dispatch.**
The reviewer for any modality may be a different model from the Author's primary model. In my experience, dispatching Domain RJ to a different model from the one that authored the work product catches defects that single-model review misses repeatedly. The protocol does not mandate cross-model dispatch but recommends it for high-stakes work.

---

## §10. Anti-Patterns

**§10.1 Vibe scores.**
Returning a score without findings, or findings without classes. Both are malformed verdicts. The verdict format catches this.

**§10.2 Scoring inflation.**
Reviewers that drift toward 9+ on every submission. Audit verdict distributions periodically; re-prime if scores cluster.

**§10.3 Recursive review.**
Running R3, R4, R5 on the same work product looking for a different answer. After R2/R3, you've extracted what RJ can give you. Halt.

**§10.4 Skipping the gate.**
Invoking RJ on every change, including trivial ones. Trains you to ignore RJ output and burns cycles.

**§10.5 Score-only floor.**
Using `score ≥ 9.0` as the floor without the C/I conjunction. The score alone is a vibe. The floor is the conjunction.

**§10.6 Negotiating findings.**
Author argues with the reviewer that an Important finding is actually Minor. The protocol does not support this. If the Author believes the classification is wrong, the path is to dispatch R2 with a counter-argument; the reviewer may revise classification, or hold. Either way, the verdict is the verdict.

**§10.7 Single-modality on dual-modality work.**
Running only Code RJ on a change that also affects domain content (or vice versa). The other modality's defects are invisible to the modality that ran. Dual RJ exists for this case.

---

## §11. Limitations

The protocol does not solve:

- **A weak reviewer.** If the reviewing model is incapable of finding defects in the work product's domain, no amount of priming will surface them. Cross-model dispatch is the partial mitigation.
- **An adversarial Author.** An Author who works around the floor (e.g., rephrasing findings to avoid Critical classification) defeats the protocol. The protocol assumes good-faith application.
- **Domain-specific correctness without domain-capable reviewers.** Legal, medical, regulated-industry content needs reviewers with domain capability. The protocol structures the review; it does not produce expertise.

---

## §12. Versioning

This is v1.0. Material changes to the taxonomy, the floor formula, or the round protocol produce v2.0. Refinements to priming, format, or anti-patterns produce v1.1, v1.2, etc.

---

*End of specification.*
