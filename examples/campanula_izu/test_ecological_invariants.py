"""Ecological invariant tests for the Campanula / Izu RACH model.

These tests verify that the simulation honours the fundamental ecological
design guarantees that the ABC inference depends on:

1. NULL MODEL FAILS POM
   With all pathway switches OFF, the proxy simulation must NOT satisfy the
   gradient POM (6 gradient-direction patterns).  If the null model always
   passed the POM, every switch combination would be accepted, making the
   Bayes factors uninformative.

2. ISLAND-SYNDROME SWITCHES PASS POM
   With S1 (Bombus-guide link) + S2 (selfing syndrome) both ON, the proxy
   simulation must satisfy the full gradient POM across the isolation axis.

3. GUIDE-ONLY SWITCH (S4 drift) PASSES GUIDE PATTERNS, FAILS SELFING PATTERNS
   S4 alone should drive guide loss (passes nectar_guide_distance and
   nectar_guide_rank) but NOT produce the selfing syndrome (fails
   selfing_distance and selfing_rank), keeping S4 distinguishable from S2.

4. PARAMETER CONSTRAINTS ARE CONSISTENT ACROSS BOTH MODULES
   C1-C4 in parameter_constraints.py and parameter_sampling.py must agree
   on rejection decisions for the same parameter set.

5. INPUT_CONTEXT ROWS DO NOT AFFECT WEIGHTED_MATCH_RATE (Issue #7)
   The Bombus_frequency_pairwise row (role=input_context) must be excluded
   from weighted_match_rate.  If it were included, the Bombus gradient would
   always match (it is injected from ecological_context, not simulated),
   artificially inflating the acceptance rate for all switch combinations.

Run with:
    python examples/campanula_izu/test_ecological_invariants.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from repo root or from this directory
_repo = Path(__file__).resolve().parent.parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from causal_model.switches import PathwaySwitches
from examples.campanula_izu.observed_data import (
    load_observed_pattern_table,
    observed_gradient_only_patterns,
    response_target_patterns,
)
from examples.campanula_izu.pattern_evaluator import evaluate_patterns
from examples.campanula_izu.proxy_simulation import simulate_campanula_isolation_gradient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(sw: PathwaySwitches, n_points: int = 8):
    outputs, synth_env = simulate_campanula_isolation_gradient(sw, n_points=n_points)
    patterns = observed_gradient_only_patterns()
    result = evaluate_patterns(list(outputs.values()), patterns, synth_env)
    return result


def _all_off() -> PathwaySwitches:
    return PathwaySwitches()


def _s1_s2() -> PathwaySwitches:
    return PathwaySwitches(direct_pollinator_to_guide=1.0, selfing_mediation=1.0)


def _s4_only() -> PathwaySwitches:
    return PathwaySwitches(drift_null=1.0)


# ---------------------------------------------------------------------------
# Test 1: Null model must FAIL the gradient POM
# ---------------------------------------------------------------------------

def test_null_fails_pom():
    result = _run(_all_off())
    assert result.weighted_match_rate < 1.0, (
        f"FAIL test_null_fails_pom: all-OFF model passed POM with "
        f"weighted_match_rate={result.weighted_match_rate:.3f} "
        f"(expected < 1.0). The POM has no discriminating power if the null "
        f"model passes — all switch combinations would be accepted."
    )
    print(f"[PASS] test_null_fails_pom  "
          f"match_rate={result.weighted_match_rate:.3f}  "
          f"matched={result.n_matched}/{result.n_total}")


# ---------------------------------------------------------------------------
# Test 2: S1+S2 must PASS the full gradient POM (6/6)
# ---------------------------------------------------------------------------

def test_island_syndrome_passes_pom():
    result = _run(_s1_s2())
    assert result.weighted_match_rate >= 1.0 - 1e-9, (
        f"FAIL test_island_syndrome_passes_pom: S1+S2 model matched only "
        f"{result.n_matched}/{result.n_total} patterns "
        f"(weighted_match_rate={result.weighted_match_rate:.3f}). "
        f"S1+S2 should always satisfy the full island-syndrome gradient POM."
    )
    print(f"[PASS] test_island_syndrome_passes_pom  "
          f"match_rate={result.weighted_match_rate:.3f}  "
          f"matched={result.n_matched}/{result.n_total}")


# ---------------------------------------------------------------------------
# Test 3: S4 (drift) passes guide patterns, fails selfing patterns
# ---------------------------------------------------------------------------

def test_s4_passes_guide_fails_selfing():
    result = _run(_s4_only())
    by_name = {m.pattern: m for m in result.matches}

    guide_slope  = by_name.get("nectar_guide_distance")
    guide_rank   = by_name.get("nectar_guide_rank")
    selfing_slope = by_name.get("selfing_distance")
    selfing_rank  = by_name.get("selfing_rank")

    assert guide_slope  is not None, "Pattern 'nectar_guide_distance' not found"
    assert guide_rank   is not None, "Pattern 'nectar_guide_rank' not found"
    assert selfing_slope is not None, "Pattern 'selfing_distance' not found"
    assert selfing_rank  is not None, "Pattern 'selfing_rank' not found"

    guide_ok   = guide_slope.matched or guide_rank.matched
    selfing_ok = selfing_slope.matched and selfing_rank.matched

    assert guide_ok, (
        f"FAIL test_s4_passes_guide_fails_selfing: S4 alone did not drive "
        f"guide loss — neither nectar_guide_distance nor nectar_guide_rank "
        f"matched.  guide_slope={guide_slope.detail}  "
        f"guide_rank={guide_rank.detail}"
    )
    assert not selfing_ok, (
        f"FAIL test_s4_passes_guide_fails_selfing: S4 alone produced a "
        f"full selfing syndrome (both selfing_distance and selfing_rank "
        f"matched).  S4 should be the 'drift null' — guide loss without "
        f"selfing syndrome.  selfing_slope={selfing_slope.detail}  "
        f"selfing_rank={selfing_rank.detail}"
    )
    print(f"[PASS] test_s4_passes_guide_fails_selfing  "
          f"guide_matched={guide_ok}  selfing_matched={selfing_ok}")


# ---------------------------------------------------------------------------
# Test 4: Constraint modules agree on rejection decisions
# ---------------------------------------------------------------------------

def test_constraint_modules_consistent():
    from causal_model.parameter_constraints import (
        check_ecological_parameter_constraints as check_a,
    )
    from causal_model.parameter_sampling import (
        check_ecological_parameter_constraints as check_b,
    )

    test_cases = [
        # (description, param_dict)
        ("nominal valid",
         {"guide_cost": 0.05, "outcrossing_benefit": 0.3, "selfing_benefit": 0.2,
          "inbreeding_depression": 0.2, "background_pollinator_efficiency": 0.3,
          "drift_strength": 0.05, "direct_pollinator_guide_benefit": 0.5,
          "cost_of_waiting_for_pollinators": 0.2}),
        ("C1 violation: extreme inbreeding",
         {"guide_cost": 0.05, "outcrossing_benefit": 0.3, "selfing_benefit": 0.1,
          "inbreeding_depression": 0.8, "background_pollinator_efficiency": 0.3,
          "drift_strength": 0.05, "direct_pollinator_guide_benefit": 0.5,
          "cost_of_waiting_for_pollinators": 0.2}),
        ("C2 violation: high bg_eff + high selfing_benefit",
         {"guide_cost": 0.05, "outcrossing_benefit": 0.3, "selfing_benefit": 0.70,
          "inbreeding_depression": 0.1, "background_pollinator_efficiency": 0.60,
          "drift_strength": 0.05, "direct_pollinator_guide_benefit": 0.5,
          "cost_of_waiting_for_pollinators": 0.2}),
        ("C4 violation: bg_eff >= primary_eff (0.80)",
         {"guide_cost": 0.05, "outcrossing_benefit": 0.3, "selfing_benefit": 0.2,
          "inbreeding_depression": 0.1, "background_pollinator_efficiency": 0.85,
          "drift_strength": 0.05, "direct_pollinator_guide_benefit": 0.5,
          "cost_of_waiting_for_pollinators": 0.2}),
    ]

    for desc, params in test_cases:
        ra = check_a(params)
        rb = check_b(params)
        assert ra.valid == rb.valid, (
            f"FAIL test_constraint_modules_consistent [{desc}]: "
            f"parameter_constraints says valid={ra.valid} "
            f"({ra.failed_constraints}) but parameter_sampling says "
            f"valid={rb.valid} ({rb.failed_constraints}).  "
            f"C1-C4 must agree between both modules."
        )
        print(f"[PASS] constraint consistency [{desc}]  valid={ra.valid}")


# ---------------------------------------------------------------------------
# Test 5: input_context rows must NOT affect weighted_match_rate (Issue #7)
# ---------------------------------------------------------------------------

def test_input_context_excluded_from_abc():
    """Verify input_context rows are not counted in weighted_match_rate.

    The Bombus_frequency_pairwise row has role=input_context.  It must be
    absent from the EvaluationResult produced by evaluate_patterns().

    Two checks:
    a) response_target_patterns() returns no input_context rows.
    b) evaluate_patterns() with a mixed list (gradient rows + one synthetic
       input_context row) produces the same weighted_match_rate as with the
       response_target-only list — the defensive role guard must filter it out.

    Note: pairwise rows (e.g. nectar_guide_pairwise) require named populations
    (Oshima, Hachijo) that do not exist in the synthetic isolation gradient.
    The test therefore uses gradient_slope / rank_order rows only, plus one
    injected input_context row with the same type, to isolate the role guard.
    """
    all_rows = load_observed_pattern_table()
    rt_rows  = response_target_patterns()

    # a) response_target_patterns() must contain no input_context rows
    input_context_in_rt = [r for r in rt_rows if r.get("role") == "input_context"]
    assert not input_context_in_rt, (
        f"FAIL test_input_context_excluded_from_abc (a): "
        f"response_target_patterns() returned {len(input_context_in_rt)} "
        f"input_context row(s): {[r['pattern'] for r in input_context_in_rt]}. "
        f"Only response_target rows should be included."
    )

    # b) evaluate_patterns() must skip input_context rows via the role guard.
    #    Build a gradient-only test list so no named population lookup is needed.
    sw = PathwaySwitches()
    outputs, synth_env = simulate_campanula_isolation_gradient(sw, n_points=8)

    gradient_rt = [
        r for r in rt_rows
        if r.get("type", "") in ("gradient_slope", "rank_order")
    ]
    # Synthetic input_context row: same type as gradient, but role=input_context.
    # If the guard works, adding this row must NOT change weighted_match_rate.
    synthetic_input_ctx = {
        "pattern": "synthetic_predictor",
        "type": "gradient_slope",
        "variable": "nectar_guide",          # same variable — would always match
        "populations": "",
        "predictor": "distance_from_mainland",
        "expected_direction": "negative",    # matches the real gradient
        "weight": "999.0",                   # enormous weight — would dominate if not skipped
        "role": "input_context",
    }
    mixed_rows = gradient_rt + [synthetic_input_ctx]

    result_rt    = evaluate_patterns(list(outputs.values()), gradient_rt,  synth_env)
    result_mixed = evaluate_patterns(list(outputs.values()), mixed_rows,   synth_env)

    assert result_mixed.weighted_match_rate == result_rt.weighted_match_rate, (
        f"FAIL test_input_context_excluded_from_abc (b): "
        f"evaluate_patterns() with mixed list gave "
        f"weighted_match_rate={result_mixed.weighted_match_rate:.4f} but "
        f"with response_target-only list gave "
        f"{result_rt.weighted_match_rate:.4f}. "
        f"The role guard is not excluding input_context rows correctly. "
        f"(A weight-999 input_context row was injected.)"
    )
    assert result_mixed.n_total == result_rt.n_total, (
        f"FAIL test_input_context_excluded_from_abc (b): "
        f"n_total differs: mixed={result_mixed.n_total} vs rt={result_rt.n_total}. "
        f"input_context rows are leaking into EvaluationResult."
    )
    n_input_ctx = sum(1 for r in all_rows if r.get("role") == "input_context")
    print(
        f"[PASS] test_input_context_excluded_from_abc  "
        f"n_input_context_in_csv={n_input_ctx}  "
        f"n_response_target_gradient={result_rt.n_total}  "
        f"match_rate_unchanged={result_rt.weighted_match_rate:.3f}"
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    failures = []
    tests = [
        test_null_fails_pom,
        test_island_syndrome_passes_pom,
        test_s4_passes_guide_fails_selfing,
        test_constraint_modules_consistent,
        test_input_context_excluded_from_abc,
    ]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"\n{'='*60}")
            print(str(e))
            print('='*60)
            failures.append(t.__name__)
        except Exception as e:
            print(f"\n[ERROR] {t.__name__}: {e}")
            failures.append(t.__name__)

    print()
    if failures:
        print(f"FAILED: {failures}")
        sys.exit(1)
    else:
        print(f"All {len(tests)} ecological invariant tests passed.")
