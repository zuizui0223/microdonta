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
) -> PopulationProxyOutput:
    """Generate provisional trait and mating-system values for one population."""

    mechanisms = {edge.source + "->" + edge.target for edge in structure.edges}
    edge_targets = {edge.target for edge in structure.edges}
    isolation = env.island_distance
    drift = max(0.0, 1.0 - env.effective_population_size)

    flower_size = 0.76
    herkogamy = 0.72
    selfing_ability = 0.35
    nectar_guide = 0.50

    if "island_isolation->selfing_rate" in mechanisms:
        selfing_ability += 0.40 * isolation
        herkogamy -= 0.28 * isolation

    if "outcrossing_opportunity->selfing_rate" in mechanisms:
        selfing_ability += 0.35 * (1.0 - env.pollinator_environment)
        herkogamy -= 0.22 * (1.0 - env.pollinator_environment)

    if "island_isolation->nectar_guide" in mechanisms:
        nectar_guide -= 0.28 * isolation

    if "Bombus_frequency->nectar_guide" in mechanisms:
        nectar_guide += 0.42 * env.bombus_frequency

    if "drift_strength" in edge_targets or "drift_strength->nectar_guide" in mechanisms:
        nectar_guide -= 0.24 * drift

    if structure.name == "M5_drift_null":
        nectar_guide = 0.52 - 0.30 * drift

    agent = PlantAgent(
        nectar_guide=clamp01(nectar_guide),
        flower_size=clamp01(flower_size),
        herkogamy=clamp01(herkogamy),
        selfing_ability=clamp01(selfing_ability),
        neutral_diversity=env.effective_population_size,
    )
    outcross = outcrossing_probability(agent, env, params)
    selfing = selfing_probability(agent, outcross)

    if "selfing_rate->nectar_guide" in mechanisms:
        agent = replace(agent, nectar_guide=clamp01(agent.nectar_guide - 0.35 * selfing))

    if structure.name in {"M2_selfing_mediated", "M3_direct_plus_mediated"}:
        agent = replace(
            agent,
            flower_size=clamp01(agent.flower_size - 0.18 * selfing),
            herkogamy=clamp01(agent.herkogamy - 0.12 * selfing),
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
