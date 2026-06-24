"""Tests for the establishment-mediated colonization backend and the three-backend invariant."""
from __future__ import annotations

from random import Random

from causal_model.abm_family_adapter import RobustnessPolicy, summarise_sweep
from causal_model.rule_transition_pipeline import analyse_rule_transitions
from causal_model.spatial_metapopulation_abm import (
    PopulationState,
    constraint_program_motifs,
    generate_sweep_records,
    make_interventions,
    sample_constrained_ecosystem,
)
from causal_model.defense_metapopulation_abm import (
    defense_program_motifs,
    generate_defense_sweep_records,
    make_defense_intervention,
    sample_constrained_defense,
)
from causal_model.colonization_metapopulation_abm import (
    colonization_program_motifs,
    equilibrate_colonization,
    generate_colonization_sweep_records,
    make_colonization_intervention,
    run_colonization_intervention,
    sample_compensated_colonization,
    sample_constrained_colonization,
    verify_colonization_reconfiguration,
)

# Use a post-loss endpoint, not the historical 10-step transient branch.
COL_KW = dict(
    equilibration_steps=40,
    outcome_steps=10,
    reequilibration_steps=60,
    grid_points=7,
    invasion_steps=5,
    invasion_cohort=10,
    invasion_replicates=2,
)


def test_colonization_traits_bounded_and_intervention_is_connectivity_loss():
    rng = Random(3)
    params, patches = sample_constrained_colonization(rng)
    state, _, _ = equilibrate_colonization(patches, params, steps=36, seed=1)
    assert isinstance(state, PopulationState)
    for ind in state.individuals:
        assert 0.0 <= ind.trait <= 1.0
    intervention = make_colonization_intervention()
    assert intervention.before.connectivity_present == 1.0
    assert intervention.after.connectivity_present == 0.0


def _accept(intervention, sampler, base_seeds, n=12):
    accepted = stationary = 0
    for base_seed in base_seeds:
        for i in range(n):
            params, patches = sampler(Random(base_seed * 1213 + i))
            result = run_colonization_intervention(
                params, patches, intervention, seed=base_seed * 1213 + i, **COL_KW
            )
            if result.stationarity != "stationary":
                continue
            stationary += 1
            accepted += int(result.accepted)
    return (accepted / stationary if stationary else 0.0), stationary


def test_connectivity_loss_reconfigures_robustly_as_contraction():
    intervention = make_colonization_intervention(loss_level=0.0, compensation=0.06)
    fraction, stationary = _accept(intervention, sample_constrained_colonization, (100, 300))
    assert stationary >= 6
    assert fraction >= 0.6
    summary = verify_colonization_reconfiguration(
        intervention,
        ecosystem_sampler=sample_constrained_colonization,
        n_draws=14,
        base_seed=300,
        **COL_KW,
    )
    contractive = summary.primary_counts.get("contraction", 0) + summary.primary_counts.get("collapse", 0)
    assert contractive >= summary.primary_counts.get("shift", 0)


def test_partial_connectivity_loss_is_the_counterexample():
    full = make_colonization_intervention(loss_level=0.0, compensation=0.06)
    partial = make_colonization_intervention(loss_level=0.55, compensation=0.45)
    constrained, _ = _accept(full, sample_constrained_colonization, (100, 300))
    compensated, _ = _accept(partial, sample_compensated_colonization, (100, 300))
    assert constrained > compensated


def test_colonization_motifs_assert_contraction():
    intervention = make_colonization_intervention()
    motifs = colonization_program_motifs(intervention)
    assert "trait_space_contraction" in motifs
    assert "trait_space_shift" not in motifs


def test_three_backend_cross_system_invariant_is_reconfiguration():
    kw = dict(
        equilibration_steps=40,
        outcome_steps=10,
        reequilibration_steps=60,
        grid_points=7,
        invasion_steps=5,
        invasion_cohort=10,
        invasion_replicates=2,
    )
    records = []
    pollination = make_interventions(compensation=0.08)["pollination_loss"]
    records += generate_sweep_records(
        pollination,
        program_id="fecundity_reward",
        program_motifs=constraint_program_motifs(pollination),
        ecosystem_sampler=sample_constrained_ecosystem,
        n_regions=6,
        seeds=(0, 1),
        base_seed=5,
        **kw,
    )
    defense = make_defense_intervention(compensation=0.08)
    records += generate_defense_sweep_records(
        defense,
        program_id="survival_reward",
        program_motifs=defense_program_motifs(defense),
        ecosystem_sampler=sample_constrained_defense,
        n_regions=6,
        seeds=(0, 1),
        base_seed=5,
        **kw,
    )
    colonization = make_colonization_intervention(loss_level=0.0, compensation=0.06)
    records += generate_colonization_sweep_records(
        colonization,
        program_id="establishment_reward",
        program_motifs=colonization_program_motifs(colonization),
        ecosystem_sampler=sample_constrained_colonization,
        n_regions=6,
        seeds=(0, 1),
        base_seed=5,
        **kw,
    )

    policy = RobustnessPolicy(min_replicates=6, min_match_fraction=0.35, fragile_max_fraction=0.15)
    summaries = {(summary.scenario, summary.program_id): summary for summary in summarise_sweep(records, policy)}
    assert summaries[("pollination_loss", "fecundity_reward")].classification == "robust"
    assert summaries[("predator_loss_defense", "survival_reward")].classification == "robust"
    assert summaries[("connectivity_loss_colonization", "establishment_reward")].classification == "robust"

    motifs = analyse_rule_transitions(records, policy).invariant_result.cross_system_common_motifs
    for motif in (
        "relation_change",
        "constraint_reconfiguration",
        "trait_space_reconfiguration",
        "finite_resources",
        "finite_patches",
        "local_interaction",
        "positive_trait_cost",
        "incomplete_compensation",
    ):
        assert motif in motifs
    assert "trait_space_contraction" not in motifs
    assert "trait_space_shift" not in motifs
