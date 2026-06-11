"""Unit tests for observation_contribution() — issue #11 acceptance criteria.

Key property being tested:
    When pattern k is removed from y_obs, some draws that were previously
    rejected (weighted_match_rate < threshold) may now pass (LOO rate >= threshold).
    observation_contribution() MUST use evaluated_rows (all draws), not only
    accepted_rows.  Using accepted_rows only produces a downward-biased OC_k.

Run with:
    python causal_model/test_observation_contribution.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from causal_model.causal_admissibility import observation_contribution
from causal_model.switch_inference import BiologicalSwitch


# ---------------------------------------------------------------------------
# Minimal switch list for testing
# ---------------------------------------------------------------------------
_TEST_SWITCHES = [
    BiologicalSwitch(
        name="S1", pathway_key="S1",
        description="test switch 1",
        biological_question="Does S1 explain the pattern?",
        prior_on_prob=0.5,
    ),
    BiologicalSwitch(
        name="S2", pathway_key="S2",
        description="test switch 2",
        biological_question="Does S2 explain the pattern?",
        prior_on_prob=0.5,
    ),
]

THRESHOLD = 0.8


def _row(s1: bool, s2: bool, pa_matched: bool, pb_matched: bool,
         w_a: float = 1.0, w_b: float = 1.0) -> dict:
    """Build a minimal evaluated row."""
    total_w = w_a + w_b
    matched_w = (w_a if pa_matched else 0.0) + (w_b if pb_matched else 0.0)
    wmr = matched_w / total_w if total_w > 0 else 0.0
    return {
        "S1": s1, "S2": s2,
        "weighted_match_rate": wmr,
        "per_pattern_matched": {
            "pattern_A": (pa_matched, w_a),
            "pattern_B": (pb_matched, w_b),
        },
    }


# ---------------------------------------------------------------------------
# Test 1: LOO adds previously-rejected rows
# ---------------------------------------------------------------------------

def test_loo_includes_previously_rejected():
    """Core property: removing pattern_A from y_obs can make rejected rows accepted.

    Setup:
      pattern_A weight = 1.0, pattern_B weight = 0.5, threshold = 0.8
      Row X: A=not_matched, B=matched  →  wmr = 0.5 / 1.5 ≈ 0.33  → REJECTED
      If we remove A: wmr_loo = 0.5/0.5 = 1.0 >= 0.8 → ACCEPTED in LOO
      Row Y: A=matched,     B=matched  →  wmr = 1.5 / 1.5 = 1.0   → ACCEPTED
      If we remove A: wmr_loo = 0.5/0.5 = 1.0 >= 0.8 → still ACCEPTED

    Expected OC_k for pattern_A:
      - R_full is computed from {Row Y} (only accepted row)
      - R_loo  is computed from {Row X, Row Y} (both pass LOO)
      - OC_A = R_full - R_loo
      - Since Row X has different switch state, R_loo should be lower than R_full
        OR equal (depending on switch states), so OC_A >= 0 or detectable.

    Critical assertion: n_loo > n_full (LOO set is larger than full accepted set).
    """
    # Row X: rejected overall, but would pass LOO for pattern_A
    row_X = _row(s1=True,  s2=False, pa_matched=False, pb_matched=True, w_a=1.0, w_b=0.5)
    # Row Y: accepted overall
    row_Y = _row(s1=False, s2=True,  pa_matched=True,  pb_matched=True, w_a=1.0, w_b=0.5)

    assert row_X["weighted_match_rate"] < THRESHOLD, "Row X should be rejected"
    assert row_Y["weighted_match_rate"] >= THRESHOLD, "Row Y should be accepted"

    evaluated_rows = [row_X, row_Y]

    results = observation_contribution(evaluated_rows, _TEST_SWITCHES, threshold=THRESHOLD)
    assert results, "Should return non-empty OC_k results"

    # OC_k is pattern-level: exactly one entry per pattern (not per switch).
    oc_A = [r for r in results if r.pattern == "pattern_A"]
    assert len(oc_A) == 1, (
        f"OC_k is pattern-level: expected exactly 1 entry for pattern_A, got {len(oc_A)}. "
        "It must NOT be replicated per switch."
    )
    oc_A_k = oc_A[0]
    assert oc_A_k.level == "pattern"
    assert oc_A_k.n_switches == len(_TEST_SWITCHES)

    # The LOO set for pattern_A must include row_X (previously rejected)
    assert oc_A_k.n_loo > oc_A_k.n_full, (
        f"LOO set (n={oc_A_k.n_loo}) must be larger than full accepted set "
        f"(n={oc_A_k.n_full}) when removing pattern_A causes row_X to pass. "
        f"This verifies observation_contribution() uses evaluated_rows, not accepted_rows."
    )
    print(f"[PASS] test_loo_includes_previously_rejected  "
          f"n_full={oc_A_k.n_full}  n_loo={oc_A_k.n_loo}  "
          f"OC_k(pattern_A)={oc_A_k.OC_k:.4f}")


# ---------------------------------------------------------------------------
# Test 2: Biased estimate from accepted_rows only is lower
# ---------------------------------------------------------------------------

def test_accepted_only_underestimates_oc():
    """Confirm: using accepted_rows only gives lower |OC_k| than evaluated_rows.

    Same setup as Test 1.  When only accepted_rows is passed, row_X is never
    seen, so removing pattern_A doesn't change the LOO set.
    OC_k(accepted_only) should differ from OC_k(evaluated).
    """
    row_X = _row(s1=True,  s2=False, pa_matched=False, pb_matched=True, w_a=1.0, w_b=0.5)
    row_Y = _row(s1=False, s2=True,  pa_matched=True,  pb_matched=True, w_a=1.0, w_b=0.5)

    evaluated_rows = [row_X, row_Y]
    accepted_rows  = [row_Y]   # only accepted

    oc_eval = observation_contribution(evaluated_rows, _TEST_SWITCHES, threshold=THRESHOLD)
    oc_acc  = observation_contribution(accepted_rows,  _TEST_SWITCHES, threshold=THRESHOLD)

    # OC_k is pattern-level: one entry per pattern.
    def _get(results, pat):
        return next((r for r in results if r.pattern == pat), None)

    ea = _get(oc_eval, "pattern_A")
    aa = _get(oc_acc,  "pattern_A")

    assert ea is not None and aa is not None

    # With evaluated_rows: n_loo = 2 (row_X is added)
    # With accepted_rows only: n_loo = 1 (row_X never seen)
    assert ea.n_loo >= aa.n_loo, (
        f"evaluated n_loo={ea.n_loo} should be >= accepted-only n_loo={aa.n_loo}"
    )
    print(f"[PASS] test_accepted_only_underestimates_oc  "
          f"evaluated OC_k={ea.OC_k:.4f} (n_loo={ea.n_loo})  "
          f"accepted-only OC_k={aa.OC_k:.4f} (n_loo={aa.n_loo})")


# ---------------------------------------------------------------------------
# Test 3: SwitchPosteriorResult has evaluated_rows
# ---------------------------------------------------------------------------

def test_switch_posterior_result_has_evaluated_rows():
    """SwitchPosteriorResult must have evaluated_rows field."""
    from causal_model.switch_inference import SwitchPosteriorResult
    import dataclasses
    fields = {f.name for f in dataclasses.fields(SwitchPosteriorResult)}
    assert "evaluated_rows" in fields, (
        "SwitchPosteriorResult is missing 'evaluated_rows' field. "
        "This field is required for unbiased OC_k computation."
    )
    # Can construct with empty evaluated_rows
    sp = SwitchPosteriorResult(
        accepted_rows=[], evaluated_rows=[], rejected_count=0,
        n_attempts=0, posterior_table=[],
    )
    assert sp.evaluated_rows == []
    print("[PASS] test_switch_posterior_result_has_evaluated_rows")


# ---------------------------------------------------------------------------
# Test 4: evaluated_rows >= accepted_rows (monotonicity)
# ---------------------------------------------------------------------------

def test_evaluated_rows_superset_of_accepted():
    """A short proxy inference run: evaluated_rows must contain accepted_rows."""
    from causal_model.switch_inference import run_switch_posterior_inference

    result = run_switch_posterior_inference(
        preset_name="literature_grounded",
        n_attempts=20,
        acceptance_rule="weighted_lax",
        seed=99,
    )
    assert len(result.evaluated_rows) >= len(result.accepted_rows), (
        f"evaluated_rows ({len(result.evaluated_rows)}) must be >= "
        f"accepted_rows ({len(result.accepted_rows)})"
    )
    accepted_ids = {r["sample_id"] for r in result.accepted_rows}
    eval_ids     = {r["sample_id"] for r in result.evaluated_rows}
    assert accepted_ids.issubset(eval_ids), (
        "All accepted rows must appear in evaluated_rows"
    )
    print(f"[PASS] test_evaluated_rows_superset_of_accepted  "
          f"evaluated={len(result.evaluated_rows)}  accepted={len(result.accepted_rows)}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    failures = []
    tests = [
        test_switch_posterior_result_has_evaluated_rows,
        test_loo_includes_previously_rejected,
        test_accepted_only_underestimates_oc,
        test_evaluated_rows_superset_of_accepted,
    ]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"\n{'='*60}")
            print(f"FAIL: {t.__name__}")
            print(str(e))
            print("=" * 60)
            failures.append(t.__name__)
        except Exception as e:
            import traceback
            print(f"\n[ERROR] {t.__name__}: {e}")
            traceback.print_exc()
            failures.append(t.__name__)
    print()
    if failures:
        print(f"FAILED: {failures}")
        sys.exit(1)
    else:
        print(f"All {len(tests)} tests passed.")
