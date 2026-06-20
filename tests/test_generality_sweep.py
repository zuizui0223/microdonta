"""Tests for the RACH-SEQ generality sweep over random confounded systems."""
import random

from causal_model.generality_sweep import (
    run_generality_sweep,
    _make_random_system,
    _abc_accept,
    _candidates_for_system,
    _truth_magnitude,
    SweepResult,
    SystemRecord,
)
from causal_model.mechanism_equivalence import mechanism_equivalence_structure


def test_random_system_disjoint_driver_pairs():
    rng = random.Random(0)
    switches, drivers, truth = _make_random_system(rng, K=6, n_confounds=2)
    assert len(switches) == 6
    assert len(drivers) == 2
    # driver pairs are disjoint
    flat = [name for pair in drivers for name in pair]
    assert len(set(flat)) == len(flat)
    # truth picks one driver from each pair
    for td, pair in zip(truth, drivers):
        assert td in pair


def test_abc_accept_produces_confounding_edges():
    """A two-driver trait yields a disjunction edge between its drivers."""
    rng = random.Random(1)
    switches, drivers, _ = _make_random_system(rng, K=4, n_confounds=1)
    accepted = _abc_accept(rng, switches, drivers, n_attempts=2000)
    assert len(accepted) > 50
    struct = mechanism_equivalence_structure(accepted, switches)
    # exactly the two drivers of the single trait should form an edge
    edge_pairs = {frozenset((e.a, e.b)) for e in struct.edges}
    assert frozenset(drivers[0]) in edge_pairs


def test_abc_accept_rows_carry_magnitude_columns():
    rng = random.Random(2)
    switches, drivers, _ = _make_random_system(rng, K=4, n_confounds=1)
    accepted = _abc_accept(rng, switches, drivers, n_attempts=500)
    assert accepted
    assert "trait0_mag" in accepted[0]


def test_truth_magnitude_distinguishes_drivers():
    pair = ("s0", "s1")
    m0 = _truth_magnitude("s0", pair)
    m1 = _truth_magnitude("s1", pair)
    assert m0 != m1


def test_candidates_one_per_trait_with_outcome():
    rng = random.Random(3)
    _, drivers, truth = _make_random_system(rng, K=6, n_confounds=2)
    cands = _candidates_for_system(drivers, truth)
    assert len(cands) == 2
    for c in cands:
        assert len(c.outcomes) == 1
        assert c.outcomes[0].extra_pattern_rows[0]["type"] == "absolute_summary"


def test_sweep_returns_records_and_summary():
    res = run_generality_sweep(n_systems=30, seed=0, n_attempts=600)
    assert isinstance(res, SweepResult)
    assert res.records
    assert all(isinstance(r, SystemRecord) for r in res.records)
    # summary fields populated
    assert 0.0 <= res.frac_converged <= 1.0
    assert 0.0 <= res.mean_frac_resolved <= 1.0


def test_sweep_resolves_most_confounds():
    """Across a modest sweep, RACH-SEQ should resolve the large majority of edges."""
    res = run_generality_sweep(n_systems=80, seed=0, n_attempts=800)
    assert res.mean_frac_resolved > 0.8     # strong, not necessarily perfect
    # resolvability should improve on average
    assert res.mean_R_final > res.mean_R0


def test_sweep_is_reproducible():
    a = run_generality_sweep(n_systems=40, seed=7, n_attempts=600)
    b = run_generality_sweep(n_systems=40, seed=7, n_attempts=600)
    assert a.mean_frac_resolved == b.mean_frac_resolved
    assert a.frac_converged == b.frac_converged
    assert len(a.records) == len(b.records)


def test_frac_resolved_property():
    rec = SystemRecord(
        K=4, n_confounds=1, n_initial_edges=2, n_resolved=1, n_unresolved=1,
        converged=False, steps_taken=1, R0=0.1, R_final=0.3,
    )
    assert rec.frac_resolved == 0.5
    rec0 = SystemRecord(
        K=4, n_confounds=0, n_initial_edges=0, n_resolved=0, n_unresolved=0,
        converged=True, steps_taken=0, R0=0.5, R_final=0.5,
    )
    assert rec0.frac_resolved == 1.0   # no edges => trivially resolved
