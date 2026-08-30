from math import isclose

import pytest

from causal_model.channel_identifiability_theory import VitalRateState, identify_from_channel_resolved_rates
from causal_model.proxy_calibration_theory import (
    calibration_drift_breakpoint,
    construct_time_varying_proxy_symmetry,
    identify_from_net_and_bounded_proxy_drift,
    identify_from_net_and_stable_proxy,
)


def _allclose(left: tuple[float, ...], right: tuple[float, ...], tolerance: float = 1e-12) -> bool:
    return len(left) == len(right) and all(
        isclose(a, b, rel_tol=tolerance, abs_tol=tolerance)
        for a, b in zip(left, right)
    )


def _state_before() -> VitalRateState:
    return VitalRateState(
        grid=(0.0, 0.25, 0.5, 0.75, 1.0),
        fecundity=(1.0, 1.3, 1.8, 2.2, 2.8),
        establishment=(2.5, 1.9, 1.4, 1.1, 0.7),
    )


def _state_after_fecundity_loss(before: VitalRateState) -> VitalRateState:
    attenuation = (1.0, 0.9, 0.75, 0.6, 0.5)
    return VitalRateState(
        grid=before.grid,
        fecundity=tuple(a * f for a, f in zip(attenuation, before.fecundity)),
        establishment=before.establishment,
    )


def test_unknown_but_stable_trait_dependent_proxy_identifies_channel_ratios():
    before = _state_before()
    after = _state_after_fecundity_loss(before)
    calibration = (0.4, 1.9, 0.7, 2.3, 0.55)
    proxy_before = tuple(q * f for q, f in zip(calibration, before.fecundity))
    proxy_after = tuple(q * f for q, f in zip(calibration, after.fecundity))

    inferred = identify_from_net_and_stable_proxy(
        net_before=before.net_performance,
        net_after=after.net_performance,
        proxy_before=proxy_before,
        proxy_after=proxy_after,
        proxy_channel="fecundity",
    )
    direct = identify_from_channel_resolved_rates(before, after)

    assert inferred.conclusion == "fecundity_only"
    assert _allclose(inferred.fecundity_ratio, direct.fecundity_ratio)
    assert _allclose(inferred.establishment_ratio, direct.establishment_ratio)


def test_stable_proxy_is_symmetric_for_an_establishment_proxy():
    before = _state_before()
    after = _state_after_fecundity_loss(before)
    calibration = (0.6, 1.2, 1.8, 0.5, 2.1)
    proxy_before = tuple(q * e for q, e in zip(calibration, before.establishment))
    proxy_after = tuple(q * e for q, e in zip(calibration, after.establishment))

    inferred = identify_from_net_and_stable_proxy(
        net_before=before.net_performance,
        net_after=after.net_performance,
        proxy_before=proxy_before,
        proxy_after=proxy_after,
        proxy_channel="establishment",
    )

    assert inferred.conclusion == "fecundity_only"
    assert _allclose(inferred.establishment_ratio, (1.0,) * len(before.grid))


def test_bounded_drift_returns_sharp_intervals_and_exact_width():
    result = identify_from_net_and_bounded_proxy_drift(
        net_before=(1.0,),
        net_after=(0.745,),
        proxy_before=(1.0,),
        proxy_after=(1.0,),
        proxy_channel="fecundity",
        delta=0.34,
    )

    assert _allclose(result.calibration_ratio_bounds, (0.66, 1.34))
    assert isclose(result.multiplicative_width, 1.34 / 0.66)
    assert _allclose(result.fecundity_ratio.lower, (1.0 / 1.34,))
    assert _allclose(result.fecundity_ratio.upper, (1.0 / 0.66,))
    assert _allclose(result.establishment_ratio.lower, (0.745 * 0.66,))
    assert _allclose(result.establishment_ratio.upper, (0.745 * 1.34,))
    assert result.establishment_ratio.direction == ("decrease",)
    assert result.fecundity_ratio.direction == ("not_identified",)
    assert isclose(result.establishment_breakdown[0].delta_star, 1.0 / 0.745 - 1.0)
    assert result.establishment_breakdown[0].direction == "decrease"


def test_direction_fails_exactly_when_interval_reaches_one():
    delta_star = 1.0 / 0.745 - 1.0
    below = identify_from_net_and_bounded_proxy_drift(
        net_before=(1.0,), net_after=(0.745,),
        proxy_before=(1.0,), proxy_after=(1.0,),
        proxy_channel="fecundity", delta=delta_star - 1e-8,
    )
    at_break = identify_from_net_and_bounded_proxy_drift(
        net_before=(1.0,), net_after=(0.745,),
        proxy_before=(1.0,), proxy_after=(1.0,),
        proxy_channel="fecundity", delta=delta_star,
        tolerance=1e-9,
    )
    assert below.establishment_ratio.direction == ("decrease",)
    assert at_break.establishment_ratio.direction == ("not_identified",)
    assert isclose(at_break.establishment_ratio.upper[0], 1.0)


def test_zero_drift_reduces_to_stable_proxy_point_identification():
    stable = identify_from_net_and_stable_proxy(
        net_before=(0.8, 1.0), net_after=(0.72, 0.75),
        proxy_before=(0.4, 0.5), proxy_after=(0.36, 0.375),
        proxy_channel="fecundity",
    )
    bounded = identify_from_net_and_bounded_proxy_drift(
        net_before=(0.8, 1.0), net_after=(0.72, 0.75),
        proxy_before=(0.4, 0.5), proxy_after=(0.36, 0.375),
        proxy_channel="fecundity", delta=0.0,
    )
    assert bounded.fecundity_ratio.lower == stable.fecundity_ratio
    assert bounded.fecundity_ratio.upper == stable.fecundity_ratio
    assert bounded.establishment_ratio.lower == stable.establishment_ratio
    assert bounded.establishment_ratio.upper == stable.establishment_ratio
    assert bounded.multiplicative_width == 1.0


def test_bounded_drift_is_symmetric_for_establishment_proxy():
    result = identify_from_net_and_bounded_proxy_drift(
        net_before=(1.0,), net_after=(1.2,),
        proxy_before=(1.0,), proxy_after=(0.8,),
        proxy_channel="establishment", delta=0.2,
    )
    # Stable ratios are rho_E=0.8 and rho_F=1.5; kappa divides E and multiplies F.
    assert _allclose(result.establishment_ratio.lower, (0.8 / 1.2,))
    assert _allclose(result.establishment_ratio.upper, (0.8 / 0.8,))
    assert _allclose(result.fecundity_ratio.lower, (1.5 * 0.8,))
    assert _allclose(result.fecundity_ratio.upper, (1.5 * 1.2,))
    assert result.fecundity_ratio.direction == ("increase",)
    assert result.establishment_ratio.direction == ("not_identified",)


def test_breakpoint_formulas_cover_multiply_divide_and_full_domain_robustness():
    multiply = calibration_drift_breakpoint(0.745, calibration_effect="multiply")
    divide = calibration_drift_breakpoint(0.745, calibration_effect="divide")
    assert isclose(multiply.delta_star, abs(0.745 - 1.0) / 0.745)
    assert isclose(divide.delta_star, abs(0.745 - 1.0))
    assert not multiply.robust_for_all_admissible_drift
    assert not divide.robust_for_all_admissible_drift

    all_drift = calibration_drift_breakpoint(0.4, calibration_effect="multiply")
    assert isclose(all_drift.delta_star, 1.5)
    assert all_drift.robust_for_all_admissible_drift



def test_invalid_calibration_effect_fails_even_at_unit_ratio():
    with pytest.raises(ValueError, match="unknown calibration_effect"):
        calibration_drift_breakpoint(1.0, calibration_effect="other")  # type: ignore[arg-type]

def test_invalid_drift_bounds_fail_closed():
    kwargs = dict(
        net_before=(1.0,), net_after=(1.0,),
        proxy_before=(1.0,), proxy_after=(1.0,),
        proxy_channel="fecundity",
    )
    with pytest.raises(ValueError, match="0 <= delta < 1"):
        identify_from_net_and_bounded_proxy_drift(**kwargs, delta=-0.01)
    with pytest.raises(ValueError, match="0 <= delta < 1"):
        identify_from_net_and_bounded_proxy_drift(**kwargs, delta=1.0)


def test_time_varying_proxy_calibration_restores_nonidentifiability():
    result = construct_time_varying_proxy_symmetry(
        net_before=(1.0, 1.0, 1.0, 1.0),
        net_after=(1.0, 1.0, 1.0, 1.0),
        proxy_before=(1.0, 1.0, 1.0, 1.0),
        proxy_after=(1.0, 1.0, 1.0, 1.0),
        baseline_calibration=(1.0, 1.0, 1.0, 1.0),
        calibration_shift=(0.5, 0.75, 1.25, 2.0),
        proxy_channel="fecundity",
    )

    assert result.ratios_a.conclusion == "unchanged"
    assert result.ratios_b.conclusion == "mixed_or_unidentified"
    assert result.ratios_a.fecundity_ratio == (1.0, 1.0, 1.0, 1.0)
    assert result.ratios_a.establishment_ratio == (1.0, 1.0, 1.0, 1.0)
    assert _allclose(result.ratios_b.fecundity_ratio, (2.0, 4.0 / 3.0, 0.8, 0.5))
    assert _allclose(result.ratios_b.establishment_ratio, (0.5, 0.75, 1.25, 2.0))


def test_no_calibration_shift_recovers_stable_proxy_result():
    result = construct_time_varying_proxy_symmetry(
        net_before=(0.8, 1.0, 1.2),
        net_after=(0.9, 1.1, 1.3),
        proxy_before=(0.5, 0.5, 0.5),
        proxy_after=(0.6, 0.55, 0.5),
        baseline_calibration=(0.7, 1.4, 2.1),
        calibration_shift=(1.0, 1.0, 1.0),
    )
    assert result.ratios_a == result.ratios_b
