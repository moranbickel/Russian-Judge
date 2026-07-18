# Evidence

What this document is: a short account of how the protocol has actually been used in production, with no individual receipts attached. The goal is to characterize the corpus the protocol was built against - not to prove correctness, just to ground the claim that the protocol is born from real work, not a thought experiment.

## Corpus

- **Volume.** The protocol has run on more than 300 distinct work products to date, across multiple modalities.
- **Modalities exercised.** Code (the largest share), formal specifications (RFC-shaped), domain content (legal drafts, technical prose), dual-modality work products that touch both code and domain content.
- **Reviewer models exercised.** Multiple capable LLMs across two model vendors. Model selection varies by modality - code review tends to use a faster, cheaper model; high-stakes domain review uses the strongest available model.
- **Round distribution.** The majority of work products converge in one or two rounds. A small minority require a third round; anything beyond that is signaling that the underlying work needs structural rework, not more review (per [PROTOCOL.md §10.3](./PROTOCOL.md)).

## Patterns observed

These are not metrics. They're patterns the protocol's continued use has surfaced, in the order they became apparent.

**Pattern 1 - Dual-modality dispatch catches what single-modality review repeatedly misses.** On work products that touch both code and domain content, running Code RJ alone (or Domain RJ alone) on the change produces verdicts that look clean but miss the cross-modality defects. Running both modalities independently - same change, two primings, two sessions - has, multiple times, surfaced Critical findings that three rounds of single-modality review never produced. This is the single highest-leverage observation from the corpus.

**Pattern 2 - Cross-model dispatch on R2 surfaces R1's blind spots.** Each capable model has consistent blind spots in its reviewing behavior. Dispatching R2 to a *different* model from R1 - same work product, same modality, different model - periodically catches defects the original model would not have surfaced regardless of how many R-rounds were dispatched on it. This is not a routine practice; it's a high-stakes-work option.

**Pattern 3 - The pass floor is the load-bearing piece.** Reviewers can be primed to score conservatively, and they generally do - but the score alone is the part of the verdict most prone to drift. The pass floor (`score ≥ 9.0 AND 0 Critical AND 0 Important`) is the part of the contract that consistently held. Authors who tried to argue down classification rather than addressing findings always ran into R2 holding the line.

**Pattern 4 - Most review effort is spent on the gate, not the verdict.** After a few weeks of use, the failure mode that recurred was not "RJ produced a wrong verdict" but "RJ was invoked on a change that didn't need it." Building discipline around the pre-check gate (per [`templates/pre-check-gate.md`](./templates/pre-check-gate.md)) saved more time than any priming refinement.

## What this corpus does NOT prove

The corpus is one author's use of the protocol on one set of domains. It does not prove:

- That RJ generalizes cleanly to every domain. Domain-specific correctness still depends on the reviewer model's capability in that domain.
- That the C/I/M taxonomy is the optimal taxonomy. It's the smallest taxonomy I found that preserves priority signal without inviting hedge - but that's an observation, not a proof of optimality.
- That the pass-floor formula generalizes to every operational context. Some domains (regulated content, safety-critical code) may want a stricter floor. Some domains may rationally want a looser one.

If you adopt the protocol and find a context where the contract breaks down, that's the kind of feedback the project is asking for. See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Honest limitation

This evidence is anecdotal - selected, narrated, and reported by the same person who designed the protocol. The reader should weight it accordingly. The corpus exists; the patterns are real; the framing is mine.

A more rigorous evidence pack - controlled comparisons against alternative review approaches, false-positive and false-negative rates measured on a held-out set, multi-author corpora - is future work, not present claim.
