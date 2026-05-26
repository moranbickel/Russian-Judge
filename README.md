# Russian Judge

**A protocol for adversarial AI review.** A reviewer model is given an explicitly adversarial role and returns a structured verdict: a score from 0 to 10, plus a list of findings classified as Critical, Important, or Minor. Pass floor: **≥ 9.0 with zero Critical or Important findings**. Anything else means another round.

I've used this on production code, formal specs, legal drafts, and prose. It's one of the highest-leverage protocols I built while developing ORCA, a production legal-AI system. This repo is the public version.

---

## The failure it solves

I shipped a fix once that passed an LLM review with an 8.5/10. Three days later it broke production. The reviewer's comment had been "looks good — minor stylistic suggestions below." That was the moment I realized:

**An unstructured 8.5/10 from an LLM means nothing.** It doesn't tell you whether the issues are blocking or cosmetic. It doesn't tell you whether to ship. It doesn't tell the author what to fix first. It's a vibe wearing a number.

Russian Judge fixes this with three pieces of structure:

1. **An adversarial role** for the reviewer. Not "give me feedback" — *try to find what's wrong*.
2. **A defect taxonomy** with three classes: Critical, Important, Minor. Every finding has a class. No class, no finding.
3. **A pass floor** that's a function of both the score and the findings: **≥ 9.0 AND zero C/I**. A 9.5 with one Critical finding doesn't pass. A 9.0 with three Minors does.

That last piece is the one that matters most. The score alone is a vibe. The score combined with the floor is a contract.

---

## What RJ is not

RJ is **not** a claim that LLM reviewers are reliably correct. The reviewer can still miss defects, hallucinate findings, or misclassify severity. Recent research on LLM-as-judge systems documents real failure modes — bias, prompt-injection vulnerability, score drift.

The protocol's value is not oracle-level correctness. Its value is forcing every review into:

1. a severity taxonomy,
2. a pass/fail contract,
3. a bounded review loop,
4. explicit human-operator responsibility.

RJ is a structured adversarial review *loop for human-operated workflows*. The Operator owns the decision to ship; the reviewer owns the structured signal. If you treat the verdict as oracle, you're holding the protocol wrong.

---

## RJ vs alternatives

Three common approaches to AI-assisted review, side by side. Use the one that fits your work product and operating constraints.

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

RJ doesn't replace human review — it makes the cases where humans aren't practical (every commit, late-night, weekends, every paragraph of a draft) reviewed at all, with structured output a human can audit later.

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
                    │  AND 0 Critical    │ ──► PASS — ship it
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

- **Code RJ** — for code changes. Reviewer is primed to look for bugs, regressions, edge cases, missing tests.
- **Domain RJ** — for domain content (in my case: legal text). Reviewer is primed for substantive correctness, not style.
- **Dual RJ** — both, run independently, for changes that touch both code and domain content. The dual modality has caught defects in my work that single-modality review missed three rounds in a row.

---

## A worked example

Suppose I've just refactored a function that calculates damages. I send it to RJ.

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

I don't argue with the score. 8.0 with two Importants means another round. I add an input guard for negatives, restore the rounding tests against the new implementation, fix the variable name, and dispatch R2.

**R2 verdict:**
```
Score: 9.4/10
Critical: 0
Important: 0
Minor: 0
PASS — ship it.
```

That's the shape. The score moved 1.4 points, but the meaningful change wasn't the score — it was the C/I count going to zero.

---

## When to use it — and when not to

RJ is the right tool when a change can introduce a new failure mode. Code that touches a contract between modules. A spec that downstream code will consume. A legal claim where the wrong word is grounds for sanctions. Anything where the cost of a missed defect outweighs the cost of an extra review cycle.

RJ is the wrong tool for changes that *cannot* introduce a new failure mode. Comment edits. Variable renames inside a single function. Documentation typos. Running RJ on these wastes time and trains you to ignore its output.

The gate isn't "is the change small?" — small changes can break things in big ways. The gate is "**can this introduce a new failure mode?**" If yes, RJ. If no, ship.

There's also a discipline of stopping. After R2 — sometimes R3 — you hit diminishing returns. The reviewer starts surfacing things that are stylistic preferences masquerading as findings. The protocol assumes you'll trust the floor: when the score is ≥ 9.0 and C/I are zero, you ship. You don't run a fourth round looking for reassurance.

---

## Adopt this in 15 minutes

1. **Copy the reviewer prompt** from [`templates/reviewer-prompt.md`](./templates/reviewer-prompt.md). Paste it as the system message of a new chat with whichever model you use for review (I use Claude for most work and GPT for cross-checks).
2. **Adopt the verdict format** in [`templates/verdict-template.md`](./templates/verdict-template.md). Ask the reviewer to return verdicts in that exact shape. Score, C/I/M with one-line each, finding IDs.
3. **Use the pre-check gate** in [`templates/pre-check-gate.md`](./templates/pre-check-gate.md) before invoking RJ. It's a four-question test that takes thirty seconds and saves you from running RJ on changes that don't need it.

The floor is **≥ 9.0 AND 0 C/I**. Don't ship below it. Don't keep reviewing above it.

For the formal protocol — round structure, modality definitions, verdict schema, anti-patterns — see [`PROTOCOL.md`](./PROTOCOL.md). For a complete end-to-end R1→R2 cycle on a synthetic code change, see [`examples/r1-r2-walkthrough.md`](./examples/r1-r2-walkthrough.md).

---

## Why "Russian Judge"

Figure-skating commentary trope: the Russian judge always gives the lowest scores. The name captures the spirit — find what's wrong, don't validate what looks right. A reviewer who returns a 9.8 on every submission is broken. A reviewer who finds two Important issues on a clean piece of work has done their job.

The name is irreverent on purpose. The protocol is serious.

---

## Related

This is one of a series of methodology pieces from building ORCA:

- **Russian Judge** — *this repo.* Adversarial AI review with structured verdicts.
- **[Three-Body Protocol](https://github.com/moranbickel/three-body-protocol)** — coordination across sessions in time.
- **[Peer-Worker Convergence](https://github.com/moranbickel/peer-worker-convergence)** — coordination across sessions in parallel.
- **[CSAE](https://github.com/moranbickel/csae)** — attestation chains for AI-generated commits.

More pieces as they're written.

---

## About

This protocol was developed for use in production on ORCA (Orchestrated Reasoning for Civil Action), an AI legal reasoning system for Israeli civil litigation. The system is closed-source; the methodology that produced it is open. Maintained by [Moran Bickel](https://github.com/moranbickel), Israeli litigator and ORCA's founder.

---

## License

- Prose: [CC BY 4.0](./LICENSE-CC-BY-4.0)
- Templates and code: [MIT](./LICENSE-MIT)

If you adopt or build on this protocol, attribution requested but not required for templates. For prose, attribution is required under CC BY 4.0.

— Moran Bickel
