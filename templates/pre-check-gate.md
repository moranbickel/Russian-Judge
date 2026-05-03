# Pre-Check Gate

Before invoking Russian Judge on a change, run this thirty-second check. It prevents you from running RJ on changes that don't need it — which both wastes cycles and trains you to ignore RJ output when it does matter.

---

## The single test

> **Can this change introduce a new failure mode?**

If yes → invoke RJ.
If no → ship without RJ.

That's the gate. Everything below is elaboration.

---

## Decision flow

```
                       ┌──────────────────────────────────┐
                       │ I am about to ship a change.     │
                       └────────────────┬─────────────────┘
                                        │
                       ┌────────────────▼─────────────────┐
                       │ Does this change touch behavior? │
                       │ (Not just comments, formatting,  │
                       │  variable renames, doc typos.)   │
                       └────────────────┬─────────────────┘
                                        │
                            ┌───────────┴───────────┐
                            │ no                yes │
                            ▼                       ▼
                      ship without RJ        ┌──────────────────────────────┐
                                             │ Does it touch a contract?    │
                                             │ - module interface           │
                                             │ - file format consumed by    │
                                             │   another process            │
                                             │ - downstream-facing schema   │
                                             │ - public API                 │
                                             └──────────────┬───────────────┘
                                                            │
                                                ┌───────────┴───────────┐
                                                │ yes                no │
                                                ▼                       ▼
                                          INVOKE RJ           ┌──────────────────────────────┐
                                                              │ Could a defect here cause    │
                                                              │ - production breakage?       │
                                                              │ - data corruption?           │
                                                              │ - legal/regulatory harm?     │
                                                              │ - security exposure?         │
                                                              │ - substantive correctness    │
                                                              │   failure in primary purpose?│
                                                              └──────────────┬───────────────┘
                                                                             │
                                                                ┌────────────┴────────────┐
                                                                │ yes                  no │
                                                                ▼                         ▼
                                                          INVOKE RJ              ship without RJ
```

---

## Examples — INVOKE RJ

- **Code that touches a module contract.** Adding a parameter to a function whose callers are in another file. Even a "small" signature change.
- **A function that produces a file consumed by another process.** Schema changes are contract changes.
- **Domain content where a wrong word matters.** Legal claims, medical instructions, regulatory filings. Wrong = harm.
- **Refactors that change behavior boundaries.** Extracting a method, inlining a method, changing what's public.
- **A new feature touching existing flows.** New code paths can interact with existing paths in ways the author didn't anticipate.
- **A "small" fix to a function that other functions depend on.** Two-line changes that drop a guard are exactly how production breaks.
- **Spec changes that downstream code will consume.** Specs are contracts.

---

## Examples — SKIP RJ

- **Comment edits.** Changing wording in a `// TODO`. Adding a docstring that describes existing behavior accurately.
- **Variable renames within a single function.** Local-only, no external visibility.
- **Documentation typos.** README typos, README clarifications, README link fixes.
- **Style-only formatting.** Running a formatter, fixing whitespace, line-length adjustments.
- **Adding a log line.** Pure observability addition with no behavior change.
- **Test-only additions** (with care). Adding a new test for existing behavior. *Do invoke RJ if the test reveals existing behavior is wrong* — at that point the work product is "should this behavior change," not "is this test correct."
- **Merging a branch where each constituent commit was already reviewed.** Pulling a vendor SDK update, integrating an upstream branch, taking a routine main-pull. The review surface is the per-commit work, which the upstream authors already RJ'd. The merge itself is mechanical. *Do invoke RJ on integration conflicts that emerge during the merge — those are new changes.*

---

## Common mistake: "the change is small"

Size is not the gate. Failure-mode-introduction is the gate.

A two-line change that removes a null check is dangerous. A two-hundred-line change that follows an established pattern, with tests covering it, can be safe.

The question "is the change small?" trains the wrong instinct. The question "could this introduce a new failure mode?" trains the right one.

---

## Common mistake: "I don't have time for RJ"

If the change passes the gate, RJ is the cheap path. The expensive path is the production incident, the corrupted data, the wrong legal filing. RJ takes minutes; the consequences of skipped review can take days.

If you're tempted to skip RJ on a change that passed the gate, the right move is usually to ship a smaller change — one that *doesn't* pass the gate — and follow up with the riskier change separately.

---

## Common mistake: "RJ on everything is safer"

It isn't. RJ on changes that don't need it produces noise — Minor findings on cosmetic changes, low-confidence Importants on safe refactors. The noise trains you to skim verdicts. When you skim, you miss real findings on real changes. RJ on everything degrades RJ.

The discipline is: gate hard, then trust the protocol when it fires.

---

## A pocket version

If you'd rather memorize than consult a flowchart:

> **Skip RJ if and only if you can answer "what's the worst that could happen?" with "nothing."** If the worst case is anything other than "nothing," invoke RJ.
