"""Tests for the truth-peek-free RACH-SEQ generality sweep.

These tests protect benchmark integrity and reproducibility. They deliberately do
not require a favourable scientific result: resolution, convergence, or hidden-
truth error rates are outputs of the frozen G2 run, not software acceptance
criteria to tune toward.
"""
import math
import random

from causal_model.generality_sweep import (
    BudgetSummary,
    SweepResult,
    SystemRecord,
    _abc_accept,
    _candidates_for_system,
    _make_random_system,
    _sample_driver_coefficients,
    _truth_magnitude,
    run_budget_sweep,
    run_generality_sweep,
)
from causal_model.mechanism_equivalence import mechanism_equivalence_structure
from causal_model.rach_seq import predictive_outcome_distribution


def test_random_system_disjoint_driver_pairs():
    rng = random.Random(0)
    switches, drivers, truth = _make_random_system(rng, K=6, n_confounds=2)
    assert len(switches) == 6
    assert len(drivers) == 2
    flat = [name for pair in drivers for name in pair]
    assert len(set(flat)) == len(flat)
    for td, pair in zip(truth, drivers):
        assert td in pair


def test_sampled_driver_coefficients_keep_magnitude_bands_separated():
    rng = random.Random(9)
    pairs = [_sample_driver_coefficients(rng) for _ in range(50)]
    assert len(set(pairs)) > 40
    for a, b in pairs:
        ratio = b / a
        assert 1.5 < ratio < 2.0


def test_abc_accept_produces_declared_confounding_edge():
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


def test_candidates_are_verified_current_region_predictive_partitions():
    rng = random.Random(3)
    switches, drivers, _truth = _make_random_system(rng, K=6, n_confounds=2)
    coeffs = _sample_driver_coefficients(rng)
    accepted = _abc_accept(
        rng, switches, drivers, n_attempts=1200, driver_coeffs=coeffs
    )
    candidates = _candidates_for_system(drivers, accepted, driver_coeffs=coeffs)
    assert len(candidates) == 2
    for candidate in candidates:
        names = {outcome.name for outcome in candidate.outcomes}
        assert names <= {"driver_a_only", "driver_b_only", "both_on"}
        assert len(names) >= 2
        assert abs(sum(o.prior_probability for o in candidate.outcomes) - 1.0) < 1e-12
        assert all(
            o.extra_pattern_rows[0]["type"] == "absolute_summary"
            for o in candidate.outcomes
        )
        # Hidden benchmark truth must never appear as a probability-one oracle.
        assert max(o.prior_probability for o in candidate.outcomes) < 1.0
        # The G2 generator is deliberately constructed so these analytic bands
        # partition every current admissible row. The benchmark should therefore
        # never need the declared-prior fallback for its own resolving candidates.
        distribution = predictive_outcome_distribution(candidate, accepted)
        assert distribution.partition_verified
        assert distribution.source == "current_admissible_region"
        for outcome in candidate.outcomes:
            assert abs(
                distribution.probabilities[outcome.name] - outcome.prior_probability
            ) < 1e-12


def test_sweep_returns_finite_truth_peek_free_metrics():
    res = run_generality_sweep(n_systems=30, seed=0, n_attempts=600)
    assert isinstance(res, SweepResult)
    assert res.records
    assert all(isinstance(r, SystemRecord) for r in res.records)
    assert all(r.truth_peek_free for r in res.records)
    assert len({(r.driver_coeff_a, r.driver_coeff_b) for r in res.records}) > 5
    assert 0.0 <= res.frac_converged <= 1.0
    assert 0.0 <= res.mean_frac_resolved <= 1.0
    assert 0.0 <= res.false_exclusion_rate <= 1.0
    assert all(
        math.isfinite(value)
        for value in (
            res.mean_R0,
            res.mean_R_final,
            res.mean_steps,
            res.mean_frac_resolved,
            res.false_exclusion_rate,
        )
    )


def test_budget_sweep_reports_results_without_encoding_a_desired_result():
    rows = run_budget_sweep((0, 1, 2), n_systems=40, seed=11, n_attempts=700)
    assert all(isinstance(row, BudgetSummary) for row in rows)
    assert [row.budget for row in rows] == [0, 1, 2]
    # The same generated systems must be compared at every observation budget.
    assert len({row.n_systems for row in rows}) == 1
    assert len({row.systems_with_edges for row in rows}) == 1
    assert rows[0].mean_steps == 0.0
    for row in rows:
        assert 0.0 <= row.frac_converged <= 1.0
        assert 0.0 <= row.mean_frac_resolved <= 1.0
        assert 0.0 <= row.false_exclusion_rate <= 1.0
        assert 0.0 <= row.mean_steps <= row.budget
        assert all(
            math.isfinite(value)
            for value in (
                row.frac_converged,
                row.mean_frac_resolved,
                row.mean_steps,
                row.false_exclusion_rate,
            )
        )


def test_sweep_is_reproducible():
    a = run_generality_sweep(n_systems=40, seed=7, n_attempts=600)
    b = run_generality_sweep(n_systems=40, seed=7, n_attempts=600)
    assert a.mean_frac_resolved == b.mean_frac_resolved
    assert a.frac_converged == b.frac_converged
    assert a.false_exclusion_rate == b.false_exclusion_rate
    assert [r.driver_coeff_a for r in a.records] == [r.driver_coeff_a for r in b.records]
    assert [r.driver_coeff_b for r in a.records] == [r.driver_coeff_b for r in b.records]
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
