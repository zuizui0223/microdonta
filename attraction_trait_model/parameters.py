"""Latent and provisional parameters for the attraction-trait model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelParameters:
    """Provisional default parameters for model development.

    These values are not biological truths. They are placeholder defaults used
    to exercise the model equations until CAPOM filtering, sensitivity
    analysis, and field data constrain plausible parameter ranges.

    Pollinator parameters
    ---------------------
    primary_pollinator_efficiency
        Per-visit pollen-transfer efficiency of the trait-responsive guild.
        High (default 0.8) — these pollinators are large-bodied, carry more
        pollen per visit, and deposit it more reliably on stigmas.

    primary_pollinator_guide_response
        Strength of the nectar-guide signal's effect on primary-pollinator
        visitation rate.  High (default 0.7) — primary pollinators actively
        use guide patterns as long-range orientation cues.

    background_pollinator_efficiency
        Per-visit pollen-transfer efficiency of the background guild.
        Lower (default 0.3) — smaller body, less pollen carried per visit.

    background_pollinator_guide_response
        Strength of the nectar-guide signal's effect on background-pollinator
        visitation rate.  Near-zero (default 0.1) — these pollinators navigate
        mainly by proximity and flower colour/scent, not guide patterns.
    """

    base_outcross_rate: float = 0.05

    # --- Trait-responsive, high-efficiency guild (Bombus in Izu system) ---
    primary_pollinator_efficiency: float = 0.8
    primary_pollinator_guide_response: float = 0.7

    # --- Background, lower-efficiency guild (halictids in Izu system) ---
    background_pollinator_efficiency: float = 0.3
    background_pollinator_guide_response: float = 0.1

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
