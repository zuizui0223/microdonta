"""Observable pattern targets for causal model comparison.

General-purpose. System-specific pattern targets belong in the corresponding
examples/ directory.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PatternTarget:
    """Observable pattern that simulated causal structures should reproduce."""

    name: str
    variable: str
    expected_relation: str
    groups: tuple[str, ...] = field(default_factory=tuple)
    weight: float = 1.0
    description: str = ""
