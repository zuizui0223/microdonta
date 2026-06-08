"""Campanula Izu Islands causal structures, latent parameters, and pattern targets.

Campanula punctata var. hondoensis / microdonta-specific instantiation of the
general causal_model framework. Moved here from causal_model/ to keep that
package layer general-purpose.

Usage::

    from causal_structures import (
        campanula_causal_structures,
        campanula_latent_parameters,
        campanula_pattern_targets,
    )
"""

from __future__ import annotations

from causal_model.latent_parameters import LatentParameter
from causal_model.pattern_targets import PatternTarget
from causal_model.structures import CausalEdge, CausalStructure


def campanula_causal_structures() -> list[CausalStructure]:
    """Return M1–M5 causal structures for the Izu Islands Campanula example."""

    return [
        CausalStructure(
            name="M1_direct_pollinator_to_guide",
            edges=(
                CausalEdge(
                    "Bombus_frequency",
                    "nectar_guide",
                    "positive",
                    "Bombus directly increases the benefit of maintaining guides.",
                ),
            ),
            latent_parameters=(
                "direct_pollinator_guide_benefit",
                "guide_maintenance_cost",
            ),
            expected_patterns=(
                "Bombus_frequency: Oshima > Hachijo",
                "nectar_guide: Oshima > Hachijo",
            ),
            description="Direct pollinator-mediated selection on nectar guides.",
        ),
        CausalStructure(
            name="M2_selfing_mediated",
            edges=(
                CausalEdge(
                    "Bombus_frequency",
                    "outcrossing_opportunity",
                    "positive",
                    "Bombus contributes to stable outcrossing opportunity.",
                ),
                CausalEdge(
                    "outcrossing_opportunity",
                    "selfing_rate",
                    "negative",
                    "Reduced outcrossing opportunity increases reproductive assurance selfing.",
                ),
                CausalEdge(
                    "selfing_rate",
                    "nectar_guide",
                    "negative",
                    "Higher selfing lowers the benefit of an outcrossing attraction signal.",
                ),
            ),
            latent_parameters=(
                "outcrossing_benefit",
                "selfing_benefit",
                "cost_of_waiting_for_pollinators",
                "guide_maintenance_cost",
                "inbreeding_depression",
            ),
            expected_patterns=(
                "Bombus_frequency: Oshima > Hachijo",
                "selfing_rate: Oshima < Hachijo",
                "herkogamy: Oshima > Hachijo",
                "Fis: Oshima < Hachijo",
                "nectar_guide: Oshima > Hachijo",
            ),
            description="Nectar-guide loss mediated through increased selfing.",
        ),
        CausalStructure(
            name="M3_direct_plus_mediated",
            edges=(
                CausalEdge(
                    "Bombus_frequency",
                    "nectar_guide",
                    "positive",
                    "Bombus directly increases guide benefit.",
                ),
                CausalEdge(
                    "Bombus_frequency",
                    "outcrossing_opportunity",
                    "positive",
                    "Bombus contributes to outcrossing opportunity.",
                ),
                CausalEdge(
                    "outcrossing_opportunity",
                    "selfing_rate",
                    "negative",
                    "Lower outcrossing opportunity increases selfing.",
                ),
                CausalEdge(
                    "selfing_rate",
                    "nectar_guide",
                    "negative",
                    "Selfing reduces the benefit of maintaining an attraction signal.",
                ),
            ),
            latent_parameters=(
                "direct_pollinator_guide_benefit",
                "outcrossing_benefit",
                "selfing_benefit",
                "cost_of_waiting_for_pollinators",
                "guide_maintenance_cost",
                "inbreeding_depression",
            ),
            expected_patterns=(
                "Bombus_frequency: Oshima > Hachijo",
                "nectar_guide: Oshima > Hachijo",
                "selfing_rate: Oshima < Hachijo",
                "herkogamy: Oshima > Hachijo",
                "Fis: Oshima < Hachijo",
            ),
            description="Direct pollinator effects and selfing-mediated effects act together.",
        ),
        CausalStructure(
            name="M4_common_island_cause",
            edges=(
                CausalEdge(
                    "island_isolation",
                    "Bombus_frequency",
                    "negative",
                    "Island isolation or colonization history can reduce Bombus frequency.",
                ),
                CausalEdge(
                    "island_isolation",
                    "selfing_rate",
                    "positive",
                    "Island conditions can favor reproductive assurance.",
                ),
                CausalEdge(
                    "island_isolation",
                    "nectar_guide",
                    "negative",
                    "Island conditions can reduce guide maintenance by shared causes.",
                ),
                CausalEdge(
                    "effective_population_size",
                    "drift_strength",
                    "negative",
                    "Smaller Ne increases the strength of drift.",
                ),
                CausalEdge(
                    "drift_strength",
                    "nectar_guide",
                    "increases_loss_risk",
                    "Drift can increase the chance of guide loss independent of direct selection.",
                ),
            ),
            latent_parameters=(
                "drift_strength",
                "future_reproductive_benefit",
                "guide_maintenance_cost",
                "small_pollinator_efficiency",
            ),
            expected_patterns=(
                "Bombus_frequency: Oshima > Hachijo",
                "selfing_rate: Oshima < Hachijo",
                "nectar_guide: Oshima > Hachijo",
                "Ne: Oshima > Hachijo",
            ),
            description="Observed covariance arises from island history, Ne, and drift.",
        ),
        CausalStructure(
            name="M5_drift_null",
            edges=(
                CausalEdge(
                    "drift_strength",
                    "nectar_guide",
                    "random_loss",
                    "Guide loss can arise without pollinator or selfing causal paths.",
                ),
                CausalEdge(
                    "random_trait_change",
                    "nectar_guide",
                    "random",
                    "Random trait change contributes to guide variation.",
                ),
            ),
            latent_parameters=(
                "drift_strength",
                "guide_maintenance_cost",
            ),
            expected_patterns=(
                "nectar_guide: Oshima > Hachijo",
            ),
            description="Null model where drift or random change explains guide loss.",
            notes="This model does not require Bombus or selfing to cause guide reduction.",
        ),
    ]


def campanula_latent_parameters() -> list[LatentParameter]:
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


def campanula_pattern_targets() -> list[PatternTarget]:
    """Return initial Campanula pattern targets used for causal filtering."""

    return [
        PatternTarget(
            name="nectar_guide_oshima_gt_hachijo",
            variable="nectar_guide",
            expected_relation="Oshima > Hachijo",
            groups=("Oshima", "Hachijo"),
            weight=2.0,
            description="Nectar guides are expected to be stronger where Bombus service remains higher.",
        ),
        PatternTarget(
            name="selfing_rate_oshima_lt_hachijo",
            variable="selfing_rate",
            expected_relation="Oshima < Hachijo",
            groups=("Oshima", "Hachijo"),
            weight=1.5,
            description="Selfing is expected to increase where outcrossing opportunity is unstable.",
        ),
        PatternTarget(
            name="herkogamy_oshima_gt_hachijo",
            variable="herkogamy",
            expected_relation="Oshima > Hachijo",
            groups=("Oshima", "Hachijo"),
            weight=1.0,
            description="Reduced herkogamy is expected under stronger selfing syndrome.",
        ),
        PatternTarget(
            name="flower_size_oshima_gt_hachijo",
            variable="flower_size",
            expected_relation="Oshima > Hachijo",
            groups=("Oshima", "Hachijo"),
            weight=1.0,
            description="Flower-size reduction helps separate attraction-trait and selfing-syndrome pathways.",
        ),
        PatternTarget(
            name="fis_oshima_lt_hachijo",
            variable="Fis",
            expected_relation="Oshima < Hachijo",
            groups=("Oshima", "Hachijo"),
            weight=1.5,
            description="Fis should increase where effective selfing or inbreeding is stronger.",
        ),
        PatternTarget(
            name="bombus_frequency_oshima_gt_hachijo",
            variable="Bombus_frequency",
            expected_relation="Oshima > Hachijo",
            groups=("Oshima", "Hachijo"),
            weight=2.0,
            description="Bombus frequency anchors the pollinator-environment contrast.",
        ),
    ]
