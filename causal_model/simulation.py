"""Generic deterministic proxy simulation for causal structure evaluation.

Provides a lightweight Stage 4 bridge between causal schema and the biological
model layer. Uses attraction_trait_model probability functions to derive pattern
relations without running a full stochastic ABM.

System-specific wrappers (environments, defaults) belong in examples/.
See: examples/campanula_izu/proxy_simulation.py
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from attraction_trait_model import (
    Environment,
    ModelParameters,
    PlantAgent,
    outcrossing_probability,
    selfing_probability,
)

from .structures import CausalStructure
from .switches import PathwaySwitches, switches_for_structure


@dataclass(frozen=True)
class PopulationProxyOutput:
    """Simulation-derived pattern values for one population."""

    population: str
    nectar_guide: float
    selfing_rate: float
    herkogamy: float
    flower_size: float
    Fis: float
    Bombus_frequency: float
    outcrossing_opportunity: float


def simulate_population_proxy(
    structure: CausalStructure,
    env: Environment,
    params: ModelParameters,
    switches: PathwaySwitches | None = None,
) -> PopulationProxyOutput:
    """Generate provisional trait and mating-system values for one population."""

    switches = switches or switches_for_structure(structure.name)
    isolation = env.island_distance
    drift = max(0.0, 1.0 - env.effective_population_size)

    flower_size = 0.76
    herkogamy = 0.72
    selfing_ability = 0.35
    nectar_guide = 0.50

    if switches.island_common_cause > 0:
        selfing_ability += switches.island_common_cause * 0.40 * isolation
        herkogamy -= switches.island_common_cause * 0.28 * isolation

    if switches.selfing_mediation > 0:
        pollination_gap = 1.0 - env.pollinator_environment
        selfing_ability += switches.selfing_mediation * 0.35 * pollination_gap
        herkogamy -= switches.selfing_mediation * 0.22 * pollination_gap

    if switches.island_common_cause > 0:
        nectar_guide -= switches.island_common_cause * 0.28 * isolation

    if switches.direct_pollinator_to_guide > 0:
        nectar_guide += switches.direct_pollinator_to_guide * 0.42 * env.bombus_frequency

    if switches.drift_null > 0:
        nectar_guide -= switches.drift_null * 0.30 * drift

    agent = PlantAgent(
        nectar_guide=clamp01(nectar_guide),
        flower_size=clamp01(flower_size),
        herkogamy=clamp01(herkogamy),
        selfing_ability=clamp01(selfing_ability),
        neutral_diversity=env.effective_population_size,
    )
    outcross = outcrossing_probability(agent, env, params)
    selfing = selfing_probability(agent, outcross)

    if switches.selfing_mediation > 0:
        agent = replace(
            agent,
            nectar_guide=clamp01(
                agent.nectar_guide - switches.selfing_mediation * 0.35 * selfing
            ),
        )

    if switches.selfing_mediation > 0:
        agent = replace(
            agent,
            flower_size=clamp01(agent.flower_size - switches.selfing_mediation * 0.18 * selfing),
            herkogamy=clamp01(agent.herkogamy - switches.selfing_mediation * 0.12 * selfing),
        )

    fis = clamp01(0.04 + 0.78 * selfing + 0.10 * drift)
    return PopulationProxyOutput(
        population=env.name,
        nectar_guide=agent.nectar_guide,
        selfing_rate=selfing,
        herkogamy=agent.herkogamy,
        flower_size=agent.flower_size,
        Fis=fis,
        Bombus_frequency=env.bombus_frequency,
        outcrossing_opportunity=outcross,
    )


def relations_from_outputs(
    outputs: list[PopulationProxyOutput],
    left: str,
    right: str,
    tolerance: float = 1e-9,
) -> dict[str, str]:
    """Convert two population outputs into relation strings such as 'Oshima > Hachijo'."""

    by_population = {output.population: output for output in outputs}
    left_output = by_population[left]
    right_output = by_population[right]
    variables = (
        "nectar_guide",
        "selfing_rate",
        "herkogamy",
        "flower_size",
        "Fis",
        "Bombus_frequency",
    )
    return {
        variable: relation_from_values(
            left,
            getattr(left_output, variable),
            right,
            getattr(right_output, variable),
            tolerance=tolerance,
        )
        for variable in variables
    }


def relation_from_values(
    left_name: str,
    left_value: float,
    right_name: str,
    right_value: float,
    tolerance: float = 1e-9,
) -> str:
    """Return a compact ordinal relation between two numeric values."""

    if abs(left_value - right_value) <= tolerance:
        return f"{left_name} ~= {right_name}"
    if left_value > right_value:
        return f"{left_name} > {right_name}"
    return f"{left_name} < {right_name}"


def clamp01(value: float) -> float:
    """Clamp a value to the closed unit interval."""

    return max(0.0, min(1.0, float(value)))
