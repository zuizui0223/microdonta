"""Tests for the survival-mediated defense backend and the cross-system invariant."""
from __future__ import annotations

from random import Random

from causal_model.abm_family_adapter import RobustnessPolicy, summarise_sweep
from causal_model.rule_transition_pipeline import analyse_rule_transitions
from causal_model.rule_transition_protocol import OUTCOME_MOTIFS
from causal_model.spatial_metapopulation_abm import (
    PopulationState,
    constraint_program_motifs,
    generate_sweep_records,
    make_interventions,
    sample_constrained_ecosystem,
)
from causal_model.defense_metapopulation_abm import (
    defense_program_motifs,
    equilibrate_defense,
    generate_defense_sweep_records,
    make_defense_intervention,
    run_defense_intervention,
    sample_compensated_defense,
    sample_constrained_defense,
    verify_defense_contraction,
)

DEF_KW = dict(
    equilibration_steps=36,
    outcome_steps=10,
    reequilibration_steps=60,
    grid_points=7,
    invasion_steps=5,
    invasion_cohort=10,
    invasion_replicates=2,
)


def test_defense_equilibrium_traits_are_bounded():
    params, patches = sample_constrained_defense(Random(3))
    state, _, report = equilibrate_defense(patches, params, steps=36, seed=1)
    assert isinstance(state, PopulationState)
    assert report.status in {"stationary", "not_converged", "extinct", "oscillating"}
    for individual in state.individuals:
        assert 0.0 <= individual.trait <= 1.0


def test_defense_intervention_is_predator_loss():
    intervention = make_defense_intervention()
    assert intervention.before.predator_present == 1.0
    assert intervention.after.predator_present == 0.0
    assert intervention.channel_motif == "antipredator_relationship_loss"


def _accept_fraction(intervention, sampler, base_seeds, n=12):
    accepted = stationary = 0
    for base_seed in base_seeds:
        for index in range(n):
            params, patches = sampler(Random(base_seed * 1213 + index))
            result = run_defense_intervention(
                params, patches, intervention, seed=base_seed * 1213 + index, **DEF_KW
            )
            if result.stationarity != "stationary":
                continue
            stationary += 1
            accepted += int(result.accepted)
    return (accepted / stationary if stationary else 0.0), stationary


def test_predator_loss_reconfigures_defense_robustly():
    intervention = make_defense_intervention(compensation=0.08)
    fraction, stationary = _accept_fraction(intervention, sample_constrained_defense, (100, 300))
    assert stationary >= 6
    assert fraction >= 0.6


def test_defense_geometry_is_shift_not_contraction():
    intervention = make_defense_intervention(compensation=0.08)
    summary = verify_defense_contraction(
        intervention,
        ecosystem_sampler=sample_constrained_defense,
        n_draws=14,
        base_seed=300,
        **DEF_KW,
    )
    assert summary.contraction_fraction <= 0.4
    assert summary.primary_counts.get("shift", 0) >= max(summary.primary_counts.get("contraction", 0), 1)


def test_defense_compensated_counterexample_accepts_less():
    constrained = make_defense_intervention(compensation=0.08)
    compensated = make_defense_intervention(compensation=0.55)
    constrained_fraction, _ = _accept_fraction(constrained, sample_constrained_defense, (100, 300))
    compensated_fraction, _ = _accept_fraction(compensated, sample_compensated_defense, (100, 300))
    assert constrained_fraction > compensated_fraction


def test_cross_system_invariant_is_reconfiguration_not_geometry():
    spatial_kw = dict(
        equilibration_steps=40,
        outcome_steps=10,
        grid_points=7,
        invasion_steps=5,
        invasion_cohort=10,
        invasion_replicates=2,
    )
    defense_kw = dict(spatial_kw, reequilibration_steps=60)
    pollination = make_interventions(compensation=0.08)["pollination_loss"]
    defense = make_defense_intervention(compensation=0.08)
    records = list(generate_sweep_records(
        pollination,
        program_id="fecundity_reward",
        program_motifs=constraint_program_motifs(pollination),
        ecosystem_sampler=sample_constrained_ecosystem,
        n_regions=6,
        seeds=(0, 1),
        base_seed=5,
        **spatial_kw,
    ))
    records += generate_defense_sweep_records(
        defense,
        program_id="survival_reward",
        program_motifs=defense_program_motifs(defense),
        ecosystem_sampler=sample_constrained_defense,
        n_regions=6,
        seeds=(0, 1),
        base_seed=5,
        **defense_kw,
    )

    policy = RobustnessPolicy(min_replicates=6, min_match_fraction=0.35, fragile_max_fraction=0.15)
    summaries = {(summary.scenario, summary.program_id): summary for summary in summarise_sweep(records, policy)}
    assert summaries[("pollination_loss", "fecundity_reward")].classification == "robust"
    assert summaries[("predator_loss_defense", "survival_reward")].classification == "robust"

    motifs = analyse_rule_transitions(records, policy).invariant_result.cross_system_common_motifs
    for motif in (
        "relation_change",
        "constraint_reconfiguration",
        "trait_space_reconfiguration",
        "finite_resources",
        "positive_trait_cost",
        "incomplete_compensation",
    ):
        assert motif in motifs
    assert "trait_space_contraction" not in motifs
    assert "trait_space_shift" not in motifs


def test_defense_program_motifs_are_assumptions_only():
    motifs = defense_program_motifs(make_defense_intervention())
    assert not (motifs & OUTCOME_MOTIFS)
    assert "antipredator_relationship_loss" in motifs
    assert "positive_trait_cost" in motifs
