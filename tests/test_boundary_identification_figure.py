from importlib.util import module_from_spec, spec_from_file_location
from math import isclose, log
from pathlib import Path

import numpy as np

from causal_model.calibration_transport_family import breakdown_factor, symmetric_interval


def _load_script(name: str):
    script = Path(__file__).resolve().parents[1] / "paper" / name
    spec = spec_from_file_location(name.replace(".py", ""), script)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gamma_geometry_and_breakdown_values_used_by_boundary_figure():
    rho_e_hat = 1.0 / 1.34
    rho_x = 0.80
    rho_w = rho_x * rho_e_hat
    gamma = 1.20

    interval = symmetric_interval(rho_e_hat, gamma=gamma)
    assert isclose(interval.lower, rho_e_hat / gamma)
    assert isclose(interval.upper, rho_e_hat * gamma)

    gamma_star, eta_star = breakdown_factor(rho_e_hat)
    assert isclose(gamma_star, 1.34)
    assert isclose(eta_star, log(1.34))

    kappas = np.geomspace(1.0 / gamma, gamma, 51)
    rho_f = rho_x / kappas
    rho_e = rho_e_hat * kappas

    assert np.allclose(rho_f * rho_e, rho_w)
    assert np.allclose(np.log(rho_f) + np.log(rho_e), log(rho_w))

    slope = (np.log(rho_e[-1]) - np.log(rho_e[0])) / (
        np.log(rho_f[-1]) - np.log(rho_f[0])
    )
    assert isclose(float(slope), -1.0)

    rho_f_upper = rho_x * gamma
    rho_e_upper = rho_e_hat * gamma
    assert not isclose(rho_f_upper * rho_e_upper, rho_w)

    assert isclose(rho_e_hat * gamma_star, 1.0)


def test_reference_reversal_keeps_figure_breakdown_factor():
    down_gamma, down_eta = breakdown_factor(1.0 / 1.34)
    up_gamma, up_eta = breakdown_factor(1.34)
    assert isclose(down_gamma, up_gamma)
    assert isclose(down_eta, up_eta)
    assert isclose(down_gamma, 1.34)


def test_boundary_figure_generator_writes_png(tmp_path):
    module = _load_script("make_boundary_identification_figure.py")
    output = tmp_path / "boundary_identification_geometry.png"
    written = module.build_figure(output)
    assert written == output
    assert output.exists()
    assert output.stat().st_size > 0


def test_mechanistic_evidence_axis_figure_writes_png_and_keeps_scope_guard(tmp_path):
    module = _load_script("make_mechanistic_evidence_axis_figure.py")
    output = tmp_path / "mechanistic_evidence_axes.png"
    written = module.build_figure(output)
    assert written == output
    assert output.exists()
    assert output.stat().st_size > 0

    source = (
        Path(__file__).resolve().parents[1]
        / "paper"
        / "make_mechanistic_evidence_axis_figure.py"
    ).read_text(encoding="utf-8")
    assert "identification strength" in source.lower()
    assert "biological measurement level" in source.lower()
    assert "conditional on the declared candidate mechanisms" in source
    assert "distinct" in source
    assert "no statistical independence" in source
    assert "orthogonal" not in source.lower()
