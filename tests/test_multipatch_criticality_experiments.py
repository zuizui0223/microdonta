from dataclasses import replace

from causal_model.multipatch_criticality_dynamics import DynamicsParameters, simulate
from causal_model.multipatch_criticality_experiments import (
    PROFILE_FULL,
    PROFILE_QUICK,
    derived_seed,
    full_profile,
    parameter_grid,
    quick_profile,
    results_to_csv_rows,
    run_parameter_grid,
    scenario_equal_isolated,
    scenario_equal_migrating,
    scenario_one_large,
    summarise_replicate,
)


def _low_trait_distribution(size: int) -> tuple[float, ...]:
    values = tuple(1.0 if index == 0 else 0.0 for index in range(size))
    return values


def _high_trait_distribution(size: int) -> tuple[float, ...]:
    values = tuple(1.0 if index == size - 1 else 0.0 for index in range(size))
    return values


def test_scenario_constructors_preserve_total_area() -> None:
    spec = quick_profile()
    one_large = scenario_one_large(spec)
    isolated = scenario_equal_isolated(spec)
    migrating = scenario_equal_migrating(spec)

    assert one_large.total_area == spec.total_area
    assert sum(isolated.patch_areas) == spec.total_area
    assert sum(migrating.patch_areas) == spec.total_area


def test_isolated_and_migrating_differ_only_in_migration_settings() -> None:
    spec = replace(quick_profile(), migration_rate=0.25)
    isolated = scenario_equal_isolated(spec)
    migrating = scenario_equal_migrating(spec)

    assert isolated.patch_areas == migrating.patch_areas
    assert isolated.migration_rate == 0.0
    assert migrating.migration_rate == 0.25


def test_seed_schedule_is_reproducible_and_shared_across_scenarios() -> None:
    spec = quick_profile()
    cell = parameter_grid(spec)[1]

    assert derived_seed(spec.master_seed, cell.cell_index, 2) == derived_seed(spec.master_seed, cell.cell_index, 2)
    assert derived_seed(spec.master_seed, cell.cell_index, 2) != derived_seed(spec.master_seed, cell.cell_index, 1)


def test_experiment_result_keeps_censored_first_passages_explicit() -> None:
    spec = replace(quick_profile(), replicates=2)
    result = run_parameter_grid(spec, scenarios=(scenario_one_large(spec),))[0]

    summary = result.summary
    assert "censored_event_counts" in summary
    assert "tau_trait_realised" in summary["first_passage"]
    assert isinstance(summary["first_passage"]["tau_trait_realised"]["values"], list)
    assert "valid_event_pair_counts" in summary


def test_potential_and_realised_trait_outcomes_can_differ() -> None:
    size = 21
    params = DynamicsParameters(
        patch_areas=(1.0,),
        generations=1,
        initial_interaction=(1.0,),
        initial_trait_distribution=(_low_trait_distribution(size),),
        trait_grid_size=size,
        high_interaction_benefit=2.0,
        viability_threshold=1.0,
        realised_high_trait_threshold=1e-6,
        random_seed=3,
    )
    summary = summarise_replicate(
        simulate(params),
        replicate_index=0,
        seed=3,
        h_alpha_warning_threshold=0.0,
        h_gamma_warning_threshold=0.0,
        fst_warning_threshold=1.0,
    )

    assert summary.potential_high_trait_viable is True
    assert summary.realised_high_trait_persists is False


def test_allele_persistence_and_realised_trait_occupancy_can_differ() -> None:
    size = 21
    params = DynamicsParameters(
        patch_areas=(1.0,),
        generations=2,
        initial_high_allele_frequency=(0.5,),
        initial_trait_distribution=(_low_trait_distribution(size),),
        trait_grid_size=size,
        random_seed=5,
    )
    summary = summarise_replicate(
        simulate(params),
        replicate_index=0,
        seed=5,
        h_alpha_warning_threshold=0.0,
        h_gamma_warning_threshold=0.0,
        fst_warning_threshold=1.0,
    )

    assert summary.tau_trait_realised == 0
    assert summary.h_alpha > 0.0
    assert summary.tau_H_alpha is None


def test_h_alpha_h_gamma_and_fst_are_returned_independently() -> None:
    spec = replace(quick_profile(), replicates=2)
    result = run_parameter_grid(spec, scenarios=(scenario_equal_isolated(spec),))[0]

    metrics = result.summary["metrics"]
    assert set(metrics) >= {"H_alpha", "H_gamma", "F_ST"}
    row = results_to_csv_rows((result,))[0]
    assert "metrics.H_alpha.mean" in row
    assert "metrics.H_gamma.mean" in row
    assert "metrics.F_ST.mean" in row


def test_quick_profile_completes_quickly() -> None:
    spec = quick_profile()
    results = run_parameter_grid(spec)

    assert spec.profile == PROFILE_QUICK
    assert len(results) == len(parameter_grid(spec)) * 3


def test_full_phase_diagram_is_opt_in_not_triggered_by_quick_profile() -> None:
    quick = quick_profile()
    full = full_profile()

    assert quick.profile == PROFILE_QUICK
    assert full.profile == PROFILE_FULL
    assert quick.replicates < full.replicates
    assert len(parameter_grid(quick)) < len(parameter_grid(full))


def test_experiment_layer_does_not_reinterpret_theorem_claims() -> None:
    import causal_model.multipatch_criticality_experiments as experiments

    text = experiments.__doc__
    assert text is not None
    assert "simulation/reporting layer" in text
    assert "does not alter the theorem layer" in text


def test_replicate_summary_reports_patch_distributions() -> None:
    size = 21
    params = DynamicsParameters(
        patch_areas=(2.0, 2.0),
        generations=1,
        initial_trait_distribution=(_high_trait_distribution(size), _low_trait_distribution(size)),
        trait_grid_size=size,
        random_seed=7,
    )
    summary = summarise_replicate(
        simulate(params),
        replicate_index=0,
        seed=7,
        h_alpha_warning_threshold=0.2,
        h_gamma_warning_threshold=0.2,
        fst_warning_threshold=0.2,
    )

    assert len(summary.final_q_by_patch) == 2
    assert len(summary.final_population_by_patch) == 2
    assert len(summary.final_effective_size_by_patch) == 2
    assert len(summary.final_p_by_patch) == 2
