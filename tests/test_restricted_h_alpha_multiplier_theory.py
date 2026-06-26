import pytest

from causal_model.multipatch_criticality_dynamics import DynamicsParameters
from causal_model.restricted_h_alpha_multiplier_theory import (
    gene_copy_upper_bound,
    heterozygosity,
    restricted_h_alpha_multiplier,
    selected_frequency,
)


def _parameters() -> DynamicsParameters:
    return DynamicsParameters(
        patch_areas=(1.0, 1.0),
        high_base=2.0,
        high_interaction_benefit=0.0,
        viability_threshold=1.0,
        selection_strength=0.5,
        effective_fraction=1.0,
        skew_penalty=0.0,
        migration_rate=0.8,
    )


def test_selection_map_and_heterozygosity_are_exact() -> None:
    assert selected_frequency(0.6, 1.5) == pytest.approx(0.6923076923)
    assert heterozygosity(0.6) == pytest.approx(0.48)


def test_restricted_interval_can_certify_expected_h_alpha_contraction() -> None:
    certificate = restricted_h_alpha_multiplier(
        _parameters(),
        allele_lower_bound=0.60,
        allele_upper_bound=0.62,
        interaction_lower_bound=0.0,
        population_upper_bound=1000,
    )

    assert certificate.high_allele_fitness_lower_bound == pytest.approx(1.5)
    assert certificate.selected_allele_lower_bound > 0.60
    assert certificate.gene_copy_upper_bound == 2000
    assert certificate.expected_h_alpha_multiplier_upper_bound < 1.0
    assert certificate.contraction_certified


def test_wide_interval_correctly_fails_to_claim_contraction() -> None:
    certificate = restricted_h_alpha_multiplier(
        _parameters(),
        allele_lower_bound=0.60,
        allele_upper_bound=0.90,
        interaction_lower_bound=0.0,
        population_upper_bound=1000,
    )

    assert certificate.expected_h_alpha_multiplier_upper_bound > 1.0
    assert not certificate.contraction_certified


def test_upper_gene_copy_bound_is_safe_for_rounding() -> None:
    parameters = DynamicsParameters(patch_areas=(1.0,), effective_fraction=0.6)
    assert gene_copy_upper_bound(5, parameters) == 6


def test_theorem_rejects_noncontractive_selection_and_invalid_interval() -> None:
    neutral = DynamicsParameters(
        patch_areas=(1.0,),
        high_base=1.0,
        high_interaction_benefit=0.0,
        viability_threshold=1.0,
        selection_strength=0.5,
    )
    with pytest.raises(ValueError):
        restricted_h_alpha_multiplier(neutral, 0.6, 0.62, 0.0, 100)
    with pytest.raises(ValueError):
        restricted_h_alpha_multiplier(_parameters(), 0.49, 0.62, 0.0, 100)
