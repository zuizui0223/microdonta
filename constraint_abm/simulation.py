"""Small simulation runner interfaces used by CAPOM examples."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .scenarios import Scenario


SimulationFunction = Callable[[dict[str, float], int], dict[str, Any]]


@dataclass(frozen=True)
class SimulationRun:
    scenario: str
    seed: int
    outputs: dict[str, Any]


def run_scenario(
    scenario: Scenario,
    base_parameters: dict[str, float],
    simulate: SimulationFunction,
    seeds: list[int],
) -> list[SimulationRun]:
    """Run one scenario across random seeds."""

    parameters = scenario.apply(base_parameters)
    return [
        SimulationRun(scenario=scenario.name, seed=seed, outputs=simulate(parameters, seed))
        for seed in seeds
    ]
