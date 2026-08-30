from math import isclose

import pytest

from causal_model.bounded_proxy_drift import (
    breakdown_point,
    design_rule_for_interval,
    identify_under_bounded_proxy_drift,
    identified_ratio_interval,
)


def test_delta_zero_recovers_stable_proxy_point_identification():
    result = identify_under_bounded_proxy_drift(
        net_ratio=0.60,
        proxy_ratio=0.80,
        delta=0.0,
        proxy_channel="fecundity",
    )
    assert result.fecundity.lower == result.fecundity.upper == 0.80
    assert result.establishment.lower == result.establishment.upper == 0.75
    assert result.fecundity.multiplicative_width == 1.0
    assert result.establishment.multiplicative_width == 1.0


def test_bounded_drift_interval_has_declared_multiplicative_width():
    delta = 0.20
    result = identify_under_bounded_proxy_drift(
        net_ratio=0.60,
        proxy_ratio=0.80,
        delta=delta,
        proxy_channel="fecundity",
    )
    expected_width = (1.0 + delta) / (1.0 - delta)
    assert isclose(result.establishment.lower, 0.60)
    assert isclose(result.establishment.upper, 0.90)
    assert isclose(result.fecundity.lower, 0.80 / 1.20)
    assert isclose(result.fecundity.upper, 0.80 / 0.80)
    assert isclose(result.establishment.multiplicative_width, expected_width)
    assert isclose(result.fecundity.multiplicative_width, expected_width)


def test_every_latent_ratio_from_admissible_calibration_is_contained():
    result = identify_under_bounded_proxy_drift(
        net_ratio=0.60,
        proxy_ratio=0.80,
        delta=0.20,
        proxy_channel="fecundity",
    )
    for kappa in (0.80, 0.95, 1.0, 1.15, 1.20):
        rho_f = 0.80 / kappa
        rho_e = (0.60 / 0.80) * kappa
        assert result.fecundity.contains(rho_f)
        assert result.establishment.contains(rho_e)
        assert isclose(rho_f * rho_e, 0.60)


def test_34_percent_breakdown_example_is_exact():
    point = 1.0 / 1.34
    breakdown, censored = breakdown_point(
        point,
        calibration_placement="multiplicative",
    )
    assert isclose(breakdown, 0.34)
    assert censored is False

    below = identified_ratio_interval(
        point,
        delta=0.339999,
        calibration_placement="multiplicative",
    )
    at = identified_ratio_interval(
        point,
        delta=0.34,
        calibration_placement="multiplicative",
    )
    assert below.direction_at_declared_bound == "decrease"
    assert below.upper < 1.0
    assert at.direction_at_declared_bound == "ambiguous"
    assert isclose(at.upper, 1.0)


def test_establishment_proxy_is_symmetric():
    result = identify_under_bounded_proxy_drift(
        net_ratio=1.20,
        proxy_ratio=1.50,
        delta=0.10,
        proxy_channel="establishment",
    )
    assert isclose(result.establishment.lower, 1.50 / 1.10)
    assert isclose(result.establishment.upper, 1.50 / 0.90)
    assert isclose(result.fecundity.lower, 0.80 * 0.90)
    assert isclose(result.fecundity.upper, 0.80 * 1.10)


def test_design_rule_for_interval_distinguishes_sign_and_ambiguity():
    sign_identified = identified_ratio_interval(
        0.75,
        delta=0.20,
        calibration_placement="multiplicative",
    )
    ambiguous = identified_ratio_interval(
        0.75,
        delta=0.40,
        calibration_placement="multiplicative",
    )

    sign_rule = design_rule_for_interval(
        sign_identified,
        target_channel="establishment",
    )
    ambiguous_rule = design_rule_for_interval(
        ambiguous,
        target_channel="establishment",
    )
    assert sign_rule.status == "sign_identified"
    assert "breakdown" in sign_rule.report
    assert ambiguous_rule.status == "partially_identified_sign_ambiguous"
    assert "do not claim" in ambiguous_rule.report


@pytest.mark.parametrize(
    "kwargs",
    [
        {"net_ratio": 0.0, "proxy_ratio": 1.0, "delta": 0.1},
        {"net_ratio": 1.0, "proxy_ratio": -1.0, "delta": 0.1},
        {"net_ratio": 1.0, "proxy_ratio": 1.0, "delta": -0.1},
        {"net_ratio": 1.0, "proxy_ratio": 1.0, "delta": 1.0},
    ],
)
def test_invalid_inputs_are_rejected(kwargs):
    with pytest.raises(ValueError):
        identify_under_bounded_proxy_drift(**kwargs)
