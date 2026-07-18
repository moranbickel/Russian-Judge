#!/usr/bin/env python3
"""Floor-invariant tests for schemas/verdict.schema.json (finding C-1).

The default pass floor is: score >= 9.0 AND 0 Critical AND 0 Important.
Minor findings do NOT affect the default floor. The Minor-inclusive and
Relaxed-Minor variants (PROTOCOL.md sec 4.5) are selected via the optional
record.floor_variant field; they never change the default semantics of
pass_asserted.

These tests validate example verdicts against the schema. A verdict that
carries record.pass_asserted MUST satisfy the floor that its floor_variant
selects; the schema enforces this so a malformed pass assertion is rejected
rather than silently accepted.

Run: python tests/test_verdict_schema_floor.py
Requires: jsonschema (pip install jsonschema)
"""
import json
import pathlib
import sys

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("FAIL: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

SCHEMA_PATH = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "verdict.schema.json"


def base(score, n_c=0, n_i=0, n_m=0, pass_asserted=None, floor_variant=None, verdict="PASS"):
    """Build a structurally-valid verdict; only the floor fields vary."""
    doc = {
        "round": "R2",
        "modality": "code",
        "score": score,
        "findings": {
            "critical": [{"id": f"C-{k+1}", "description": "x.", "impact": "y."} for k in range(n_c)],
            "important": [{"id": f"I-{k+1}", "description": "x.", "impact": "y."} for k in range(n_i)],
            "minor": [{"id": f"M-{k+1}", "description": "x."} for k in range(n_m)],
        },
        "verdict": verdict,
    }
    if pass_asserted is not None:
        rec = {"pass_asserted": pass_asserted}
        if floor_variant is not None:
            rec["floor_variant"] = floor_variant
        doc["record"] = rec
    return doc


# (name, doc, should_validate)
CASES = [
    # --- The ruled key case: default floor permits Minors. 9.2 / 0C / 0I / 2M is a PASS. ---
    ("default_pass_two_minors", base(9.2, n_m=2, pass_asserted=True), True),
    ("default_pass_zero_findings", base(9.4, pass_asserted=True), True),

    # --- Malformed pass assertions under the default floor: RED source. ---
    ("malformed_pass_with_critical", base(9.2, n_c=1, pass_asserted=True), False),
    ("malformed_pass_with_important", base(9.5, n_i=1, pass_asserted=True), False),
    ("malformed_pass_subfloor_score", base(8.9, pass_asserted=True), False),

    # --- pass_asserted:false is not constrained by the floor (it is not a pass claim). ---
    ("honest_fail_below_floor", base(8.0, n_c=2, pass_asserted=False, verdict="REVISE"), True),

    # --- Ad-hoc verdict with no record: floor fields absent, unconstrained. ---
    ("adhoc_no_record_two_minors", base(9.2, n_m=2), True),

    # --- Minor-inclusive variant: Minors DO block. ---
    ("minor_inclusive_clean", base(9.1, pass_asserted=True, floor_variant="minor_inclusive"), True),
    ("minor_inclusive_blocks_minor", base(9.1, n_m=1, pass_asserted=True, floor_variant="minor_inclusive"), False),

    # --- Relaxed-Minor variant: score bar 8.5, one Minor allowed. ---
    ("relaxed_minor_pass", base(8.7, n_m=1, pass_asserted=True, floor_variant="relaxed_minor"), True),
    ("relaxed_minor_subfloor_score", base(8.3, pass_asserted=True, floor_variant="relaxed_minor"), False),
    ("relaxed_minor_blocks_critical", base(9.0, n_c=1, pass_asserted=True, floor_variant="relaxed_minor"), False),
]


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    failures = []
    for name, doc, should_validate in CASES:
        errors = list(validator.iter_errors(doc))
        did_validate = not errors
        ok = did_validate == should_validate
        status = "ok  " if ok else "FAIL"
        print(f"[{status}] {name}: validated={did_validate} expected={should_validate}")
        if not ok:
            failures.append((name, should_validate, did_validate,
                             [e.message for e in errors][:2]))
    print()
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for name, exp, got, msgs in failures:
            print(f"  - {name}: expected validate={exp}, got {got}. {msgs}")
        sys.exit(1)
    print(f"All {len(CASES)} floor cases pass.")
    sys.exit(0)


if __name__ == "__main__":
    main()
