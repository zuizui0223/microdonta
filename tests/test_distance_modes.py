from __future__ import annotations

from types import SimpleNamespace


def test_absolute_summary_standardized_distance():
    from examples.campanula_izu.pattern_evaluator import (
        evaluate_patterns,
        weighted_standardized_distance,
    )

    outs = [SimpleNamespace(population="Oshima", flower_size=0.75)]
    rows = [{
        "pattern": "flower_abs",
        "type": "absolute_summary",
        "variable": "flower_size",
        "population": "Oshima",
        "observed_value": "0.80",
        "scale": "0.10",
        "weight": "1.0",
        "tolerance": "1.0",
        "role": "observed_target",
    }]
    res = evaluate_patterns(outs, rows, {"Oshima": {}})
    assert res.n_total == 1
    assert res.matches[0].matched
    assert "standardized=0.5000" in res.matches[0].detail
    assert 0.16 < weighted_standardized_distance(res) < 0.17


def test_adaptive_epsilon_percentile_and_min_accept():
    from causal_model.switch_inference import select_adaptive_epsilon

    selected = select_adaptive_epsilon([0.9, 0.1, 0.2, 0.3, 0.4], percentile=5.0, min_accept=3)
    assert selected["epsilon"] == 0.3
    assert selected["n_accepted"] == 3
    assert "min_accept" in selected["warning"]


def test_structure_prior_lambda_zero_and_positive():
    from causal_model.switch_inference import (
        CAMPANULA_SWITCHES,
        compute_switch_posterior_table,
        structure_prior_weight,
    )

    names = [sw.name for sw in CAMPANULA_SWITCHES[:2]]
    simple = {names[0]: True, names[1]: True}
    sparse = {names[0]: True, names[1]: False}
    assert structure_prior_weight(simple, CAMPANULA_SWITCHES[:2], 0.0) == 1.0
    assert structure_prior_weight(simple, CAMPANULA_SWITCHES[:2], 1.0) < structure_prior_weight(
        sparse, CAMPANULA_SWITCHES[:2], 1.0
    )

    rows = [
        {names[0]: True, names[1]: True, "structure_prior_weight": 0.1},
        {names[0]: False, names[1]: False, "structure_prior_weight": 1.0},
    ]
    unweighted = compute_switch_posterior_table(rows, CAMPANULA_SWITCHES[:2])
    weighted = compute_switch_posterior_table(rows, CAMPANULA_SWITCHES[:2], weight_key="structure_prior_weight")
    assert unweighted[0]["P_posterior_ON"] == 0.5
    assert weighted[0]["P_posterior_ON"] < 0.1
