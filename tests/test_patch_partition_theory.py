import pytest

from causal_model.patch_partition_theory import (
    PatchInteractionSystem,
    admissible_equal_patch_counts,
    area_from_mutation_drift_heterozygosity,
    critical_heterozygosity_for_local_mode,
    equal_partition_service,
    high_trait_supported,
    interaction_service,
    local_mode_supported_by_heterozygosity,
    max_equal_patch_count_for_high_trait,
    merge_direction,
    merge_service_change,
    min_equal_patch_count_for_high_trait,
    mutation_drift_heterozygosity,
)


def test_superlinear_coarsening_strictly_increases_interaction_service():
    system = PatchInteractionSystem(
        total_area=10.0,
        interaction_yield=1.0,
        aggregation_exponent=2.0,
        interaction_requirement=75.0,
    )
    fragmented = interaction_service((5.0, 5.0), interaction_yield=1.0, aggregation_exponent=2.0)
    merged = interaction_service((10.0,), interaction_yield=1.0, aggregation_exponent=2.0)

    assert merge_direction(system) == "increases"
    assert merge_service_change(5.0, 5.0, interaction_yield=1.0, aggregation_exponent=2.0) == pytest.approx(50.0)
    assert merged > fragmented
    assert high_trait_supported(merged, system.interaction_requirement)
    assert not high_trait_supported(fragmented, system.interaction_requirement)


def test_sublinear_fragmentation_strictly_increases_interaction_service():
    system = PatchInteractionSystem(
        total_area=10.0,
        interaction_yield=1.0,
        aggregation_exponent=0.5,
        interaction_requirement=4.0,
    )
    fragmented = interaction_service((5.0, 5.0), interaction_yield=1.0, aggregation_exponent=0.5)
    merged = interaction_service((10.0,), interaction_yield=1.0, aggregation_exponent=0.5)

    assert merge_direction(system) == "decreases"
    assert merge_service_change(5.0, 5.0, interaction_yield=1.0, aggregation_exponent=0.5) < 0.0
    assert fragmented > merged


def test_linear_service_is_partition_neutral():
    system = PatchInteractionSystem(
        total_area=10.0,
        interaction_yield=3.0,
        aggregation_exponent=1.0,
        interaction_requirement=30.0,
    )
    assert merge_direction(system) == "neutral"
    assert merge_service_change(3.0, 7.0, interaction_yield=3.0, aggregation_exponent=1.0) == pytest.approx(0.0)
    assert equal_partition_service(system, 1) == pytest.approx(30.0)
    assert equal_partition_service(system, 10) == pytest.approx(30.0)
    assert max_equal_patch_count_for_high_trait(system) is None
    assert min_equal_patch_count_for_high_trait(system) == 1


def test_superlinear_equal_partition_has_exact_maximum_patch_count():
    # I_n = 10^2 / n. Requirement 25 is met through n=4, not n=5.
    system = PatchInteractionSystem(
        total_area=10.0,
        interaction_yield=1.0,
        aggregation_exponent=2.0,
        interaction_requirement=25.0,
    )

    assert equal_partition_service(system, 4) == pytest.approx(25.0)
    assert equal_partition_service(system, 5) == pytest.approx(20.0)
    assert max_equal_patch_count_for_high_trait(system) == 4
    assert admissible_equal_patch_counts(system, max_count=8) == (1, 2, 3, 4)


def test_sublinear_equal_partition_has_exact_minimum_patch_count():
    # I_n = sqrt(10*n); requirement 5 is met from n=3 onward.
    system = PatchInteractionSystem(
        total_area=10.0,
        interaction_yield=1.0,
        aggregation_exponent=0.5,
        interaction_requirement=5.0,
    )
    assert equal_partition_service(system, 2) < 5.0
    assert equal_partition_service(system, 3) > 5.0
    assert min_equal_patch_count_for_high_trait(system) == 3
    assert admissible_equal_patch_counts(system, max_count=5) == (3, 4, 5)


def test_local_area_threshold_maps_to_equilibrium_heterozygosity_threshold():
    # A_c = sqrt(25)=5 under eta=1, alpha=2.
    system = PatchInteractionSystem(
        total_area=20.0,
        interaction_yield=1.0,
        aggregation_exponent=2.0,
        interaction_requirement=25.0,
    )
    h_critical = critical_heterozygosity_for_local_mode(
        system,
        effective_density=100.0,
        mutation_rate=0.001,
    )
    assert h_critical == pytest.approx(2.0 / 3.0)
    assert area_from_mutation_drift_heterozygosity(
        h_critical, effective_density=100.0, mutation_rate=0.001
    ) == pytest.approx(5.0)
    assert local_mode_supported_by_heterozygosity(
        h_critical, system, effective_density=100.0, mutation_rate=0.001
    )
    assert not local_mode_supported_by_heterozygosity(
        mutation_drift_heterozygosity(4.0, effective_density=100.0, mutation_rate=0.001),
        system,
        effective_density=100.0,
        mutation_rate=0.001,
    )


def test_invalid_area_partition_and_heterozygosity_inputs_are_rejected():
    with pytest.raises(ValueError):
        interaction_service((1.0, 0.0), interaction_yield=1.0, aggregation_exponent=2.0)
    with pytest.raises(ValueError):
        mutation_drift_heterozygosity(0.0, effective_density=1.0, mutation_rate=0.01)
    with pytest.raises(ValueError):
        area_from_mutation_drift_heterozygosity(1.0, effective_density=1.0, mutation_rate=0.01)
