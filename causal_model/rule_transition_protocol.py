"""Public contracts for non-circular rule-transition experiments.

The original ABM modules pre-date the hardened inference layer.  This module
centralises two contracts that must hold regardless of backend:

* an intervention changes exactly one ecological mechanism channel; optional
  compensation is a separately parameterised baseline route; and
* a program motif set contains assumptions only, never a trait-space outcome.

``install_rule_transition_contracts`` is called when :mod:`causal_model` is
imported, so the public factories exposed by the existing backend modules obey
these contracts without changing their simulation equations.
"""
from __future__ import annotations

from typing import Callable, Iterable

OUTCOME_MOTIFS = frozenset({
    "trait_space_contraction",
    "trait_space_fragmentation",
    "trait_space_shift",
    "trait_space_expansion",
    "trait_space_collapse",
    "trait_space_conserved",
    "trait_space_reconfiguration",
})


def assumption_motifs(motifs: Iterable[str]) -> frozenset[str]:
    """Return only structural assumptions, removing every outcome label."""
    return frozenset(motif for motif in motifs if motif not in OUTCOME_MOTIFS)


def changed_mechanism_channels(before: object, after: object) -> frozenset[str]:
    """Return changed biological channels, excluding optional compensation.

    ``repro_baseline`` is intentionally not included: it is an independently
    parameterised compensation route, rather than the intervention channel.
    """
    channels = ("interaction_scale", "predation_scale", "dispersal_scale")
    return frozenset(
        channel
        for channel in channels
        if getattr(before, channel) != getattr(after, channel)
    )


def make_decoupled_spatial_interventions(
    loss_level: float = 0.0,
    compensation: float = 0.0,
) -> dict[str, object]:
    """Create isolated spatial interventions.

    ``loss_level`` affects only the named channel.  ``compensation`` is applied
    through ``repro_baseline`` and can be varied independently in a sensitivity
    sweep; it never rescales a second biological channel.
    """
    from causal_model.spatial_metapopulation_abm import Intervention, Regime

    before = Regime()
    return {
        "pollination_loss": Intervention(
            "pollination_loss",
            before=before,
            after=Regime(
                interaction_scale=loss_level,
                repro_baseline=compensation,
            ),
            channel_motif="interaction_relationship_loss",
        ),
        "predation_loss": Intervention(
            "predation_loss",
            before=before,
            after=Regime(
                predation_scale=loss_level,
                repro_baseline=compensation,
            ),
            channel_motif="topdown_control_loss",
        ),
        "dispersal_loss": Intervention(
            "dispersal_loss",
            before=before,
            after=Regime(
                dispersal_scale=loss_level,
                repro_baseline=compensation,
            ),
            channel_motif="dispersal_pathway_loss",
        ),
    }


def _clean_factory(factory: Callable[[object], Iterable[str]]) -> Callable[[object], frozenset[str]]:
    def cleaned(intervention: object) -> frozenset[str]:
        return assumption_motifs(factory(intervention))

    cleaned.__name__ = factory.__name__
    cleaned.__doc__ = (
        "Return structural program assumptions only; trait-space outcomes are "
        "derived from simulator metadata."
    )
    return cleaned


def install_rule_transition_contracts() -> None:
    """Install clean public factories on the three ABM backend modules.

    The installation is idempotent so package reloads and test collection cannot
    stack wrappers around the same factory.
    """
    from causal_model import colonization_metapopulation_abm as colonization
    from causal_model import defense_metapopulation_abm as defense
    from causal_model import spatial_metapopulation_abm as spatial

    if getattr(spatial, "_RULE_TRANSITION_PROTOCOL_INSTALLED", False):
        return

    spatial.make_interventions = make_decoupled_spatial_interventions
    spatial.constraint_program_motifs = _clean_factory(spatial.constraint_program_motifs)
    spatial.compensated_program_motifs = _clean_factory(spatial.compensated_program_motifs)
    defense.defense_program_motifs = _clean_factory(defense.defense_program_motifs)
    colonization.colonization_program_motifs = _clean_factory(
        colonization.colonization_program_motifs
    )
    spatial._RULE_TRANSITION_PROTOCOL_INSTALLED = True
