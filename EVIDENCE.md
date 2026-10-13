# Evidence

## Status

Effectiveness is anecdotal. It comes from the author's private use of the protocol,
for which there are no public receipts. **No public evaluation of reviewer accuracy
exists yet.** This repository does not establish defect-detection rates,
false-positive rates, or superiority over any other review method, and nothing here
should be read as a reliability claim.

If you have run the protocol, or an alternative, on work you can share, please
[open an issue](https://github.com/moranbickel/Russian-Judge/issues) with what you
found, including cases where it failed. Public reports are the evidence this project
lacks. See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Design observations (author's impressions, not measurements)

These are impressions that shaped the design. They are hypotheses to test, not
results, and they carry no frequency or success-rate claim.

**Dual-modality dispatch.** On work that touches both code and domain content,
running a Code review and a Domain review independently (same change, two primings,
two sessions) seemed to surface cross-modality defects that either alone missed.

**Cross-model dispatch on R2.** Reviewer models appear to have consistent blind
spots. Dispatching R2 to a different model than R1 is offered as an option for
high-stakes work (per [PROTOCOL.md §9](./PROTOCOL.md)); its benefit has not been
measured.

**The pass floor.** The floor (`score ≥ 9.0 AND 0 Critical AND 0 Important`) is the
part of the contract that is mechanical and checkable. The score alone is the
part of a verdict most prone to drift.

**The pre-check gate.** In the author's experience, the recurring failure was not a
wrong verdict but invoking the review on a change that did not need it. See
[`templates/pre-check-gate.md`](./templates/pre-check-gate.md).

## What has not been shown

- That the protocol generalizes to every domain. Domain-specific correctness still
  depends on the reviewer model's capability in that domain.
- That the Critical/Important/Minor taxonomy is the best one.
- That the pass-floor formula suits every operational context. Safety-critical or
  regulated work may want a stricter floor; other contexts may want a looser one.
- Any accuracy, calibration, or inter-reviewer agreement figure.

## What a stronger evidence base would need

Controlled comparisons against alternative review approaches, false-positive and
false-negative rates on a held-out set, and multi-author corpora with public
receipts. That is future work, not a present claim.
