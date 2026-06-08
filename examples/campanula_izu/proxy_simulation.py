"""Campanula Izu: deterministic proxy simulation for causal structure comparison.

Wraps the generic causal_model.simulation functions with campanula-specific
default environments. Kept in examples/campanula_izu/ to leave causal_model/
general-purpose.

Entry points
------------
simulate_campanula_causal_structure(structure, ...)
    Original function. Accepts a pre-defined CausalStructure (M1–M5).
    Switches default to the structure's canonical pathway configuration.

simulate_campanula_with_switches(switches, ...)
    New function for switch posterior inference.
    Accepts an explicit PathwaySwitches object; no CausalStructure required.
    Used by causal_model.switch_inference.

simulate_campanula_gradient(switches, ...)
    Multi-population gradient simulation.
    Runs all four populations (mainland, Oshima, Kozushima, Hachijo) and
    returns outputs keyed by population name.

environments_from_population_env(env_table)
    Convert a population_env.csv dict (from observed_data.load_population_env)
    into {population_name: Environment} for gradient simulation.
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
    """Generate Oshima/Hachijo pattern relations for one pre-defined causal structure.

    Parameters
    ----------
    structure:
        One of the M1–M5 CausalStructure objects.  Used to look up default
        pathway switches when ``switches`` is None.
    params:
        Latent ecological parameters.  Defaults to ModelParameters defaults.
    environments:
        Population environments.  Defaults to Oshima / Hachijo defaults.
    switches:
        Explicit pathway switches.  If None, derived from ``structure.name``.
    """

    params = params or ModelParameters()
    environments = environments or default_campanula_proxy_environments()
    switches = switches or switches_for_structure(structure.name)
    outputs = [
        simulate_population_proxy(structure, env, params, switches=switches)
        for env in environments.values()
    ]
    relations = relations_from_outputs(outputs, left="Oshima", right="Hachijo")
    return relations, outputs


def simulate_campanula_with_switches(
    switches: PathwaySwitches,
    params: ModelParameters | None = None,
    environments: dict[str, Environment] | None = None,
) -> tuple[dict[str, str], list[PopulationProxyOutput]]:
    """Generate Oshima/Hachijo pattern relations for an explicit switch state.

    This is the entry point for switch posterior inference.  No pre-defined
    CausalStructure is required — the switches fully specify the biological
    pathways that are active in this simulation run.

    Parameters
    ----------
    switches:
        Explicit :class:`PathwaySwitches` object specifying pathway weights.
        Created by :func:`causal_model.switch_inference.pathway_switches_from_state`.
    params:
        Latent ecological parameters.  Defaults to ModelParameters defaults.
    environments:
        Population environments.  Defaults to Oshima / Hachijo defaults.

    Returns
    -------
    tuple
        (relations_dict, outputs_list)
        ``relations_dict`` maps pattern names to ordinal relation strings
        (e.g. ``"Oshima > Hachijo"``).
    """

    params = params or ModelParameters()
    environments = environments or default_campanula_proxy_environments()

    # Create a minimal placeholder structure.  Its name is never used because
    # switches are passed explicitly; we only need a valid object type.
    _placeholder = CausalStructure(
        name="switch_inference",
        description="Switch posterior inference — no fixed structure",
        edges=[],
        expected_patterns=[],
        latent_parameters=[],
    )

    outputs = [
        simulate_population_proxy(_placeholder, env, params, switches=switches)
        for env in environments.values()
    ]
    relations = relations_from_outputs(outputs, left="Oshima", right="Hachijo")
    return relations, outputs


# ---------------------------------------------------------------------------
# Multi-population gradient simulation (Tasks 5-6)
# ---------------------------------------------------------------------------

def environments_from_population_env(
    env_table: dict[str, dict],
) -> dict[str, Environment]:
    """Convert population_env.csv data into Environment objects.

    Parameters
    ----------
    env_table:
        Dict returned by observed_data.load_population_env().
        Keys are population names; values are dicts with numeric columns.

    Returns
    -------
    dict
        {population_name: Environment} in CSV row order.
    """
    result: dict[str, Environment] = {}
    for pop_name, row in env_table.items():
        result[pop_name] = Environment(
            name=pop_name,
            bombus_frequency=float(row.get("Bombus_frequency", 0.0)),
            small_pollinator_frequency=float(row.get("small_pollinator_frequency", 0.5)),
            pollinator_environment=float(row.get("pollinator_environment", 0.5)),
            migration_rate=float(row.get("migration_rate", 0.05)),
            effective_population_size=float(row.get("effective_population_size_proxy", 0.5)),
            island_distance=float(row.get("isolation", 0.0)),
        )
    return result


def default_campanula_gradient_environments() -> dict[str, Environment]:
    """Return default mainland / Oshima / Kozushima / Hachijo environments."""
    return {
        "mainland": Environment(
            name="mainland",
            bombus_frequency=0.80,
            small_pollinator_frequency=0.50,
            pollinator_environment=0.88,
            migration_rate=0.15,
            effective_population_size=1.00,
            island_distance=0.00,
        ),
        "Oshima": Environment(
            name="Oshima",
            bombus_frequency=0.45,
            small_pollinator_frequency=0.50,
            pollinator_environment=0.62,
            migration_rate=0.05,
            effective_population_size=0.75,
            island_distance=0.35,
        ),
        "Kozushima": Environment(
            name="Kozushima",
            bombus_frequency=0.20,
            small_pollinator_frequency=0.55,
            pollinator_environment=0.44,
            migration_rate=0.02,
            effective_population_size=0.45,
            island_distance=0.60,
        ),
        "Hachijo": Environment(
            name="Hachijo",
            bombus_frequency=0.00,
            small_pollinator_frequency=0.60,
            pollinator_environment=0.34,
            migration_rate=0.01,
            effective_population_size=0.35,
            island_distance=0.85,
        ),
    }


def simulate_campanula_gradient(
    switches: PathwaySwitches,
    params: ModelParameters | None = None,
    environments: dict[str, Environment] | None = None,
) -> dict[str, PopulationProxyOutput]:
    """Simulate all gradient populations and return outputs by population name.

    Parameters
    ----------
    switches:
        PathwaySwitches specifying which pathways are active.
    params:
        Latent ecological parameters. Defaults to ModelParameters defaults.
    environments:
        {population_name: Environment}. Defaults to four-population gradient.

    Returns
    -------
    dict
        {population_name: PopulationProxyOutput} in population order.
    """
    params = params or ModelParameters()
    environments = environments or default_campanula_gradient_environments()

    _placeholder = CausalStructure(
        name="gradient_inference",
        description="Multi-population gradient simulation",
        edges=[],
        expected_patterns=[],
        latent_parameters=[],
    )

    return {
        pop_name: simulate_population_proxy(
            _placeholder, env, params, switches=switches
        )
        for pop_name, env in environments.items()
    }
