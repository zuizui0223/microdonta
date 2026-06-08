"""High-level runner that ties causal structures to stochastic ABM simulations.

This module provides :func:`run_causal_structure_simulation` as the primary
entry point and :func:`final_summary` as a convenience extractor.

Example::

    from causal_model.structures import CausalStructure
    from attraction_trait_model.scenario_runner import (
        run_causal_structure_simulation,
        final_summary,
    )

    rows = run_causal_structure_simulation(structure, env, seed=42)
    last = final_summary(rows)
"""

from __future__ import annotations

from typing import Optional

from causal_model.structures import CausalStructure
from causal_model.switches import switches_for_structure

from .environment import Environment
from .parameters import ModelParameters
from .simulation import simulate_population


def run_causal_structure_simulation(
    structure: CausalStructure,
    env: Environment,
    params: Optional[ModelParameters] = None,
    generations: int = 50,
    population_size: int = 200,
    seed: Optional[int] = None,
) -> list[dict]:
    """Run a stochastic ABM for *structure* and return generation summaries.

    Pathway switches are derived automatically from *structure.name* via
    :func:`causal_model.switches.switches_for_structure`.

    Parameters
    ----------
    structure:
        Named causal structure (e.g. ``M1_direct_pollinator_to_guide``).
    env:
        Population environment for the simulation.
    params:
        Biological parameters.  Defaults to ``ModelParameters()`` when *None*.
    generations:
        Number of generations to simulate.
    population_size:
        Number of individuals per generation.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    list[dict]
        One summary dict per generation from :func:`simulate_population`.
    """
    switches = switches_for_structure(structure.name)
    params = params or ModelParameters()
    return simulate_population(env, params, switches, generations, population_size, seed)


def final_summary(simulation_rows: list[dict]) -> dict:
    """Return the last generation's summary from *simulation_rows*.

    Parameters
    ----------
    simulation_rows:
        Output of :func:`run_causal_structure_simulation` or
        :func:`simulate_population`.

    Returns
    -------
    dict
        The last row, or an empty dict when the list is empty.
    """
    return simulation_rows[-1] if simulation_rows else {}
