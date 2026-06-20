"""Tests for the Bergmann's-rule worked example (published-rule generality)."""
from causal_model.bergmann_worked_example import (
    run_bergmann_demo,
    _abc_accept,
    _cline,
    _switches,
    BergmannResult,
)
from causal_model.mechanism_equivalence import mechanism_equivalence_structure


def test_cline_only_driven_by_two_mechanisms():
    # resource_productivity and dispersal_gradient must not affect the cline
    base = {"heat_conservation": False, "fasting_endurance": False,
            "resource_productivity": True, "dispersal_gradient": True}
    assert _cline(base, 1.0) == 0.0
    on = dict(base, heat_conservation=True)
    assert _cline(on, 1.0) > 0.0


def test_abc_accept_produces_confounding_edge():
    acc = _abc_accept(n_attempts=3000, seed=1)
    assert len(acc) > 500
    struct = mechanism_equivalence_structure(acc, _switches())
    edge_pairs = {frozenset((e.a, e.b)) for e in struct.edges}
    assert frozenset(("heat_conservation", "fasting_endurance")) in edge_pairs


def test_accepted_rows_carry_assay_signatures():
    acc = _abc_accept(n_attempts=500, seed=1)
    assert acc
    for col in ("clade_thermalsig", "clade_fastingsig", "clade_clinemag"):
        assert col in acc[0]


def test_demo_reports_confound_then_resolves():
    res = run_bergmann_demo(truth="fasting_endurance", n_attempts=3000, seed=1)
    assert isinstance(res, BergmannResult)
    # the two real mechanisms are confounded near CA≈2/3, controls near 0.5
    assert 0.55 < res.ca_j["heat_conservation"] < 0.75
    assert 0.55 < res.ca_j["fasting_endurance"] < 0.75
    assert abs(res.ca_j["resource_productivity"] - 0.5) < 0.1
    assert abs(res.ca_j["dispersal_gradient"] - 0.5) < 0.1
    # resolution drives the true mechanism up and the confounded one down
    assert res.ca_j_after["fasting_endurance"] > 0.9
    assert res.ca_j_after["heat_conservation"] < 0.1
    # degeneracy decreases, resolvability increases
    assert res.D_after < res.D_RACH
    assert res.R_after > res.R_RACH


def test_demo_truth_heat_conservation_symmetric():
    res = run_bergmann_demo(truth="heat_conservation", n_attempts=3000, seed=2)
    assert res.ca_j_after["heat_conservation"] > 0.9
    assert res.ca_j_after["fasting_endurance"] < 0.1


def test_demo_is_reproducible():
    a = run_bergmann_demo(truth="fasting_endurance", n_attempts=2000, seed=5)
    b = run_bergmann_demo(truth="fasting_endurance", n_attempts=2000, seed=5)
    assert a.ca_j == b.ca_j
    assert a.D_after == b.D_after
    assert a.R_after == b.R_after


def test_seq_trace_present():
    res = run_bergmann_demo(truth="fasting_endurance", n_attempts=2000, seed=1)
    assert "RACH-SEQ" in res.seq_trace
    assert "converged" in res.seq_trace
