"""Campanula Izu: deterministic proxy simulation for causal structure comparison.

Wraps the generic causal_model.simulation functions with campanula-specific
default environments. Kept in examples/campanula_izu/ to leave causal_model/
general-purpose.

Two entry points
----------------
simulate_campanula_causal_structure(structure, ...)
    Original function. Accepts a pre-defined CausalStructure (M1–M5).
    Switches default to the structure's canonical pathway configuration.

simulate_campanula_with_switches(switches, ...)
    New function for switch posterior inference.
    Accepts an explicit PathwaySwitches object; no CausalStructure required.
    Used by causal_model.switch_inference.
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
