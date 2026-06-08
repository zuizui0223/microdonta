"""Campanula Izu: deterministic proxy simulation for causal structure comparison.

Wraps the generic causal_model.simulation functions with campanula-specific
default environments. Kept in examples/campanula_izu/ to leave causal_model/
general-purpose.
"""

from __future__ import annotations

from attraction_trait_model import Environment, ModelParameters
from causal_model.simulation import (
    PopulationProxyOutput,
    relations_from_outputs,
    simulate_population_proxy,
)
from causal_model.structures import CausalStructure
from causal_model.switches import PathwaySwitches, switches_for_structure


def default_campanula_proxy_environments() -> dict[str, Environment]:
    """Return provisional Oshima / Hachijo environments for causal comparison."""

    return {
        "Oshima": Environment(
            name="Oshima",
            bombus_frequency=0.35,
            small_pollinator_frequency=0.55,
            pollinator_environment=0.62,
            migration_rate=0.05,
            effective_population_size=0.55,
            island_distance=0.35,
        ),
        "Hachijo": Environment(
            name="Hachijo",
            bombus_frequency=0.00,
            small_pollinator_frequency=0.72,
            pollinator_environment=0.34,
            migration_rate=0.01,
            effective_population_size=0.22,
            island_distance=0.90,
        ),
    }


def simulate_campanula_causal_structure(
    structure: CausalStructure,
    params: ModelParameters | None = None,
    environments: dict[str, Environment] | None = None,
    switches: PathwaySwitches | None = None,
) -> tuple[dict[str, str], list[PopulationProxyOutput]]:
    """Generate Oshima/Hachijo pattern relations for one causal structure."""

    params = params or ModelParameters()
    environments = environments or default_campanula_proxy_environments()
    switches = switches or switches_for_structure(structure.name)
    outputs = [
        simulate_population_proxy(structure, env, params, switches=switches)
        for env in environments.values()
    ]
    relations = relations_from_outputs(outputs, left="Oshima", right="Hachijo")
    return relations, outputs
