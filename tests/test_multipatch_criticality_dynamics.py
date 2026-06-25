import pytest

from causal_model.multipatch_criticality_dynamics import (
    DynamicsParameters,
    first_alpha_warning,
    first_high_trait_absence,
    simulate,
    trait_fitness,
    trait_space_summary,
)


def test_trait_surface_has_low_component_and_interaction_enabled_high_component():
    parameters = DynamicsParameters(patch_areas=(1.0,))
    low = trait_space_summary(0.0, parameters)
    high = trait_space_summary(1.0, parameters)

    assert low.viable_components == 1
    assert not low.high_trait_component_present
    assert high.viable_components >= 2
    assert high.high_trait_component_present
    assert high.high_trait_margin > 0.0
    assert trait_fitness(1.0, 1.0, parameters) > parameters.viability_threshold


def test_simulation_is_reproducible_for_declared_seed():
    parameters = DynamicsParameters(
        patch_areas=(1.0, 1.0),
        initial_population=(30, 30),
        initial_interaction=(0.8, 0.2),
        initial_high_allele_frequency=(0.7, 0.3),
        generations=8,
        random_seed=42,
    )
    first = simulate(parameters)
    second = simulate(parameters)
    assert first == second
    assert len(first.snapshots) == 9


def test_snapshots_separate_interaction_trait_population_and_genetic_outputs():
    result = simulate(
        DynamicsParameters(
            patch_areas=(1.0, 2.0),
            initial_population=(20, 50),
            initial_interaction=(0.9, 0.9),
            initial_high_allele_frequency=(0.5, 0.5),
            generations=2,
            random_seed=4,
        )
    )
    snapshot = result.snapshots[-1]
    assert len(snapshot.interaction) == 2
    assert len(snapshot.population) == 2
    assert len(snapshot.effective_size) == 2
    assert len(snapshot.high_allele_frequency) == 2
    assert len(snapshot.trait_space) == 2
    assert 0.0 <= snapshot.h_alpha <= 1.0
    assert 0.0 <= snapshot.h_gamma <= 1.0
    assert snapshot.fst is None or 0.0 <= snapshot.fst <= 1.0 + 1e-12


def test_high_trait_absence_and_alpha_warning_are_predeclared_first_passages():
    low_interaction = DynamicsParameters(
        patch_areas=(0.1,),
        initial_population=(2,),
        initial_interaction=(0.0,),
        initial_high_allele_frequency=(0.5,),
        interaction_barrier=10.0,
        generations=3,
        random_seed=1,
    )
    result = simulate(low_interaction)
    assert first_high_trait_absence(result) == 0
    warning = first_alpha_warning(result, 1.0)
    assert warning == 0


def test_migration_parameter_is_exposed_not_implicit():
    isolated = DynamicsParameters(
        patch_areas=(1.0, 1.0),
        initial_population=(40, 40),
        initial_interaction=(0.5, 0.5),
        initial_high_allele_frequency=(1.0, 0.0),
        migration_rate=0.0,
        generations=1,
        random_seed=3,
    )
    mixed = DynamicsParameters(
        patch_areas=(1.0, 1.0),
        initial_population=(40, 40),
        initial_interaction=(0.5, 0.5),
        initial_high_allele_frequency=(1.0, 0.0),
        migration_rate=1.0,
        generations=1,
        random_seed=3,
    )
    result_isolated = simulate(isolated)
    result_mixed = simulate(mixed)
    assert result_isolated.snapshots[-1].high_allele_frequency != result_mixed.snapshots[-1].high_allele_frequency


def test_invalid_dynamic_parameters_are_rejected():
    with pytest.raises(ValueError):
        DynamicsParameters(patch_areas=())
    with pytest.raises(ValueError):
        DynamicsParameters(patch_areas=(1.0,), migration_rate=1.1)
    with pytest.raises(ValueError):
        DynamicsParameters(patch_areas=(1.0,), trait_grid_size=2)
