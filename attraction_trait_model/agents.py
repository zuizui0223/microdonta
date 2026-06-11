"""Individual plant agents for the attraction-trait evolution model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PlantAgent:
    """Individual plant with evolving attraction and mating-system traits.

    Trait values are expected to be scaled to the interval 0-1:
    nectar_guide, flower_size, herkogamy, selfing_ability, and
    neutral_diversity. Later simulation modules should clamp inherited values
    to that range after mutation and drift.
    """

    nectar_guide: float
    flower_size: float
    # herkogamy: autonomous-selfing avoidance, 0-1. NOTE: Campanula punctata /
    # microdonta is protandrous with secondary pollen presentation, so this is
    # NOT a static anther-stigma distance. It denotes female-phase delayed-selfing
    # geometry (how far the recurving stigma stays from self-pollen on the style);
    # high = stigma avoids self-pollen (no delayed selfing), low = contacts it.
    herkogamy: float
    selfing_ability: float
    neutral_diversity: float
    x: float = 0.0
    y: float = 0.0
    reproduction_mode: str = "none"
    fitness: float = 1.0
