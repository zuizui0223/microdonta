"""Peer-review diagnostic tests for the spatial metapopulation backend.

These lock in the causal-isolation and robustness claims that defend the headline
result against the obvious reviewer objections:

* channel decomposition: contraction is driven by losing the *trait-supporting
  relationship*, not by the secondary predation/dispersal toggle; predator removal
  alone does not contract trait space (a dissociation); dispersal loss is a
  separate spatial route to contraction;
* the constrained-vs-compensated separation is not an artefact of the acceptance or
  contraction thresholds;
* the contraction estimate is stable across independent seeds.
"""
from __future__ import annotations

from causal_model.spatial_metapopulation_abm import make_interventions
from causal_model.spatial_metapopulation_analysis import (
    decompose_channels,
    seed_spread,
    threshold_sensitivity,
)

# Small but stable settings.
KW = dict(
    equilibration_steps=34, outcome_steps=10, grid_points=7,
    invasion_steps=5, invasion_cohort=10, invasion_replicates=2,
)


def test_interaction_loss_is_the_contraction_driver():
    """Losing the trait-supporting interaction contracts trait space in every scenario."""
    iv = make_interventions(compensation=0.08)
    for name in iv:
        dec = decompose_channels(iv[name], n_draws=10, base_seed=100, **KW)
        assert dec.interaction_only >= 0.6, (name, dec.interaction_only)


def test_predator_removal_alone_does_not_contract():
    """Dissociation: removing the predator with the interaction intact does NOT contract."""
    iv = make_interventions(compensation=0.08)
    dec = decompose_channels(iv["predation_loss"], n_draws=10, base_seed=100, **KW)
    assert dec.secondary_only < 0.3
    assert dec.interaction_only > dec.secondary_only + 0.25
    assert dec.interaction_is_driver


def test_pollination_has_no_secondary_channel():
    """Pollination loss is pure trait-support loss: the secondary-only variant is inert."""
    iv = make_interventions(compensation=0.08)
    dec = decompose_channels(iv["pollination_loss"], n_draws=10, base_seed=100, **KW)
    assert dec.secondary_only == 0.0
    assert dec.interaction_is_driver


def test_dispersal_loss_is_an_independent_spatial_route():
    """Cutting dispersal alone (interaction intact) still contracts via spatial isolation."""
    iv = make_interventions(compensation=0.08)
    dec = decompose_channels(iv["dispersal_loss"], n_draws=10, base_seed=100, **KW)
    assert dec.secondary_only > 0.2          # dispersal loss alone contracts trait space


def test_threshold_separation_is_not_an_artifact():
    """Constrained is admitted more than the compensated counterexample across thresholds."""
    inc = make_interventions(compensation=0.08)
    suf = make_interventions(compensation=0.55)
    ts = threshold_sensitivity(
        inc["pollination_loss"], suf["pollination_loss"],
        n_draws=10, base_seed=100,
        epsilons=(0.0, 0.2, 0.4), contraction_tols=(0.10, 0.15, 0.25), **KW,
    )
    assert ts.separation_holds
    assert ts.min_separation > 0.1


def test_contraction_is_stable_across_seeds():
    """The contraction fraction does not hinge on one lucky seed."""
    iv = make_interventions(compensation=0.08)
    ss = seed_spread(iv["pollination_loss"], base_seeds=(11, 42, 100), n_draws=10, **KW)
    assert ss.lo >= 0.35          # consistently contracting on every seed
    assert ss.mean >= 0.5


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
    for bs in base_seeds:
        r = verify_persistent_contraction(intervention, ecosystem_sampler=sampler,
                                          n_draws=n_draws, base_seed=bs, **REEQ)
        persist += r.n_persistent_contraction
        reeq += r.n_reequilibrated
        destab += r.n_destabilised
        total += r.n_total
    cond = persist / reeq if reeq else 0.0
    destab_frac = destab / total if total else 0.0
    return cond, destab_frac, reeq


def test_contraction_persists_after_reequilibration():
    """Among systems that re-stabilise, contraction persists far more under
    incomplete compensation than under sufficient compensation."""
    from causal_model.spatial_metapopulation_abm import (
        make_interventions, sample_constrained_ecosystem, sample_compensated_ecosystem,
    )
    iv = make_interventions(compensation=0.08)["pollination_loss"]
    ivc = make_interventions(compensation=0.55)["pollination_loss"]
    con_cond, _, con_reeq = _aggregate_persistence(iv, sample_constrained_ecosystem, (100, 250, 400))
    comp_cond, _, comp_reeq = _aggregate_persistence(ivc, sample_compensated_ecosystem, (100, 250, 400))
    assert con_reeq >= 3 and comp_reeq >= 3            # enough re-stabilised systems to compare
    assert con_cond >= 0.55                            # persistent contraction is the dominant endpoint
    assert con_cond > comp_cond + 0.2                  # and far exceeds the compensated counterexample


def test_relationship_loss_destabilises_only_under_incomplete_compensation():
    """Sufficient compensation keeps the post-loss system stable; incomplete
    compensation makes the loss destabilising (extinction / non-convergence)."""
    from causal_model.spatial_metapopulation_abm import (
        make_interventions, sample_constrained_ecosystem, sample_compensated_ecosystem,
    )
    iv = make_interventions(compensation=0.08)["pollination_loss"]
    ivc = make_interventions(compensation=0.55)["pollination_loss"]
    _, con_destab, _ = _aggregate_persistence(iv, sample_constrained_ecosystem, (100, 250, 400))
    _, comp_destab, _ = _aggregate_persistence(ivc, sample_compensated_ecosystem, (100, 250, 400))
    assert comp_destab <= 0.1                           # sufficient compensation -> stable
    assert con_destab > comp_destab                     # incomplete compensation -> destabilising


# ---------------------------------------------------------------------------
# (4) Benefit-form robustness and (5) contraction conditions
# ---------------------------------------------------------------------------

INST = dict(
    equilibration_steps=34, outcome_steps=10, grid_points=7,
    invasion_steps=5, invasion_cohort=10, invasion_replicates=2,
)


def test_contraction_is_robust_to_benefit_shape_but_needs_a_load_bearing_relationship():
    from causal_model.spatial_metapopulation_abm import make_interventions
    from causal_model.spatial_metapopulation_analysis import benefit_form_sweep
    iv = make_interventions(compensation=0.08)["pollination_loss"]
    bf = benefit_form_sweep(iv, n_draws=12, base_seed=100, **INST)
    # not an artefact of linear benefit: saturating benefit still contracts
    assert bf["robust_to_shape"]
    # but a weak (non-load-bearing) relationship does not contract
    mag = bf["contraction_by_benefit_magnitude"]
    assert mag[0.1] < mag[1.0]
    assert mag[0.1] <= 0.4


def test_conditions_report_separates_contraction_from_no_contraction():
    from causal_model.spatial_metapopulation_analysis import contraction_conditions_report
    rep = contraction_conditions_report(n_draws=12, base_seed=100, **INST)
    c = rep["contracts_when"]["instantaneous_contraction_fraction"]
    nc = rep["does_not_contract_when"]["instantaneous_contraction_fraction"]
    assert c > nc + 0.3
