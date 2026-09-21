# Russian Judge

A review prompt and verdict format for AI-assisted work. Findings have a severity,
an explanation, and a consequence. The default pass rule is **score >= 9.0,
zero Critical findings, and zero Important findings**.

## Try it

1. Copy the relevant section of the [reviewer prompt](templates/reviewer-prompt.md)
   into a fresh review session.
2. Supply the change, its scope, and the relevant source files.
3. Ask for the [verdict format](templates/verdict-template.md). Verify the findings
   against the source before deciding what to fix.

Synthetic example:

```text
Score: 9.5
Critical: 0
Important: 1 — The supplied approval covers an older revision.
Verdict: REVISE
```

The high score does not cancel a blocking finding. Conversely, a reviewer should
not invent defects to appear rigorous. An empty findings list can be correct.

For a runnable example of an approval that no longer covers the work, try the
[stale-review crash test](https://github.com/moranbickel/agent-crash-tests/tree/main/cases/stale-review).
It checks revision binding; it does not measure an LLM reviewer's accuracy.

## What is here

- [Complete review cycle](examples/r1-r2-walkthrough.md) and
  [disputed finding](examples/disputed-finding-walkthrough.md): synthetic walkthroughs.
- [JSON verdict schema](schemas/verdict.schema.json): a machine-readable format.
- [Pre-check](templates/pre-check-gate.md): decide whether the work needs this review.
- [Protocol](PROTOCOL.md): rounds, severity rules, variants, and stopping conditions.
- [Evidence](EVIDENCE.md): single-author experience and what has not been measured.
- [Adoption guide](docs/how-to-adopt.md) and [FAQ](docs/faq.md).

## Limits

A structured verdict can still be wrong. The score is a reviewer's judgment,
not a calibrated probability of correctness. This repository does not establish
defect-detection rates, false-positive rates, or superiority over another review
method. Passing the protocol does not authorize deployment or replace other
required checks.

Related evaluation work includes [MT-Bench](https://arxiv.org/abs/2306.05685) and
[HELM](https://arxiv.org/abs/2211.09110). See the protocol for the workflow here.

Maintained by [Moran Bickel](https://github.com/moranbickel).
Prose: [CC BY 4.0](LICENSE-CC-BY-4.0). Templates and code: [MIT](LICENSE-MIT).
