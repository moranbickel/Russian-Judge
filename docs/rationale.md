# Rationale

Why Russian Judge exists. What it replaces. What it does not solve.

---

## Why this exists

The first version of my AI-collaborative review process was the obvious one: I'd ask the model "is this good?" or "any problems with this?" The answers were always some shade of "this looks great, with a few minor suggestions."

The model was being agreeable. That's its default. Agreeable reviews don't catch defects.

I tried the next obvious thing: ask the model to score the work. "Rate this 1–10."

The scores were also agreeable. 8.5. 9.0. 8.7. The score moved a tenth or two but never delivered information. A 9.0 from this kind of reviewer was indistinguishable from an 8.5; both meant "no major flags." The number was a vibe.

The 8.5/10-then-broke-production incident referenced in the README is the example I keep coming back to. The reviewer's findings — vague, unprioritized, mixed in with stylistic suggestions — had buried the defect under cosmetic noise. The score told me the work was acceptable. The structure of the review told me nothing about which of the comments mattered.

That was the moment I built the protocol. Three things had to change:

1. **The reviewer's role.** Default LLM behavior is agreeable; I had to invert it explicitly with adversarial framing.
2. **The defect taxonomy.** Findings without a class are unprioritized. Three classes — Critical, Important, Minor — make priority structural rather than implicit.
3. **The pass criterion.** The score alone is a vibe. The score *combined with the finding counts* is a contract: `≥ 9.0 AND 0 Critical AND 0 Important`. That conjunction is what separates "ship" from "almost ship."

That third piece is the load-bearing one. I cannot overstate this. A 9.5 with a Critical finding does not pass. A 9.0 with three Minors does. The score is the reviewer's opinion; the floor is the contract.

---

## Failure modes the protocol addresses

**The agreeable reviewer.** Default LLM tone is sycophantic. Adversarial priming inverts it. Without the priming, no other piece of the protocol matters.

**The vibe score.** A score returned without a finding list, or with findings buried in prose. The mandatory verdict format (§7 of the protocol) makes this malformed.

**Score inflation.** Reviewers that drift toward 9+ on every submission. Periodic auditing of verdict distributions catches this. The conservative-scoring instruction in the priming retards it.

**The unprioritized review.** "Here are some thoughts" with no signal about which thoughts are blocking. C/I/M classification forces priority into every finding.

**The negotiation.** Author argues with the reviewer that an Important finding is actually Minor. The protocol doesn't support this — re-classification happens in the next round, not in dialog. (See §10.6.)

**The sunk-cost fourth round.** Author keeps requesting reviews because they want a higher score. After R2/R3, the protocol mandates halting at the floor or escalating. Continued review on the same work product extracts no further signal.

---

## Failure modes the protocol does not address

I want to be explicit about this. RJ is structure, not capability.

**A weak reviewer.** If the reviewing model lacks the domain capability to find defects in the work product, no priming, no taxonomy, no floor will surface them. Cross-model dispatch (running RJ across two different models) is a partial mitigation but not a full one. Domain-specific work needs domain-capable reviewers.

**An adversarial Author.** An Author who phrases findings to avoid Critical classification, or who declares Important findings as Minor and ships, has worked around the protocol. The protocol assumes good-faith application by the Author. Bad-faith Authors get the failures they avoided in review.

**The unknown unknown.** RJ cannot find what neither the reviewer nor the priming directs attention toward. A Code-RJ-only review on a change that affects domain content will not catch the domain-content defect. Modality discipline (§9) addresses this; but if the Author misclassifies the modality, the gap is invisible.

**Substantive expertise.** A protocol structures judgment. It does not produce judgment. RJ on legal content needs reviewers with legal capability. RJ on medical content needs medical capability. Generic-purpose models often fail in regulated domains.

---

## What I'd build differently knowing what I know now

**I'd version the priming earlier.** As models change, priming that worked on one model degrades on the next. Treat the priming as a versioned artifact and benchmark new model releases against it before adopting them as reviewers.

**I'd track verdict distributions from day one.** Knowing whether your reviewer's scores are clustering tightly above 9.0 vs. distributed across the bands tells you whether the priming is working. I wish I'd been logging this from the first day.

**I'd separate Code-RJ and Domain-RJ tooling earlier.** Trying to run both modalities through one priming and one model produces worse review than running each modality separately. The dual-modality discipline in §9 is the correct shape; I arrived at it later than I should have.

**I'd write the spec before the practice.** The protocol existed informally for months before I wrote it down. During that time I made small drift decisions that the formal spec later caught. Writing this PROTOCOL.md was the most useful single artifact in the entire body of work.

---

*Version notes: this is the v1.0 rationale. Revisions tracked in CHANGELOG.md.*
