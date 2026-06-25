import pytest

from causal_model.patch_metapopulation_genetics import (
    equal_partition_drift_contrast,
    metapopulation_diversity,
)


def test_alpha_gamma_and_fst_for_equal_patch_frequencies():
    diversity = metapopulation_diversity((0.4, 0.4), (1.0, 1.0))
    assert diversity.mean_allele_frequency == pytest.approx(0.4)
    assert diversity.alpha_heterozygosity == pytest.approx(0.48)
    assert diversity.gamma_heterozygosity == pytest.approx(0.48)
    assert diversity.fst == pytest.approx(0.0)


def test_between_patch_frequency_difference_reduces_alpha_and_increases_fst():
    diversity = metapopulation_diversity((0.1, 0.9), (0.5, 0.5))
    assert diversity.mean_allele_frequency == pytest.approx(0.5)
    assert diversity.alpha_heterozygosity == pytest.approx(0.18)
    assert diversity.gamma_heterozygosity == pytest.approx(0.5)
    assert diversity.fst == pytest.approx(0.64)


def test_globally_fixed_population_has_undefined_fst_not_a_fabricated_value():
    diversity = metapopulation_diversity((0.0, 0.0), (1.0, 1.0))
    assert diversity.alpha_heterozygosity == 0.0
    assert diversity.gamma_heterozygosity == 0.0
    assert diversity.fst is None


def test_equal_isolated_partition_multiplies_within_patch_drift_exactly_by_patch_count():
    contrast = equal_partition_drift_contrast(
        total_area=24.0,
        patch_count=6,
        interaction_availability=0.7,
        density_scale=10.0,
        baseline_density=0.2,
    )
    assert contrast.equal_patch_effective_size == pytest.approx(
        contrast.single_patch_effective_size / 6.0
    )
    assert contrast.equal_patch_erosion_rate == pytest.approx(
        6.0 * contrast.single_patch_erosion_rate
    )
    assert contrast.erosion_rate_multiplier == pytest.approx(6.0)


def test_one_patch_is_the_neutral_partition_case():
    contrast = equal_partition_drift_contrast(
        total_area=8.0,
        patch_count=1,
        interaction_availability=0.4,
        density_scale=12.0,
        baseline_density=0.4,
    )
    assert contrast.single_patch_effective_size == pytest.approx(contrast.equal_patch_effective_size)
    assert contrast.erosion_rate_multiplier == pytest.approx(1.0)


def test_invalid_metapopulation_inputs_are_rejected():
    with pytest.raises(ValueError):
        metapopulation_diversity((), ())
    with pytest.raises(ValueError):
        metapopulation_diversity((0.2,), (0.0,))
    with pytest.raises(ValueError):
        equal_partition_drift_contrast(1.0, 0, 0.5, density_scale=1.0, baseline_density=0.5)
