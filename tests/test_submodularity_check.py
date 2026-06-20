"""Tests for the RACH-SEQ greedy near-optimality (submodularity) check."""
from causal_model.submodularity_check import (
    run_bergmann_submodularity,
    run_eco_rules_submodularity,
    check_submodularity,
    realised_filters,
    SubmodularityResult,
)


def test_bergmann_driver_assays_are_submodular():
    """The two driving-mechanism assays (the genuine 2-way confound) give a
    monotone, non-negative, submodular resolvability objective — so the greedy
    (1 - 1/e) guarantee provably applies."""
    res = run_bergmann_submodularity(n_attempts=3000, seed=1, min_size=8)
    assert res.n_observations == 2
    assert res.monotone
    assert res.nonnegative
    assert res.submodular
    assert res.greedy_guarantee_applies


def test_greedy_attains_optimum_on_every_rule():
    """Even where submodularity fails (higher-order confounds), RACH-SEQ's greedy
    selection still reaches the exact optimum empirically (ratio == 1.0)."""
    results = run_eco_rules_submodularity(n_attempts=3000, seed=1, min_size=8)
    assert len(results) >= 4
    for name, r in results.items():
        assert r.greedy_ratio == 1.0, f"{name}: greedy/optimal = {r.greedy_ratio}"


def test_objective_is_monotone_and_nonnegative_everywhere():
    results = run_eco_rules_submodularity(n_attempts=3000, seed=1, min_size=8)
    for name, r in results.items():
        assert r.monotone, f"{name} not monotone"
        assert r.nonnegative, f"{name} negative resolvability"


def test_higher_order_confound_can_break_submodularity():
    """Honest documentation: a 3-way confound (Foster) need not be submodular —
    two assays can jointly cut an edge neither cuts alone (synergy)."""
    results = run_eco_rules_submodularity(n_attempts=3000, seed=1, min_size=8)
    foster = results["Foster_island"]
    assert foster.n_observations == 4          # 3 assays + 1 decoy
    # submodularity is NOT guaranteed here; the worst-case bound does not apply,
    # but greedy still attains the optimum (checked above).
    assert not foster.submodular


def test_check_submodularity_on_trivial_single_observation():
    """A one-observation ground set is trivially submodular."""
    from causal_model.bergmann_worked_example import _switches, _abc_accept
    acc = _abc_accept(2000, 1)
    sw = _switches()
    # build a single filter that keeps rows with fasting signature present
    filters = {"only": [{
        "type": "absolute_summary", "variable": "fastingsig", "population": "clade",
        "observed_value": "1.0000", "scale": "0.0500",
    }]}
    res = check_submodularity(acc, sw, filters, min_size=8)
    assert isinstance(res, SubmodularityResult)
    assert res.n_observations == 1
    assert res.submodular           # nothing to violate
    assert res.monotone


def test_realised_filters_picks_chosen_outcome():
    from causal_model.bergmann_worked_example import _candidate_observations, _truth_overrides
    cands = _candidate_observations("fasting_endurance")
    filters = realised_filters(cands, _truth_overrides("fasting_endurance"))
    # both assays present, each mapped to its realised outcome's pattern rows
    assert set(filters) == {"thermal_physiology_assay", "fasting_endurance_assay"}
    assert all(isinstance(v, list) and v for v in filters.values())
