from math import isclose

import pytest

from causal_model.patch_genetic_drift_theory import (
    branch_genetic_erosion,
    drift_erosion_rate,
    drift_is_unavoidable_interior,
    effective_population_size,
    expected_heterozygosity_after_drift,
    heterozygosity,
    moment_identity_holds,
    selected_allele_frequency,
    selection_drift_step,
)


def test_selection_then_drift_has_exact_wright_fisher_moments():
    step = selection_drift_step(
        allele_frequency=0.4,
        fitness_high=1.5,
        fitness_low=1.0,
        effective_size=100.0,
    )

    expected_p = 0.4 * 1.5 / (0.4 * 1.5 + 0.6 * 1.0)
    assert step.allele_frequency_after_selection == pytest.approx(expected_p)
    assert step.expected_allele_frequency_after_drift == pytest.approx(expected_p)
    assert step.allele_frequency_variance_after_drift == pytest.approx(
        expected_p * (1.0 - expected_p) / 200.0
    )
    assert moment_identity_holds(step)


def test_drift_strictly_erodes_expected_heterozygosity_in_finite_interior_population():
    p = 0.5
    n_e = 20.0
    h = heterozygosity(p)
    h_next = expected_heterozygosity_after_drift(p, n_e)

    assert h == 0.5
    assert h_next == pytest.approx((1.0 - 1.0 / 40.0) * 0.5)
    assert h_next < h
    assert drift_is_unavoidable_interior(p, n_e)


def test_drift_does_not_claim_strict_loss_at_absorbing_or_nonfinite_boundary():
    assert not drift_is_unavoidable_interior(0.0, 20.0)
    assert not drift_is_unavoidable_interior(1.0, 20.0)
    assert not drift_is_unavoidable_interior(0.5, 0.5)


def test_effective_size_increases_with_patch_size_and_interaction_availability():
    low_patch = effective_population_size(
        2.0, 0.5, density_scale=10.0, baseline_density=0.2
    )
    large_patch = effective_population_size(
        4.0, 0.5, density_scale=10.0, baseline_density=0.2
    )
    high_interaction = effective_population_size(
        2.0, 0.9, density_scale=10.0, baseline_density=0.2
    )

    assert low_patch < large_patch
    assert low_patch < high_interaction
    assert drift_erosion_rate(large_patch) < drift_erosion_rate(low_patch)


def test_interaction_bistability_creates_history_dependent_genetic_erosion_rates():
    result = branch_genetic_erosion(
        patch_size=3.0,
        feedback_strength=2.0,
        density_scale=30.0,
        baseline_density=0.2,
    )

    assert result.low_interaction_availability < result.high_interaction_availability
    assert result.low_effective_population_size < result.high_effective_population_size
    assert result.low_drift_erosion_rate > result.high_drift_erosion_rate
    assert result.erosion_rate_jump_at_collapse > 0.0


def test_no_interaction_demography_coupling_means_no_branch_erosion_difference():
    result = branch_genetic_erosion(
        patch_size=3.0,
        feedback_strength=2.0,
        density_scale=30.0,
        baseline_density=1.0,
    )

    assert isclose(result.low_effective_population_size, result.high_effective_population_size)
    assert isclose(result.low_drift_erosion_rate, result.high_drift_erosion_rate)
    assert isclose(result.erosion_rate_jump_at_collapse, 0.0)


def test_invalid_genetic_parameters_are_rejected():
    with pytest.raises(ValueError):
        selected_allele_frequency(1.1, 1.0, 1.0)
    with pytest.raises(ValueError):
        selected_allele_frequency(0.5, 0.0, 1.0)
    with pytest.raises(ValueError):
        effective_population_size(0.0, 0.5, density_scale=1.0, baseline_density=0.2)
    with pytest.raises(ValueError):
        effective_population_size(1.0, 0.5, density_scale=1.0, baseline_density=0.0)
    with pytest.raises(ValueError):
        expected_heterozygosity_after_drift(0.5, 0.49)
