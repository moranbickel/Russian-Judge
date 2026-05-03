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

VERDICT: REVISE
```

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
    ]
  },
  "verdict": "REVISE"
}
```

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
- **Empty classes** — represented as `None` (markdown) or `[]` (JSON), never omitted.

---

## Anti-patterns the format catches

- **Untyped findings.** "Issue" or "Concern" without a class. The format has no slot for them.
- **Findings without IDs.** Cannot be referenced in R2 dispatches.
- **Vibe verdicts.** A score with no findings list. The format requires the list, even if empty.
- **Verdict-score inconsistency.** A `PASS` with Critical findings is malformed. Validators should reject.
