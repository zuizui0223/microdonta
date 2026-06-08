"""Scenario definitions for constraint-aware ABM experiments."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Scenario:
    """A causal hypothesis encoded as parameter overrides and notes."""

    name: str
    parameter_overrides: dict[str, float] = field(default_factory=dict)
    enabled_processes: tuple[str, ...] = ()
    description: str = ""

    def apply(self, base_parameters: dict[str, float]) -> dict[str, float]:
        return {**base_parameters, **self.parameter_overrides}
