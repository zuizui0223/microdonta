"""Observable patterns and latent parameter definitions for the Campanula Izu case study.

Observed values are derived from:
  - Inoue & Amano 1986 (Plant Species Biology)
  - Inoue 1989 (bumblebee-absence hypothesis)
  - Nagano et al. 2014 (Ecology and Evolution)
and supplemented by the PRESETS in shimahotarubukuro_tensnap_abm.py.

These are intentionally approximate: the point of CAPOM is not to fit
exact values but to constrain which latent parameter ranges can
simultaneously reproduce the qualitative gradient across populations.
"""

from __future__ import annotations

from constraint_abm.constraints import Constraint, within
from constraint_abm.latent import LatentParameter
from constraint_abm.patterns import ObservablePattern, ordinal_pattern


# ---------------------------------------------------------------------------
# Fixed (observable / well-constrained) parameters per population
# ---------------------------------------------------------------------------

POPULATION_FIXED_PARAMS: dict[str, dict[str, float]] = {
    "Mainland": {
        "nectar_guide": 0.62,
        "flower_size": 0.82,
        "herkogamy": 0.78,
        "pollen_ovule_ratio": 0.78,
        "pollinator_environment": 0.78,
        "bombus_frequency": 1.0,
        "bombus_pollination_efficiency": 0.86,
        "other_pollinator_efficiency": 0.34,
        "selfing_ability": 0.22,
        "inbreeding_load": 0.32,
        "seed_set_selfing": 0.46,
        "seed_set_outcrossing": 0.92,
        "germination_selfed": 0.54,
        "germination_outcrossed": 0.86,
        "migration_rate": 0.10,
        "admixture_index": 0.00,
        # shared mechanistic constants (overridden by latent inference)
        "guide_cost": 0.06,
        "base_outcross": 0.10,
        "pollinator_environment_outcross_effect": 0.42,
        "bombus_guide_dependence": 0.75,
        "other_pollinator_guide_use": 0.12,
        "mutation_sd": 0.055,
        "genetic_drift_strength": 0.035,
    },
    "Oshima": {
        "nectar_guide": 0.55,
        "flower_size": 0.72,
        "herkogamy": 0.62,
        "pollen_ovule_ratio": 0.64,
        "pollinator_environment": 0.58,
        "bombus_frequency": 1.0,
        "bombus_pollination_efficiency": 0.78,
        "other_pollinator_efficiency": 0.34,
        "selfing_ability": 0.36,
        "inbreeding_load": 0.25,
        "seed_set_selfing": 0.55,
        "seed_set_outcrossing": 0.84,
        "germination_selfed": 0.57,
        "germination_outcrossed": 0.82,
        "migration_rate": 0.05,
        "admixture_index": 0.20,
        "guide_cost": 0.06,
        "base_outcross": 0.10,
        "pollinator_environment_outcross_effect": 0.42,
        "bombus_guide_dependence": 0.75,
        "other_pollinator_guide_use": 0.12,
        "mutation_sd": 0.055,
        "genetic_drift_strength": 0.035,
    },
    "Kozu": {
        "nectar_guide": 0.42,
        "flower_size": 0.58,
        "herkogamy": 0.44,
        "pollen_ovule_ratio": 0.48,
        "pollinator_environment": 0.42,
        "bombus_frequency": 0.0,
        "bombus_pollination_efficiency": 0.86,
        "other_pollinator_efficiency": 0.30,
        "selfing_ability": 0.52,
        "inbreeding_load": 0.18,
        "seed_set_selfing": 0.64,
        "seed_set_outcrossing": 0.76,
        "germination_selfed": 0.60,
        "germination_outcrossed": 0.78,
        "migration_rate": 0.025,
        "admixture_index": 0.35,
        "guide_cost": 0.06,
        "base_outcross": 0.10,
        "pollinator_environment_outcross_effect": 0.42,
        "bombus_guide_dependence": 0.0,
        "other_pollinator_guide_use": 0.18,
        "mutation_sd": 0.055,
        "genetic_drift_strength": 0.035,
    },
    "Hachijo": {
        "nectar_guide": 0.28,
        "flower_size": 0.46,
        "herkogamy": 0.30,
        "pollen_ovule_ratio": 0.34,
        "pollinator_environment": 0.36,
        "bombus_frequency": 0.0,
        "bombus_pollination_efficiency": 0.86,
        "other_pollinator_efficiency": 0.30,
        "selfing_ability": 0.68,
        "inbreeding_load": 0.12,
        "seed_set_selfing": 0.72,
        "seed_set_outcrossing": 0.68,
        "germination_selfed": 0.62,
        "germination_outcrossed": 0.74,
        "migration_rate": 0.01,
        "admixture_index": 0.45,
        "guide_cost": 0.06,
        "base_outcross": 0.10,
        "pollinator_environment_outcross_effect": 0.42,
        "bombus_guide_dependence": 0.0,
        "other_pollinator_guide_use": 0.18,
        "mutation_sd": 0.055,
        "genetic_drift_strength": 0.035,
    },
}


# ---------------------------------------------------------------------------
# Observable patterns per population
# Weights reflect relative reliability of the evidence source:
#   2.0 = direct count/measurement  |  1.5 = experimental  |  1.0 = inferred
# ---------------------------------------------------------------------------

def _patterns(
    mean_ng: float,
    selfing: float,
    outcrossing: float,
    fis: float,
) -> list[ObservablePattern]:
    return [
        ObservablePattern(
            name="mean_nectar_guide",
            kind="numeric",
            target=mean_ng,
            weight=2.0,
            tolerance=0.12,
            description="mean nectar-guide area fraction (image analysis target)",
        ),
        ObservablePattern(
            name="selfing_rate",
            kind="numeric",
            target=selfing,
            weight=1.5,
            tolerance=0.10,
            description="proportion of plants reproducing by selfing (bagging assay)",
        ),
        ObservablePattern(
            name="outcrossing_rate",
            kind="numeric",
            target=outcrossing,
            weight=1.5,
            tolerance=0.10,
            description="proportion of plants outcrossing (pollinator observation + crossing)",
        ),
        ObservablePattern(
            name="Fis",
            kind="numeric",
            target=fis,
            weight=1.0,
            tolerance=0.08,
            description="inbreeding coefficient (SNP-derived)",
        ),
    ]


POPULATION_OBSERVED: dict[str, list[ObservablePattern]] = {
    "Mainland": _patterns(mean_ng=0.62, selfing=0.22, outcrossing=0.65, fis=0.08),
    "Oshima":   _patterns(mean_ng=0.55, selfing=0.35, outcrossing=0.50, fis=0.14),
    "Kozu":     _patterns(mean_ng=0.42, selfing=0.52, outcrossing=0.32, fis=0.28),
    "Hachijo":  _patterns(mean_ng=0.28, selfing=0.68, outcrossing=0.18, fis=0.42),
}

# Ordinal gradient pattern for cross-population inference
# "the nectar guide declines monotonically from Mainland to Hachijo"
GRADIENT_PATTERN = ordinal_pattern(
    name="nectar_guide_gradient",
    ordered=["Mainland", "Oshima", "Kozu", "Hachijo"],
    description="nectar guide declines along the island isolation gradient",
)


# ---------------------------------------------------------------------------
# Latent parameters — the difficult-to-measure trade-offs being estimated
# ---------------------------------------------------------------------------

LATENT_PARAMS: list[LatentParameter] = [
    LatentParameter(
        name="guide_cost",
        lower=0.01,
        upper=0.16,
        default=0.06,
        description=(
            "Metabolic cost of nectar-guide maintenance per unit guide strength. "
            "Deducted from fitness as guide_cost * flower_size * nectar_guide."
        ),
    ),
    LatentParameter(
        name="bombus_guide_dependence",
        lower=0.30,
        upper=0.95,
        default=0.75,
        description=(
            "Degree to which Bombus pollination efficiency is mediated by the "
            "nectar guide (guide-dependent vs. guide-independent search)."
        ),
    ),
    LatentParameter(
        name="other_pollinator_guide_use",
        lower=0.04,
        upper=0.35,
        default=0.15,
        description=(
            "Small-bee / non-Bombus guide utilisation. Expected lower than "
            "bombus_guide_dependence; constrained biologically."
        ),
    ),
    LatentParameter(
        name="genetic_drift_strength",
        lower=0.010,
        upper=0.080,
        default=0.035,
        description=(
            "Standard deviation of the per-generation Gaussian drift added to "
            "neutral diversity. Higher on smaller, more isolated islands."
        ),
    ),
    LatentParameter(
        name="mutation_sd",
        lower=0.020,
        upper=0.090,
        default=0.055,
        description=(
            "Standard deviation of the Gaussian mutation applied to nectar_guide "
            "each generation."
        ),
    ),
    LatentParameter(
        name="base_outcross",
        lower=0.03,
        upper=0.20,
        default=0.10,
        description=(
            "Baseline outcrossing probability in the absence of any pollinators. "
            "Represents wind, gravity, and incidental contact."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Biological constraints — hard filters that reject implausible candidates
# ---------------------------------------------------------------------------

BIOLOGICAL_CONSTRAINTS: list[Constraint] = [
    # Bombus is a more effective guide-user than small bees
    Constraint(
        name="bombus_guide_dominance",
        predicate=lambda p: p.get("bombus_guide_dependence", 1.0) > p.get("other_pollinator_guide_use", 0.0),
        description="Bombus must use guides more than other pollinators",
    ),
    # Guide cost must stay below a threshold where outcrossing can still be favoured
    within("guide_cost", 0.0, 0.20),
    # Drift strength bounded to realistic per-generation values
    within("genetic_drift_strength", 0.005, 0.10),
    # Mutation rate bounded to realistic quantitative-genetics range
    within("mutation_sd", 0.01, 0.12),
    # Baseline outcrossing must be positive
    within("base_outcross", 0.01, 0.30),
]
