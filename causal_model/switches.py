"""Pathway switches for causal generative models."""

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
    small_pollinator_pathway: float = 0.0
    # NOTE: drift_null removed — genetic drift is always active in any finite
    # population and is not a binary switch.  Drift strength is controlled by
    # the continuous parameter drift_strength in θ and by Ne derived from
    # island_distance in the Environment.  The null model (all selection
    # switches OFF) is now M0_null_selection.


def switches_for_structure(structure_name: str) -> PathwaySwitches:
    """Return default pathway switches for a named causal structure.

    Drift is NOT a switch.  All structures include drift as a background
    process parameterised by θ (drift_strength) and Ne (from island_distance).
    Only selection-based mechanisms are toggleable switches.
    """

    defaults = {
        # M0: true null model — no selection mechanism active.
        # Only environmental gradient + continuous drift (Ne from island_distance) operate.
        # This is the correct ecological null: drift is always present, not "switched on".
        "M0_null_selection": PathwaySwitches(),
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
        # Bombus-guide (S1) or selfing syndrome (S2).
        "M4_common_island_cause": PathwaySwitches(
            island_common_cause=1.0,
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
        "small_pollinator_pathway": switches.small_pollinator_pathway,
    }
