from math import isclose

from causal_model.bounded_proxy_drift import identify_under_bounded_proxy_drift


def test_joint_log_geometry_and_breakdown_values_used_by_boundary_figure():
    rho_e_hat = 1.0 / 1.34
    rho_x = 0.80
    rho_w = rho_x * rho_e_hat

    result = identify_under_bounded_proxy_drift(
        net_ratio=rho_w,
        proxy_ratio=rho_x,
        delta=0.20,
        proxy_channel="fecundity",
    )

    segment = result.joint_log_segment
    assert isclose(segment.slope, -1.0)
    assert segment.satisfies_net_constraint()
    assert isclose(result.establishment.breakdown_delta, 0.34)

    # Independent marginal-upper reporting would admit an impossible pair.
    impossible_product = result.fecundity.upper * result.establishment.upper
    assert not isclose(impossible_product, rho_w)

    # The actual joint endpoints preserve the observed net ratio exactly.
    for rho_f, rho_e in result.joint_ratio_endpoints:
        assert isclose(rho_f * rho_e, rho_w)
