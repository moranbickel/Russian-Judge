# Russian Judge — Protocol Specification

**Version:** 1.1
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

**§3.6 Note (N) — the no-impact observation.**
A Note is an observation the reviewer wants on the record that is *not a defect in the work product under review*: an out-of-scope remark, a no-action recommendation ("nothing to fix here, but worth knowing"), a sibling-class observation, a future-improvement suggestion. Notes carry **no score impact and no floor impact** — they are not findings. They use the ID form `N-1`, `N-2`, etc.

The Note class exists to give the reviewer somewhere to put a true observation that is not a Minor. Without it, a conscientious reviewer who has nothing to fix but something to say is pushed to file the remark as a Minor — and a Minor, under the stricter floor variants (§4.5), can block. The asymmetry is real: a reviewer whose own narrative says "no fix required" or "out of scope for this review" but who files the remark as a Minor has produced a verdict that fails its own floor for a non-defect. When a finding's narrative reads as a Note, classify it as a Note. (This is what §10.8 — the calibration-loop tactic — turns on.)

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

**§4.2.1 What the contract binds — and what it does not.**
The floor is a contract over the *pass decision*: given the findings as classified, ship/no-ship is determined by rule, not by operator mood or reviewer tone. It removes discretion-creep ("it's basically fine, ship it"). It does **not** guarantee the reviewer classified correctly — a reviewer that misclassifies a Critical as Minor passes the floor silently, and the floor itself has no internal detection loop for that. That residual risk lives in the reviewer-reliability layer, not the floor; RJ mitigates it (classify-upward-when-uncertain in the priming, cross-model dispatch for high-stakes work per §9, and the Operator owning the final ship decision) but does not eliminate it. The floor makes the *decision rule* honest; it does not make the reviewer infallible.

**§4.3 No score inflation.**
The reviewer is primed to score conservatively. A reviewer that defaults to 9+ on every submission is broken. The operator should periodically audit verdicts for distribution; if scores cluster above 9.0 without corresponding empirical quality, re-prime the reviewer.

**§4.4 The pass-assertion invariant (machine-checkable floor).**
When a verdict carries an explicit pass flag — i.e. the reviewer states `pass_asserted: true|false` in a stored or programmatic verdict (§13) rather than just narrating a `PASS`/`REVISE`/`REWORK` value — that flag MUST equal the floor formula:

```
pass_asserted  ==  (score >= 9.0)  AND  (critical + important + minor == 0)
```

A `pass_asserted: true` with any non-zero blocking-class count is a **malformed verdict**, not a pass. This is the machine-checkable form of the §10.5 anti-pattern (score-only floor): a reviewer that asserts PASS off the score alone, ignoring the finding counts, is caught by recomputing the formula from the counts and rejecting the mismatch. Validators should always recompute rather than trust the asserted flag — the counts are the ground truth; the assertion is the claim. (Whether `minor` is in the conjunction depends on the floor variant in force — see §4.5.)

**§4.5 Floor variants.**
The default floor is `score >= 9.0 AND 0 C AND 0 I` (§4.2). Two stricter variants are sometimes warranted, set per operator policy, not per verdict:

- **Minor-inclusive floor:** `score >= 9.0 AND 0 C AND 0 I AND 0 M`. Used where even cosmetic residue is unacceptable before a change is recorded as clean — e.g. a regulated audit trail. Under this variant a single un-addressed Minor blocks, which is precisely why the Note class (§3.6) matters: a no-action observation filed as a Minor would otherwise block a clean work product for a non-defect.
- **Relaxed-Minor floor:** `score >= 8.5 AND 0 C AND 0 I`, with one well-grounded Minor acceptable as a documented deferral. Used for low-stakes or exploratory work where the cost of an extra round outweighs the residual Minor.

The variant is an operator decision, fixed for a class of work and applied uniformly — not a per-verdict negotiation. The pass-assertion invariant (§4.4) is computed against whichever variant is in force.

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
- **Operator override.** The Operator may halt at any verdict that includes only Important findings if the Operator accepts the residual risk and documents the override. The override record must name *who* authorized it, *which* Important findings are being accepted, the *residual-risk rationale*, and the *date* — captured wherever verdicts are stored (commit message, review log, or PR comment). An override without that record is indistinguishable from ignoring the finding. Critical findings are not subject to override.

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
ROUND: R<n>
MODALITY: code | domain | dual

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

`ROUND` and `MODALITY` echo the dispatch (the round you are on; the priming you were given) and are required by [`schemas/verdict.schema.json`](./schemas/verdict.schema.json) — a verdict that omits them fails validation. A JSON variant of the format is in [`templates/verdict-template.md`](./templates/verdict-template.md) for programmatic pipelines.

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

**§10.8 The praise-Minor calibration loop — and the escalation tactic.**
A specific failure mode of weaker or cheaper reviewer models: on otherwise-clean work, the reviewer manufactures a fresh non-actionable "no fix required" remark each round, files it as a *Minor* rather than a Note (§3.6), and then asserts `pass_asserted: true` anyway — violating the invariant (§4.4). Under a Minor-inclusive floor (§4.5) the non-zero Minor count blocks; re-prompting the same model to reclassify just invites the next praise-Minor next round. The fold of round N's praise-Minor produces round N+1's praise-Minor. It is a *loop*, not a convergence.

The tactic that breaks it: **escalate the terminal round to a stronger model** (the cross-model dispatch of §9.4, applied as a recovery move rather than a routine triangulation). A stronger reviewer reliably classifies no-action observations as Notes — no score impact, no floor impact — and returns the clean `0/0/0` terminal verdict the work product actually warrants. The trigger is two or more consecutive rounds from the weaker model each emitting exactly one self-asserted-PASS praise-Minor. This is model-agnostic: it is the weaker-reviewer limitation (§11) surfacing as a calibration artifact, and the escape hatch is the same one §9.4 already names.

---

## §11. Limitations

The protocol does not solve:

- **A weak reviewer.** If the reviewing model is incapable of finding defects in the work product's domain, no amount of priming will surface them. Cross-model dispatch is the partial mitigation.
- **An adversarial Author.** An Author who works around the floor (e.g., rephrasing findings to avoid Critical classification) defeats the protocol. The protocol assumes good-faith application.
- **Domain-specific correctness without domain-capable reviewers.** Legal, medical, regulated-industry content needs reviewers with domain capability. The protocol structures the review; it does not produce expertise.

---

## §12. Versioning

This is v1.1. Material changes to the taxonomy, the floor formula, or the round protocol produce v2.0. Refinements to priming, format, or anti-patterns produce v1.1, v1.2, etc. v1.1 added the Note class (§3.6), the pass-assertion invariant (§4.4), floor variants (§4.5), the calibration-loop escalation tactic (§10.8), and the verdict record (§13).

---

## §13. Verdict Records (optional)

The five-field verdict of §7 (round, modality, score, findings, verdict) is sufficient for ad-hoc, single-session use: you read it, you act on it, you move on. But once verdicts are *stored* — as an audit trail, or as inputs to a programmatic pipeline — they need to be **chainable, bindable, and attributable**. A bare verdict message cannot be: it does not say which round it succeeds, which exact change it reviewed, or which reviewer produced it. The verdict record is the optional metadata that closes those gaps. It wraps the core verdict; it does not change it.

**§13.1 The record fields.**

| Field | Purpose |
|---|---|
| `verdict_id` | A stable, unique identifier for this verdict within the store. The anchor that the next round points back to. |
| `predecessor_verdict` | The `verdict_id` of the preceding round (null for R1). Chains the round protocol (§5) into a verifiable lineage instead of relying on round numbers alone. |
| `review_scope` | What the reviewer actually examined, per modality (a `code_dimensions` list and a `domain_dimensions` list, each present, the off-modality one empty). Makes a PASS honest: it certifies *this scope*, not adjacent files or downstream consumers (§4.2.1). |
| `covers_range` | The exact change the verdict is bound to — a commit range, a revision id, a content hash. A verdict authored against one state does not certify a later state; the binding is what lets tooling gate the *shipped* change rather than a stale one. |
| `reviewer_model` | Which model (or human) produced the verdict. Without it, cross-model dispatch (§9.4) is not auditable — you cannot say which reviewer caught a finding if you did not record who reviewed. |
| `review_round` | The round identifier, mirrored into the record so the stored verdict is self-describing. |
| `pass_asserted` | The reviewer's own pass claim, governed by the §4.4 invariant — it must equal the floor formula recomputed from the counts. |
| `issued_at` | When the verdict was issued (ISO 8601 UTC recommended). Orders the lineage and supports the drift auditing of §4.3 / §10.2. |

**§13.2 Why each field earns its place.**
Every record field defends a property the bare verdict cannot. `review_scope` + `covers_range` are the verdict-coverage honesty the §4.2.1 gap demands made explicit: a stored PASS that does not say *what it covered* and *which state it covered* will eventually be cited as certifying more than it did. `predecessor_verdict` + `verdict_id` make the round protocol auditable as a chain rather than a guess from filenames. `reviewer_model` is the precondition for any claim about cross-model dispatch having happened. `pass_asserted` is the field the §4.4 invariant is computed against. None of this is required for the protocol to *run* — it is required for the protocol to leave a record you can trust later.

**§13.3 What stays out of the protocol.**
The record schema is intentionally minimal. Storage format, identity scheme (UUID vs. content hash vs. monotonic counter), how `covers_range` is expressed (commit SHAs, revision ids, hashes), and how the store is indexed are implementation choices, not protocol. The schema in [`schemas/verdict.schema.json`](./schemas/verdict.schema.json) carries the record as an optional `record` object so a programmatic pipeline can validate it, while a single-session user can ignore it entirely.

---

*End of specification.*
