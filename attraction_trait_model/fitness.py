"""Fitness functions for attraction-trait evolution."""

from __future__ import annotations

from .agents import PlantAgent
from .parameters import ModelParameters


FAILED_REPRODUCTIVE_OUTPUT = 0.001


def reproductive_output(mode: str, params: ModelParameters) -> float:
    """Return reproductive output for a reproduction mode."""

    if mode == "outcrossing":
        return (
            params.seed_set_outcrossing
            * params.germination_outcrossed
            * (1.0 + params.outcrossing_benefit)
        )
    if mode == "selfing":
        return (
            params.seed_set_selfing
            * params.germination_outcrossed
            * (1.0 - params.inbreeding_depression)
            * (1.0 + params.selfing_benefit)
        )
    if mode == "failed":
        return FAILED_REPRODUCTIVE_OUTPUT
    return FAILED_REPRODUCTIVE_OUTPUT


def guide_cost_effect(agent: PlantAgent, params: ModelParameters) -> float:
    """Cost of maintaining a nectar guide on a floral display."""

    return params.guide_cost * agent.nectar_guide * agent.flower_size


def flower_cost_effect(agent: PlantAgent, params: ModelParameters) -> float:
    """Cost of maintaining floral display size."""

    return params.flower_size_cost * agent.flower_size


def fitness(
    agent: PlantAgent,
    params: ModelParameters,
    min_fitness: float = 0.001,
) -> float:
    """Calculate fitness from reproductive output minus trait costs."""

    value = (
        reproductive_output(agent.reproduction_mode, params)
        - guide_cost_effect(agent, params)
        - flower_cost_effect(agent, params)
    )
    return max(min_fitness, value)
