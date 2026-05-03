# FAQ

Anticipated questions about Russian Judge.

---

### Why "Russian Judge"?

Figure-skating commentary trope: the Russian judge always gives the lowest scores. The name captures the spirit — find what's wrong, don't validate what looks right. The name is irreverent; the protocol is serious.

---

### How is this different from "just asking the LLM to review my code"?

Three load-bearing differences:

1. **Adversarial role priming.** The reviewer is told its job is to find what's wrong, not to validate. Default LLM tone is sycophantic; the priming inverts it.
2. **Defect taxonomy.** Every finding is classified Critical, Important, or Minor. Findings without a class are malformed.
3. **Pass floor as a contract, not a vibe.** The floor is `score ≥ 9.0 AND 0 Critical AND 0 Important`. The conjunction is non-negotiable. A 9.5 with a Critical finding does not pass; a 9.0 with three Minors does.

A free-form "review this" gets you a paragraph of agreeable feedback. RJ gets you a verdict you can act on.

---

### Why three classes? Why not five, or two?

Two classes (e.g., "blocking" / "non-blocking") collapses real distinctions. There's a meaningful difference between "this will break production" and "this misses an edge case the reviewer thinks is unlikely."

Five or more classes diffuses the signal. Reviewers start hedging classifications across adjacent levels, which produces the same noise problem unstructured reviews have.

C/I/M is the smallest taxonomy that preserves priority signal without inviting hedge.

---

### Why does the floor require zero Important findings, not just zero Critical?

Because Important findings are the dangerous ones to defer. Criticals are obvious — you don't ship them. The temptation to defer is highest with Importants: "we'll address that next sprint," "the customer probably won't hit that edge case," "the test coverage gap isn't blocking."

Importants are exactly where defects get smuggled into production. The floor demands them addressed because that's where the discipline matters.

You can override Important findings with explicit operator authority and documented residual risk acceptance (per §5.5 of the protocol). But the default — the floor — is zero.

---

### Can I use this with [model X]?

Yes, as long as the model is capable enough to follow the priming and produce structured output. Claude (Sonnet 4+, Opus 4+) and GPT-5 work well. Smaller / older models often fail to maintain the adversarial framing across a session and drift back to agreeable defaults.

If you find a model that won't hold the priming, that's a signal to pick a different reviewer for high-stakes work.

---

### What about programmatic use? Can I script this?

Yes. The JSON verdict format in [`templates/verdict-template.md`](../templates/verdict-template.md) is designed for it. A reasonable shape for a programmatic pipeline:

1. Author commits a change.
2. CI dispatches the change to the reviewer model with the priming.
3. Reviewer returns JSON verdict.
4. CI validates the verdict shape, computes pass/fail against the floor, and gates the merge.

Caveats: the priming-stickiness behavior makes single-session calls more reliable than long-running session reuse. For each review, start a fresh session.

---

### How do I keep score inflation from creeping in?

Three mitigations:

1. The priming explicitly tells the reviewer not to inflate.
2. Periodically audit verdict distributions. If scores cluster above 9.0 without corresponding empirical quality (e.g., post-ship defects that should have been caught), re-prime with stronger conservative-scoring instructions.
3. Cross-model dispatch. Models inflate differently. A second reviewer with a different baseline can catch drift in the first.

If a reviewer has been used for hundreds of dispatches and its scores are no longer informative, it has burned out for your work. Switch reviewers.

---

### What about reviewer fatigue? Should I rotate?

LLMs don't fatigue in the literal sense — each session starts fresh. But priming drift across a long session is real. The pragmatic answer: dispatch each review in a new session, with the priming pasted fresh. This is simpler than rotation schedules and gives you the same effect.

---

### Can the reviewer be wrong?

Yes, often. The protocol structures judgment, it does not produce judgment. The reviewer can:

- Misclassify a finding (Important when it's Critical, or vice versa).
- Miss findings entirely.
- Surface false-positive findings.
- Inflate or deflate the score.

The author's response to a wrong verdict is not to argue with it but to apply judgment: address what's worth addressing, dispatch R2, and let the protocol play out. If a reviewer is consistently wrong, change reviewers. If a class of error keeps slipping through, that's a signal for cross-model dispatch on that class of work.

---

### Why not just have a human reviewer?

Human reviewers are better than LLM reviewers on most axes. They're also slower, more expensive, and frequently unavailable. RJ is not a replacement for human review; it's a tool for the cases where human review isn't practical (every commit, every pre-draft of every paragraph, late at night, on a weekend).

A reasonable shape: RJ catches the floor, human review catches the things RJ can't (architecture, judgment calls, domain expertise the model lacks). RJ doesn't substitute for the human; it lets the human focus on what only the human can see.

---

### Does this work for things other than code?

Yes. I've used it on:

- Code (the obvious case).
- Formal specs (RFC-shaped documents).
- Legal claims (the original ORCA use case).
- Prose (this README went through RJ before publication).
- Proposals and pitch decks.

The Domain RJ priming is designed for non-code work. The pass floor and round protocol are modality-agnostic.

---

### What if I disagree with the verdict?

You're allowed to disagree. The protocol doesn't override your judgment. But the protocol also doesn't support arguing with the reviewer in-session — re-classification, if it happens, happens at the next round.

The pragmatic discipline: if you disagree often, your reviewer is wrong-shaped for your work or your priming needs adjustment. Investigate. Don't just override case-by-case; that's how the protocol degrades to vibes.

---

### How long does this take to adopt?

The 15-minute version is in [`docs/how-to-adopt.md`](./how-to-adopt.md). Functional adoption — running RJ as a habit on real work — usually takes a week. Fluent use, where you stop thinking about the protocol and just use it, takes 2–4 weeks of consistent application.

---

### Did you really build this for legal-AI work?

Yes. ORCA is a production system that generates Israeli civil litigation drafts. The cost of a wrong fact, citation, or claim in a legal filing is non-trivial — sanctions, malpractice exposure, lost cases. Vague review wasn't tenable. RJ emerged from needing structure.

The protocol generalized cleanly to non-legal work, which is why this repo exists. But the adversarial framing and the strict floor came from a context where defects had real cost.

---

### Where's the code?

The protocol is the artifact. There's no central tool to install. The templates in this repo are copy-paste — drop them into your reviewer's system message and verdict-parsing code as you see fit.

If interest develops, a thin tool to wrap the dispatch (priming + verdict validation + halt logic) is plausible for v2. For now: copy, paste, run.

---

### How do I cite this?

See [`CITATION.md`](../CITATION.md) at the repo root.

---

### Is this related to any model vendor's similarly-named offering?

No. The name predates anything else and is independent of any model vendor.

---

### Suggestions / improvements?

Open an issue on this repo. Real-use-case feedback is the most valuable input — generic suggestions less so.
