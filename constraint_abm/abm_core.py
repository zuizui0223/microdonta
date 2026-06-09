"""ABM simulation runner — assembles attraction_trait_model components.

Bridge between the biological model layer (attraction_trait_model) and the
CAPOM inference pipeline (constraint_abm). Provides a callable simulate() /
simulate_multi_seed() interface that accepts a flat parameter dict.
"""

from __future__ import annotations

import math
import random

from attraction_trait_model.agents import PlantAgent
from attraction_trait_model.environment import Environment
from attraction_trait_model.fitness import fitness as compute_fitness
from attraction_trait_model.inheritance import drift_strength, inherit_trait
from attraction_trait_model.parameters import ModelParameters
from attraction_trait_model.reproduction import (
    clamp,
    outcrossing_probability,
    selfing_probability,
)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


# ---------------------------------------------------------------------------
# Parameter bridging: flat dict → typed model objects
# ---------------------------------------------------------------------------

def _env(params: dict) -> Environment:
    primary = clamp(params.get("bombus_frequency", params.get("bombus_present", 0.0)))
    return Environment(
        name=params.get("population_name", "unknown"),
        primary_pollinator_frequency=primary,
        background_pollinator_frequency=clamp(1.0 - primary),
        community_pollinator_abundance=clamp(params.get("pollinator_environment", 0.5)),
        migration_rate=clamp(params.get("migration_rate", 0.05), 0.0, 1.0),
        effective_population_size=float(params.get("effective_population_size", 100.0)),
        island_distance=float(params.get("island_distance", 0.0)),
    )


def _mp(params: dict) -> ModelParameters:
    mu = params.get("mutation_sd", 0.055)
    mu_t = params.get("mutation_sd_trait", mu * 0.5)
    return ModelParameters(
        base_outcross_rate=params.get("base_outcross", 0.10),
        primary_pollinator_efficiency=params.get("bombus_pollination_efficiency", 0.86),
        background_pollinator_efficiency=params.get("other_pollinator_efficiency", 0.34),
        primary_pollinator_guide_response=params.get("bombus_guide_dependence", 0.75),
        background_pollinator_guide_response=params.get("other_pollinator_guide_use", 0.12),
        seed_set_outcrossing=params.get("seed_set_outcrossing", 0.92),
        seed_set_selfing=params.get("seed_set_selfing", 0.46),
        germination_outcrossed=params.get("germination_outcrossed", 0.86),
        inbreeding_depression=params.get("inbreeding_load", 0.32),
        guide_cost=params.get("guide_cost", 0.06),
        flower_size_cost=params.get("flower_size_cost", 0.02),
        selfing_benefit=params.get("selfing_benefit", 0.0),
        outcrossing_benefit=params.get("outcrossing_benefit", 0.0),
        mutation_sd_guide=mu,
        mutation_sd_flower_size=mu_t,
        mutation_sd_herkogamy=mu_t,
        mutation_sd_selfing_ability=mu_t,
        base_drift_strength=params.get("genetic_drift_strength", 0.035),
    )


# ---------------------------------------------------------------------------
# Population lifecycle
# ---------------------------------------------------------------------------

def _init_population(params: dict, size: int, rng: random.Random) -> list[PlantAgent]:
    def g(key: str, default: float, sd: float) -> float:
        return clamp(rng.gauss(params.get(key, default), sd))

    return [
        PlantAgent(
            nectar_guide=g("nectar_guide", 0.5, 0.08),
            flower_size=g("flower_size", 0.65, 0.08),
            herkogamy=g("herkogamy", 0.55, 0.08),
            selfing_ability=g("selfing_ability", 0.40, 0.06),
            neutral_diversity=clamp(rng.gauss(0.78, 0.08)),
            x=rng.uniform(0, 1),
            y=rng.uniform(0, 1),
        )
        for _ in range(size)
    ]


def _evaluate(
    population: list[PlantAgent],
    env: Environment,
    mp: ModelParameters,
    rng: random.Random,
) -> None:
    for agent in population:
        p_out = outcrossing_probability(agent, env, mp)
        p_self = selfing_probability(agent, p_out)
        r = rng.random()
        if r < p_out:
            agent.reproduction_mode = "outcrossing"
        elif r < p_out + p_self:
            agent.reproduction_mode = "selfing"
        else:
            agent.reproduction_mode = "failed"
        agent.fitness = compute_fitness(agent, mp)


def _offspring(
    parent: PlantAgent,
    env: Environment,
    mp: ModelParameters,
    rng: random.Random,
) -> PlantAgent:
    d_sd = drift_strength(env, mp)
    if parent.reproduction_mode == "outcrossing":
        diversity = parent.neutral_diversity + 0.045
    elif parent.reproduction_mode == "selfing":
        diversity = parent.neutral_diversity * (1.0 - 0.5 * mp.inbreeding_depression)
    else:
        diversity = parent.neutral_diversity * 0.96
    diversity += env.migration_rate * (0.82 - diversity)
    return PlantAgent(
        nectar_guide=inherit_trait(parent.nectar_guide, mp.mutation_sd_guide, d_sd, rng),
        flower_size=inherit_trait(parent.flower_size, mp.mutation_sd_flower_size, d_sd, rng),
        herkogamy=inherit_trait(parent.herkogamy, mp.mutation_sd_herkogamy, d_sd, rng),
        selfing_ability=inherit_trait(parent.selfing_ability, mp.mutation_sd_selfing_ability, d_sd, rng),
        neutral_diversity=clamp(diversity + rng.gauss(0, d_sd)),
        x=clamp(parent.x + rng.gauss(0, 0.055)),
        y=clamp(parent.y + rng.gauss(0, 0.055)),
    )


def _summary(population: list[PlantAgent], env: Environment) -> dict[str, float]:
    selfing_rate = _mean([1.0 if a.reproduction_mode == "selfing" else 0.0 for a in population])
    outcrossing_rate = _mean([1.0 if a.reproduction_mode == "outcrossing" else 0.0 for a in population])
    diversity_vals = [a.neutral_diversity for a in population]
    fis = clamp(selfing_rate * (1.0 - 0.5 * env.migration_rate))
    fst = clamp(
        (1.0 - env.migration_rate) * (1.0 - outcrossing_rate) * (1.0 - _mean(diversity_vals))
    )
    return {
        "mean_nectar_guide": _mean([a.nectar_guide for a in population]),
        "mean_flower_size": _mean([a.flower_size for a in population]),
        "mean_herkogamy": _mean([a.herkogamy for a in population]),
        "mean_selfing_ability": _mean([a.selfing_ability for a in population]),
        "selfing_rate": selfing_rate,
        "outcrossing_rate": outcrossing_rate,
        "failed_rate": _mean([1.0 if a.reproduction_mode == "failed" else 0.0 for a in population]),
        "mean_fitness": _mean([a.fitness for a in population]),
        "mean_neutral_diversity": _mean(diversity_vals),
        "Fis": fis,
        "Fst": fst,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def simulate(
    params: dict,
    generations: int = 80,
    population_size: int = 160,
    seed: int = 42,
) -> dict[str, float]:
    """Run ABM and return final-generation summary statistics.

    Environment params (bombus_frequency, pollinator_environment, migration_rate)
    and latent mechanistic params (guide_cost, genetic_drift_strength, mutation_sd)
    are passed as a single flat dict. Trait starting distributions are initialised
    around nectar_guide, flower_size, herkogamy, selfing_ability if provided.
    """
    rng = random.Random(seed)
    env = _env(params)
    mp = _mp(params)
    population = _init_population(params, population_size, rng)
    _evaluate(population, env, mp, rng)

    for _ in range(generations):
        total_fitness = sum(a.fitness for a in population)
        if total_fitness <= 0:
            break
        weights = [a.fitness / total_fitness for a in population]
        parents = rng.choices(population, weights=weights, k=population_size)
        population = [_offspring(p, env, mp, rng) for p in parents]
        _evaluate(population, env, mp, rng)

    return _summary(population, env)


def simulate_multi_seed(
    params: dict,
    generations: int = 80,
    population_size: int = 160,
    seeds: list[int] | None = None,
) -> dict[str, float]:
    """Average summary statistics across multiple seeds."""
    if seeds is None:
        seeds = [42, 43, 44]
    runs = [simulate(params, generations, population_size, s) for s in seeds]
    keys = list(runs[0].keys())
    return {k: _mean([r[k] for r in runs]) for k in keys}
