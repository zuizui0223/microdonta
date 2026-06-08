"""Latent parameter schema for causal generative models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LatentParameter:
    """Unobserved or hard-to-measure quantity constrained by pattern matching."""

    name: str
    meaning: str
    lower: float | None = None
    upper: float | None = None
    unit: str = ""
    notes: str = ""


def default_campanula_latent_parameters() -> list[LatentParameter]:
    """Return provisional latent quantities for the Campanula worked example."""

    return [
        LatentParameter(
            name="direct_pollinator_guide_benefit",
            meaning="Benefit of nectar guides through direct Bombus-mediated attraction.",
            lower=0.0,
            upper=1.0,
        ),
        LatentParameter(
            name="outcrossing_benefit",
            meaning="Fitness benefit of successful outcrossing relative to selfing.",
            lower=0.0,
            upper=1.0,
        ),
        LatentParameter(
            name="selfing_benefit",
            meaning="Reproductive-assurance benefit when pollinator service is unreliable.",
            lower=0.0,
            upper=1.0,
        ),
        LatentParameter(
            name="guide_maintenance_cost",
            meaning="Cost of maintaining nectar-guide pigmentation or patterning.",
            lower=0.0,
            upper=0.3,
        ),
        LatentParameter(
            name="inbreeding_depression",
            meaning="Fitness reduction caused by selfing and inbreeding.",
            lower=0.0,
            upper=1.0,
        ),
        LatentParameter(
            name="small_pollinator_efficiency",
            meaning="Relative outcrossing efficiency of small pollinators.",
            lower=0.0,
            upper=1.0,
        ),
        LatentParameter(
            name="drift_strength",
            meaning="Magnitude of random trait change due to finite population size.",
            lower=0.0,
            upper=0.25,
        ),
        LatentParameter(
            name="future_reproductive_benefit",
            meaning="Future benefit of retaining outcrossing ability or attraction traits.",
            lower=0.0,
            upper=1.0,
        ),
        LatentParameter(
            name="cost_of_waiting_for_pollinators",
            meaning="Opportunity cost of delayed reproduction under unreliable pollination.",
            lower=0.0,
            upper=1.0,
        ),
    ]
