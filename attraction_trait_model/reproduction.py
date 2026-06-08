"""Reproduction probability functions for the attraction-trait model."""

from __future__ import annotations

from .agents import PlantAgent
from .environment import Environment
from .parameters import ModelParameters


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp a numeric value to a closed interval."""

    return max(low, min(high, float(value)))


def small_pollinator_access(flower_size: float) -> float:
    """First-pass access function for small pollinators.

    The provisional assumption is that smaller flowers are easier for small
    pollinators to access or handle effectively.
    """

    return clamp(1.0 - flower_size)


def outcrossing_probability(
    agent: PlantAgent,
    env: Environment,
    params: ModelParameters,
) -> float:
    """Probability that an individual reproduces by outcrossing.

    Implements the Issue #2 model rule:

    P_outcross_i =
      base_outcross_rate
      + pollinator_environment * [
          bombus_frequency * bombus_efficiency * (1 + bombus_guide_use * G_i)
          + small_pollinator_frequency * small_pollinator_efficiency
            * small_pollinator_access(F_i)
            * (1 + small_pollinator_guide_use * G_i)
        ]
    """

    bombus_channel = (
        env.bombus_frequency
        * params.bombus_efficiency
        * (1.0 + params.bombus_guide_use * agent.nectar_guide)
    )
    small_pollinator_channel = (
        env.small_pollinator_frequency
        * params.small_pollinator_efficiency
        * small_pollinator_access(agent.flower_size)
        * (1.0 + params.small_pollinator_guide_use * agent.nectar_guide)
    )
    probability = (
        params.base_outcross_rate
        + env.pollinator_environment * (bombus_channel + small_pollinator_channel)
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
