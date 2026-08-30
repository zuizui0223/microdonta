from math import isclose

from causal_model.channel_identifiability_theory import VitalRateState, identify_from_channel_resolved_rates
from causal_model.proxy_calibration_theory import (
    bounded_drift_identified_interval,
    construct_time_varying_proxy_symmetry,
    decline_breakdown_point,
    identify_from_net_and_stable_proxy,
    sampling_aware_bounded_drift_interval,
    sampling_aware_decline_breakdown_point,
)


def _allclose(left: tuple[float, ...], right: tuple[float, ...], tolerance: float = 1e-12) -> bool:
    return len(left) == len(right) and all(isclose(a, b, rel_tol=tolerance, abs_tol=tolerance) for a, b in zip(left, right))


def _state_before() -> VitalRateState:
    return VitalRateState(grid=(0.0, 0.25, 0.5, 0.75, 1.0), fecundity=(1.0, 1.3, 1.8, 2.2, 2.8), establishment=(2.5, 1.9, 1.4, 1.1, 0.7))


def _state_after_fecundity_loss(before: VitalRateState) -> VitalRateState:
    attenuation = (1.0, 0.9, 0.75, 0.6, 0.5)
    return VitalRateState(grid=before.grid, fecundity=tuple(a * f for a, f in zip(attenuation, before.fecundity)), establishment=before.establishment)


def test_unknown_but_stable_trait_dependent_proxy_identifies_channel_ratios():
    before = _state_before()
    after = _state_after_fecundity_loss(before)
    calibration = (0.4, 1.9, 0.7, 2.3, 0.55)
    proxy_before = tuple(q * f for q, f in zip(calibration, before.fecundity))
    proxy_after = tuple(q * f for q, f in zip(calibration, after.fecundity))
    inferred = identify_from_net_and_stable_proxy(net_before=before.net_performance, net_after=after.net_performance, proxy_before=proxy_before, proxy_after=proxy_after, proxy_channel="fecundity")
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
    inferred = identify_from_net_and_stable_proxy(net_before=before.net_performance, net_after=after.net_performance, proxy_before=proxy_before, proxy_after=proxy_after, proxy_channel="establishment")
    assert inferred.conclusion == "fecundity_only"
    assert _allclose(inferred.establishment_ratio, (1.0,) * len(before.grid))


def test_bounded_drift_interval_has_declared_multiplicative_width():
    result = bounded_drift_identified_interval(stable_ratio=0.66, delta=0.2)
    assert isclose(result.lower, 0.66 / 1.2)
    assert isclose(result.upper, 0.66 / 0.8)
    assert isclose(result.multiplicative_width, 1.2 / 0.8)
    assert result.excludes_no_change()


def test_bounded_drift_interval_is_sharp_by_endpoint_attainment():
    stable_ratio = 0.66
    delta = 0.2
    result = bounded_drift_identified_interval(stable_ratio=stable_ratio, delta=delta)
    assert isclose(stable_ratio / (1.0 + delta), result.lower)
    assert isclose(stable_ratio / (1.0 - delta), result.upper)
    for kappa in (1.0 - delta, 0.9, 1.0, 1.1, 1.0 + delta):
        candidate = stable_ratio / kappa
        assert result.lower <= candidate <= result.upper


def test_decline_breakdown_point_is_34_percent_for_ratio_066():
    assert isclose(decline_breakdown_point(stable_ratio=0.66), 0.34)
    before = bounded_drift_identified_interval(stable_ratio=0.66, delta=0.339999)
    at_boundary = bounded_drift_identified_interval(stable_ratio=0.66, delta=0.34)
    assert before.upper < 1.0
    assert isclose(at_boundary.upper, 1.0)
    assert not at_boundary.excludes_no_change()


def test_sampling_and_identification_uncertainty_are_separate():
    result = sampling_aware_bounded_drift_interval(stable_ci_lower=0.60, stable_ci_upper=0.72, delta=0.1)
    assert isclose(result.lower, 0.60 / 1.1)
    assert isclose(result.upper, 0.72 / 0.9)
    assert isclose(sampling_aware_decline_breakdown_point(stable_ci_upper=0.72), 0.28)


def test_delta_zero_recovers_stable_calibration_ratio():
    result = bounded_drift_identified_interval(stable_ratio=0.83, delta=0.0)
    assert result.lower == result.upper == 0.83
    assert result.multiplicative_width == 1.0


def test_interval_width_increases_with_delta():
    widths = [bounded_drift_identified_interval(stable_ratio=0.8, delta=d).multiplicative_width for d in (0.0, 0.1, 0.2, 0.4)]
    assert widths == sorted(widths)
    assert len(set(widths)) == len(widths)


def test_time_varying_proxy_calibration_restores_nonidentifiability():
    result = construct_time_varying_proxy_symmetry(net_before=(1.0, 1.0, 1.0, 1.0), net_after=(1.0, 1.0, 1.0, 1.0), proxy_before=(1.0, 1.0, 1.0, 1.0), proxy_after=(1.0, 1.0, 1.0, 1.0), baseline_calibration=(1.0, 1.0, 1.0, 1.0), calibration_shift=(0.5, 0.75, 1.25, 2.0), proxy_channel="fecundity")
    assert result.ratios_a.conclusion == "unchanged"
    assert result.ratios_b.conclusion == "mixed_or_unidentified"
    assert result.ratios_a.fecundity_ratio == (1.0, 1.0, 1.0, 1.0)
    assert result.ratios_a.establishment_ratio == (1.0, 1.0, 1.0, 1.0)
    assert _allclose(result.ratios_b.fecundity_ratio, (2.0, 4.0 / 3.0, 0.8, 0.5))
    assert _allclose(result.ratios_b.establishment_ratio, (0.5, 0.75, 1.25, 2.0))


def test_no_calibration_shift_recovers_stable_proxy_result():
    result = construct_time_varying_proxy_symmetry(net_before=(0.8, 1.0, 1.2), net_after=(0.9, 1.1, 1.3), proxy_before=(0.5, 0.5, 0.5), proxy_after=(0.6, 0.55, 0.5), baseline_calibration=(0.7, 1.4, 2.1), calibration_shift=(1.0, 1.0, 1.0))
    assert result.ratios_a == result.ratios_b
