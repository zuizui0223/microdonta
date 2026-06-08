"""Ecological constraints that restrict plausible latent mechanisms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Constraint:
    """A biological rule used to reject implausible parameter sets."""

    name: str
    predicate: Callable[[dict[str, float]], bool]
    description: str = ""

    def satisfied_by(self, parameters: dict[str, float]) -> bool:
        return bool(self.predicate(parameters))


def within(key: str, lower: float, upper: float, description: str = "") -> Constraint:
    """Create a bounded-value constraint for a single parameter.

    Usage::

        within("guide_cost", 0.0, 0.20)
        within("mutation_sd", 0.01, 0.12, "realistic quantitative-genetics range")
    """
    return Constraint(
        name=f"{key}_within_range",
        predicate=lambda params, k=key, lo=lower, hi=upper: lo <= float(params.get(k, lo)) <= hi,
        description=description or f"{key} ∈ [{lower}, {upper}].",
    )