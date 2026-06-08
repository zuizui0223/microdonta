"""ABM simulation core for CAPOM inference.

Extracted from streamlit_app.py so that constraint_abm and inference
pipelines can import it without Streamlit.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    if math.isnan(float(value)):
        return low
    return max(low, min(high, float(value)))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


@dataclass
class Plant:
    guide: float
    diversity: float
    x: float
    y: float
    mode: str = "outcrossing"
    seed_output: float = 1.0
    germination: float = 1.0
    fitness: float = 1.0


def _outcross_prob(plant: Plant, params: dict) -> float:
    bombus_freq = clamp(params.get("bombus_frequency", params.get("bombus_present", 0.0)))
    poll_eff = (
        bombus_freq * params["bombus_pollination_efficiency"]
        + (1.0 - bombus_freq) * params["other_pollinator_efficiency"]
    )
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
    effective_selfing = clamp(params["selfing_ability"] * (1.0 - params["herkogamy"]))
    guide_cost = params["guide_cost"] * params["flower_size"]
    for plant in population:
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
        plant.fitness = max(
            0.001,
            plant.seed_output * plant.germination - guide_cost * plant.guide,
        )


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
        Full parameter dict (fixed + latent combined).
    generations:
        Number of generations to run.
    population_size:
        Number of Plant agents.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    dict with keys: mean_nectar_guide, selfing_rate, outcrossing_rate,
    failed_rate, mean_fitness, mean_neutral_diversity, Fis, Fst.
    """
    rng = random.Random(seed)
    guide_start = clamp(params.get("nectar_guide", 0.5))
    population = [
        Plant(
            guide=clamp(rng.gauss(guide_start, 0.12)),
            diversity=clamp(rng.gauss(0.78, 0.08)),
            x=rng.uniform(0, 1),
            y=rng.uniform(0, 1),
        )
        for _ in range(population_size)
    ]
    evaluate_population(population, params, rng)

    for _ in range(generations):
        total_fitness = sum(p.fitness for p in population)
        if total_fitness <= 0:
            break
        weights = [p.fitness / total_fitness for p in population]
        parents = rng.choices(population, weights=weights, k=population_size)
        next_pop: list[Plant] = []
        for parent in parents:
            guide = clamp(parent.guide + rng.gauss(0.0, params["mutation_sd"]))
            if parent.mode == "outcrossing":
                diversity = parent.diversity + 0.045
            elif parent.mode == "selfing":
                diversity = parent.diversity * (1.0 - 0.5 * params["inbreeding_load"])
            else:
                diversity = parent.diversity * 0.96
            diversity += params["migration_rate"] * (0.82 - diversity)
            diversity += rng.gauss(0.0, params["genetic_drift_strength"])
            next_pop.append(
                Plant(
                    guide=guide,
                    diversity=clamp(diversity),
                    x=clamp(parent.x + rng.gauss(0, 0.055)),
                    y=clamp(parent.y + rng.gauss(0, 0.055)),
                )
            )
        population = next_pop
        evaluate_population(population, params, rng)

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
        "selfing_rate": selfing_rate,
        "outcrossing_rate": outcrossing_rate,
        "failed_rate": _mean([1.0 if p.mode == "failed" else 0.0 for p in population]),
        "mean_fitness": _mean([p.fitness for p in population]),
        "mean_neutral_diversity": _mean(diversity_vals),
        "Fis": fis,
        "Fst": fst,
    }


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
