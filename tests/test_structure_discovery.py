"""Tests for mechanism-free causal structure discovery."""
import pytest
from causal_model.structure_discovery import (
    run_structure_discovery,
    _abc_accept,
    _propagate,
    _path_support,
    _EDGES,
    _TRAITS,
    _MEDIATORS,
    DiscoveryResult,
)


# ---------------------------------------------------------------------------
# Unit: _propagate
# ---------------------------------------------------------------------------

def test_propagate_direct_only():
    """A single direct edge X->T1 gives v[T1] == weight."""
    present = {e: False for e in _EDGES}
    present["X->T1"] = True
    weight = {e: 0.0 for e in _EDGES}
    weight["X->T1"] = 1.0
    v = _propagate(present, weight)
    assert abs(v["T1"] - 1.0) < 1e-9
    assert abs(v["T2"]) < 1e-9


def test_propagate_mediated_path():
    """X->Ma->T1: v[T1] == w(X->Ma) * w(Ma->T1)."""
    present = {e: False for e in _EDGES}
    present["X->Ma"] = True
    present["Ma->T1"] = True
    weight = {e: 0.0 for e in _EDGES}
    weight["X->Ma"] = 0.8
    weight["Ma->T1"] = 1.2
    v = _propagate(present, weight)
    assert abs(v["T1"] - 0.96) < 1e-6
    assert abs(v["T2"]) < 1e-9


def test_propagate_two_hop_via_mb():
    """X->Ma->Mb->T1: v[T1] == product of three weights."""
    present = {e: False for e in _EDGES}
    for e in ("X->Ma", "Ma->Mb", "Mb->T1"):
        present[e] = True
    weight = {e: 0.0 for e in _EDGES}
    weight["X->Ma"] = 1.0
    weight["Ma->Mb"] = 0.5
    weight["Mb->T1"] = 2.0
    v = _propagate(present, weight)
    assert abs(v["T1"] - 1.0) < 1e-9


def test_propagate_additive_paths():
    """Direct and mediated paths sum linearly."""
    present = {e: False for e in _EDGES}
    present["X->T1"] = True
    present["X->Ma"] = True
    present["Ma->T1"] = True
    weight = {e: 0.0 for e in _EDGES}
    weight["X->T1"] = 0.3
    weight["X->Ma"] = 1.0
    weight["Ma->T1"] = 0.4
    v = _propagate(present, weight)
    assert abs(v["T1"] - 0.7) < 1e-9


# ---------------------------------------------------------------------------
# Unit: _abc_accept
# ---------------------------------------------------------------------------

def test_abc_accept_returns_list_of_dicts():
    acc = _abc_accept({"T1": -1, "T2": -1}, n_attempts=500, seed=42)
    assert isinstance(acc, list)
    assert len(acc) > 0
    assert all(isinstance(r, dict) for r in acc)


def test_abc_accept_rows_have_edge_keys():
    acc = _abc_accept({"T1": -1, "T2": -1}, n_attempts=200, seed=7)
    for row in acc[:5]:
        for e in _EDGES:
            assert e in row
            assert isinstance(row[e], bool)


def test_abc_accept_direction_columns_match_value():
    acc = _abc_accept({"T1": -1}, n_attempts=300, seed=3)
    for row in acc:
        for n in ("T1", "T2", "Ma", "Mb"):
            v = row[f"v{n}"]
            d = row[f"dir_{n}"]
            if abs(v) <= 0.05:
                assert d == 0
            elif v > 0:
                assert d == 1
            else:
                assert d == -1


def test_abc_accept_all_match_observed_direction():
    observed = {"T1": -1, "T2": -1}
    acc = _abc_accept(observed, n_attempts=1000, seed=5)
    for row in acc:
        assert row["dir_T1"] == -1
        assert row["dir_T2"] == -1


def test_abc_accept_positive_pattern():
    """If both traits must go up, accepted rows must all have dir +1."""
    acc = _abc_accept({"T1": 1, "T2": 1}, n_attempts=1000, seed=9)
    assert len(acc) > 0
    for row in acc:
        assert row["dir_T1"] == 1
        assert row["dir_T2"] == 1


def test_abc_accept_is_reproducible():
    a = _abc_accept({"T1": -1}, n_attempts=500, seed=99)
    b = _abc_accept({"T1": -1}, n_attempts=500, seed=99)
    assert len(a) == len(b)
    assert a[0] == b[0]


# ---------------------------------------------------------------------------
# Unit: _path_support
# ---------------------------------------------------------------------------

def test_path_support_direct_route():
    """When only direct edge X->T1 is present, direct should be ~1.0."""
    rows = []
    for _ in range(10):
        row = {e: False for e in _EDGES}
        row["X->T1"] = True
        for n in ("T1", "T2", "Ma", "Mb"):
            row[f"v{n}"] = 0.0
            row[f"dir_{n}"] = 0
        rows.append(row)
    ps = _path_support(rows, "T1")
    assert ps["direct"] == 1.0
    assert ps["via_Ma"] == 0.0
    assert ps["via_Mb"] == 0.0


def test_path_support_mediated_via_ma():
    """Mediated via Ma: X->Ma and Ma->T1 both on."""
    rows = []
    for _ in range(10):
        row = {e: False for e in _EDGES}
        row["X->Ma"] = True
        row["Ma->T1"] = True
        for n in ("T1", "T2", "Ma", "Mb"):
            row[f"v{n}"] = 0.0
            row[f"dir_{n}"] = 0
        rows.append(row)
    ps = _path_support(rows, "T1")
    assert ps["direct"] == 0.0
    assert ps["via_Ma"] == 1.0
    assert ps["via_Mb"] == 0.0


def test_path_support_empty_returns_empty():
    assert _path_support([], "T1") == {}


# ---------------------------------------------------------------------------
# Integration: run_structure_discovery
# ---------------------------------------------------------------------------

def test_run_returns_discovery_result():
    res = run_structure_discovery({"T1": -1, "T2": -1}, n_attempts=5000, seed=1)
    assert isinstance(res, DiscoveryResult)


def test_result_has_expected_fields():
    res = run_structure_discovery({"T1": -1, "T2": -1}, n_attempts=3000, seed=2)
    assert res.n_accepted > 0
    assert res.n_attempts == 3000
    assert set(res.edge_posterior.keys()) == set(_EDGES)
    assert set(res.path_support.keys()) == set(_TRAITS)


def test_structural_degeneracy_is_high():
    """With only ordinal pattern on two traits, structural D should be high (≥5 bits)."""
    res = run_structure_discovery({"T1": -1, "T2": -1}, n_attempts=10000, seed=1)
    assert res.D_structural >= 5.0


def test_edge_posteriors_in_valid_range():
    res = run_structure_discovery({"T1": -1, "T2": -1}, n_attempts=5000, seed=3)
    for e, p in res.edge_posterior.items():
        assert 0.0 <= p <= 1.0, f"edge {e}: posterior {p} out of [0,1]"


def test_direct_and_mediated_jointly_supported():
    """Both direct and mediated routes should be non-negligible before any resolution."""
    res = run_structure_discovery({"T1": -1, "T2": -1}, n_attempts=10000, seed=1)
    ps = res.path_support["T1"]
    assert ps["direct"] > 0.2, f"direct path support too low: {ps['direct']}"
    assert ps["via_Ma"] > 0.1, f"via_Ma too low: {ps['via_Ma']}"
    assert ps["via_Mb"] > 0.1, f"via_Mb too low: {ps['via_Mb']}"


def test_nov_identifies_mediator():
    """NOV should recommend measuring a mediator (not nothing), ΔD > 0."""
    res = run_structure_discovery({"T1": -1, "T2": -1}, n_attempts=10000, seed=1)
    assert len(res.nov) == 2
    assert res.nov[0][0] in _MEDIATORS
    assert res.nov[0][1] > 0.0


def test_path_support_after_mediator_drops_via_route():
    """After measuring top mediator as silent, its via-route should drop to 0."""
    res = run_structure_discovery({"T1": -1, "T2": -1}, n_attempts=15000, seed=1)
    if not res.path_support_after:
        pytest.skip("Not enough accepted rows in silent-mediator subset")
    top_m = res.nov[0][0]
    for t in _TRAITS:
        if t in res.path_support_after:
            after = res.path_support_after[t]
            assert after[f"via_{top_m}"] < 0.05, (
                f"via_{top_m} should drop to ~0 after measuring it silent, got {after[f'via_{top_m}']}")


def test_single_trait_observation():
    """Observing only T1 direction should still work."""
    res = run_structure_discovery({"T1": -1}, n_attempts=5000, seed=4)
    assert res.n_accepted > 0
    assert "T1" in res.path_support


def test_is_reproducible():
    a = run_structure_discovery({"T1": -1, "T2": -1}, n_attempts=3000, seed=7)
    b = run_structure_discovery({"T1": -1, "T2": -1}, n_attempts=3000, seed=7)
    assert a.n_accepted == b.n_accepted
    assert a.D_structural == b.D_structural
    assert a.edge_posterior == b.edge_posterior
