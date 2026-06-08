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


def within(name: str, key: str, lower: float, upper: float, description: str = "") -> Constraint:
    """Create a simple bounded-value constraint."""

    return Constraint(
        name=name,
        predicate=lambda params: lower <= float(params[key]) <= upper,
        description=description or f"{key} must be between {lower} and {upper}.",
    )
