from math import isclose, log

import pytest

from causal_model.calibration_transport_family import (
    SymmetricCalibrationBound,
    anchor_ladder,
    breakdown_factor,
    identify_with_observed_kappa,
    observed_kappa,
    symmetric_interval,
)


def test_gamma_family_recovers_stable_bounded_and_unrestricted_limit():
    stable = SymmetricCalibrationBound(1.0)
    assert stable.identification_state == "point_identified"
    assert isclose(stable.kappa_lower, 1.0)
    assert isclose(stable.kappa_upper, 1.0)
    assert isclose(stable.eta, 0.0)

    bounded = SymmetricCalibrationBound(1.34)
    assert bounded.identification_state == "partially_identified"
    assert isclose(bounded.kappa_lower, 1 / 1.34)
    assert isclose(bounded.kappa_upper, 1.34)

    # Finite Gamma always yields a bounded positive interval.  As Gamma grows,
    # the admissible kappa range approaches the unrestricted positive line.
    huge = SymmetricCalibrationBound(1e12)
    assert huge.kappa_lower < 1e-11
    assert huge.kappa_upper > 1e11


def test_symmetric_breakdown_is_invariant_to_reference_regime_reversal():
    decline = 1.0 / 1.34
    increase = 1.34

    gamma_down, eta_down = breakdown_factor(decline)
    gamma_up, eta_up = breakdown_factor(increase)

    assert isclose(gamma_down, 1.34)
    assert isclose(gamma_up, 1.34)
    assert isclose(eta_down, log(1.34))
    assert isclose(eta_up, log(1.34))


def test_symmetric_interval_has_log_symmetric_endpoints():
    point = 0.8
    result = symmetric_interval(point, gamma=1.25)
    assert isclose(result.lower, point / 1.25)
    assert isclose(result.upper, point * 1.25)
    assert isclose(result.multiplicative_width, 1.25**2)
    assert isclose(log(point) - log(result.lower), log(result.upper) - log(point))


def test_two_anchors_measure_kappa_and_remove_need_for_external_bound():
    # q0 = 2, q1 = 3, so kappa = 1.5.
    kappa = observed_kappa(proxy_0=20, channel_0=10, proxy_1=45, channel_1=15)
    assert isclose(kappa, 1.5)

    rho_f, rho_e = identify_with_observed_kappa(
        net_ratio=0.72,
        proxy_ratio=0.9,
        kappa=kappa,
        proxy_channel="fecundity",
    )
    assert isclose(rho_f, 0.6)
    assert isclose(rho_e, 1.2)
    assert isclose(rho_f * rho_e, 0.72)


def test_anchor_ladder_maps_measurement_effort_to_identification_strength():
    zero = anchor_ladder(0)
    one = anchor_ladder(1)
    two = anchor_ladder(2)

    assert zero.identification == "non_identified"
    assert one.identification == "partially_identified"
    assert two.identification == "point_identified"
    assert "Gamma" in one.calibration_object
    assert "kappa" in two.calibration_object


def test_invalid_gamma_and_anchor_count_are_rejected():
    with pytest.raises(ValueError):
        SymmetricCalibrationBound(0.99)
    with pytest.raises(ValueError):
        anchor_ladder(3)
