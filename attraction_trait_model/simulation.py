"""Stochastic individual-based population simulation for the attraction-trait model.

This module provides the full agent-based Monte-Carlo simulation layer that sits
on top of the deterministic proxy pipeline.  It is intentionally self-contained:
all biological mechanics are delegated to existing modules
(``reproduction``, ``fitness``, ``inheritance``), and only the population-level
loop and summary statistics are implemented here.

Typical usage::

    from attraction_trait_model.simulation import simulate_population
    from attraction_trait_model.environment import Environment
    from attraction_trait_model.parameters import ModelParameters
    from causal_model.switches import PathwaySwitches

    env = Environment(name="Oshima", bombus_frequency=0.6, ...)
    params = ModelParameters()
    switches = PathwaySwitches(direct_pollinator_to_guide=1.0)
    rows = simulate_population(env, params, switches, generations=50, seed=42)
"""

from __future__ import annotations

import dataclasses
import random
from typing import Optional

from .agents import PlantAgent
from .environment import Environment
from .fitness import fitness
from .inheritance import drift_strength, inherit_trait
from .parameters import ModelParameters
from .reproduction import (
    clamp,
    outcrossing_probability,
    selfing_probability,
)

try:
    from causal_model.switches import PathwaySwitches
except ImportError:  # pragma: no cover — allows standalone testing
    PathwaySwitches = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_rng(seed: Optional[int]) -> random.Random:
    """Return a seeded :class:`random.Random` instance."""
    rng = random.Random()
    if seed is not None:
        rng.seed(seed)
    return rng


def _normal(rng: random.Random, mu: float, sd: float) -> float:
    """Draw a Gaussian sample, supporting both ``random.Random`` and NumPy RNG."""
    try:
        return rng.gauss(mu, sd)
    except AttributeError:
        return float(rng.normal(mu, sd))


# ---------------------------------------------------------------------------
# 1. Initialize population
# ---------------------------------------------------------------------------

def initialize_population(
    population_size: int,
    initial_agent: Optional[PlantAgent] = None,
    rng: Optional[random.Random] = None,
) -> list[PlantAgent]:
    """Create an initial population of :class:`PlantAgent` objects.

    Parameters
    ----------
    population_size:
        Number of individuals to create.
    initial_agent:
        Template agent.  When provided each individual is a clone of this
        agent with small Gaussian noise (SD = 0.05) added to every trait.
        When *None* default trait values are used instead.
    rng:
        Random-number generator.  A fresh :class:`random.Random` is created
        if not supplied.

    Returns
    -------
    list[PlantAgent]
        Freshly initialised population.
    """
    if rng is None:
        rng = random.Random()

    NOISE_SD = 0.05

    def _make_agent() -> PlantAgent:
        if initial_agent is not None:
            return PlantAgent(
                nectar_guide=clamp(_normal(rng, initial_agent.nectar_guide, NOISE_SD)),
                flower_size=clamp(_normal(rng, initial_agent.flower_size, NOISE_SD)),
                herkogamy=clamp(_normal(rng, initial_agent.herkogamy, NOISE_SD)),
                selfing_ability=clamp(_normal(rng, initial_agent.selfing_ability, NOISE_SD)),
                neutral_diversity=clamp(
                    _normal(rng, initial_agent.neutral_diversity, NOISE_SD)
                ),
            )
        else:
            return PlantAgent(
                nectar_guide=clamp(_normal(rng, 0.6, NOISE_SD)),
                flower_size=clamp(_normal(rng, 0.7, NOISE_SD)),
                herkogamy=clamp(_normal(rng, 0.7, NOISE_SD)),
                selfing_ability=clamp(_normal(rng, 0.3, NOISE_SD)),
                neutral_diversity=clamp(_normal(rng, 0.8, NOISE_SD)),
            )

    return [_make_agent() for _ in range(population_size)]


# ---------------------------------------------------------------------------
# 2. Choose reproduction mode
# ---------------------------------------------------------------------------

def choose_reproduction_mode(
    agent: PlantAgent,
    env: Environment,
    params: ModelParameters,
    rng: random.Random,
    switches: Optional["PathwaySwitches"] = None,
) -> str:
    """Stochastically assign a reproduction mode to *agent*.

    Parameters
    ----------
    agent:
        The individual plant being evaluated.
    env:
        Population environment (pollinator frequencies, etc.).
    params:
        Model-level biological parameters.
    rng:
        Random-number generator.
    switches:
        Pathway switches controlling mechanistic pathways.  When *None* all
        switch weights are effectively zero.

    Returns
    -------
    str
        One of ``"outcrossing"``, ``"selfing"``, or ``"failed"``.
    """
    outcrossing_benefit = getattr(params, "outcrossing_benefit", 0.0)

    p_out = outcrossing_probability(agent, env, params)

    # M1 pathway: direct pollinator-to-guide bonus
    if switches is not None and switches.direct_pollinator_to_guide > 0:
        bonus = (
            switches.direct_pollinator_to_guide
            * env.bombus_frequency
            * params.bombus_guide_use
            * agent.nectar_guide
        )
        p_out = clamp(p_out + bonus * outcrossing_benefit)

    p_self = selfing_probability(agent, p_out)

    r = rng.random()
    if r < p_out:
        return "outcrossing"
    elif r < p_out + p_self:
        return "selfing"
    else:
        return "failed"


# ---------------------------------------------------------------------------
# 3. Evaluate population
# ---------------------------------------------------------------------------

def evaluate_population(
    population: list[PlantAgent],
    env: Environment,
    params: ModelParameters,
    rng: random.Random,
    switches: Optional["PathwaySwitches"] = None,
) -> list[PlantAgent]:
    """Assign reproduction mode and fitness to every agent.

    Returns a *new* list of agents (originals are not mutated).

    Parameters
    ----------
    population:
        Current generation of plants.
    env:
        Population environment.
    params:
        Biological parameters.
    rng:
        Random-number generator.
    switches:
        Pathway switches.

    Returns
    -------
    list[PlantAgent]
        Evaluated population with updated ``reproduction_mode`` and ``fitness``
        fields.
    """
    evaluated: list[PlantAgent] = []
    for agent in population:
        mode = choose_reproduction_mode(agent, env, params, rng, switches)
        # Set reproduction_mode first so fitness() can read it from agent
        agent_with_mode = dataclasses.replace(agent, reproduction_mode=mode)
        fit = fitness(agent_with_mode, params)
        evaluated.append(dataclasses.replace(agent_with_mode, fitness=fit))
    return evaluated


# ---------------------------------------------------------------------------
# 4. Select parent
# ---------------------------------------------------------------------------

def select_parent(
    population: list[PlantAgent],
    rng: random.Random,
) -> PlantAgent:
    """Fitness-proportional (roulette-wheel) parent selection.

    Falls back to uniform random sampling when total fitness is zero to avoid
    division-by-zero errors.

    Parameters
    ----------
    population:
        Evaluated population (agents must have ``fitness`` set).
    rng:
        Random-number generator.

    Returns
    -------
    PlantAgent
        Selected parent individual.
    """
    total = sum(a.fitness for a in population)
    if total <= 0.0:
        return rng.choice(population)
    r = rng.random() * total
    cumulative = 0.0
    for agent in population:
        cumulative += agent.fitness
        if cumulative >= r:
            return agent
    return population[-1]


# ---------------------------------------------------------------------------
# 5. Produce child
# ---------------------------------------------------------------------------

def produce_child(
    parent: PlantAgent,
    env: Environment,
    params: ModelParameters,
    rng: random.Random,
    switches: Optional["PathwaySwitches"] = None,
) -> PlantAgent:
    """Generate a child agent from *parent* via inheritance, mutation, and drift.

    Applies pathway-specific trait shifts when the relevant switch is active:

    * **selfing_mediation** (M2): selfing syndrome shifts reduce nectar guide,
      flower size, herkogamy and increase selfing ability.
    * **drift_null** (M5): amplifies the drift component.
    * **island_common_cause** (M4): slightly inflates drift based on island
      distance.

    Parameters
    ----------
    parent:
        Parent individual (must have ``reproduction_mode`` set).
    env:
        Population environment.
    params:
        Biological parameters.
    rng:
        Random-number generator.
    switches:
        Pathway switches.

    Returns
    -------
    PlantAgent
        New child agent with all traits clamped to [0, 1].
    """
    mut_sd_guide = getattr(params, "mutation_sd_guide", 0.03)
    mut_sd_flower = getattr(params, "mutation_sd_flower_size", 0.03)
    mut_sd_herk = getattr(params, "mutation_sd_herkogamy", 0.03)
    mut_sd_self = getattr(params, "mutation_sd_selfing_ability", 0.03)
    trait_corr = getattr(params, "trait_correlation_strength", 0.02)

    base_drift_sd = drift_strength(env, params)

    # M5: drift_null amplifies genetic drift
    drift_sd = base_drift_sd
    if switches is not None and switches.drift_null > 0:
        drift_sd = base_drift_sd * (1.0 + switches.drift_null)

    # M4: island common cause adds extra drift proportional to island distance
    if switches is not None and switches.island_common_cause > 0:
        drift_sd = drift_sd + env.island_distance * switches.island_common_cause * 0.1

    nectar_guide = inherit_trait(parent.nectar_guide, mut_sd_guide, drift_sd, rng)
    flower_size = inherit_trait(parent.flower_size, mut_sd_flower, drift_sd, rng)
    herkogamy = inherit_trait(parent.herkogamy, mut_sd_herk, drift_sd, rng)
    selfing_ability = inherit_trait(parent.selfing_ability, mut_sd_self, drift_sd, rng)

    # M2: selfing-mediation syndrome shift
    if (
        switches is not None
        and switches.selfing_mediation > 0
        and parent.reproduction_mode == "selfing"
    ):
        shift = trait_corr * switches.selfing_mediation
        nectar_guide -= shift
        flower_size -= shift * 0.6
        herkogamy -= shift * 0.5
        selfing_ability += shift * 0.4

    # Clamp traits
    nectar_guide = clamp(nectar_guide)
    flower_size = clamp(flower_size)
    herkogamy = clamp(herkogamy)
    selfing_ability = clamp(selfing_ability)

    # Neutral diversity: carry forward with migration mixing
    mig_neutral = _normal(rng, 0.5, 0.1)
    migration_rate = getattr(env, "migration_rate", 0.01)
    neutral_diversity = clamp(
        parent.neutral_diversity * (1.0 - migration_rate) + mig_neutral * migration_rate
    )

    return PlantAgent(
        nectar_guide=nectar_guide,
        flower_size=flower_size,
        herkogamy=herkogamy,
        selfing_ability=selfing_ability,
        neutral_diversity=neutral_diversity,
    )


# ---------------------------------------------------------------------------
# 6. Next generation
# ---------------------------------------------------------------------------

def next_generation(
    evaluated_population: list[PlantAgent],
    env: Environment,
    params: ModelParameters,
    rng: random.Random,
    switches: Optional["PathwaySwitches"] = None,
    population_size: Optional[int] = None,
) -> list[PlantAgent]:
    """Produce the next generation by fitness-proportional selection.

    Parameters
    ----------
    evaluated_population:
        Current generation, already evaluated (fitness and reproduction_mode
        assigned).
    env:
        Population environment.
    params:
        Biological parameters.
    rng:
        Random-number generator.
    switches:
        Pathway switches.
    population_size:
        Target offspring count.  Defaults to ``len(evaluated_population)``.

    Returns
    -------
    list[PlantAgent]
        Next generation of plants.
    """
    n = population_size if population_size is not None else len(evaluated_population)
    children: list[PlantAgent] = []
    for _ in range(n):
        parent = select_parent(evaluated_population, rng)
        child = produce_child(parent, env, params, rng, switches)
        children.append(child)
    return children


# ---------------------------------------------------------------------------
# 7. Summarize population
# ---------------------------------------------------------------------------

def summarize_population(
    population: list[PlantAgent],
    generation: int,
    env: Environment,
) -> dict:
    """Compute generation-level summary statistics.

    Parameters
    ----------
    population:
        Evaluated population for this generation.
    generation:
        Zero-indexed generation number.
    env:
        Population environment (provides ``name``).

    Returns
    -------
    dict
        Keys:

        * ``generation`` — generation index
        * ``population_name`` — ``env.name``
        * ``mean_nectar_guide``
        * ``mean_flower_size``
        * ``mean_herkogamy``
        * ``mean_selfing_ability``
        * ``mean_neutral_diversity``
        * ``selfing_rate`` — fraction of individuals that selfed
        * ``outcrossing_rate``
        * ``failed_rate``
        * ``mean_fitness``
        * ``Fis_proxy`` — proxy inbreeding coefficient
        * ``guide_status`` — ``"maintained"`` or ``"reduced"``
    """
    n = len(population)
    if n == 0:
        return {
            "generation": generation,
            "population_name": env.name,
            "mean_nectar_guide": 0.0,
            "mean_flower_size": 0.0,
            "mean_herkogamy": 0.0,
            "mean_selfing_ability": 0.0,
            "mean_neutral_diversity": 0.0,
            "selfing_rate": 0.0,
            "outcrossing_rate": 0.0,
            "failed_rate": 0.0,
            "mean_fitness": 0.0,
            "Fis_proxy": 0.0,
            "guide_status": "reduced",
        }

    mean_ng = sum(a.nectar_guide for a in population) / n
    mean_fs = sum(a.flower_size for a in population) / n
    mean_hk = sum(a.herkogamy for a in population) / n
    mean_sa = sum(a.selfing_ability for a in population) / n
    mean_nd = sum(a.neutral_diversity for a in population) / n
    mean_fit = sum(a.fitness for a in population) / n

    selfing_count = sum(1 for a in population if a.reproduction_mode == "selfing")
    outcrossing_count = sum(1 for a in population if a.reproduction_mode == "outcrossing")
    failed_count = sum(1 for a in population if a.reproduction_mode == "failed")

    selfing_rate = selfing_count / n
    outcrossing_rate = outcrossing_count / n
    failed_rate = failed_count / n

    fis_proxy = clamp(selfing_rate * 0.8 + (1.0 - mean_nd) * 0.2)
    guide_status = "maintained" if mean_ng >= 0.5 else "reduced"

    return {
        "generation": generation,
        "population_name": env.name,
        "mean_nectar_guide": mean_ng,
        "mean_flower_size": mean_fs,
        "mean_herkogamy": mean_hk,
        "mean_selfing_ability": mean_sa,
        "mean_neutral_diversity": mean_nd,
        "selfing_rate": selfing_rate,
        "outcrossing_rate": outcrossing_rate,
        "failed_rate": failed_rate,
        "mean_fitness": mean_fit,
        "Fis_proxy": fis_proxy,
        "guide_status": guide_status,
    }


# ---------------------------------------------------------------------------
# 8. Simulate population
# ---------------------------------------------------------------------------

def simulate_population(
    env: Environment,
    params: ModelParameters,
    switches: Optional["PathwaySwitches"] = None,
    generations: int = 50,
    population_size: int = 200,
    seed: Optional[int] = None,
    initial_agent: Optional[PlantAgent] = None,
) -> list[dict]:
    """Run a full stochastic individual-based simulation.

    Parameters
    ----------
    env:
        Population environment.
    params:
        Biological parameters.
    switches:
        Pathway switches encoding the active causal structure.  When *None*
        no pathway modifiers are applied.
    generations:
        Number of generations to simulate.
    population_size:
        Number of individuals per generation.
    seed:
        Random seed for reproducibility.
    initial_agent:
        Template for population initialisation.  See
        :func:`initialize_population`.

    Returns
    -------
    list[dict]
        One summary dict per generation (generation 0 … *generations* - 1).
    """
    rng = _get_rng(seed)
    population = initialize_population(population_size, initial_agent=initial_agent, rng=rng)

    summaries: list[dict] = []
    for gen in range(generations):
        evaluated = evaluate_population(population, env, params, rng, switches)
        summary = summarize_population(evaluated, gen, env)
        summaries.append(summary)
        population = next_generation(
            evaluated, env, params, rng, switches, population_size
        )

    return summaries
