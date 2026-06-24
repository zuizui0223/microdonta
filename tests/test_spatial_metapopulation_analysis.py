"""Peer-review diagnostic tests for the spatial metapopulation backend.

The intervention protocol is deliberately isolated: mutualism, predation, and
dispersal losses change different biological channels.  Channel decomposition is
therefore used to test the mutualism mechanism itself, while predator and
dispersal tests verify that they are not silently relabelled as interaction loss.
"""
from __future__ import annotations

from causal_model.spatial_metapopulation_abm import make_interventions
from causal_model.spatial_metapopulation_analysis import (
    decompose_channels,
    seed_spread,
    threshold_sensitivity,
)

KW = dict(
    equilibration_steps=34, outcome_steps=10, grid_points=7,
    invasion_steps=5, invasion_cohort=10, invasion_replicates=2,
)


def test_mutualism_loss_is_the_contraction_driver():
    """Only pollination loss removes the trait-supporting interaction."""
    intervention = make_interventions(compensation=0.08)["pollination_loss"]
    decomposition = decompose_channels(intervention, n_draws=10, base_seed=100, **KW)
    assert decomposition.full >= 0.6
    assert decomposition.interaction_only >= 0.6
    assert decomposition.secondary_only == 0.0
    assert decomposition.interaction_is_driver


def test_predator_removal_is_an_isolated_predation_intervention():
    """Predator removal leaves mutualism and dispersal channels intact."""
    intervention = make_interventions(compensation=0.08)["predation_loss"]
    assert intervention.before.interaction_scale == intervention.after.interaction_scale == 1.0
    assert intervention.before.dispersal_scale == intervention.after.dispersal_scale == 1.0
    assert intervention.before.predation_scale == 1.0
    assert intervention.after.predation_scale == 0.0


def test_dispersal_loss_is_an_isolated_dispersal_intervention():
    """Dispersal loss leaves mutualism and predation channels intact."""
    intervention = make_interventions(compensation=0.08)["dispersal_loss"]
    assert intervention.before.interaction_scale == intervention.after.interaction_scale == 1.0
    assert intervention.before.predation_scale == intervention.after.predation_scale == 1.0
    assert intervention.before.dispersal_scale == 1.0
    assert intervention.after.dispersal_scale == 0.0


def test_pollination_has_no_secondary_channel():
    intervention = make_interventions(compensation=0.08)["pollination_loss"]
    decomposition = decompose_channels(intervention, n_draws=10, base_seed=100, **KW)
    assert decomposition.secondary_only == 0.0
    assert decomposition.interaction_is_driver


def test_threshold_separation_is_not_an_artifact():
    inc = make_interventions(compensation=0.08)
    suf = make_interventions(compensation=0.55)
    sensitivity = threshold_sensitivity(
        inc["pollination_loss"], suf["pollination_loss"],
        n_draws=10, base_seed=100,
        epsilons=(0.0, 0.2, 0.4), contraction_tols=(0.10, 0.15, 0.25), **KW,
    )
    assert sensitivity.separation_holds
    assert sensitivity.min_separation > 0.1


def test_contraction_is_stable_across_seeds():
    intervention = make_interventions(compensation=0.08)["pollination_loss"]
    spread = seed_spread(intervention, base_seeds=(11, 42, 100), n_draws=10, **KW)
    assert spread.lo >= 0.35
    assert spread.mean >= 0.5


# ---------------------------------------------------------------------------
# (2) Persistence after resident re-equilibration (circularity defence)
# ---------------------------------------------------------------------------

REEQ = dict(
    equilibration_steps=40, reequilibration_steps=55, grid_points=5,
    invasion_steps=4, invasion_cohort=8, invasion_replicates=1,
)


def _aggregate_persistence(intervention, sampler, base_seeds, n_draws=10):
    from causal_model.spatial_metapopulation_analysis import verify_persistent_contraction
    persist = reeq = destab = total = 0
    for base_seed in base_seeds:
        result = verify_persistent_contraction(intervention, ecosystem_sampler=sampler,
                                              n_draws=n_draws, base_seed=base_seed, **REEQ)
        persist += result.n_persistent_contraction
        reeq += result.n_reequilibrated
        destab += result.n_destabilised
        total += result.n_total
    return persist / reeq if reeq else 0.0, destab / total if total else 0.0, reeq


def test_contraction_persists_after_reequilibration():
    from causal_model.spatial_metapopulation_abm import sample_compensated_ecosystem, sample_constrained_ecosystem

    incomplete = make_interventions(compensation=0.08)["pollination_loss"]
    sufficient = make_interventions(compensation=0.55)["pollination_loss"]
    constrained_fraction, _, constrained_reeq = _aggregate_persistence(
        incomplete, sample_constrained_ecosystem, (100, 250, 400)
    )
    compensated_fraction, _, compensated_reeq = _aggregate_persistence(
        sufficient, sample_compensated_ecosystem, (100, 250, 400)
    )
    assert constrained_reeq >= 3 and compensated_reeq >= 3
    assert constrained_fraction >= 0.55
    assert constrained_fraction > compensated_fraction + 0.2


def test_relationship_loss_destabilises_only_under_incomplete_compensation():
    from causal_model.spatial_metapopulation_abm import sample_compensated_ecosystem, sample_constrained_ecosystem

    incomplete = make_interventions(compensation=0.08)["pollination_loss"]
    sufficient = make_interventions(compensation=0.55)["pollination_loss"]
    _, constrained_destabilisation, _ = _aggregate_persistence(
        incomplete, sample_constrained_ecosystem, (100, 250, 400)
    )
    _, compensated_destabilisation, _ = _aggregate_persistence(
        sufficient, sample_compensated_ecosystem, (100, 250, 400)
    )
    assert compensated_destabilisation <= 0.1
    assert constrained_destabilisation > compensated_destabilisation


# ---------------------------------------------------------------------------
# (4) Benefit-form robustness and (5) contraction conditions
# ---------------------------------------------------------------------------

INST = dict(
    equilibration_steps=34, outcome_steps=10, grid_points=7,
    invasion_steps=5, invasion_cohort=10, invasion_replicates=2,
)


def test_contraction_is_robust_to_benefit_shape_but_needs_a_load_bearing_relationship():
    from causal_model.spatial_metapopulation_analysis import benefit_form_sweep

    intervention = make_interventions(compensation=0.08)["pollination_loss"]
    benefit_form = benefit_form_sweep(intervention, n_draws=12, base_seed=100, **INST)
    assert benefit_form["robust_to_shape"]
    magnitude = benefit_form["contraction_by_benefit_magnitude"]
    assert magnitude[0.1] < magnitude[1.0]
    assert magnitude[0.1] <= 0.4


def test_conditions_report_separates_contraction_from_no_contraction():
    from causal_model.spatial_metapopulation_analysis import contraction_conditions_report

    report = contraction_conditions_report(n_draws=12, base_seed=100, **INST)
    contracts = report["contracts_when"]["instantaneous_contraction_fraction"]
    non_contracts = report["does_not_contract_when"]["instantaneous_contraction_fraction"]
    assert contracts > non_contracts + 0.3
