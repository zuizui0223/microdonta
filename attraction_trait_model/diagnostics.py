"""Diagnostic summaries for attraction-trait simulations."""

from __future__ import annotations

from .reproduction import clamp


def selfing_syndrome_score(
    mean_nectar_guide: float,
    mean_flower_size: float,
    mean_herkogamy: float,
    mean_selfing_ability: float,
    selfing_rate: float,
    outcrossing_rate: float,
) -> float:
    """Diagnostic score for selfing-syndrome-like patterns.

    This is not a causal fitness term. Higher values indicate that reduced
    attraction traits and increased selfing are co-occurring in the output.
    """

    score = (
        (1.0 - mean_nectar_guide)
        + (1.0 - mean_flower_size)
        + (1.0 - mean_herkogamy)
        + mean_selfing_ability
        + selfing_rate
        + (1.0 - outcrossing_rate)
    ) / 6.0
    return clamp(score)


def guide_status(mean_nectar_guide: float, threshold: float = 0.5) -> str:
    """Classify nectar-guide status using a provisional diagnostic cutoff.

    The default 0.5 threshold is a visualization and diagnostic convention, not
    a fixed biological threshold. It should be sensitivity-tested in later
    phase-diagram work.
    """

    if mean_nectar_guide >= threshold:
        return "maintained"
    if mean_nectar_guide >= threshold / 2.0:
        return "reduced"
    return "lost"
