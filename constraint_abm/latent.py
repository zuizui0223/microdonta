"""Latent trade-off parameter definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LatentParameter:
    """A difficult-to-measure parameter explored across plausible ranges."""

    name: str
    lower: float
    upper: float
    default: float | None = None
    description: str = ""

    def grid(self, steps: int) -> list[float]:
        if steps < 2:
            return [self.default if self.default is not None else (self.lower + self.upper) / 2]
        span = self.upper - self.lower
        return [self.lower + span * i / (steps - 1) for i in range(steps)]

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper
