"""ABM simulation core for CAPOM inference.

Individual-level heritable traits
----------------------------------
nectar_guide, flower_size, herkogamy, selfing_ability, neutral_diversity
are all carried by each Plant agent and evolve via inheritance + mutation.

Population-level params (fixed)
---------------------------------
pollinator_environment, bombus_frequency, seed_set_*, germination_*,
migration_rate, guide_cost, bombus_*_efficiency, *_guide_*, base_outcross,
mutation_sd, genetic_drift_strength.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    if math.isnan(float(value)):
        return low
    return max(low, min(high, float(value)))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

@dataclass
class Plant:
    # --- heritable, mutable individual traits ---
    guide: float            # nectar-guide intensity
    flower_size: float      # corolla size / floral display
    herkogamy: float        # anther-stigma separation
    selfing_ability: float  # intrinsic self-compatibility
    diversity: float        # neutral genetic diversity proxy

    # --- position (spatial jitter only, no selection) ---
    x: float
    y: float

    # --- state updated each generation by evaluate_population ---
    mode: str = "outcrossing"
    seed_output: float = 1.0
    germination: float = 1.0
    fitness: float = 1.0


# ---------------------------------------------------------------------------
# Fitness evaluation
# ---------------------------------------------------------------------------

def _outcross_prob(plant: Plant, params: dict) -> float:
    bombus_freq = clamp(params.get("bombus_frequency", params.get("bombus_present", 0.0)))
    poll_eff = (
        bombus_freq * params["bombus_pollination_efficiency"]
        + (1.0 - bombus_freq) * params["other_pollinator_efficiency"]
    )
    # Guide alignment uses the *individual* plant's nectar-guide intensity
    guide_align = (
        bombus_freq * params["bombus_guide_dependence"]
        + (1.0 - bombus_freq) * params["other_pollinator_guide_use"]
    )
    return clamp(
        params["base_outcross"]
        + params["pollinator_environment"]
        * poll_eff
        * (params["pollinator_environment_outcross_effect"] + guide_align * plant.guide)
    )


def evaluate_population(population: list[Plant], params: dict, rng: random.Random) -> None:
    """Assign reproduction mode and fitness to every plant in-place.

    Key change from v1: uses *individual* plant.herkogamy, plant.selfing_ability,
    and plant.flower_size rather than population-level constants.
    """
    for plant in population:
        # Herkogamy constrains realised selfing ability at the individual level
        effective_selfing = clamp(plant.selfing_ability * (1.0 - plant.herkogamy))

        outcrossing = rng.random() < _outcross_prob(plant, params)
        selfing = (not outcrossing) and (rng.random() < effective_selfing)
        plant.mode = "outcrossing" if outcrossing else "selfing" if selfing else "failed"

        if outcrossing:
            plant.seed_output = params["seed_set_outcrossing"]
            plant.germination = params["germination_outcrossed"]
        elif selfing:
            plant.seed_output = params["seed_set_selfing"]
            plant.germination = max(
                0.0,
                min(
                    params["germination_selfed"],
                    params["germination_outcrossed"] - params["inbreeding_load"],
                ),
            )
        else:
            plant.seed_output = 0.02
            plant.germination = 0.02

        # Floral display cost scales with the *individual* flower_size
        guide_cost = params["guide_cost"] * plant.flower_size
        plant.fitness = max(
            0.001,
            plant.seed_output * plant.germination - guide_cost * plant.guide,
        )


# ---------------------------------------------------------------------------
# Offspring production
# ---------------------------------------------------------------------------

def _inherit(parent_val: float, rng: random.Random, mutation_sd: float) -> float:
    return clamp(parent_val + rng.gauss(0.0, mutation_sd))


def _make_offspring(
    parent: Plant,
    rng: random.Random,
    params: dict,
) -> Plant:
    """Produce one offspring from a parent via inheritance + mutation + drift."""
    mu = params["mutation_sd"]
    # Structural traits (flower_size, herkogamy, selfing_ability) are assumed
    # more developmentally canalized than nectar_guide, so they mutate at half
    # the rate. This is a conservative default; adjust via mutation_sd_trait.
    mu_trait = params.get("mutation_sd_trait", mu * 0.5)

    if parent.mode == "outcrossing":
        diversity = parent.diversity + 0.045
    elif parent.mode == "selfing":
        diversity = parent.diversity * (1.0 - 0.5 * params["inbreeding_load"])
    else:
        diversity = parent.diversity * 0.96
    diversity += params["migration_rate"] * (0.82 - diversity)
    diversity += rng.gauss(0.0, params["genetic_drift_strength"])

    return Plant(
        guide=_inherit(parent.guide, rng, mu),
        flower_size=_inherit(parent.flower_size, rng, mu_trait),
        herkogamy=_inherit(parent.herkogamy, rng, mu_trait),
        selfing_ability=_inherit(parent.selfing_ability, rng, mu_trait),
        diversity=clamp(diversity),
        x=clamp(parent.x + rng.gauss(0, 0.055)),
        y=clamp(parent.y + rng.gauss(0, 0.055)),
    )


# ---------------------------------------------------------------------------
# Population initialisation
# ---------------------------------------------------------------------------

def _init_population(
    params: dict,
    population_size: int,
    rng: random.Random,
) -> list[Plant]:
    """Initialise agents from normal distributions around population starting values.

    Starting values (means) come from params; individual variation is ±0.08
    for guide / flower_size / herkogamy, ±0.06 for selfing_ability.
    """
    return [
        Plant(
            guide=clamp(rng.gauss(params.get("nectar_guide", 0.5), 0.08)),
            flower_size=clamp(rng.gauss(params.get("flower_size", 0.65), 0.08)),
            herkogamy=clamp(rng.gauss(params.get("herkogamy", 0.55), 0.08)),
            selfing_ability=clamp(rng.gauss(params.get("selfing_ability", 0.40), 0.06)),
            diversity=clamp(rng.gauss(0.78, 0.08)),
            x=rng.uniform(0, 1),
            y=rng.uniform(0, 1),
        )
        for _ in range(population_size)
    ]


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

def _summary(population: list[Plant], params: dict) -> dict[str, float]:
    selfing_rate = _mean([1.0 if p.mode == "selfing" else 0.0 for p in population])
    outcrossing_rate = _mean([1.0 if p.mode == "outcrossing" else 0.0 for p in population])
    diversity_vals = [p.diversity for p in population]
    fis = clamp(selfing_rate * (1.0 - 0.5 * params["migration_rate"]))
    fst = clamp(
        (1.0 - params["migration_rate"])
        * (1.0 - outcrossing_rate)
        * (1.0 - _mean(diversity_vals))
    )
    return {
        "mean_nectar_guide": _mean([p.guide for p in population]),
        "mean_flower_size": _mean([p.flower_size for p in population]),
        "mean_herkogamy": _mean([p.herkogamy for p in population]),
        "mean_selfing_ability": _mean([p.selfing_ability for p in population]),
        "selfing_rate": selfing_rate,
        "outcrossing_rate": outcrossing_rate,
        "failed_rate": _mean([1.0 if p.mode == "failed" else 0.0 for p in population]),
        "mean_fitness": _mean([p.fitness for p in population]),
        "mean_neutral_diversity": _mean(diversity_vals),
        "Fis": fis,
        "Fst": fst,
    }


# ---------------------------------------------------------------------------
# Public simulation API
# ---------------------------------------------------------------------------

def simulate(
    params: dict,
    generations: int = 80,
    population_size: int = 160,
    seed: int = 42,
) -> dict[str, float]:
    """Run ABM and return final-generation summary statistics.

    Parameters
    ----------
    params:
        Combined parameter dict.  Individual-trait starting means are read
        from keys: nectar_guide, flower_size, herkogamy, selfing_ability.
        These are now *initial conditions*, not fixed-across-generations values.
    generations, population_size, seed:
        Simulation settings.

    Returns
    -------
    dict with keys: mean_nectar_guide, mean_flower_size, mean_herkogamy,
    mean_selfing_ability, selfing_rate, outcrossing_rate, failed_rate,
    mean_fitness, mean_neutral_diversity, Fis, Fst.
    """
    rng = random.Random(seed)
    population = _init_population(params, population_size, rng)
    evaluate_population(population, params, rng)

    for _ in range(generations):
        total_fitness = sum(p.fitness for p in population)
        if total_fitness <= 0:
            break
        weights = [p.fitness / total_fitness for p in population]
        parents = rng.choices(population, weights=weights, k=population_size)
        population = [_make_offspring(p, rng, params) for p in parents]
        evaluate_population(population, params, rng)

    return _summary(population, params)


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
