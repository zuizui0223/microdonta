"""Latent and provisional parameters for the attraction-trait model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelParameters:
    """Provisional default parameters for model development.

    These values are not biological truths. They are placeholder defaults used
    to exercise the model equations until CAPOM filtering, sensitivity
    analysis, and field data constrain plausible parameter ranges.
    """

    base_outcross_rate: float = 0.05
    bombus_efficiency: float = 0.8
    small_pollinator_efficiency: float = 0.3
    bombus_guide_use: float = 0.7
    small_pollinator_guide_use: float = 0.1

    seed_set_outcrossing: float = 0.8
    seed_set_selfing: float = 0.5
    germination_outcrossed: float = 0.8

    inbreeding_depression: float = 0.2
    guide_cost: float = 0.05
    flower_size_cost: float = 0.03
    selfing_benefit: float = 0.1
    outcrossing_benefit: float = 0.2

    mutation_sd_guide: float = 0.03
    mutation_sd_flower_size: float = 0.03
    mutation_sd_herkogamy: float = 0.03
    mutation_sd_selfing_ability: float = 0.03

    trait_correlation_strength: float = 0.02
    base_drift_strength: float = 0.05
