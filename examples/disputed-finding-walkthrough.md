# Worked Example: A Disputed Finding

The [R1 → R2 walkthrough](./r1-r2-walkthrough.md) shows the easy case: the reviewer is right, the author agrees, the findings get fixed. This example shows the hard case: **the reviewer raises a finding the author believes is wrong.** That's the protocol's sharpest judgment call, because it sits directly on the gap [PROTOCOL.md §4](../PROTOCOL.md) names: the floor decides ship/no-ship *given the findings as classified*, but it does not guarantee the reviewer classified correctly.

Synthetic again, chosen to illustrate the mechanics, not to represent a real review.

---

## The work product

A change to a pricing function. The author has refactored how an order discount is applied.

```python
# pricing.py - modified
def apply_discount(order, discount_rate):
    """Return the order total after applying a fractional discount."""
    return order.subtotal * (1 - discount_rate)
```

The author dispatches Code RJ.

---

## R1 verdict

```
ROUND: R1
MODALITY: code

SCORE: 6.5/10

CRITICAL (C):
  - C-1: apply_discount does not validate that discount_rate <= 1.0. A rate
         above 1.0 produces a negative multiplier and returns a negative
         total, which propagates into billing as a credit the customer
         never earned.

IMPORTANT (I):
  None

MINOR (M):
  - M-1: No docstring note on the expected range of discount_rate.

VERDICT: REWORK
```

The author reads C-1 and immediately disagrees: *that can't happen.* `discount_rate` only ever comes from `load_discount_config()`, which clamps every rate to `[0, 0.9]`. No caller can pass a value above 1.0. The reviewer flagged a bug that doesn't exist in the running system.

This is the moment the protocol is built for. There are three things the author could do, and only one of them is the protocol.

---

## The wrong move (and why)

The tempting move: *the reviewer is wrong, I'll ship.* The author knows the call site. The reviewer only saw the diff. Author wins, right?

No, and not because the author is necessarily wrong about the facts. It's because **a Critical is not the author's to overrule.** [PROTOCOL.md §5.5](../PROTOCOL.md) is explicit: the Operator override exists only for Important findings, with a documented who/which/why/date, and *Critical findings are not subject to override at all.* The entire point of the floor is to remove the "it's basically fine, ship it" discretion, and "I know this finding is wrong" is exactly that discretion wearing a confident face. If the author can dissolve a Critical by being sure, the floor is decorative.

So "I'm sure it's a false positive" is not a halt condition. It's the start of one of the two real moves below.

---

## The right move: assume the reviewer is right, then look

The author re-reads C-1 as if it were correct and asks *what would have to be true.* Two things are immediately clear:

1. **The reviewer's literal claim is a false positive.** The author greps the callers. Every call to `apply_discount` is fed by `load_discount_config()`, which clamps to `[0, 0.9]`. In the system as it stands, no negative total can occur. The reviewer, scoped to the diff, could not see that guarantee.
2. **The reviewer's underlying point is real.** The safety of `apply_discount` lives entirely in an *implicit* contract enforced by one caller. `apply_discount` is a public function with no guard of its own. The next engineer to call it directly (a batch job, a test fixture, a new endpoint) reintroduces the exact bug C-1 describes, and nothing stops them.

This is the usual anatomy of a "false positive": a true finding about a latent fragility, mis-scoped as an active bug because the reviewer only sees the diff. The reviewer was wrong about the system as it runs today, and right about the function itself.

So the author does not argue. The author makes the implicit contract explicit:

```python
# pricing.py - revised
def apply_discount(order, discount_rate):
    """Return the order total after applying a fractional discount.

    discount_rate must be in [0, 1]. Callers typically source it from
    load_discount_config(), which clamps to [0, 0.9].
    """
    if not 0 <= discount_rate <= 1:
        raise ValueError(f"discount_rate out of range: {discount_rate!r}")
    return order.subtotal * (1 - discount_rate)
```

R2 dispatch includes the revised diff and one line of context: *C-1 could not occur via current callers (config clamps to [0, 0.9]), but the function had no guard of its own; added an explicit range check and documented the contract.*

```
ROUND: R2
MODALITY: code

SCORE: 9.5/10

CRITICAL (C):
  None

IMPORTANT (I):
  None

MINOR (M):
  None

VERDICT: PASS
```

The "false positive" produced a real improvement. The author never had to win the argument, because making the contract explicit dissolved the dispute.

---

## The harder branch: the dispute survives

Sometimes there is genuinely nothing to fix: the reviewer misread the code, the finding is wrong on the facts, and there is no latent fragility to harden. The author provides the missing context in the R2 dispatch and the reviewer **withdraws** the finding. That is the normal resolution, and it is a *verdict* withdrawing the finding, not the author dismissing it.

But suppose the reviewer holds. R2 still asserts C-1, and the author still believes it's wrong. Now what?

Still not author fiat. The escape hatch is an **independent second opinion**, per [PROTOCOL.md §9.4](../PROTOCOL.md) (cross-model dispatch): send the same work product and the disputed verdict to a different model.

- If the second reviewer also holds C-1, the author is almost certainly the one who is wrong. Two independent adversarial reviewers converging on a finding is strong signal.
- If the second reviewer withdraws it after seeing the context, you have evidence the finding was model-specific, the kind of artifact (position bias, a misread) the [Prior art](../README.md#prior-art) literature predicts. You ship on the second verdict, and you have a record of *why*.

Either way, the thing that resolves the dispute is a verdict from a reviewer the author doesn't control, not the author's confidence.

---

## What to notice

- **A disputed Critical is not resolved by the author deciding they're right.** §5.5: Critical findings are not overridable. "I'm sure it's a false positive" is the start of a process, not a halt condition.
- **"False positive" usually decomposes into "true finding, wrong scope."** The reviewer sees the diff, not the system; context-dependent safety reads as unsafe. Making the implicit contract explicit converts most disputes into improvements and ends the argument.
- **The genuine-false-positive escape hatch is an independent reviewer (§9.4), not self-certification.** The dispute is broken by a verdict the author doesn't control.
- **The one move the protocol forbids is the tempting one:** ignoring a Critical because you *know* it's wrong. That is precisely the discretion-creep the floor exists to remove.

---

## See also

- [R1 → R2 walkthrough](./r1-r2-walkthrough.md) - the clean case, where author and reviewer agree.
- [PROTOCOL.md §4](../PROTOCOL.md) - the floor as a contract over the decision, and the reviewer-reliability gap it does not close.
- [PROTOCOL.md §5.5](../PROTOCOL.md) - halt conditions and the Operator-override boundary (Importants only; Criticals never).
- [PROTOCOL.md §9.4](../PROTOCOL.md) - cross-model dispatch.
