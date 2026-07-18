# Russian Judge

**A protocol for adversarial AI review.** You give a reviewer model an openly adversarial role, and it returns a structured verdict: a score from 0 to 10, plus a list of findings, each marked Critical, Important, or Minor. The pass floor is **≥ 9.0 with zero Critical or Important findings**. Anything short of that means another round.

I've used it on production code, formal specs, legal drafts, and prose. It's one of the highest-leverage protocols I built while developing ORCA, a production legal-AI system. This repo is the public version.

---

## The failure it solves

I once shipped a fix that passed an LLM review with an 8.5/10. Three days later it broke production. The reviewer's comment had been "looks good, minor stylistic suggestions below." That was the moment it clicked:

**An unstructured 8.5/10 from an LLM tells you almost nothing.** It doesn't say whether the problems are blocking or cosmetic. It doesn't say whether to ship. It doesn't tell the author what to fix first. It's a feeling dressed up as a number.

Russian Judge replaces the feeling with three pieces of structure:

1. **An adversarial role** for the reviewer. Not "give me feedback," but "try to find what's wrong."
2. **A defect taxonomy** with three classes: Critical, Important, Minor. Every finding gets a class, or it isn't a finding.
3. **A pass floor** that depends on both the score and the findings: **≥ 9.0 AND zero C/I**. A 9.5 with one Critical finding does not pass. A 9.0 with three Minors does.

The third piece matters most. A score on its own is still just a feeling. A score plus the floor is a contract, and the contract is over the *decision* (given how the findings were classified), not a promise that the reviewer classified them correctly. That second gap is real, and the next section is about it.

---

## What RJ is not

RJ is **not** a claim that LLM reviewers are reliably correct. The reviewer can still miss defects, invent findings, or get the severity wrong. Recent research on LLM-as-judge systems documents real failure modes: bias, prompt-injection weakness, score drift (see [Prior art](#prior-art) below).

The protocol's value isn't oracle-level correctness. Its value is forcing every review into:

1. a severity taxonomy,
2. a pass/fail contract,
3. a bounded review loop,
4. clear human-operator responsibility.

RJ is a structured adversarial review *loop for human-operated workflows*. The Operator owns the decision to ship; the reviewer owns the structured signal. Treat the verdict as an oracle and you're using the protocol against its own design.

---

## RJ vs. alternatives

Three common approaches to AI-assisted review, side by side. Use the one that fits your work and your constraints.

| Dimension | Free-form LLM review | Russian Judge | Human review |
|---|---|---|---|
| Output shape | Prose, unstructured | Score + C/I/M findings + verdict | Variable, often prose |
| Pass criterion | Reader's interpretation | `score ≥ 9.0 AND 0 C/I` (contract) | Reviewer judgment |
| Round protocol | None | R1 → fix → R2 → halt at floor | Variable |
| Defect prioritization | Mixed in with cosmetic notes | Explicit class on every finding | Implicit |
| Time per review | Minutes | Minutes | Hours to days |
| Cost per review | Low | Low | High |
| Domain capability | Bounded by reviewer model | Bounded by reviewer model | Bounded by reviewer human |
| Audit trail | None | Verdict format is the record | Variable, often informal |
| Best for | Quick sanity checks, exploratory work | Pre-merge gate on every change that can introduce a new failure mode | Architecture, judgment calls, regulated-domain decisions |

RJ doesn't replace human review. It covers the cases where human review isn't practical (every commit, late nights, weekends, every paragraph of a draft), and it leaves a structured record a human can audit later.

---

## Prior art

The academic cousin of this protocol is **LLM-as-judge**: using a language model to score another model's output. Zheng et al. (2023) formalized it for evaluating chat assistants and, in the same paper, named its failure modes: position bias, verbosity bias, self-enhancement bias, and weak reasoning on hard problems.[^mtbench] Holistic benchmarks like HELM evaluate models across many scenarios and metrics.[^helm] But that work is about *ranking and evaluating models*. Russian Judge is about *gating one piece of work before it ships*. Same mechanism (an LLM produces a structured judgment), different goal.

What sets RJ apart is what it refuses to inherit. The biases Zheng et al. document are exactly why RJ never treats the verdict as an oracle. It primes the reviewer adversarially to push back against sycophancy and self-flattery, it puts the ship decision on the human Operator rather than the model, and it recommends sending high-stakes work to a second model so no single model's bias is load-bearing. RJ is the LLM-as-judge idea wrapped in a contract and a loop, with the known failure modes named and contained rather than wished away.

[^mtbench]: Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, NeurIPS 2023. [arXiv:2306.05685](https://arxiv.org/abs/2306.05685).
[^helm]: Liang et al., *Holistic Evaluation of Language Models (HELM)*, 2022. [arXiv:2211.09110](https://arxiv.org/abs/2211.09110).

---

## The protocol, at a glance

```
                    ┌──────────────────┐
   Work product ──► │   Reviewer (R1)  │ ──► Verdict (score + C/I/M list)
                    │  adversarial role │
                    └──────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Score ≥ 9.0       │
                    │  AND 0 Critical    │ ──► PASS - ship it
                    │  AND 0 Important   │
                    └─────────┬──────────┘
                              │ no
                              ▼
                    Author addresses findings
                              │
                              ▼
                    ┌──────────────────┐
                    │   Reviewer (R2)  │ ──► same verdict shape
                    └──────────────────┘
                              │
                    pass or escalate to R3 / different reviewer
```

Three review modalities, depending on the work:

- **Code RJ**, for code changes. The reviewer is primed to look for bugs, regressions, edge cases, and missing tests.
- **Domain RJ**, for domain content (in my case, legal text). The reviewer is primed for substantive correctness, not style.
- **Dual RJ**, both run independently, for changes that touch both code and domain content. The dual modality has caught defects in my work that single-modality review missed three rounds running.

---

## A worked example

Say I've just refactored a function that calculates damages. I send it to RJ.

**R1 verdict:**
```
Score: 8.0/10
Critical: 0
Important: 2
  - I-1: Edge case for negative inputs not handled. Function will return
         a negative damage amount, which is nonsensical and will propagate
         downstream into the relief calculation.
  - I-2: Test coverage drops from 94% to 71% on this module after the
         refactor. The removed tests covered the rounding behavior, which
         the new implementation also handles but no longer tests.
Minor: 1
  - M-1: Variable name `tmp_calc` is uninformative. Suggest `subtotal`.
```

I don't argue with the score. An 8.0 with two Importants means another round. I add an input guard for negatives, restore the rounding tests against the new implementation, fix the variable name, and dispatch R2.

**R2 verdict:**
```
Score: 9.4/10
Critical: 0
Important: 0
Minor: 0
PASS - ship it.
```

That's the shape. The score moved 1.4 points, but the change that mattered was the C/I count going to zero.

---

## When to use it, and when not to

RJ is the right tool when a change can introduce a new failure mode: code that touches a contract between modules, a spec that downstream code will consume, a legal claim where the wrong word is grounds for sanctions. Anything where the cost of a missed defect is larger than the cost of one more review cycle.

RJ is the wrong tool for changes that *can't* introduce a new failure mode: comment edits, variable renames inside a single function, documentation typos. Running RJ on those wastes time and teaches you to ignore its output.

The question isn't "is the change small?" Small changes can break things in big ways. The question is "**can this introduce a new failure mode?**" If yes, run RJ. If no, ship.

There's also a discipline of stopping. After R2, sometimes R3, you hit diminishing returns: the reviewer starts surfacing stylistic preferences dressed up as findings. The protocol assumes you'll trust the floor. Once the score is ≥ 9.0 and C/I are zero, you ship. You don't run a fourth round looking for reassurance.

---

## Adopt this in 15 minutes

1. **Copy the reviewer prompt** from [`templates/reviewer-prompt.md`](./templates/reviewer-prompt.md). Paste it as the system message of a new chat with whichever capable model you use for review. For high-stakes work, cross-check with a second model, ideally a different one (see [`PROTOCOL.md`](./PROTOCOL.md) §9.4).
2. **Adopt the verdict format** in [`templates/verdict-template.md`](./templates/verdict-template.md). Ask the reviewer to return verdicts in that exact shape: score, C/I/M with one line each, finding IDs.
3. **Use the pre-check gate** in [`templates/pre-check-gate.md`](./templates/pre-check-gate.md) before invoking RJ. It's a four-question test that takes thirty seconds and keeps you from running RJ on changes that don't need it.

The floor is **≥ 9.0 AND 0 C/I**. Don't ship below it. Don't keep reviewing above it. Stricter and relaxed floor variants are documented in [`PROTOCOL.md`](./PROTOCOL.md) §4.5.

For the formal protocol (round structure, modality definitions, verdict schema, anti-patterns), see [`PROTOCOL.md`](./PROTOCOL.md). For a complete R1→R2 cycle on a synthetic code change, see [`examples/r1-r2-walkthrough.md`](./examples/r1-r2-walkthrough.md). For the harder case, a finding the author believes is a false positive, see [`examples/disputed-finding-walkthrough.md`](./examples/disputed-finding-walkthrough.md).

---

## Why "Russian Judge"

It's a figure-skating commentary trope: the Russian judge always gives the lowest scores. The name captures the spirit of the thing. Find what's wrong; don't rubber-stamp what looks right. A reviewer who returns a 9.8 on every submission is broken. A reviewer who finds two Important issues on a clean piece of work is doing its job.

The name is a joke. The protocol isn't.

---

## Related

This is one of a series of methodology pieces from building ORCA:

- **Russian Judge** - *this repo.* Adversarial AI review with structured verdicts.
- **[Three-Body Protocol](https://github.com/moranbickel/Three-Body-Protocol)** - coordination across sessions in time.
- **[Peer-Worker Convergence](https://github.com/moranbickel/Peer-Worker-Convergence)** - coordination across sessions in parallel.
- **[CSAE](https://github.com/moranbickel/CSAE)** - attestation chains for AI-generated commits.
- **[Pre-IMPL Forensic Discipline](https://github.com/moranbickel/Pre-IMPL-Forensic-Discipline)** - catching wrong premises before they become wrong commits (v0.1 draft).

More pieces as they're written.

---

## About

This protocol was developed for use in production on ORCA (Orchestrated Reasoning for Civil Action), an AI legal reasoning system for Israeli civil litigation. The system is closed-source; the methodology behind it is open. Maintained by [Moran Bickel](https://github.com/moranbickel), Israeli litigator and ORCA's founder.

---

## License

- Prose: [CC BY 4.0](./LICENSE-CC-BY-4.0)
- Templates and code: [MIT](./LICENSE-MIT)

If you adopt or build on this protocol, attribution is requested but not required for templates. For prose, attribution is required under CC BY 4.0.

- Moran Bickel
