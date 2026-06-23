"""Tests for the survival-mediated defense backend and the cross-system invariant.

The defense model is a *mechanistically independent* second ecosystem: the trait
(anti-predator defense) is rewarded through SURVIVAL (gated by predator presence)
and paid for through FECUNDITY — the opposite vital-rate wiring of the pollination
backend. It is used to test whether the rule-transition invariant generalises
across structurally different models, and to show that the *geometry* of the
trait-space change (contraction vs shift) is mechanism-specific, not universal.
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
    DefenseParameters,
    defense_program_motifs,
    equilibrate_defense,
    generate_defense_sweep_records,
    make_defense_intervention,
    run_defense_intervention,
    sample_compensated_defense,
    sample_constrained_defense,
    verify_defense_contraction,
)

DEF_KW = dict(equilibration_steps=36, outcome_steps=10, grid_points=7,
              invasion_steps=5, invasion_cohort=10, invasion_replicates=2)


# ---------------------------------------------------------------------------
# Engine basics: emergent, bounded, no trait direction input
# ---------------------------------------------------------------------------

def test_defense_equilibrium_traits_are_bounded():
    rng = Random(3)
    params, patches = sample_constrained_defense(rng)
    state, _, report = equilibrate_defense(patches, params, steps=36, seed=1)
    assert isinstance(state, PopulationState)
    assert report.status in {"stationary", "not_converged", "extinct", "oscillating"}
    for ind in state.individuals:
        assert 0.0 <= ind.trait <= 1.0


def test_defense_intervention_is_predator_loss():
    iv = make_defense_intervention()
    assert iv.before.predator_present == 1.0
    assert iv.after.predator_present == 0.0
    assert iv.channel_motif == "antipredator_relationship_loss"


# ---------------------------------------------------------------------------
# Defense reconfigures trait space as a SHIFT (not contraction)
# ---------------------------------------------------------------------------

def _accept_fraction(intervention, sampler, base_seeds, n=12):
    acc = stat = 0
    for bs in base_seeds:
        for i in range(n):
            p, patches = sampler(Random(bs * 1213 + i))
            r = run_defense_intervention(p, patches, intervention, seed=bs * 1213 + i, **DEF_KW)
            if r.stationarity != "stationary":
                continue
            stat += 1
            acc += int(r.accepted)
    return (acc / stat if stat else 0.0), stat


def test_predator_loss_reconfigures_defense_robustly():
    """Constrained predator loss robustly reconfigures the viable set (shift)."""
    iv = make_defense_intervention(compensation=0.08)
    frac, stat = _accept_fraction(iv, sample_constrained_defense, (100, 300))
    assert stat >= 6
    assert frac >= 0.6


def test_defense_geometry_is_shift_not_contraction():
    """The survival-mediated loss shifts the viable set; contraction is NOT dominant."""
    iv = make_defense_intervention(compensation=0.08)
    summary = verify_defense_contraction(
        iv, ecosystem_sampler=sample_constrained_defense, n_draws=14, base_seed=300, **DEF_KW)
    # contraction is rare; shift dominates the reconfiguration
    assert summary.contraction_fraction <= 0.4
    assert summary.primary_counts.get("shift", 0) >= max(
        summary.primary_counts.get("contraction", 0), 1)


def test_defense_compensated_counterexample_accepts_less():
    iv = make_defense_intervention(compensation=0.08)
    ivc = make_defense_intervention(compensation=0.55)
    con, _ = _accept_fraction(iv, sample_constrained_defense, (100, 300))
    comp, _ = _accept_fraction(ivc, sample_compensated_defense, (100, 300))
    assert con > comp


# ---------------------------------------------------------------------------
# Cross-system invariant across two structurally independent backends
# ---------------------------------------------------------------------------

def test_cross_system_invariant_is_reconfiguration_not_geometry():
    """The robust cross-system invariant across fecundity-rewarded (pollination)
    and survival-rewarded (defense) ecosystems is trait-space *reconfiguration*
    under the physical constraints — NOT the specific geometry (contraction/shift),
    which is mechanism-specific."""
    kw = dict(equilibration_steps=40, outcome_steps=10, grid_points=7,
              invasion_steps=5, invasion_cohort=10, invasion_replicates=2)
    records = []
    piv = make_interventions(compensation=0.08)["pollination_loss"]
    records += generate_sweep_records(
        piv, program_id="fecundity_reward", program_motifs=constraint_program_motifs(piv),
        ecosystem_sampler=sample_constrained_ecosystem, n_regions=6, seeds=(0, 1), base_seed=5, **kw)
    div = make_defense_intervention(compensation=0.08)
    records += generate_defense_sweep_records(
        div, program_id="survival_reward", program_motifs=defense_program_motifs(div),
        ecosystem_sampler=sample_constrained_defense, n_regions=6, seeds=(0, 1), base_seed=5, **kw)

    policy = RobustnessPolicy(min_replicates=6, min_match_fraction=0.35, fragile_max_fraction=0.15)
    summaries = {(s.scenario, s.program_id): s for s in summarise_sweep(records, policy)}
    # both structurally different backends are robust
    assert summaries[("pollination_loss", "fecundity_reward")].classification == "robust"
    assert summaries[("predator_loss_defense", "survival_reward")].classification == "robust"

    motifs = analyse_rule_transitions(records, policy).invariant_result.cross_system_common_motifs
    # shared: the rule-transition chain and the physical constraints
    for m in ("relation_change", "constraint_reconfiguration", "trait_space_reconfiguration",
              "finite_resources", "positive_trait_cost", "incomplete_compensation"):
        assert m in motifs
    # NOT shared: the specific geometry is mechanism-dependent
    assert "trait_space_contraction" not in motifs
    assert "trait_space_shift" not in motifs


def test_defense_motifs_assert_shift_not_contraction():
    div = make_defense_intervention()
    m = defense_program_motifs(div)
    assert "trait_space_shift" in m
    assert "trait_space_contraction" not in m
