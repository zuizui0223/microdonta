from __future__ import annotations

from types import SimpleNamespace


def _proxy_population(population: str, flower_size: float) -> SimpleNamespace:
    return SimpleNamespace(
        population=population,
        nectar_guide=0.5,
        selfing_rate=0.2,
        herkogamy=0.6,
        flower_size=flower_size,
        Fis=0.1,
        primary_pollinator_frequency=0.5,
    )


def test_absolute_summary_standardized_distance():
    from examples.campanula_izu.pattern_evaluator import (
        distance_components,
        evaluate_patterns,
        multi_component_distance,
        weighted_standardized_distance,
    )

    outs = [_proxy_population("Oshima", 0.75)]
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
    assert 0.16 < multi_component_distance(res, mode="standardized") < 0.17
    components = distance_components(res)
    assert components[0]["pattern"] == "flower_abs"
    assert 0.16 < components[0]["component"] < 0.17


def test_multi_component_distance_combines_ordinal_and_absolute_summary():
    from examples.campanula_izu.pattern_evaluator import evaluate_patterns, multi_component_distance

    outs = [_proxy_population("Oshima", 0.75), _proxy_population("Hachijo", 0.40)]
    rows = [
        {
            "pattern": "ordinal_ok",
            "type": "pairwise_relation",
            "variable": "flower_size",
            "left_population": "Oshima",
            "right_population": "Hachijo",
            "relation": "Oshima > Hachijo",
            "weight": "1.0",
            "role": "observed_target",
        },
        {
            "pattern": "flower_abs",
            "type": "absolute_summary",
            "variable": "flower_size",
            "population": "Oshima",
            "observed_value": "0.45",
            "scale": "0.10",
            "weight": "1.0",
            "role": "observed_target",
        },
    ]
    res = evaluate_patterns(outs, rows, {"Oshima": {}, "Hachijo": {}})
    # Ordinal component matches (=0); absolute delta is capped at 3 SD (=1).
    assert abs(multi_component_distance(res, mode="standardized") - 0.5) < 1e-12


def test_strict_all_requires_core_patterns_and_allows_soft_distance():
    from causal_model.switch_inference import strict_core_soft_acceptance
    from examples.campanula_izu.pattern_evaluator import evaluate_patterns

    outs = [
        SimpleNamespace(population="Oshima", selfing_rate=0.2, flower_size=0.8),
        SimpleNamespace(population="Hachijo", selfing_rate=0.8, flower_size=0.4),
    ]
    env = {"Oshima": {"distance_from_mainland": 100}, "Hachijo": {"distance_from_mainland": 300}}
    rows = [
        {
            "pattern": "selfing_distance",
            "type": "gradient_slope",
            "variable": "selfing_rate",
            "predictor": "distance_from_mainland",
            "expected_direction": "positive",
            "weight": "1.0",
            "role": "observed_target",
        },
        {
            "pattern": "flower_size_distance",
            "type": "gradient_slope",
            "variable": "flower_size",
            "predictor": "distance_from_mainland",
            "expected_direction": "negative",
            "weight": "1.0",
            "role": "observed_target",
        },
        {
            "pattern": "flower_abs",
            "type": "absolute_summary",
            "variable": "flower_size",
            "population": "Oshima",
            "observed_value": "0.75",
            "scale": "0.10",
            "weight": "1.0",
            "role": "observed_target",
        },
    ]
    accepted = strict_core_soft_acceptance(evaluate_patterns(outs, rows, env), "standardized", epsilon=0.2)
    assert accepted["core_required_passed"]
    assert accepted["accepted"]

    rows[0]["expected_direction"] = "negative"
    rejected = strict_core_soft_acceptance(evaluate_patterns(outs, rows, env), "standardized", epsilon=1.0)
    assert not rejected["core_required_passed"]
    assert not rejected["accepted"]


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
