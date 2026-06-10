"""Inheritance, mutation, and drift helpers."""

from __future__ import annotations

import math
from typing import Any

from .agents import PlantAgent
from .environment import Environment
from .parameters import ModelParameters
from .reproduction import clamp


def drift_strength(
    env: Environment,
    params: ModelParameters,
    population_size: int = 1,
) -> float:
    """Return per-individual drift SD scaled by actual effective population size.

    Uses the same Ne definition as the Wright-Fisher H update in
    simulate_population:
        Ne_eff = population_size × env.effective_population_size

    where ``env.effective_population_size`` ∈ [0.05, 1.0] is a relative
    measure derived from island isolation
    (Ne_proxy = max(0.05, 1.0 − 0.765 × island_distance)).

    Previously used ``max(1.0, ne_scale)`` alone (ne_scale ∈ [0.05, 1.0]),
    which decoupled individual trait drift from population-level H loss.
    The fix multiplies by population_size so both mechanisms share the same
    Ne, matching biological reality: drift affects all loci equally.

    Parameters
    ----------
    env:
        Population environment (provides effective_population_size).
    params:
        Model parameters (provides base_drift_strength).
    population_size:
        Current census population size N.  Defaults to 1 for backward-
        compatibility with callers that do not pass this argument; however,
        simulate_population always passes the actual value.
    """

    ne_scale = max(0.05, float(env.effective_population_size))
    actual_ne = max(1.0, float(population_size) * ne_scale)
    return clamp(params.base_drift_strength / math.sqrt(actual_ne), 0.0, 0.25)


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
