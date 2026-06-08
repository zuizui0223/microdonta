"""Generic deterministic proxy simulation for causal structure evaluation.

Provides a lightweight Stage 4 bridge between causal schema and the biological
model layer. Uses attraction_trait_model probability functions to derive pattern
relations without running a full stochastic ABM.

This proxy is intentionally simple, but it should still respond to sampled
latent benefit/cost parameters. In particular, guide_cost, outcrossing_benefit,
selfing_benefit, inbreeding_depression, small_pollinator_efficiency,
base_drift_strength, and bombus_guide_use all influence the generated pattern.

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
    """Generate provisional trait and mating-system values for one population.

    This is not a full stochastic ABM. It is a fast proxy used for Streamlit
    Research Mode and causal-structure debugging. The important design principle
    is that sampled latent parameters must change the generated patterns.

    Parameter effects implemented here:

    - ``guide_cost`` lowers nectar-guide and flower-size values.
    - ``outcrossing_benefit`` and ``bombus_guide_use`` increase guide retention
      when the direct pollinator-to-guide pathway is active.
    - ``selfing_benefit`` increases selfing tendency when the selfing-mediated
      pathway is active.
    - ``inbreeding_depression`` reduces the net advantage of selfing.
    - ``small_pollinator_efficiency`` increases outcrossing opportunity via the
      attraction_trait_model reproduction equation.
    - ``base_drift_strength`` amplifies drift-driven guide loss under drift/null
      and low-Ne/common-island pathways.

    The coefficients below are provisional; they should later be replaced by
    sensitivity analysis or a full stochastic generative ABM.
    """

    switches = switches or switches_for_structure(structure.name)
    isolation = clamp01(env.island_distance)
    ne_proxy = clamp01(env.effective_population_size)
    low_ne = clamp01(1.0 - ne_proxy)

    # Drift should depend on both island Ne and sampled latent drift strength.
    sampled_drift = clamp01(params.base_drift_strength)
    drift = clamp01(low_ne * (0.75 + 1.50 * sampled_drift))

    # Start from a generic outcrossing-like floral state.
    flower_size = 0.76
    herkogamy = 0.72
    selfing_ability = 0.35
    nectar_guide = 0.50

    # Parameter-level trade-off quantities.
    guide_net_benefit = (
        params.outcrossing_benefit
        + params.bombus_guide_use * env.bombus_frequency
        - params.guide_cost
    )
    selfing_net_benefit = params.selfing_benefit - params.inbreeding_depression
    pollination_gap = clamp01(1.0 - env.pollinator_environment)

    # Common-cause island pathway: island isolation shifts multiple variables
    # upstream without forcing a direct Bombus -> guide causal interpretation.
    if switches.island_common_cause > 0:
        selfing_ability += switches.island_common_cause * 0.32 * isolation
        selfing_ability += switches.island_common_cause * 0.20 * max(0.0, selfing_net_benefit)
        herkogamy -= switches.island_common_cause * 0.24 * isolation
        flower_size -= switches.island_common_cause * 0.12 * isolation
        nectar_guide -= switches.island_common_cause * 0.20 * isolation
        nectar_guide -= switches.island_common_cause * 0.10 * drift

    # Selfing-mediated pathway: pollination gaps and positive selfing net benefit
    # increase selfing ability and reduce traits associated with outcrossing.
    if switches.selfing_mediation > 0:
        selfing_pressure = clamp01(
            0.55 * pollination_gap
            + 0.45 * max(0.0, selfing_net_benefit)
        )
        selfing_ability += switches.selfing_mediation * 0.45 * selfing_pressure
        herkogamy -= switches.selfing_mediation * 0.25 * selfing_pressure
        flower_size -= switches.selfing_mediation * 0.16 * selfing_pressure

    # Direct pollinator-to-guide pathway: Bombus and guide use make guide
    # retention beneficial, but maintenance cost opposes it.
    if switches.direct_pollinator_to_guide > 0:
        direct_benefit = (
            env.bombus_frequency
            * params.bombus_guide_use
            * params.outcrossing_benefit
        )
        nectar_guide += switches.direct_pollinator_to_guide * 0.50 * direct_benefit

    # Trait-maintenance costs act regardless of causal scenario.
    nectar_guide -= 0.45 * params.guide_cost
    flower_size -= 0.20 * params.flower_size_cost

    # If the net guide benefit is negative, guide expression is harder to retain.
    if guide_net_benefit < 0.0:
        nectar_guide += 0.25 * guide_net_benefit
    else:
        nectar_guide += 0.10 * min(guide_net_benefit, 1.0)

    # Drift/null pathway: guide can move downward stochastically/approximately,
    # but this should not automatically create the full selfing syndrome.
    if switches.drift_null > 0:
        nectar_guide -= switches.drift_null * 0.32 * drift

    agent = PlantAgent(
        nectar_guide=clamp01(nectar_guide),
        flower_size=clamp01(flower_size),
        herkogamy=clamp01(herkogamy),
        selfing_ability=clamp01(selfing_ability),
        neutral_diversity=ne_proxy,
    )

    outcross = outcrossing_probability(agent, env, params)
    selfing = selfing_probability(agent, outcross)

    # Once realised selfing is high, the selfing-mediated pathway further reduces
    # outcrossing-associated signals. The strength depends on sampled parameters.
    if switches.selfing_mediation > 0:
        realised_selfing_pressure = clamp01(
            selfing
            * (0.60 + 0.40 * max(0.0, params.selfing_benefit))
            * (1.0 - 0.50 * params.inbreeding_depression)
        )
        agent = replace(
            agent,
            nectar_guide=clamp01(
                agent.nectar_guide
                - switches.selfing_mediation * 0.30 * realised_selfing_pressure
                - switches.selfing_mediation * 0.12 * params.guide_cost
            ),
            flower_size=clamp01(
                agent.flower_size - switches.selfing_mediation * 0.14 * realised_selfing_pressure
            ),
            herkogamy=clamp01(
                agent.herkogamy - switches.selfing_mediation * 0.10 * realised_selfing_pressure
            ),
        )

    # Fis proxy: selfing raises Fis; low Ne/drift also contributes weakly.
    fis = clamp01(
        0.04
        + 0.72 * selfing
        + 0.10 * drift
        + 0.08 * max(0.0, selfing_net_benefit)
    )

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
