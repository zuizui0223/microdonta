"""Observable pattern targets for causal model comparison."""

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


def default_campanula_pattern_targets() -> list[PatternTarget]:
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
            description="Flower-size reduction can help separate attraction-trait and selfing-syndrome pathways.",
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
