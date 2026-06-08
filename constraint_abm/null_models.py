"""Null and negative-control scenario helpers."""

from __future__ import annotations

from .scenarios import Scenario


def default_null_scenarios() -> list[Scenario]:
    """Return minimal null models for the Campanula worked example."""

    return [
        Scenario(
            name="N1_drift_only",
            parameter_overrides={"pollinator_environment": 0.5, "selfing_ability": 0.0},
            enabled_processes=("drift",),
            description="Trait change is driven by drift without directional pollinator or selfing effects.",
        ),
        Scenario(
            name="N2_pollinator_loss_only",
            parameter_overrides={"selfing_ability": 0.0, "inbreeding_load": 0.0},
            enabled_processes=("pollinator_loss",),
            description="Pollinator environment changes, but selfing and inbreeding feedbacks are disabled.",
        ),
        Scenario(
            name="N3_selfing_only",
            parameter_overrides={"bombus_guide_dependence": 0.0, "other_pollinator_guide_use": 0.0},
            enabled_processes=("selfing",),
            description="Selfing changes without guide-mediated pollinator selection.",
        ),
        Scenario(
            name="N4_random_trait_loss",
            parameter_overrides={"guide_cost": 0.0},
            enabled_processes=("random_trait_loss",),
            description="Nectar-guide change is treated as random loss without maintenance cost.",
        ),
    ]
