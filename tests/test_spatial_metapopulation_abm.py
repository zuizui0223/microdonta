"""Tests for the spatial metapopulation rule-transition backend.

The spatial backend distinguishes mechanism channels explicitly.  Only a
pollination intervention removes the mutualistic interaction; predation and
dispersal interventions are isolated perturbations rather than aliases for
pollination loss.
"""
from __future__ import annotations

from random import Random

import pytest

from causal_model.abc_distance import accepted_by_epsilon
from causal_model.abm_family_adapter import RobustnessPolicy, SweepRecord, summarise_sweep
from causal_model.rule_transition_invariants import ProgramRun, infer_rule_transition_invariants
from causal_model.rule_transition_pipeline import analyse_rule_transitions
from causal_model.rule_transition_protocol import OUTCOME_MOTIFS, changed_mechanism_channels
from causal_model.spatial_metapopulation_abm import (
    DEFAULT_EPSILON,
    POM_PATTERN_NAMES,
    Individual,
    Patch,
    PopulationState,
    Regime,
    ViableTraitSet,
    assess_stationarity,
    classify_trait_space_change,
    compensated_program_motifs,
    constraint_program_motifs,
    default_observed_pattern,
    default_patches,
    equilibrate,
    estimate_omega_inv,
    generate_sweep_records,
    invasion_growth_rate,
    make_interventions,
    pom_distance,
    run_intervention_experiment,
    sample_compensated_ecosystem,
    sample_constrained_ecosystem,
    verify_contraction_robustness,
)

FAST = dict(
    equilibration_steps=30,
    outcome_steps=8,
    grid_points=7,
    invasion_steps=4,
    invasion_cohort=10,
    invasion_replicates=1,
)


def test_individual_has_required_fields():
    individual = Individual(0.6, 0.5, 2, 1, (0.3, 0.7))
    assert individual.trait == pytest.approx(0.6)
    assert individual.lineage == 0
    with pytest.raises((AttributeError, TypeError)):
        individual.trait = 0.1  # type: ignore[misc]


def test_patch_and_population_metrics():
    patch = Patch(0, 1.0, 20, {1: 0.5})
    assert patch.connectivity[1] == pytest.approx(0.5)
    individuals = tuple(Individual(t, t, 1, 0, (0.1, 0.1)) for t in (0.2, 0.4, 0.6, 0.8))
    state = PopulationState(individuals, {0: 0.5})
    assert state.n_total == 4
    assert state.mean_trait() == pytest.approx(0.5)
    assert state.trait_variance() > 0.0
    assert state.occupied_patches() == frozenset({0})


def test_default_patches_are_finite_and_connected():
    patches = default_patches(3)
    assert len(patches) == 3
    for patch_id, patch in patches.items():
        assert set(patch.connectivity) == {i for i in range(3) if i != patch_id}


def test_no_trait_direction_input_traits_stay_bounded():
    params, patches = sample_constrained_ecosystem(Random(3))
    state, _, _ = equilibrate(patches, params, steps=30, seed=1)
    for individual in state.individuals:
        assert 0.0 <= individual.trait <= 1.0
        assert 0.0 <= individual.genotype <= 1.0


def test_equilibrate_returns_state_and_report():
    params, patches = sample_constrained_ecosystem(Random(5))
    state, patch_states, report = equilibrate(patches, params, steps=30, seed=2)
    assert isinstance(state, PopulationState)
    assert set(patch_states) == set(patches)
    assert report.status in {"stationary", "not_converged", "extinct", "oscillating"}


def test_stationarity_classifies_flat_extinct_trending_and_oscillating_series():
    assert assess_stationarity([30] * 12, [0.4] * 12, [3] * 12, [0.05] * 12).status == "stationary"
    assert assess_stationarity([10, 5, 0], [0.4, 0.3, 0.0], [3, 2, 0], [0.05, 0.04, 0.0]).status == "extinct"
    assert assess_stationarity(list(range(10, 70, 5)), [0.1 + 0.04 * i for i in range(12)], [3] * 12, [0.05] * 12).status == "not_converged"
    assert assess_stationarity([20, 40, 20, 40, 20, 40, 20, 40], [0.4] * 8, [3] * 8, [0.05] * 8).status == "oscillating"


def test_invasion_growth_rate_and_omega_are_grid_aligned():
    params, patches = sample_constrained_ecosystem(Random(7))
    resident, states, _ = equilibrate(patches, params, steps=30, seed=1)
    rate = invasion_growth_rate(resident, states, patches, params, Regime(), 0.3, steps=4, cohort=10, seed=4)
    assert isinstance(rate, float)
    omega = estimate_omega_inv(resident, states, patches, params, Regime(), grid_points=7, invasion_steps=4, cohort=10, replicates=1, seed=2)
    assert len(omega.grid) == len(omega.mask) == len(omega.growth_rates) == 7
    assert 0.0 <= omega.measure <= 1.0


def test_viable_set_measure_components_and_centroid():
    viable = ViableTraitSet(
        grid=(0.0, 0.25, 0.5, 0.75, 1.0),
        mask=(True, True, False, True, False),
        growth_rates=(0.1, 0.1, -0.1, 0.1, -0.2),
    )
    assert viable.measure == pytest.approx(3 / 5)
    assert viable.n_components == 2
    assert viable.viable_values == (0.0, 0.25, 0.75)


def _vts(mask, grid=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)):
    return ViableTraitSet(grid=grid, mask=mask, growth_rates=tuple(0.0 for _ in grid))


def test_trait_space_classification_covers_multiple_geometries():
    assert classify_trait_space_change(_vts((True, True, True, True, True, False)), _vts((True, True, False, False, False, False))).primary == "contraction"
    assert classify_trait_space_change(_vts((True, True, True, False, False, False)), _vts((False, False, False, False, False, False))).primary == "collapse"
    fragmented = classify_trait_space_change(_vts((True, True, True, True, False, False)), _vts((True, False, True, False, True, False)))
    assert fragmented.fragmented
    assert classify_trait_space_change(_vts((True, True, True, False, False, False)), _vts((True, True, True, False, False, False))).primary == "conserved"


def test_pom_has_five_components_and_distance_is_ordinal():
    observed = default_observed_pattern()
    assert set(observed) == set(POM_PATTERN_NAMES)
    assert pom_distance(observed, observed) == pytest.approx(0.0)
    changed = dict(observed)
    changed["omega_inv_state"] = "expanded"
    assert pom_distance(changed, observed) == pytest.approx(1 / 5)


def test_pollination_acceptance_requires_contraction_signature():
    params, patches = sample_constrained_ecosystem(Random(11))
    intervention = make_interventions()["pollination_loss"]
    for seed in range(8):
        result = run_intervention_experiment(params, patches, intervention, seed=seed, **FAST)
        if result.stationarity == "stationary" and result.p_sim.get("omega_inv_state") != "contracted":
            if accepted_by_epsilon(result.distance, DEFAULT_EPSILON):
                assert not result.accepted
                break


def test_intervention_result_is_well_formed():
    params, patches = sample_constrained_ecosystem(Random(13))
    result = run_intervention_experiment(params, patches, make_interventions()["pollination_loss"], seed=1, **FAST)
    assert result.intervention == "pollination_loss"
    assert result.stationarity in {"stationary", "not_converged", "extinct", "oscillating"}
    if result.stationarity == "stationary":
        assert set(result.p_sim) == set(POM_PATTERN_NAMES)
        assert result.accepted == (
            accepted_by_epsilon(result.distance, DEFAULT_EPSILON)
            and result.p_sim["omega_inv_state"] == "contracted"
        )


def test_interventions_change_exactly_one_mechanism_channel_without_compensation():
    interventions = make_interventions()
    expected = {
        "pollination_loss": frozenset({"interaction_scale"}),
        "predation_loss": frozenset({"predation_scale"}),
        "dispersal_loss": frozenset({"dispersal_scale"}),
    }
    assert set(interventions) == set(expected)
    for name, intervention in interventions.items():
        assert isinstance(intervention.before, Regime)
        assert isinstance(intervention.after, Regime)
        assert changed_mechanism_channels(intervention.before, intervention.after) == expected[name]
        assert intervention.after.repro_baseline == intervention.before.repro_baseline == 0.0


def test_compensation_is_independent_of_the_changed_mechanism_channel():
    interventions = make_interventions(compensation=0.08)
    expected = {
        "pollination_loss": frozenset({"interaction_scale"}),
        "predation_loss": frozenset({"predation_scale"}),
        "dispersal_loss": frozenset({"dispersal_scale"}),
    }
    for name, intervention in interventions.items():
        assert changed_mechanism_channels(intervention.before, intervention.after) == expected[name]
        assert intervention.after.repro_baseline == pytest.approx(0.08)


def test_generate_sweep_records_returns_sweeprecords():
    intervention = make_interventions(compensation=0.08)["pollination_loss"]
    records = generate_sweep_records(
        intervention,
        program_id="physical_constraint",
        program_motifs=constraint_program_motifs(intervention),
        ecosystem_sampler=sample_constrained_ecosystem,
        n_regions=3,
        seeds=(0, 1),
        base_seed=1,
        **FAST,
    )
    assert len(records) == 6
    assert all(isinstance(record, SweepRecord) for record in records)
    for record in records:
        assert record.motifs == constraint_program_motifs(intervention)
        assert "omega_inv_state" in record.metadata["P_sim"] or record.metadata["P_sim"] == {}
        assert record.metadata["accepted"] == record.pattern_matched


def test_program_motifs_are_assumptions_only():
    intervention = make_interventions(compensation=0.08)["pollination_loss"]
    constrained = constraint_program_motifs(intervention)
    compensated = compensated_program_motifs(intervention)
    assert not (constrained & OUTCOME_MOTIFS)
    assert not (compensated & OUTCOME_MOTIFS)
    for required in (
        "relation_change",
        "finite_resources",
        "finite_patches",
        "local_interaction",
        "positive_trait_cost",
        "incomplete_compensation",
    ):
        assert required in constrained


def test_pollination_constrained_program_matches_more_than_compensated_counterexample():
    constrained = make_interventions(compensation=0.08)["pollination_loss"]
    compensated = make_interventions(compensation=0.55)["pollination_loss"]
    constrained_records = generate_sweep_records(
        constrained,
        program_id="physical_constraint",
        program_motifs=constraint_program_motifs(constrained),
        ecosystem_sampler=sample_constrained_ecosystem,
        n_regions=6,
        seeds=(0, 1),
        base_seed=5,
        **FAST,
    )
    compensated_records = generate_sweep_records(
        compensated,
        program_id="compensated",
        program_motifs=compensated_program_motifs(compensated),
        ecosystem_sampler=sample_compensated_ecosystem,
        n_regions=6,
        seeds=(0, 1),
        base_seed=5,
        **FAST,
    )
    policy = RobustnessPolicy(min_replicates=6, min_match_fraction=0.4, fragile_max_fraction=0.15)
    summaries = {(summary.scenario, summary.program_id): summary for summary in summarise_sweep(constrained_records + compensated_records, policy)}
    assert summaries[("pollination_loss", "compensated")].classification != "robust"
    assert summaries[("pollination_loss", "physical_constraint")].match_fraction > summaries[("pollination_loss", "compensated")].match_fraction


def test_no_common_rule_when_robust_programs_disagree():
    result = infer_rule_transition_invariants([
        ProgramRun("sysA", "p", frozenset({"interaction_relationship_loss"}), robust=True),
        ProgramRun("sysB", "q", frozenset({"dispersal_pathway_loss"}), robust=True),
    ])
    assert result.no_cross_system_common_rule


def test_constrained_pollination_contracts_more_than_compensated():
    constrained = make_interventions(compensation=0.08)["pollination_loss"]
    compensated = make_interventions(compensation=0.55)["pollination_loss"]
    constrained_summary = verify_contraction_robustness(constrained, ecosystem_sampler=sample_constrained_ecosystem, n_draws=12, base_seed=42, **FAST)
    compensated_summary = verify_contraction_robustness(compensated, ecosystem_sampler=sample_compensated_ecosystem, n_draws=12, base_seed=42, **FAST)
    assert constrained_summary.contraction_fraction > compensated_summary.contraction_fraction
    assert compensated_summary.contraction_fraction <= 0.34


def test_verify_reports_stationarity_and_primary_counts():
    intervention = make_interventions(compensation=0.08)["pollination_loss"]
    summary = verify_contraction_robustness(intervention, ecosystem_sampler=sample_constrained_ecosystem, n_draws=8, base_seed=42, **FAST)
    assert summary.n_runs == 8
    assert sum(summary.stationarity_counts.values()) == 8
    assert sum(summary.primary_counts.values()) == 8
    assert summary.classification in {"robust", "fragile", "insufficient"}
