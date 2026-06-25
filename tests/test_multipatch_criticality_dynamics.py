import pytest

from causal_model.multipatch_criticality_dynamics import (
    DynamicsParameters,
    first_alpha_warning,
    first_fst_warning,
    first_high_trait_absence,
    first_h_gamma_warning,
    first_potential_high_trait_absence,
    first_realised_high_trait_absence,
    simulate,
    tau_FST,
    tau_H_alpha,
    tau_H_gamma,
    tau_trait_potential,
    tau_trait_realised,
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
    assert len(snapshot.trait_occupancy) == 2
    assert len(snapshot.trait_occupancy[0].distribution) == result.parameters.trait_grid_size
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
    assert first_potential_high_trait_absence(result) == 0
    warning = first_alpha_warning(result, 1.0)
    assert warning == 0
    assert first_h_gamma_warning(result, 1.0) == 0


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


def test_potential_viability_can_exist_while_realised_occupancy_is_zero():
    parameters = DynamicsParameters(
        patch_areas=(1.0,),
        initial_interaction=(1.0,),
        initial_trait_distribution=(_low_trait_distribution(101),),
        generations=0 + 1,
        random_seed=2,
    )
    snapshot = simulate(parameters).snapshots[0]
    assert snapshot.trait_space[0].high_trait_component_present
    assert snapshot.trait_occupancy[0].high_trait_mass == 0.0
    assert not snapshot.trait_occupancy[0].realised_high_trait_occupied


def test_realised_high_trait_occupancy_can_persist_after_potential_is_lost():
    parameters = DynamicsParameters(
        patch_areas=(0.05,),
        initial_population=(2,),
        initial_interaction=(1.0,),
        initial_high_allele_frequency=(0.0,),
        initial_trait_distribution=(_high_trait_distribution(101),),
        interaction_barrier=10.0,
        generations=1,
        random_seed=5,
    )
    result = simulate(parameters)
    assert result.snapshots[0].trait_space[0].high_trait_component_present
    assert not result.snapshots[1].trait_space[0].high_trait_component_present
    assert result.snapshots[1].trait_occupancy[0].realised_high_trait_occupied
    assert first_potential_high_trait_absence(result) == 1
    assert tau_trait_potential(result) == 1
    assert first_realised_high_trait_absence(result) is None
    assert tau_trait_realised(result) is None


def test_first_passages_are_separate_for_potential_realised_and_genetics():
    parameters = DynamicsParameters(
        patch_areas=(0.05, 0.05),
        initial_population=(10, 10),
        initial_interaction=(0.0, 0.0),
        initial_high_allele_frequency=(1.0, 0.0),
        initial_trait_distribution=(_high_trait_distribution(101), _low_trait_distribution(101)),
        generations=1,
        random_seed=8,
    )
    result = simulate(parameters)
    assert first_potential_high_trait_absence(result) == 0
    assert first_realised_high_trait_absence(result) is None
    assert first_fst_warning(result, 0.5) == 0
    assert tau_H_alpha(result, 1.0) == 0
    assert tau_H_gamma(result, 1.0) == 0
    assert tau_FST(result, 0.5) == 0


def test_trait_occupancy_is_simulation_state_not_theorem_text():
    parameters = DynamicsParameters(patch_areas=(1.0,))
    assert parameters.trait_occupancy_model == "viability_selection_local_recruitment"
    assert "theorem" not in parameters.trait_occupancy_model


def _low_trait_distribution(size: int) -> tuple[float, ...]:
    grid = tuple(index / (size - 1) for index in range(size))
    return tuple(1.0 if z < 0.3 else 0.0 for z in grid)


def _high_trait_distribution(size: int) -> tuple[float, ...]:
    grid = tuple(index / (size - 1) for index in range(size))
    return tuple(1.0 if z >= 0.8 else 0.0 for z in grid)
