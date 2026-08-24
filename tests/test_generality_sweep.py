"""Tests for the truth-peek-free RACH-SEQ generality sweep."""
import random

from causal_model.generality_sweep import (
    BudgetSummary,
    SweepResult,
    SystemRecord,
    _abc_accept,
    _candidates_for_system,
    _make_random_system,
    _truth_magnitude,
    run_budget_sweep,
    run_generality_sweep,
)
from causal_model.mechanism_equivalence import mechanism_equivalence_structure


def test_random_system_disjoint_driver_pairs():
    rng = random.Random(0)
    switches, drivers, truth = _make_random_system(rng, K=6, n_confounds=2)
    assert len(switches) == 6
    assert len(drivers) == 2
    flat = [name for pair in drivers for name in pair]
    assert len(set(flat)) == len(flat)
    for td, pair in zip(truth, drivers):
        assert td in pair


def test_abc_accept_produces_confounding_edges():
    rng = random.Random(1)
    switches, drivers, _ = _make_random_system(rng, K=4, n_confounds=1)
    accepted = _abc_accept(rng, switches, drivers, n_attempts=2000)
    assert len(accepted) > 50
    struct = mechanism_equivalence_structure(accepted, switches)
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
    assert _truth_magnitude("s0", pair) != _truth_magnitude("s1", pair)


def test_candidates_are_predictive_distribution_from_admissible_region():
    rng = random.Random(3)
    switches, drivers, _truth = _make_random_system(rng, K=6, n_confounds=2)
    accepted = _abc_accept(rng, switches, drivers, n_attempts=1200)
    cands = _candidates_for_system(drivers, accepted)
    assert len(cands) == 2
    for candidate in cands:
        names = {outcome.name for outcome in candidate.outcomes}
        assert names <= {"driver_a_only", "driver_b_only", "both_on"}
        assert len(names) >= 2
        assert abs(sum(o.prior_probability for o in candidate.outcomes) - 1.0) < 1e-12
        assert all(o.extra_pattern_rows[0]["type"] == "absolute_summary" for o in candidate.outcomes)
        # No outcome is a probability-one oracle supplied from hidden truth.
        assert max(o.prior_probability for o in candidate.outcomes) < 1.0


def test_sweep_returns_records_and_summary():
    res = run_generality_sweep(n_systems=30, seed=0, n_attempts=600)
    assert isinstance(res, SweepResult)
    assert res.records
    assert all(isinstance(r, SystemRecord) for r in res.records)
    assert all(r.truth_peek_free for r in res.records)
    assert 0.0 <= res.frac_converged <= 1.0
    assert 0.0 <= res.mean_frac_resolved <= 1.0
    assert 0.0 <= res.false_exclusion_rate <= 1.0


def test_sweep_resolves_most_confounds_without_truth_peeking():
    res = run_generality_sweep(n_systems=80, seed=0, n_attempts=800)
    assert res.mean_frac_resolved > 0.8
    assert res.mean_R_final > res.mean_R0
    assert res.false_exclusion_rate < 0.05


def test_budget_sweep_reports_error_control_and_efficiency():
    rows = run_budget_sweep((0, 1, 2), n_systems=40, seed=11, n_attempts=700)
    assert all(isinstance(row, BudgetSummary) for row in rows)
    assert [row.budget for row in rows] == [0, 1, 2]
    assert rows[0].mean_frac_resolved <= rows[1].mean_frac_resolved <= rows[2].mean_frac_resolved
    assert all(0.0 <= row.false_exclusion_rate <= 1.0 for row in rows)


def test_sweep_is_reproducible():
    a = run_generality_sweep(n_systems=40, seed=7, n_attempts=600)
    b = run_generality_sweep(n_systems=40, seed=7, n_attempts=600)
    assert a.mean_frac_resolved == b.mean_frac_resolved
    assert a.frac_converged == b.frac_converged
    assert a.false_exclusion_rate == b.false_exclusion_rate
    assert len(a.records) == len(b.records)


def test_frac_resolved_property():
    rec = SystemRecord(
        K=4,
        n_confounds=1,
        n_initial_edges=2,
        n_resolved=1,
        n_unresolved=1,
        converged=False,
        steps_taken=1,
        R0=0.1,
        R_final=0.3,
    )
    assert rec.frac_resolved == 0.5
    rec0 = SystemRecord(
        K=4,
        n_confounds=0,
        n_initial_edges=0,
        n_resolved=0,
        n_unresolved=0,
        converged=True,
        steps_taken=0,
        R0=0.5,
        R_final=0.5,
    )
    assert rec0.frac_resolved == 1.0
