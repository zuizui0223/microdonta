"""Causal structure schema for latent causal generative models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CausalEdge:
    """Directed causal relation between two named variables."""

    source: str
    target: str
    relation: str = "positive"
    description: str = ""


@dataclass(frozen=True)
class CausalStructure:
    """Candidate causal hypothesis to be tested by generative pattern matching."""

    name: str
    edges: tuple[CausalEdge, ...] = field(default_factory=tuple)
    latent_parameters: tuple[str, ...] = field(default_factory=tuple)
    expected_patterns: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    notes: str = ""


def default_campanula_causal_structures() -> list[CausalStructure]:
    """Return the first Campanula causal hypotheses from Issue #3."""

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
