"""Generic deterministic proxy simulation for causal structure evaluation.

Design principle
----------------
Each biological switch controls whether an environmental difference
(e.g. Bombus presence on Oshima but not Hachijo) propagates into a
trait difference. With all switches OFF, the two populations start
from the same neutral baseline and diverge only trivially (Bombus
frequency and a small drift-driven Fis shift). Meaningful trait
divergence requires at least one relevant switch to be ON.

This ensures that:
1. Switch posterior inference has actual discriminating power --
   P(switch ON | accepted) departs from the 0.5 prior only when
   the switch genuinely produces the observed patterns.
2. Acceptance rate (ABC) is low for random switch combinations and
   high for biologically plausible combinations, giving sharp BFs.

Tolerance
---------
relations_from_outputs uses tolerance=RELATION_TOLERANCE (default 0.05).
Islands must differ by at least 5 percentage points on a trait for the
relation to count as directional. This prevents noise-level differences
from spuriously matching observed patterns.

System-specific wrappers belong in examples/.
See: examples/campanula_izu/proxy_simulation.py
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from attraction_trait_model import (
    Environment,
    ModelParameters,
)

from .structures import CausalStructure
from .switches import PathwaySwitches, switches_for_structure

# Minimum absolute difference required to call a directional relation.
# 0.05 = 5 percentage points. Below this threshold the two populations
# are treated as equal (~=), which counts as a pattern mismatch.
RELATION_TOLERANCE: float = 0.05


@dataclass(frozen=True)
class PopulationProxyOutput:
    """Simulation-derived pattern values for one population."""

    population: str
    nectar_guide: float
    selfing_rate: float
    herkogamy: float
    flower_size: float
    Fis: float
    Bombus_frequency: float
    outcrossing_opportunity: float


def simulate_population_proxy(
    structure: CausalStructure,
    env: Environment,
    params: ModelParameters,
    switches: PathwaySwitches | None = None,
) -> PopulationProxyOutput:
    """Generate provisional trait values for one population.

    Switch-gated design
    -------------------
    Each switch controls whether a specific environmental input produces
    a phenotypic response:

    S1  direct_pollinator_to_guide
        Bombus presence (Oshima) vs absence (Hachijo) drives guide
        retention/loss. OFF: guide does not track Bombus.

    S2  selfing_mediation
        Pollination gap + positive selfing net benefit drives convergent
        selfing-syndrome evolution (selfing, herkogamy, flower size, guide).
        OFF: traits do not respond to pollinator scarcity.

    S3  island_common_cause
        Island isolation acts as a single upstream cause, simultaneously
        shifting ALL traits. OFF: isolation has no direct trait effect.

    S4  drift_null
        Genetic drift in small-Ne populations causes guide loss without
        producing a full selfing syndrome. OFF: guide is drift-neutral.

    S5  small_pollinator_pathway
        Halictid efficiency suppresses selfing pressure from pollination gap.
        OFF: halictids do not compensate for Bombus absence.

    Baseline
    --------
    With all switches OFF both populations start at the same trait values.
    Only Bombus_frequency (environmental, always 0.35 vs 0.00) and a small
    drift-driven Fis shift differ between islands in the null case. This
    ensures switches have real discriminating power.
    """

    switches = switches or switches_for_structure(structure.name)

    # ------------------------------------------------------------------
    # Environmental inputs
    # ------------------------------------------------------------------
    bombus     = env.bombus_frequency             # Oshima: 0.35  Hachijo: 0.00
    poll_gap   = clamp01(1.0 - env.pollinator_environment)  # O: 0.38  H: 0.66
    isolation  = clamp01(env.island_distance)     # O: 0.35  H: 0.90
    ne_proxy   = clamp01(env.effective_population_size)     # O: 0.55  H: 0.22
    low_ne     = clamp01(1.0 - ne_proxy)          # O: 0.45  H: 0.78
    small_poll = clamp01(env.small_pollinator_frequency)    # O: 0.55  H: 0.72

    # ------------------------------------------------------------------
    # Latent parameters
    # ------------------------------------------------------------------
    gc  = params.guide_cost
    ob  = params.outcrossing_benefit
    sb  = params.selfing_benefit
    ibd = params.inbreeding_depression
    spe = params.small_pollinator_efficiency
    ds  = params.base_drift_strength
    bgb = params.bombus_guide_use  # = direct_pollinator_guide_benefit

    # Derived
    drift       = clamp01(low_ne * (0.50 + 2.50 * ds))
    selfing_net = sb - ibd  # negative = selfing costly; positive = selfing beneficial

    # ------------------------------------------------------------------
    # Neutral baseline: identical for both populations
    # A universal guide maintenance cost applies uniformly.
    # ------------------------------------------------------------------
    guide     = 0.56 - 0.38 * gc
    herkogamy = 0.68
    flower    = 0.73 - 0.15 * gc
    selfing   = 0.18

    # ------------------------------------------------------------------
    # S1: guide_attracts_bombus  (direct_pollinator_to_guide)
    # ------------------------------------------------------------------
    # Bombus present (Oshima) → guide maintained/increased by direct benefit.
    # Bombus absent  (Hachijo) → guide not reinforced; opportunity cost applies.
    # OFF: guide stays at neutral baseline regardless of Bombus.
    if switches.direct_pollinator_to_guide > 0:
        w = switches.direct_pollinator_to_guide
        # Positive term when Bombus present; negative penalty when absent.
        guide += w * (1.30 * bombus * bgb * ob - 0.35 * (1.0 - bombus) * ob)

    # ------------------------------------------------------------------
    # S2: selfing_mediation
    # ------------------------------------------------------------------
    # Pollination gap triggers selfing-syndrome co-evolution when selfing
    # is net beneficial (sb > ibd).  Magnitude scales with both the gap
    # and the net selfing advantage.
    # OFF: traits do not respond to pollinator scarcity at all.
    #
    # NOTE: S2 does NOT strongly drive nectar-guide divergence.
    # Guide loss specifically requires S1 (Bombus-guide link), S3
    # (isolation as common cause), or S4 (drift).  Without one of those,
    # guide divergence stays below RELATION_TOLERANCE (0.05) even when
    # the full selfing syndrome is active.  This makes S1 identifiable.
    if switches.selfing_mediation > 0:
        w = switches.selfing_mediation
        # sm: joint pressure from pollination gap AND net selfing benefit
        sm = poll_gap * clamp01(0.50 + selfing_net)
        selfing   += w * 0.70 * sm
        herkogamy -= w * 0.52 * sm
        flower    -= w * 0.48 * sm
        guide     -= w * 0.04 * sm  # negligible: guide needs S1 or S4, not S2
        # Max guide_diff from S2 alone = 0.04 * (0.66-0.38) * 1.0 = 0.011 << 0.05
        # Combined with S3 max: 0.011 + 0.035 = 0.046 < 0.05
        # → S2 alone or S2+S3 combined still cannot exceed RELATION_TOLERANCE.

    # ------------------------------------------------------------------
    # S3: island_isolation_common_cause
    # ------------------------------------------------------------------
    # Island isolation drives the selfing syndrome (selfing, herkogamy,
    # flower size) as a single upstream environmental cause, via reduced
    # pollinator service and reproductive-assurance pressure.
    # OFF: isolation has no direct trait effect.
    #
    # DESIGN NOTE -- guide is NOT driven by S3 at all:
    # Nectar-guide retention/loss is determined by pollinator IDENTITY
    # (Bombus specifically), not pollinator quantity.  Guides function as
    # long-range Bombus attractants; small halictids use them less.
    # S3 (isolation) reduces pollinator service overall but does NOT
    # directly affect guide expression -- that requires S1 (Bombus absence)
    # or S4 (genetic drift).  This makes S1 identifiable: only the Bombus-
    # guide pathway produces a guide divergence above RELATION_TOLERANCE.
    #
    # Previously coefficient was 0.07, but that allowed mainland-Hachijo
    # guide difference = 0.07 * 0.85 = 0.0595 > RELATION_TOLERANCE (0.05),
    # violating the design intent when a full gradient (incl. mainland) is
    # used as POM.  Set to 0.00 to strictly enforce the design.
    if switches.island_common_cause > 0:
        w = switches.island_common_cause
        # Isolation drives selfing syndrome regardless of selfing_net.
        # The selfing increase scales with (1 - ob) because high outcrossing
        # benefit partially resists reproductive-assurance selfing pressure.
        selfing_drive = isolation * clamp01(0.55 + (1.0 - ob) * 0.45)
        selfing   += w * 0.55 * selfing_drive
        herkogamy -= w * 0.40 * isolation
        flower    -= w * 0.28 * isolation
        # guide: S3 has zero direct effect on nectar guide (needs S1 or S4)

    # ------------------------------------------------------------------
    # S4: drift_drives_guide_loss
    # ------------------------------------------------------------------
    # Genetic drift in small populations (high low_ne) causes stochastic
    # guide loss.  Does NOT produce a full selfing syndrome (null model).
    # OFF: guide expression is drift-neutral.
    if switches.drift_null > 0:
        w = switches.drift_null
        guide -= w * 0.55 * drift

    # ------------------------------------------------------------------
    # S5: small_pollinator_substitution
    # ------------------------------------------------------------------
    # Halictid efficiency and availability can partially compensate for
    # Bombus absence, suppressing reproductive-assurance selfing pressure.
    # Only reduces selfing that was generated by S2 pollination-gap logic.
    # OFF: halictids do not substitute for Bombus.
    if switches.small_pollinator_pathway > 0:
        w = switches.small_pollinator_pathway
        sub = spe * small_poll
        # Suppresses poll_gap driven selfing (proportional to gap)
        selfing -= w * 0.40 * sub * poll_gap

    # ------------------------------------------------------------------
    # Clamp all traits to [0, 1]
    # ------------------------------------------------------------------
    guide     = clamp01(guide)
    herkogamy = clamp01(herkogamy)
    flower    = clamp01(flower)
    selfing   = clamp01(selfing)

    # Fis: driven by realised selfing rate + drift contribution.
    # Even with all switches OFF, high drift (Hachijo) produces a slightly
    # higher Fis than low drift (Oshima), but the difference (~0.035)
    # is below RELATION_TOLERANCE (0.05) so Fis does not spuriously match.
    fis = clamp01(0.03 + 0.68 * selfing + 0.14 * drift)

    return PopulationProxyOutput(
        population=env.name,
        nectar_guide=guide,
        selfing_rate=selfing,
        herkogamy=herkogamy,
        flower_size=flower,
        Fis=fis,
        Bombus_frequency=bombus,
        outcrossing_opportunity=clamp01(1.0 - selfing),
    )


def relations_from_outputs(
    outputs: list[PopulationProxyOutput],
    left: str,
    right: str,
    tolerance: float = RELATION_TOLERANCE,
) -> dict[str, str]:
    """Convert two population outputs into ordinal relation strings.

    Parameters
    ----------
    tolerance:
        Minimum absolute difference to call a directional relation.
        Below this threshold the relation is '~=' (equal), which
        counts as a pattern mismatch.  Default: RELATION_TOLERANCE (0.05).
    """

    by_population = {output.population: output for output in outputs}
    left_output  = by_population[left]
    right_output = by_population[right]
    variables = (
        "nectar_guide",
        "selfing_rate",
        "herkogamy",
        "flower_size",
        "Fis",
        "Bombus_frequency",
    )
    return {
        variable: relation_from_values(
            left,
            getattr(left_output, variable),
            right,
            getattr(right_output, variable),
            tolerance=tolerance,
        )
        for variable in variables
    }


def relation_from_values(
    left_name: str,
    left_value: float,
    right_name: str,
    right_value: float,
    tolerance: float = RELATION_TOLERANCE,
) -> str:
    """Return a compact ordinal relation between two numeric values."""

    if abs(left_value - right_value) <= tolerance:
        return f"{left_name} ~= {right_name}"
    if left_value > right_value:
        return f"{left_name} > {right_name}"
    return f"{left_name} < {right_name}"


def clamp01(value: float) -> float:
    """Clamp a value to the closed unit interval."""

    return max(0.0, min(1.0, float(value)))
