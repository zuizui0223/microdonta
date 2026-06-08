"""Observable field-pattern definitions for CAPOM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PatternKind = Literal["numeric", "ordinal", "binary", "categorical"]


@dataclass(frozen=True)
class ObservablePattern:
    """A field-measurable pattern that simulations should reproduce."""

    name: str
    kind: PatternKind
    target: float | str | list[str]
    weight: float = 1.0
    tolerance: float | None = None
    description: str = ""

    def distance(self, simulated: float | str | list[str]) -> float:
        if self.kind == "numeric":
            target = float(self.target)
            value = float(simulated)
            scale = self.tolerance if self.tolerance not in (None, 0) else 1.0
            return abs(value - target) / scale
        if self.kind == "ordinal":
            return 0.0 if list(simulated) == list(self.target) else 1.0
        return 0.0 if simulated == self.target else 1.0


def ordinal_pattern(name: str, ordered_levels: list[str], weight: float = 1.0) -> ObservablePattern:
    """Define an ordinal pattern such as Mainland > Oshima > Kozu > Hachijo."""

    return ObservablePattern(name=name, kind="ordinal", target=ordered_levels, weight=weight)
