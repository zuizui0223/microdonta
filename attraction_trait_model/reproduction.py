"""Reproduction probability functions for the attraction-trait model."""

from __future__ import annotations

from .agents import PlantAgent
from .environment import Environment
from .parameters import ModelParameters


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp a numeric value to a closed interval."""

    return max(low, min(high, float(value)))


def background_pollinator_access(flower_size: float) -> float:
    """Physical access of background pollinators as a function of flower size.

    Background pollinators (small-bodied, e.g. halictids) access smaller
    flowers more easily; large corollas restrict their entry or handling.
    Returns a value in [0, 1]: smaller flowers → higher access.

    Note: primary pollinators (large-bodied, e.g. Bombus) are large enough to
    access any flower size and are therefore not modulated by this function.

    Functional form — linear `1 - flower_size`:
        A linear decrease in access with corolla size is a simplifying
        assumption.  It is mechanistically motivated by:
        - Inouye (1980) Am. Nat.: body-size matching between bee width and
          corolla-tube diameter determines access in resource-partitioned
          pollinator communities.
        - Harder (1985) Oecologia: small bees more effectively exploit
          shallow or narrow corollas; large Bombus force open or bypass
          tight tubes.
        No Campanula-specific measurement of halictid access vs corolla
        size is currently available; the linear form is a working assumption
        pending field data.  A sigmoidal or threshold form may be more
        realistic if corolla-size variation is concentrated near a critical
        access threshold.
    """

    return clamp(1.0 - flower_size)


def outcrossing_probability(
    agent: PlantAgent,
    env: Environment,
    params: ModelParameters,
) -> float:
    """Probability that an individual reproduces by outcrossing.

    Two additive pollinator channels, scaled by community abundance:

        P_outcross =
          base_outcross_rate
          + community_pollinator_abundance × [
                primary_pollinator_frequency
                × primary_pollinator_efficiency
                × (1 + primary_pollinator_guide_response × G_i)
              +
                background_pollinator_frequency
                × background_pollinator_efficiency
                × background_pollinator_access(F_i)
                × (1 + background_pollinator_guide_response × G_i)
            ]

    Primary channel (trait-responsive, efficient guild)
        Visitation rate scales strongly with nectar-guide expression G via
        ``primary_pollinator_guide_response``.  Per-visit efficiency is high
        (``primary_pollinator_efficiency`` ≈ 0.8).  This is the channel
        through which guide loss directly reduces outcrossing.

    Background channel (trait-non-responsive guild)
        Flower SIZE (not guide) limits access via
        ``background_pollinator_access(F) = 1 - F``.  Guide expression has
        minimal influence (``background_pollinator_guide_response`` ≈ 0.1).
        Per-visit efficiency is lower (``background_pollinator_efficiency``
        ≈ 0.3).  This channel still contributes to outcrossing even after
        guide loss.

    Community scalar
        ``community_pollinator_abundance`` multiplies both channels, encoding
        landscape-level variation in total pollinator service (habitat quality,
        resource competition, island area effects).
    """

    primary_channel = (
        env.primary_pollinator_frequency
        * params.primary_pollinator_efficiency
        * (1.0 + params.primary_pollinator_guide_response * agent.nectar_guide)
    )
    background_channel = (
        env.background_pollinator_frequency
        * params.background_pollinator_efficiency
        * background_pollinator_access(agent.flower_size)
        * (1.0 + params.background_pollinator_guide_response * agent.nectar_guide)
    )
    probability = (
        params.base_outcross_rate
        + env.community_pollinator_abundance * (primary_channel + background_channel)
    )
    return clamp(probability)


def selfing_probability(agent: PlantAgent, outcross_prob: float) -> float:
    """Probability of autonomous selfing after outcrossing failure."""

    probability = (
        (1.0 - clamp(outcross_prob))
        * agent.selfing_ability
        * (1.0 - agent.herkogamy)
    )
    return clamp(probability)
