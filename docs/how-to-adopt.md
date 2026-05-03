# How to Adopt Russian Judge

Concrete steps to start using RJ today. Estimated time to functional adoption: **15 minutes**. Estimated time to fluent use: **a week of real work**.

---

## Day one — the 15-minute setup

### Step 1. Pick your reviewer.

Use whichever capable LLM you have access to. Claude (Sonnet or Opus) and GPT-5 work well for general code and prose review. For domain-specific work (legal, medical, regulated), prefer the model that demonstrates the strongest domain capability in your evaluations.

### Step 2. Open a new session for the reviewer.

Keep RJ sessions separate from other work. Don't mix the adversarial primer with sessions where you also want collaborative help — the primer is sticky and will degrade collaborative behavior.

### Step 3. Paste the priming.

Copy the system message from [`templates/reviewer-prompt.md`](../templates/reviewer-prompt.md). Paste it as the system message of your new session. Pick the modality (Code, Domain) that fits the work product.

### Step 4. Run your first review.

Paste a recent code change or piece of writing as the first user message. The reviewer should return a verdict in the §7 format. If it returns prose preamble or a vibe score, the priming did not take — start a new session and re-paste.

### Step 5. Apply the floor.

If the verdict is `score ≥ 9.0 AND 0 Critical AND 0 Important`, you ship. Otherwise, address the C/I findings and dispatch R2 with the addendum from the templates.

That's the loop.

---

## Week one — building the discipline

### Day 1–2: Run RJ on every non-trivial change.

You're calibrating the reviewer to your work and yourself to the protocol. Expect noise in the first few verdicts — Minors that aren't Minors, classification calls you disagree with. Don't fix it yet. Just observe. (You're intentionally widening the gate during calibration to learn the protocol's noise floor — Day 3–4 will tighten it back via the pre-check gate.)

### Day 3–4: Start using the pre-check gate.

Apply the gate from [`templates/pre-check-gate.md`](../templates/pre-check-gate.md) before invoking RJ. You'll find that maybe half of what you were sending to RJ doesn't need RJ. Skip those. The signal-to-noise ratio of RJ output should improve immediately.

### Day 5–6: Track your halts.

For each RJ session, note: how many rounds did it take to converge? What was the final score? Were any verdicts overridden by you? After a week, you'll have a picture of how RJ is interacting with your work.

### Day 7: Audit verdict distributions.

If most of your verdicts are scoring 8.0–9.5, the protocol is working. If they're clustering at 9.5+, your reviewer is inflating — re-prime with more emphasis on conservative scoring. If they're clustering at 7–8, the work coming into RJ is too rough — invoke RJ later in your authoring process, after you've self-reviewed.

---

## Week two and beyond — fluency

### Add Dual RJ for high-stakes work.

When a change touches both code and domain content, run both modalities. Two sessions, two primings, two independent verdicts. The work passes only if both pass.

### Add cross-model dispatch.

If you have access to multiple capable models, periodically dispatch the same review to a different model. Different models have different blind spots. I have personally watched a different model find a Critical defect that three previous rounds with the same model missed. The asymmetry between cost (one extra dispatch) and benefit (a defect that wouldn't have been caught) is dramatic.

### Establish team conventions.

If you're working with collaborators, agree on:
- Which modality is the default for which kind of change.
- Who is allowed to override Critical findings (often: nobody).
- Who is allowed to override Important findings.
- Where verdicts are stored — in commit messages, in a review log, or ephemerally.

### Refuse the recursive-review temptation.

The protocol is not "review until you get a 10." After R2/R3, you're extracting noise. The discipline is to halt at the floor when the floor is met, even when you suspect the work is "really" 8.7 and not 9.1. The reviewer's verdict is the verdict.

---

## What "fluent use" looks like

You'll know you've adopted RJ when:

- You run it without thinking about it on changes that pass the gate.
- You don't run it on changes that don't.
- You stop reading verdicts as praise or criticism — you read them as a structured signal that tells you what to do next.
- You ship at the floor without seeking reassurance above it.
- You halt at R2/R3 without seeking a fourth round.
- Your verdict distributions stabilize in the 8.0–9.5 band, with occasional outliers in both directions.

This typically takes 2–4 weeks of consistent use.

---

## Common adoption failures

**Skipping the priming and asking the model "review this rigorously."** Doesn't work. The priming is load-bearing.

**Combining RJ with collaborative help in the same session.** The priming is sticky and degrades the collaborative parts. The collaborative parts are sticky and degrade the priming. Separate sessions.

**Treating the score as the floor.** The most common failure. `score ≥ 9.0` alone is not the pass criterion. The conjunction with `0 Critical AND 0 Important` is.

**Negotiating findings.** "Reviewer, this Important finding is actually Minor — please reclassify." The protocol does not support in-session negotiation. If you disagree with classification, address the finding and let R2 reveal whether the reviewer holds.

**Running RJ on everything.** Trains you to skim verdicts. Skim verdicts means missed findings on real changes. Use the gate.

---

## When RJ doesn't fit your work

Some work products genuinely don't benefit from RJ:

- Exploratory code that you'll throw away after answering a question.
- First drafts of prose where you know structural rewrites are coming.
- Configuration tweaks where the test of correctness is "does it run."

The pre-check gate catches most of these. When in doubt: if you cannot articulate what failure mode RJ would defend against on this specific change, you don't need RJ.

---

## Need help?

Issues and discussions on this repo are open. If you adopt RJ in your work and find a sharp edge that the protocol doesn't address, I want to know.

— Moran Bickel
