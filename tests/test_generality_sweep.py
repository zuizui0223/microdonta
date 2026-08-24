"""Integrity tests for the truth-peek-free G2 selection benchmark.

These tests protect the benchmark construction, matched-policy comparison, and
reproducibility. They deliberately do **not** require RACH-SEQ to beat random
selection or to achieve any favourable scientific performance threshold.
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
    for true_driver, pair in zip(truth, drivers):
        assert true_driver in pair


def test_sampled_driver_coefficients_keep_magnitude_bands_separated():
    rng = random.Random(9)
    pairs = [_sample_driver_coefficients(rng) for _ in range(50)]
    assert len(set(pairs)) > 40
    for a, b in pairs:
        assert 1.5 < b / a < 2.0


def test_abc_accept_produces_declared_confounding_edge():
    rng = random.Random(1)
    switches, drivers, _ = _make_random_system(rng, K=4, n_confounds=1)
    accepted = _abc_accept(rng, switches, drivers, n_attempts=2000)
    assert len(accepted) > 50
    structure = mechanism_equivalence_structure(accepted, switches)
    edge_pairs = {frozenset((edge.a, edge.b)) for edge in structure.edges}
    assert frozenset(drivers[0]) in edge_pairs


def test_abc_accept_can_add_binary_distractor_columns():
    rng = random.Random(2)
    switches, drivers, _ = _make_random_system(rng, K=4, n_confounds=1)
    accepted = _abc_accept(
        rng,
        switches,
        drivers,
        n_attempts=800,
        n_distractors=2,
    )
    assert accepted
    assert "trait0_mag" in accepted[0]
    for index in (0, 1):
        values = {row[f"decoy{index}_marker"] for row in accepted}
        assert values == {0.0, 1.0}


def test_truth_magnitude_distinguishes_drivers():
    pair = ("s0", "s1")
    assert _truth_magnitude("s0", pair) != _truth_magnitude("s1", pair)


def test_resolving_and_distractor_candidates_are_verified_partitions():
    rng = random.Random(3)
    switches, drivers, _truth = _make_random_system(rng, K=6, n_confounds=2)
    coeffs = _sample_driver_coefficients(rng)
    accepted = _abc_accept(
        rng,
        switches,
        drivers,
        n_attempts=1600,
        driver_coeffs=coeffs,
        n_distractors=2,
    )
    candidates = _candidates_for_system(
        drivers,
        accepted,
        driver_coeffs=coeffs,
        n_distractors=2,
    )
    resolving = [c for c in candidates if c.name.startswith("measure_trait")]
    distractors = [c for c in candidates if c.name.startswith("measure_decoy")]
    assert len(resolving) == 2
    assert len(distractors) == 2

    for candidate in candidates:
        distribution = predictive_outcome_distribution(candidate, accepted)
        assert distribution.partition_verified
        assert distribution.source == "current_admissible_region"
        assert abs(sum(distribution.probabilities.values()) - 1.0) < 1e-12
        assert max(distribution.probabilities.values()) < 1.0

    for candidate in resolving:
        names = {outcome.name for outcome in candidate.outcomes}
        assert names <= {"driver_a_only", "driver_b_only", "both_on"}
        assert len(names) >= 2
        assert candidate.target_switches

    for candidate in distractors:
        assert candidate.target_switches == []
        assert {outcome.name for outcome in candidate.outcomes} == {"marker_0", "marker_1"}


def _record_signature(record: SystemRecord):
    return (
        record.K,
        record.n_confounds,
        record.n_initial_edges,
        record.driver_coeff_a,
        record.driver_coeff_b,
        record.n_distractors,
    )


def test_policies_run_on_the_same_generated_systems():
    kwargs = dict(
        n_systems=30,
        seed=17,
        n_attempts=700,
        budget=1,
        n_distractors=2,
    )
    rach = run_generality_sweep(policy="rach_seq", **kwargs)
    random_order = run_generality_sweep(policy="random_order", **kwargs)
    assert len(rach.records) == len(random_order.records)
    assert [_record_signature(row) for row in rach.records] == [
        _record_signature(row) for row in random_order.records
    ]
    assert all(row.truth_peek_free for row in rach.records)
    assert all(row.truth_peek_free for row in random_order.records)
    # Deliberately no assertion that one policy must outperform the other.


def test_sweep_returns_finite_truth_peek_free_metrics_for_each_policy():
    for policy in ("rach_seq", "random_order"):
        result = run_generality_sweep(
            n_systems=25,
            seed=4,
            n_attempts=650,
            budget=2,
            n_distractors=2,
            policy=policy,
        )
        assert isinstance(result, SweepResult)
        assert result.policy == policy
        assert result.records
        assert all(isinstance(row, SystemRecord) for row in result.records)
        assert all(row.truth_peek_free for row in result.records)
        assert 0.0 <= result.frac_converged <= 1.0
        assert 0.0 <= result.mean_frac_resolved <= 1.0
        assert 0.0 <= result.false_exclusion_rate <= 1.0
        assert 0.0 <= result.mean_distractors_selected <= result.mean_steps
        assert all(
            math.isfinite(value)
            for value in (
                result.mean_R0,
                result.mean_R_final,
                result.mean_steps,
                result.mean_frac_resolved,
                result.false_exclusion_rate,
                result.mean_distractors_selected,
            )
        )


def test_budget_sweep_reports_matched_policy_rows_without_success_gate():
    rows = run_budget_sweep(
        (0, 1, 2),
        n_systems=30,
        seed=11,
        n_attempts=650,
        n_distractors=2,
        policies=("rach_seq", "random_order"),
    )
    assert all(isinstance(row, BudgetSummary) for row in rows)
    assert {(row.policy, row.budget) for row in rows} == {
        (policy, budget)
        for policy in ("rach_seq", "random_order")
        for budget in (0, 1, 2)
    }
    by_key = {(row.policy, row.budget): row for row in rows}
    for budget in (0, 1, 2):
        left = by_key[("rach_seq", budget)]
        right = by_key[("random_order", budget)]
        assert left.n_systems == right.n_systems
        assert left.systems_with_edges == right.systems_with_edges
    for row in rows:
        assert 0.0 <= row.frac_converged <= 1.0
        assert 0.0 <= row.mean_frac_resolved <= 1.0
        assert 0.0 <= row.false_exclusion_rate <= 1.0
        assert 0.0 <= row.mean_steps <= row.budget
        assert 0.0 <= row.mean_distractors_selected <= row.mean_steps
        assert all(
            math.isfinite(value)
            for value in (
                row.frac_converged,
                row.mean_frac_resolved,
                row.mean_steps,
                row.false_exclusion_rate,
                row.mean_distractors_selected,
            )
        )
    assert by_key[("rach_seq", 0)].mean_steps == 0.0
    assert by_key[("random_order", 0)].mean_steps == 0.0


def test_each_policy_is_reproducible():
    for policy in ("rach_seq", "random_order"):
        kwargs = dict(
            n_systems=30,
            seed=7,
            n_attempts=600,
            budget=2,
            n_distractors=2,
            policy=policy,
        )
        a = run_generality_sweep(**kwargs)
        b = run_generality_sweep(**kwargs)
        assert a.mean_frac_resolved == b.mean_frac_resolved
        assert a.frac_converged == b.frac_converged
        assert a.false_exclusion_rate == b.false_exclusion_rate
        assert a.mean_distractors_selected == b.mean_distractors_selected
        assert [_record_signature(row) for row in a.records] == [
            _record_signature(row) for row in b.records
        ]


def test_frac_resolved_property():
    record = SystemRecord(
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
    assert record.frac_resolved == 0.5
    no_edges = SystemRecord(
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
    assert no_edges.frac_resolved == 1.0
