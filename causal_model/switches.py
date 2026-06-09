"""Pathway switches for causal generative models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PathwaySwitches:
    """Mechanistic switch weights used by a biological generator.

    Values are initially 0/1 or weak/strong defaults. They can later be treated
    as continuous latent parameters and filtered by CAPOM pattern matching.
    """

    direct_pollinator_to_guide: float = 0.0
    selfing_mediation: float = 0.0
    island_common_cause: float = 0.0
    drift_null: float = 0.0
    small_pollinator_pathway: float = 0.0


def switches_for_structure(structure_name: str) -> PathwaySwitches:
    """Return default pathway switches for a named causal structure."""

    defaults = {
        "M1_direct_pollinator_to_guide": PathwaySwitches(
            direct_pollinator_to_guide=1.0,
        ),
        "M2_selfing_mediated": PathwaySwitches(
            selfing_mediation=1.0,
        ),
        "M3_direct_plus_mediated": PathwaySwitches(
            direct_pollinator_to_guide=1.0,
            selfing_mediation=1.0,
        ),
        # M4: island isolation acts as a SINGLE upstream common cause.
        # All other switches are OFF so that the pattern contribution is
        # attributable purely to the isolation pathway (S3), not to
        # Bombus-guide (S1), selfing syndrome (S2), or drift (S4).
        # The previous definition included S1=0.25, S4=0.25, which conflated
        # multiple mechanisms and prevented clean M4 identification.
        "M4_common_island_cause": PathwaySwitches(
            island_common_cause=1.0,
        ),
        "M5_drift_null": PathwaySwitches(
            drift_null=1.0,
        ),
    }
    try:
        return defaults[structure_name]
    except KeyError as exc:
        raise ValueError(f"Unknown causal structure: {structure_name}") from exc


def switches_to_dict(switches: PathwaySwitches) -> dict[str, float]:
    """Return switch values as a plain dictionary for config and CSV output."""

    return {
        "direct_pollinator_to_guide": switches.direct_pollinator_to_guide,
        "selfing_mediation": switches.selfing_mediation,
        "island_common_cause": switches.island_common_cause,
        "drift_null": switches.drift_null,
        "small_pollinator_pathway": switches.small_pollinator_pathway,
    }
