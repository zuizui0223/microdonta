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
