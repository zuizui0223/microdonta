"""Inheritance, mutation, and drift helpers."""

from __future__ import annotations

import math
from typing import Any

from .agents import PlantAgent
from .environment import Environment
from .parameters import ModelParameters
from .reproduction import clamp


def drift_strength(env: Environment, params: ModelParameters) -> float:
    """Return drift strength scaled by effective population size.

    The value is bounded to avoid explosive drift when effective population
    size is very small and to keep trait changes in a provisional model range.
    """

    effective_ne = max(1.0, float(env.effective_population_size))
    return clamp(params.base_drift_strength / math.sqrt(effective_ne), 0.0, 0.25)


def _normal(rng: Any, mean: float, sd: float) -> float:
    if hasattr(rng, "gauss"):
        return float(rng.gauss(mean, sd))
    if hasattr(rng, "normal"):
        return float(rng.normal(mean, sd))
    if hasattr(rng, "normalvariate"):
        return float(rng.normalvariate(mean, sd))
    raise TypeError("rng must provide gauss(), normal(), or normalvariate().")


def inherit_trait(parent_value: float, mutation_sd: float, drift_sd: float, rng: Any) -> float:
    """Inherit a trait with mutation and drift, clamped to 0-1."""

    mutation = _normal(rng, 0.0, mutation_sd)
    drift = _normal(rng, 0.0, drift_sd)
    return clamp(parent_value + mutation + drift)


def selfing_syndrome_shift(agent: PlantAgent, params: ModelParameters) -> dict[str, float]:
    """Future extension for weak selfing-syndrome trait correlations.

    Stage 2 does not impose syndrome-driven trait change. Later simulations can
    use `trait_correlation_strength` to weakly bias nectar_guide, flower_size,
    herkogamy, and selfing_ability when selfing is repeatedly favored.
    """

    _ = (agent, params)
    return {
        "nectar_guide": 0.0,
        "flower_size": 0.0,
        "herkogamy": 0.0,
        "selfing_ability": 0.0,
    }
