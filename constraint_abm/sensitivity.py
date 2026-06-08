"""Sensitivity utilities for latent CAPOM parameters."""

from __future__ import annotations

from collections.abc import Callable

from .latent import LatentParameter


def one_at_a_time_grid(
    base_parameters: dict[str, float],
    latent_parameters: list[LatentParameter],
    steps: int = 5,
) -> list[dict[str, float]]:
    """Generate one-at-a-time parameter sets for early robustness checks."""

    rows: list[dict[str, float]] = []
    for latent in latent_parameters:
        for value in latent.grid(steps):
            row = dict(base_parameters)
            row[latent.name] = value
            rows.append(row)
    return rows


def evaluate_sensitivity(
    parameter_sets: list[dict[str, float]],
    simulate_score: Callable[[dict[str, float]], float],
) -> list[tuple[dict[str, float], float]]:
    """Attach a scalar score to each parameter set."""

    return [(params, simulate_score(params)) for params in parameter_sets]
