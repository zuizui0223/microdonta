"""Tests for the establishment-mediated colonization backend (third ecosystem)
and the three-backend cross-system invariant.

The colonization model rewards the focal trait (dispersal investment) through
OFFSPRING ESTABLISHMENT — escaping local competition / recolonising patches emptied
by local extinction — gated by connectivity, and paid through fecundity. It is the
third mechanistically independent vital-rate wiring (after fecundity and survival).
Connectivity loss makes committed dispersal lethal, so it CONTRACTS the viable set
(like pollination, unlike the survival-gated defense which shifts).
"""
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

COL_KW = dict(equilibration_steps=40, outcome_steps=10, grid_points=7,
              invasion_steps=5, invasion_cohort=10, invasion_replicates=2)


def test_colonization_traits_bounded_and_intervention_is_connectivity_loss():
    rng = Random(3)
    params, patches = sample_constrained_colonization(rng)
    state, _, report = equilibrate_colonization(patches, params, steps=36, seed=1)
    assert isinstance(state, PopulationState)
    for ind in state.individuals:
        assert 0.0 <= ind.trait <= 1.0
    iv = make_colonization_intervention()
    assert iv.before.connectivity_present == 1.0
    assert iv.after.connectivity_present == 0.0


def _accept(intervention, sampler, base_seeds, n=12):
    acc = stat = 0
    for bs in base_seeds:
        for i in range(n):
            p, patches = sampler(Random(bs * 1213 + i))
            r = run_colonization_intervention(p, patches, intervention, seed=bs * 1213 + i, **COL_KW)
            if r.stationarity != "stationary":
                continue
            stat += 1
            acc += int(r.accepted)
    return (acc / stat if stat else 0.0), stat


def test_connectivity_loss_reconfigures_robustly_as_contraction():
    iv = make_colonization_intervention(loss_level=0.0, compensation=0.06)
    frac, stat = _accept(iv, sample_constrained_colonization, (100, 300))
    assert stat >= 6
    assert frac >= 0.6
    summary = verify_colonization_reconfiguration(
        iv, ecosystem_sampler=sample_constrained_colonization, n_draws=14, base_seed=300, **COL_KW)
    # contraction/collapse dominate (the geometry patterns with pollination, not defense)
    contractive = summary.primary_counts.get("contraction", 0) + summary.primary_counts.get("collapse", 0)
    assert contractive >= summary.primary_counts.get("shift", 0)


def test_partial_connectivity_loss_is_the_counterexample():
    """If corridors are only degraded (dispersers still establish), trait space is
    not robustly reconfigured."""
    full = make_colonization_intervention(loss_level=0.0, compensation=0.06)
    partial = make_colonization_intervention(loss_level=0.55, compensation=0.45)
    con, _ = _accept(full, sample_constrained_colonization, (100, 300))
    comp, _ = _accept(partial, sample_compensated_colonization, (100, 300))
    assert con > comp


def test_colonization_motifs_assert_contraction():
    civ = make_colonization_intervention()
    m = colonization_program_motifs(civ)
    assert "trait_space_contraction" in m
    assert "trait_space_shift" not in m


def test_three_backend_cross_system_invariant_is_reconfiguration():
    """Across three structurally independent ecosystems — fecundity-rewarded
    (pollination), survival-rewarded (defense), establishment-rewarded
    (colonization) — the robust cross-system invariant is trait-space
    RECONFIGURATION under the physical constraints; the specific geometry
    (contraction for two, shift for one) is NOT cross-system."""
    kw = dict(equilibration_steps=40, outcome_steps=10, grid_points=7,
              invasion_steps=5, invasion_cohort=10, invasion_replicates=2)
    recs = []
    piv = make_interventions(compensation=0.08)["pollination_loss"]
    recs += generate_sweep_records(
        piv, program_id="fecundity_reward", program_motifs=constraint_program_motifs(piv),
        ecosystem_sampler=sample_constrained_ecosystem, n_regions=6, seeds=(0, 1), base_seed=5, **kw)
    div = make_defense_intervention(compensation=0.08)
    recs += generate_defense_sweep_records(
        div, program_id="survival_reward", program_motifs=defense_program_motifs(div),
        ecosystem_sampler=sample_constrained_defense, n_regions=6, seeds=(0, 1), base_seed=5, **kw)
    civ = make_colonization_intervention(loss_level=0.0, compensation=0.06)
    recs += generate_colonization_sweep_records(
        civ, program_id="establishment_reward", program_motifs=colonization_program_motifs(civ),
        ecosystem_sampler=sample_constrained_colonization, n_regions=6, seeds=(0, 1), base_seed=5, **kw)

    policy = RobustnessPolicy(min_replicates=6, min_match_fraction=0.35, fragile_max_fraction=0.15)
    summaries = {(s.scenario, s.program_id): s for s in summarise_sweep(recs, policy)}
    assert summaries[("pollination_loss", "fecundity_reward")].classification == "robust"
    assert summaries[("predator_loss_defense", "survival_reward")].classification == "robust"
    assert summaries[("connectivity_loss_colonization", "establishment_reward")].classification == "robust"

    motifs = analyse_rule_transitions(recs, policy).invariant_result.cross_system_common_motifs
    for m in ("relation_change", "constraint_reconfiguration", "trait_space_reconfiguration",
              "finite_resources", "finite_patches", "local_interaction",
              "positive_trait_cost", "incomplete_compensation"):
        assert m in motifs
    assert "trait_space_contraction" not in motifs   # absent in defense (shift)
    assert "trait_space_shift" not in motifs          # absent in pollination/colonization
