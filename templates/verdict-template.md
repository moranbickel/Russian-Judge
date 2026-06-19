# Verdict Format

The Russian Judge verdict is a structured output. Two equivalent formats are supported: a human-readable markdown form and a JSON form for programmatic pipelines.

---

## Markdown form (default)

```
ROUND: R1
MODALITY: code

SCORE: 8.5/10

CRITICAL (C):
  None

IMPORTANT (I):
  - I-1: Edge case for negative inputs not handled. Function returns
         a negative value which propagates downstream and corrupts the
         relief calculation.
  - I-2: Test coverage drops from 94% to 71% on this module after the
         refactor. The removed tests covered rounding behavior, which
         the new implementation handles but no longer tests.

MINOR (M):
  - M-1: Variable name `tmp_calc` is uninformative. Suggest `subtotal`.

NOTES (N):
  None

VERDICT: REVISE
```

The `NOTES (N)` slot is optional and may be omitted entirely when the reviewer has no non-defect observations. When present, it holds remarks with no score or floor impact (PROTOCOL.md §3.6).

### Pass example

```
ROUND: R2
MODALITY: code

SCORE: 9.4/10

CRITICAL (C):
  None

IMPORTANT (I):
  None

MINOR (M):
  - M-1: Comment on line 47 is now stale and should be updated.

NOTES (N):
  - N-1: The module would benefit from a property-based test suite, but
         that is out of scope for this change.

VERDICT: PASS
```

### Rework example

```
ROUND: R1
MODALITY: code

SCORE: 6.5/10

CRITICAL (C):
  - C-1: The function signature contradicts the contract documented in
         the module's interface spec. Calling code will break.
  - C-2: No error handling for the network call. A transient failure
         will surface as an unhandled exception.

IMPORTANT (I):
  - I-1: Logic in lines 30-50 duplicates `helper_module.normalize`.
  - I-2: No tests for the new code path.

MINOR (M):
  None

VERDICT: REWORK
```

---

## JSON form (for programmatic pipelines)

A formal JSON Schema for the verdict shape lives at [`schemas/verdict.schema.json`](../schemas/verdict.schema.json). Use it to validate verdicts in CI pipelines.


```json
{
  "round": "R1",
  "modality": "code",
  "score": 8.5,
  "findings": {
    "critical": [],
    "important": [
      {
        "id": "I-1",
        "description": "Edge case for negative inputs not handled.",
        "impact": "Function returns a negative value which propagates downstream and corrupts the relief calculation."
      },
      {
        "id": "I-2",
        "description": "Test coverage drops from 94% to 71% on this module after the refactor.",
        "impact": "The removed tests covered rounding behavior, which the new implementation handles but no longer tests."
      }
    ],
    "minor": [
      {
        "id": "M-1",
        "description": "Variable name `tmp_calc` is uninformative. Suggest `subtotal`."
      }
    ],
    "notes": []
  },
  "verdict": "REVISE"
}
```

### JSON form with a verdict record

When verdicts are stored or piped (not just read once), attach the optional `record` block (PROTOCOL.md §13). It makes the verdict chainable, bindable, and attributable. A single-session user can omit it entirely; a programmatic pipeline carries it.

```json
{
  "round": "R2",
  "modality": "code",
  "score": 9.4,
  "findings": {
    "critical": [],
    "important": [],
    "minor": [],
    "notes": [
      {
        "id": "N-1",
        "description": "The GC is opportunistic and accumulates memory while idle — worth a docstring note, but out of scope for this change."
      }
    ]
  },
  "verdict": "PASS",
  "record": {
    "verdict_id": "9f2c1a7e-...",
    "predecessor_verdict": "1b4d8e02-...",
    "review_scope": {
      "code_dimensions": ["edge cases", "concurrency", "test coverage"],
      "domain_dimensions": []
    },
    "covers_range": "a1b2c3d..e4f5a6b",
    "reviewer_model": "<reviewer model id>",
    "review_round": "R2",
    "pass_asserted": true,
    "issued_at": "2026-06-19T100000Z"
  }
}
```

In this example the no-action remark that the reviewer wanted on the record is filed as a **Note** (`N-1`), not a Minor — so it carries no floor impact, and `pass_asserted: true` is consistent with a `0/0/0` blocking-class count. Filing the same remark as a Minor would, under a Minor-inclusive floor, have made `pass_asserted: true` a malformed verdict (see PROTOCOL.md §4.4).

### Verdict values

- `PASS` — `score >= 9.0 AND len(critical) == 0 AND len(important) == 0`
- `REVISE` — below the floor but `score >= 7.0`
- `REWORK` — `score < 7.0`

The verdict value is computed from the score and finding counts, not stated independently. Implementations should validate consistency.

---

## Field rules

- **`round`** — string identifier for the review round (`R1`, `R2`, etc.). Required in both forms.
- **`modality`** — one of `code`, `domain`, `dual`. Required in both forms.
- **`score`** — float in `[0.0, 10.0]`, one decimal of precision.
- **Finding `id`** — `<class-letter>-<index>`, indices start at 1, monotonically increasing within class.
- **Finding `description`** — single sentence, ends with a period.
- **Finding `impact`** — single sentence, required for Critical and Important, optional for Minor.
- **`notes`** — optional. Observations with no score or floor impact (out-of-scope, no-action, sibling-class, future-improvement), IDs `N-1`, `N-2`. Per PROTOCOL.md §3.6. A remark whose own wording says "no fix required" belongs here, not in `minor`.
- **`record`** — optional. The auditable-record metadata for stored / piped verdicts (PROTOCOL.md §13): `verdict_id`, `predecessor_verdict`, `review_scope`, `covers_range`, `reviewer_model`, `review_round`, `pass_asserted`, `issued_at`. Omit for ad-hoc single-session use.
- **`record.pass_asserted`** — when present, MUST equal `(score >= 9.0) AND (critical + important + minor == 0)` (the floor variant in force; PROTOCOL.md §4.4). Validators recompute and reject a mismatch.
- **Empty classes** — represented as `None` (markdown) or `[]` (JSON), never omitted.

---

## Anti-patterns the format catches

- **Untyped findings.** "Issue" or "Concern" without a class. The format has no slot for them.
- **Findings without IDs.** Cannot be referenced in R2 dispatches.
- **Vibe verdicts.** A score with no findings list. The format requires the list, even if empty.
- **Verdict-score inconsistency.** A `PASS` with Critical findings is malformed. Validators should reject.
- **Pass-assertion mismatch.** A stored verdict with `record.pass_asserted: true` and a non-zero blocking-class count. The floor invariant (PROTOCOL.md §4.4) is recomputed from the counts; the assertion is the claim, the counts are the ground truth.
- **No-action remark filed as Minor.** A reviewer with nothing to fix but something to say files it as a Minor, which can block under a Minor-inclusive floor. The Note class (`N-`) is where it belongs.
