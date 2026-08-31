from importlib.util import module_from_spec, spec_from_file_location
from math import exp, isclose
from pathlib import Path

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

    # The two actual joint endpoints are the exponentiated log-segment endpoints
    # and preserve the observed net ratio exactly.
    endpoints = (
        (
            exp(segment.log_fecundity_at_kappa_lower),
            exp(segment.log_establishment_at_kappa_lower),
        ),
        (
            exp(segment.log_fecundity_at_kappa_upper),
            exp(segment.log_establishment_at_kappa_upper),
        ),
    )
    for rho_f, rho_e in endpoints:
        assert isclose(rho_f * rho_e, rho_w)


def test_boundary_figure_generator_writes_png(tmp_path):
    script = Path(__file__).resolve().parents[1] / "paper" / "make_boundary_identification_figure.py"
    spec = spec_from_file_location("boundary_figure", script)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    output = tmp_path / "boundary_identification_geometry.png"
    written = module.build_figure(output)
    assert written == output
    assert output.exists()
    assert output.stat().st_size > 0
