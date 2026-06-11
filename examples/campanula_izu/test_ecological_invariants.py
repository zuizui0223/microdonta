"""Ecological invariant tests for the Campanula / Izu RACH model.

IMPORTANT — two distinct pattern sets are used here:

  observed_target   : field_derived Inoue-series gradient patterns.  These are
                      the ONLY valid y_obs for RACH inference.  Used in ABC
                      acceptance.

  hypothesis_prediction: gradient/rank patterns expected from hypotheses
                      but NOT directly measured.  Excluded from ABC to prevent
                      circular inference (using hypothesis predictions to test
                      hypotheses).  USED IN THESE TESTS for model mechanics
                      verification only — verifying the model CAN produce the
                      expected gradients when the relevant switches are ON.

These tests verify model MECHANICS, not ABC inference validity:

1. NULL MODEL FAILS GRADIENT POM (mechanics test, hypothesis_prediction)
   With all switches OFF, the model must NOT satisfy the gradient POM
   (hypothesis_prediction patterns).  This verifies the gradient patterns
   have discriminating power for model diagnostics.

2. ISLAND-SYNDROME SWITCHES PASS GRADIENT POM (mechanics test)
   With S1+S2 ON, the model must satisfy the full gradient.
   Confirms the selection mechanisms produce the expected gradients.

3. NULL MODEL PRODUCES NEUTRAL DIVERSITY GRADIENT (axiom test)
   Wright-Fisher drift is always active (finite population axiom).
   neutral_diversity must decline with isolation even with all switches OFF.

4. PARAMETER CONSTRAINTS CONSISTENT ACROSS MODULES

5. INPUT_CONTEXT / hypothesis_prediction EXCLUDED FROM ABC WEIGHTED_MATCH_RATE

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
    ABC_TARGET_ROLES,
)
from examples.campanula_izu.pattern_evaluator import evaluate_patterns
from examples.campanula_izu.campanula_phenomenological import simulate_campanula_isolation_gradient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gradient_patterns_for_mechanics():
    """Return gradient/rank patterns for MODEL MECHANICS tests.

    These are observed_target gradients plus hypothesis_prediction patterns,
    re-labelled as response_target so evaluate_patterns() will process them.
    This is valid here because we are testing MODEL BEHAVIOR (can the
    simulation produce the expected gradients?) not ABC inference validity.
    The role override is local to this test module.
    """
    all_rows = load_observed_pattern_table()
    rows = [
        row for row in all_rows
        if row.get("role") in {"hypothesis_prediction", "observed_target"}
        and row.get("type") in ("gradient_slope", "rank_order")
    ]
    # Override role so evaluate_patterns() processes them (role guard skips
    # hypothesis_prediction; for mechanics tests we want all evaluated)
    return [{**r, "role": "response_target"} for r in rows]


def _run(sw: PathwaySwitches, n_points: int = 8):
    """Run phenomenological model and evaluate against gradient mechanics patterns."""
    outputs, synth_env = simulate_campanula_isolation_gradient(sw, n_points=n_points)
    patterns = _gradient_patterns_for_mechanics()
    result = evaluate_patterns(list(outputs.values()), patterns, synth_env)
    return result


def _all_off() -> PathwaySwitches:
    return PathwaySwitches()


def _s1_s2() -> PathwaySwitches:
    return PathwaySwitches(direct_pollinator_to_guide=1.0, selfing_mediation=1.0)


def _s3_only() -> PathwaySwitches:
    return PathwaySwitches(island_common_cause=1.0)


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
# Test 3: M0 null (all OFF) produces neutral_diversity gradient
#         — drift is always-on, Ne from island_distance
# ---------------------------------------------------------------------------

def test_null_produces_neutral_diversity_gradient():
    """With all selection switches OFF, neutral_diversity must STILL decline
    with isolation because Ne is always derived from island_distance (not S4).

    This verifies the ecological principle: drift is a continuous background
    process, not a binary switch.  The gradient emerges from Ne alone.
    """
    result = _run(_all_off())
    by_name = {m.pattern: m for m in result.matches}

    nd_pattern = by_name.get("neutral_diversity_isolation")
    assert nd_pattern is not None, "Pattern 'neutral_diversity_isolation' not found"

    assert nd_pattern.matched, (
        f"FAIL test_null_produces_neutral_diversity_gradient: "
        f"neutral_diversity_isolation did not pass with all switches OFF.  "
        f"drift is always-on (Ne from island_distance) so a negative gradient "
        f"is always expected.  detail={nd_pattern.detail}"
    )
    print(f"[PASS] test_null_produces_neutral_diversity_gradient  "
          f"neutral_diversity matched={nd_pattern.matched}  "
          f"detail={nd_pattern.detail}")


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
    """Verify input_context, diagnostic_only, and hypothesis_prediction rows are
    not counted in weighted_match_rate.

    Role taxonomy (three excluded roles):
    - input_context: env predictor variable, always matches by construction
    - diagnostic_only: syndrome/mechanism definition (circular)
    - hypothesis_prediction: gradient expected from hypothesis, not field data

    Only observed_target rows enter ABC. The field-derived y_obs rows are
    Inoue-series gradients: flower_size (Amano & Inoue 1986) and
    selfing_rate/outcrossing (Inoue 1990). nectar_guide is planned own
    field data, not yet collected) and herkogamy is diagnostic_only (latent
    dichogamy in this protandrous species) — both excluded from ABC.

    Two checks:
    a) response_target_patterns() contains no excluded-role rows.
    b) evaluate_patterns() with a mixed list (response_target rows + one
       synthetic input_context row) produces the same weighted_match_rate —
       the role guard must filter it out.
    """
    all_rows = load_observed_pattern_table()
    rt_rows  = response_target_patterns()

    # a) response_target_patterns() must contain only ABC-target rows
    #    (role == "observed_target" or legacy "response_target")
    excluded_in_rt = [r for r in rt_rows if r.get("role") not in ABC_TARGET_ROLES]
    assert not excluded_in_rt, (
        f"FAIL test_input_context_excluded_from_abc (a): "
        f"response_target_patterns() returned {len(excluded_in_rt)} "
        f"non-ABC-target row(s): {[r['pattern'] for r in excluded_in_rt]}. "
        f"Only observed_target / response_target rows should be included."
    )

    # b) evaluate_patterns() must skip all excluded-role rows via the role guard.
    #    Use gradient mechanics rows plus a synthetic input_context row.
    sw = PathwaySwitches()
    outputs, synth_env = simulate_campanula_isolation_gradient(sw, n_points=8)

    gradient_hp = _gradient_patterns_for_mechanics()
    # Synthetic input_context row with enormous weight — must NOT change rate
    synthetic_input_ctx = {
        "pattern": "synthetic_predictor",
        "type": "gradient_slope",
        "variable": "nectar_guide",
        "populations": "",
        "predictor": "distance_from_mainland",
        "expected_direction": "negative",
        "weight": "999.0",
        "role": "input_context",
    }
    mixed_rows = gradient_hp + [synthetic_input_ctx]

    result_hp    = evaluate_patterns(list(outputs.values()), gradient_hp,   synth_env)
    result_mixed = evaluate_patterns(list(outputs.values()), mixed_rows,    synth_env)

    assert result_mixed.weighted_match_rate == result_hp.weighted_match_rate, (
        f"FAIL test_input_context_excluded_from_abc (b): "
        f"evaluate_patterns() with mixed list gave "
        f"weighted_match_rate={result_mixed.weighted_match_rate:.4f} but "
        f"with hypothesis_prediction-only list gave "
        f"{result_hp.weighted_match_rate:.4f}. "
        f"The role guard is not excluding input_context rows. "
        f"(A weight-999 input_context row was injected.)"
    )
    assert result_mixed.n_total == result_hp.n_total, (
        f"FAIL test_input_context_excluded_from_abc (b): "
        f"n_total differs: mixed={result_mixed.n_total} vs hp={result_hp.n_total}. "
        f"input_context rows are leaking into EvaluationResult."
    )
    n_excluded = sum(1 for r in all_rows if r.get("role") not in ABC_TARGET_ROLES)
    n_abc = sum(1 for r in all_rows if r.get("role") in ABC_TARGET_ROLES)
    print(
        f"[PASS] test_input_context_excluded_from_abc  "
        f"n_abc_patterns={n_abc}  "
        f"n_excluded={n_excluded}  "
        f"match_rate_unchanged={result_hp.weighted_match_rate:.3f}"
    )


def test_observed_targets_are_independent_provenance():
    """Guard RACH well-posedness against circular or pseudo-independent y_obs.

    A_epsilon should condition only on observations whose epistemic role is
    independent of the simulator's internal definitions. Rows that are planned,
    theoretical, derived from selfing in the simulator, or fixed x_obs context
    must not enter observed_target.
    """
    rows = load_observed_pattern_table()
    target_vars = {
        r.get("variable"): r
        for r in rows
        if r.get("role") in ABC_TARGET_ROLES
    }
    assert set(target_vars) == {"selfing_rate", "flower_size"}, (
        "Current empirical y_obs should be restricted to Inoue-series "
        f"independent gradients selfing_rate and flower_size, got {sorted(target_vars)}"
    )
    target_patterns = {
        r.get("pattern")
        for r in rows
        if r.get("role") in ABC_TARGET_ROLES
    }
    assert target_patterns == {"selfing_distance", "flower_size_distance"}, (
        "Current empirical y_obs should be encoded as Inoue-series gradient "
        f"targets, got {sorted(target_patterns)}"
    )

    forbidden = {
        "nectar_guide": "planned own-field observation, not yet measured",
        "herkogamy": "theoretical/latent dichogamy mechanism, not measured endpoint",
        "Fis": "pending independent genetic validation; current proxy double-counts selfing",
        "primary_pollinator_frequency": "fixed x_obs context, not response evidence",
    }
    leaks = [
        (r.get("pattern"), r.get("variable"), forbidden.get(r.get("variable")))
        for r in rows
        if r.get("role") in ABC_TARGET_ROLES and r.get("variable") in forbidden
    ]
    assert not leaks, f"Unsupported or circular rows leaked into y_obs: {leaks}"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    failures = []
    tests = [
        test_null_fails_pom,
        test_island_syndrome_passes_pom,
        test_null_produces_neutral_diversity_gradient,
        test_constraint_modules_consistent,
        test_input_context_excluded_from_abc,
        test_observed_targets_are_independent_provenance,
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
