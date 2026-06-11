"""Ecology-principled parameter constraints and trade-off sampling.

Design principle
----------------
Parameter prior ranges are derived from published empirical literature wherever
measurable. Only parameters with no direct measurement (e.g. guide_cost,
cost_of_waiting_for_pollinators) retain broad exploratory ranges. This avoids
the circularity of hand-tuned priors that implicitly favour particular causal
hypotheses.

Two presets are provided:

    literature_grounded  (default, recommended)
        Prior ranges derived from empirical literature. Each bound is
        annotated with its source in the LiteratureSource records.

    broad_prior
        Maximally broad ranges for sensitivity analysis. Use to verify
        that conclusions are not artefacts of the literature-grounded
        prior bounds.

Key literature
--------------
Husband & Schemske 1996  Evolution 50:54-70
    Meta-analysis of inbreeding depression across 62 plant species.
    Outcrossing species: mean delta ~ 0.50 (range 0.0-0.9).

Lloyd 1979  NZ J Bot 17:535-550
    Reproductive assurance theory: up to 3/2 fitness advantage of selfing
    before inbreeding depression costs.

Larsson 2005  Oikos 109:400-408; Raine & Chittka 2007
    Halictid (small) bee pollination efficiency relative to Bombus:
    typically 20-55% of Bombus pollen transfer per visit.

Inoue & Amano 1986  Plant Species Biol 1(1):89-97
    Field observations: Honshu Bombus diversus, Oshima Bombus ardens plus
    halictid bees, and halictid-dominated Niijima/Kozushima/Hachijo; island
    flowers smaller than mainland; breeding-system shifts across the Izu system.

Inoue 1988 Plant Species Biol 3(2):125-128; Inoue 1990 Plant Species Biol
5(1):57-64; Inoue 1990 Plant Species Biol 5(2):197-203
    Breeding-system, mating-system, and dichogamy/sex-allocation summaries.
    Static herkogamy and Fis are not treated as direct Inoue-series y_obs.

Ushimaru et al. 2003 / Takahashi et al.
    Campanula microdonta mating system variation along the Izu isolation gradient
    (older literature may refer to the broader C. punctata complex).
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LiteratureSource:
    """One empirical source justifying a parameter range.

    Attributes
    ----------
    citation:
        Author-year and journal reference.
    parameter:
        Name of the latent parameter this constrains.
    empirical_range:
        The value or range reported in the source (as a string for display).
    modelled_range:
        The (lo, hi) tuple used in the preset, derived from the source.
    notes:
        How the empirical range was translated to the modelled range.
    """

    citation: str
    parameter: str
    empirical_range: str
    modelled_range: tuple[float, float]
    notes: str


@dataclass(frozen=True)
class TradeoffPreset:
    """A named set of prior ranges over latent benefit/cost parameters.

    Attributes
    ----------
    name:
        Short identifier.
    description:
        Biological motivation for this range configuration.
    ranges:
        Mapping from parameter name to (lower, upper) uniform prior bounds.
    constraints:
        Names of extra constraints applied after sampling (in addition to
        universal constraints C1-C3).
    literature_sources:
        Empirical citations supporting each range.  Empty for broad_prior.
    """

    name: str
    description: str
    ranges: dict[str, tuple[float, float]]
    constraints: tuple[str, ...] = ()
    literature_sources: tuple[LiteratureSource, ...] = ()


@dataclass(frozen=True)
class ConstraintResult:
    """Outcome of checking ecological parameter constraints."""

    valid: bool
    failed_constraints: tuple[str, ...] = ()
    notes: str = ""


# ---------------------------------------------------------------------------
# Literature sources
# ---------------------------------------------------------------------------

_LIT_INBREEDING = LiteratureSource(
    citation="Husband & Schemske 1996 Evolution 50:54-70",
    parameter="inbreeding_depression",
    empirical_range="mean delta=0.23 (all plants); outcrossing spp. mean ~0.50; "
                    "dataset range 0.0-0.90",
    modelled_range=(0.10, 0.70),
    notes="Lower bound 0.10 excludes near-zero values uncommon in outcrossing "
          "Campanula. Upper bound 0.70 is the 90th percentile of the dataset. "
          "Uniform over this range is conservative relative to the empirical "
          "distribution.",
)

_LIT_SELFING = LiteratureSource(
    citation="Lloyd 1979 NZ J Bot; Husband & Schemske 1996; "
             "Inoue 1990 Plant Species Biology 5(1):57-64",
    parameter="selfing_benefit",
    empirical_range="Honshu/Oshima: SI and obligately outcrossing; "
                    "Toshima/Niijima: SC and largely outcrossing; "
                    "Miyake/Hachijo: SC and predominantly inbreeding. "
                    "Theoretical 3/2 advantage minus delta.",
    modelled_range=(0.05, 0.55),
    notes="Upper bound: net selfing advantage = 0.5 * (1 - 2*delta) for "
          "delta~0.25 gives ~0.25; we allow up to 0.55 to cover populations "
          "with lower inbreeding depression. Lower bound 0.05 (not zero) "
          "because southern Izu populations empirically show substantial "
          "selfing/inbreeding. Numeric t values require primary-PDF "
          "transcription before use as absolute y_obs.",
)

_LIT_OUTCROSSING = LiteratureSource(
    citation="Knight et al. 2005 Am J Bot (outcrossing benefit meta-analysis); "
             "Inoue & Amano 1986 Plant Species Biology 1(1):89-97; "
             "Inoue 1990 Plant Species Biology 5(1):57-64",
    parameter="outcrossing_benefit",
    empirical_range="Seed set improvement from cross-pollination: 10-70% in "
                    "mixed-mating plants.",
    modelled_range=(0.10, 0.75),
    notes="Campanula microdonta is treated here as the Izu Islands focal species; "
          "older literature may refer to the broader C. punctata complex. "
          "Outcrossing benefit "
          "includes genetic diversity and seed quality components. Range "
          "0.10-0.75 covers the empirical interquartile range for such species.",
)

_LIT_SMALL_POLLINATOR = LiteratureSource(
    citation="Larsson 2005 Oikos 109:400-408; Raine & Chittka 2007 "
             "PLoS ONE; general Halictidae vs Bombus comparisons",
    parameter="background_pollinator_efficiency",
    empirical_range="Halictid pollen transfer ~20-55% of Bombus per visit "
                    "in several plant families.",
    modelled_range=(0.10, 0.60),
    notes="Lower bound 0.10 (not zero): halictids are present on all Izu "
          "islands and provide some outcrossing. Upper bound 0.60 reflects "
          "the maximum reported relative efficiency. Campanula-specific data "
          "lacking; this is a generalisation from related systems.",
)

_LIT_GUIDE_COST = LiteratureSource(
    citation="No direct Campanula measurement available.",
    parameter="guide_cost",
    empirical_range="UV-reflecting pigment allocation: estimated <10% of "
                    "floral resource budget (general estimate).",
    modelled_range=(0.00, 0.15),
    notes="No direct measurement. Upper bound 0.15 based on the assumption "
          "that nectar-guide pigmentation is a minor metabolic investment "
          "relative to overall flower construction. Kept relatively broad "
          "to avoid over-constraining an unmeasured parameter.",
)

_LIT_DIRECT_GUIDE_BENEFIT = LiteratureSource(
    citation="Gumbert 2000 Oecologia; Raine & Chittka 2007; "
             "general Bombus guide-following experiments",
    parameter="direct_pollinator_guide_benefit",
    empirical_range="Guide manipulation experiments: 30-80% change in "
                    "Bombus landing accuracy / pollen transfer efficiency.",
    modelled_range=(0.20, 0.90),
    notes="Range covers published guide-manipulation results. Upper bound "
          "0.90 allows for near-obligate guide dependence in Bombus-pollinated "
          "morphs. Campanula-specific experiments lacking.",
)

_LIT_DRIFT = LiteratureSource(
    citation="Inoue & Kawahara 1990 American Journal of Botany 77:1440-1448; "
             "island biogeography",
    parameter="drift_strength",
    empirical_range="Independent genetic structure is expected to vary with "
                    "isolation, but exact per-island Fis/Ne values are pending "
                    "source confirmation.",
    modelled_range=(0.00, 0.25),
    notes="Drift strength is a proxy for 1/(2Ne) relative effects. The range is "
          "a conservative structure prior rather than an Inoue 1986 observation. "
          "Do not use simulator Fis_proxy as independent evidence.",
)

_LIT_NE_SLOPE = LiteratureSource(
    citation="Izu Island population census / allozyme survey; "
             "island biogeography (MacArthur & Wilson 1967)",
    parameter="Ne_isolation_slope",
    empirical_range="Fitted R²=0.93 at slope=0.765 for Izu Islands. "
                    "Direction (negative) is a universal principle; "
                    "magnitude is system-specific.",
    modelled_range=(0.30, 1.50),
    notes="DIRECTION fixed by principle: Ne decreases with isolation. "
          "SLOPE is a latent parameter θ. Prior centre 0.765 (Izu fit). "
          "Range (0.30, 1.50) covers plausible island biogeography slopes "
          "while keeping Ne_proxy in (0.05, 1.0) for all island distances. "
          "Lower bound > 0 enforces the direction principle.",
)

_LIT_MIGRATION_DECAY = LiteratureSource(
    citation="Izu geography / island biogeography exponential distance decay; "
             "empirical migration estimates pending source confirmation",
    parameter="migration_decay_rate",
    empirical_range="Exponential distance-decay prior over island isolation; "
                    "not a direct Inoue & Amano 1986 migration estimate.",
    modelled_range=(1.50, 6.00),
    # The empirical_range text above is a legacy distance-decay scaffold, not a
    # direct migration estimate from Inoue & Amano 1986.
    notes="LEGACY STRUCTURE PRIOR, not direct Inoue data. "
          "DIRECTION fixed: migration decays with isolation (universal). "
          "RATE k is a latent parameter. Range (1.50, 6.00) spans slow to rapid "
          "decay across island systems.",
)

_LIT_POLLINATOR_LOSS = LiteratureSource(
    citation="Inoue & Amano 1986 Plant Species Biology 1(1):89-97; "
             "Inoue 1988 Plant Species Biology 3(2):125-128",
    parameter="pollinator_loss_slope",
    empirical_range="Honshu: Bombus diversus; Oshima: Bombus ardens plus "
                    "halictids; Niijima/Kozushima/Hachijo: halictids. "
                    "Bumblebees absent from Izu except Oshima.",
    modelled_range=(0.50, 1.50),
    # The source-confirmed fact is the assemblage contrast, not a numeric
    # Bombus-frequency regression. Keep the slope as optional structure prior.
    notes="Source-confirmed assemblage contrast supports the direction; the "
          "numeric slope is an optional structure prior, not y_obs. "
          "DIRECTION fixed: Bombus frequency declines with isolation (observed). "
          "SLOPE k is a latent parameter. Range (0.50, 1.50) allows variation "
          "around the source-confirmed assemblage gradient.",
)

_LIT_WAITING_COST = LiteratureSource(
    citation="Harder & Barrett 1996 (pollinator limitation); "
             "reproductive assurance theory (Lloyd 1979)",
    parameter="cost_of_waiting_for_pollinators",
    empirical_range="Pollen limitation: 0-70% seed set reduction in "
                    "pollinator-limited populations.",
    modelled_range=(0.05, 0.80),
    notes="On Hachijo (no Bombus), waiting cost is effectively high. "
          "On Oshima, it is lower. Range 0.05-0.80 reflects this "
          "gradient. Lower bound > 0 because even on Oshima some "
          "pollinator stochasticity exists.",
)

LITERATURE_SOURCES: tuple[LiteratureSource, ...] = (
    _LIT_INBREEDING,
    _LIT_SELFING,
    _LIT_OUTCROSSING,
    _LIT_SMALL_POLLINATOR,
    _LIT_GUIDE_COST,
    _LIT_DIRECT_GUIDE_BENEFIT,
    _LIT_DRIFT,
    _LIT_WAITING_COST,
    _LIT_NE_SLOPE,
    _LIT_MIGRATION_DECAY,
    _LIT_POLLINATOR_LOSS,
)


# ---------------------------------------------------------------------------
# Trade-off presets
# ---------------------------------------------------------------------------

def predefined_tradeoff_presets() -> dict[str, TradeoffPreset]:
    """Return literature-grounded and broad-prior trade-off presets.

    literature_grounded  (recommended)
        Prior ranges derived from published empirical literature.
        Use this as the primary analysis preset.

    broad_prior
        Maximally broad ranges for sensitivity analysis.
        Use to verify that conclusions hold outside the literature-grounded
        prior region.

    Returns
    -------
    dict mapping preset name -> TradeoffPreset
    """

    literature_grounded = TradeoffPreset(
        name="literature_grounded",
        description=(
            "Prior ranges derived from empirical literature on plant mating "
            "systems and pollinator ecology (Husband & Schemske 1996; Lloyd "
            "1979; Larsson 2005; Inoue & Amano 1986). Measurable parameters "
            "are constrained by published values; unmeasurable parameters "
            "(guide_cost, cost_of_waiting) retain broad ranges. "
            "Use this preset as the primary analysis."
        ),
        ranges={
            "guide_cost":                      _LIT_GUIDE_COST.modelled_range,
            "outcrossing_benefit":             _LIT_OUTCROSSING.modelled_range,
            "selfing_benefit":                 _LIT_SELFING.modelled_range,
            "inbreeding_depression":           _LIT_INBREEDING.modelled_range,
            "background_pollinator_efficiency":     _LIT_SMALL_POLLINATOR.modelled_range,
            "drift_strength":                  _LIT_DRIFT.modelled_range,
            "direct_pollinator_guide_benefit": _LIT_DIRECT_GUIDE_BENEFIT.modelled_range,
            "cost_of_waiting_for_pollinators": _LIT_WAITING_COST.modelled_range,
            # Environmental slope parameters (θ) — direction fixed by principle,
            # magnitude inferred via ABC.
            "Ne_isolation_slope":             _LIT_NE_SLOPE.modelled_range,
            "migration_decay_rate":           _LIT_MIGRATION_DECAY.modelled_range,
            "pollinator_loss_slope":          _LIT_POLLINATOR_LOSS.modelled_range,
        },
        literature_sources=LITERATURE_SOURCES,
    )

    broad_prior = TradeoffPreset(
        name="broad_prior",
        description=(
            "Maximally broad exploratory ranges covering most biologically "
            "conceivable combinations. Use for sensitivity analysis: if "
            "RACH conclusions change substantially relative to "
            "literature_grounded, the result is prior-sensitive and should "
            "be reported with caution."
        ),
        ranges={
            "guide_cost":                      (0.00, 0.30),
            "outcrossing_benefit":             (0.00, 1.00),
            "selfing_benefit":                 (0.00, 0.80),
            "inbreeding_depression":           (0.00, 0.80),
            "background_pollinator_efficiency":     (0.00, 0.70),
            "drift_strength":                  (0.00, 0.30),
            "direct_pollinator_guide_benefit": (0.00, 1.00),
            "cost_of_waiting_for_pollinators": (0.00, 1.00),
            # Environmental slopes — broad prior keeps direction constraint
            # (lower bound > 0) but allows wide magnitude range.
            "Ne_isolation_slope":             (0.10, 2.00),
            "migration_decay_rate":           (0.50, 8.00),
            "pollinator_loss_slope":          (0.20, 2.00),
        },
        literature_sources=(),
    )

    return {
        "literature_grounded": literature_grounded,
        "broad_prior":         broad_prior,
    }


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def sample_parameters_from_preset(
    preset: TradeoffPreset,
    rng: random.Random,
) -> dict[str, float]:
    """Draw one parameter set uniformly from a preset's prior ranges."""

    return {
        name: rng.uniform(lo, hi)
        for name, (lo, hi) in preset.ranges.items()
    }


# ---------------------------------------------------------------------------
# Ecological parameter constraints
# ---------------------------------------------------------------------------

def check_ecological_parameter_constraints(
    params: dict[str, float],
    preset_name: str | None = None,
) -> ConstraintResult:
    """Check a parameter set against ecological parameter constraints.

    Hard rejection constraints
    --------------------------
    C1  selfing_benefit - inbreeding_depression >= -0.30
        Net selfing fitness must not be impossibly negative.
        (Avoids degenerate parameter combinations where selfing is
        catastrophically maladaptive yet still modelled as spreading.)

    C2  NOT (background_pollinator_efficiency > 0.55 AND selfing_benefit > 0.55)
        High small-pollinator substitution AND high selfing advantage
        cannot both be extreme simultaneously. If small pollinators
        adequately replace Bombus, reproductive-assurance selfing pressure
        is relieved.

    C3  NOT (guide_cost > 0.20 AND outcrossing_benefit < 0.05
             AND direct_pollinator_guide_benefit > 0.80)
        Internally inconsistent: maintaining a costly guide while
        outcrossing provides near-zero benefit yet guide expression
        dramatically increases pollinator attraction makes no fitness sense.

    C4  background_pollinator_efficiency < 0.80
        Background (trait-non-responsive) pollinators must be less efficient
        per visit than primary (trait-responsive) pollinators.  Primary
        efficiency is fixed at 0.80 (ModelParameters default, justified by
        Larsson 2005: halictid pollen transfer 20–55% of Bombus per visit).
        The functional distinction between the two guilds collapses if the
        background guild is equally or more efficient — the model would then
        have no identifiable primary channel.  Upper bound 0.80 corresponds
        to the primary_pollinator_efficiency default; values >= 0.80 are
        biologically implausible for the background guild in this system.

    C5 / C6  informational tradeoff classifications (never reject).
    """

    failed: list[str] = []
    notes_parts: list[str] = []

    gc   = params.get("guide_cost", 0.0)
    ob   = params.get("outcrossing_benefit", 0.0)
    sb   = params.get("selfing_benefit", 0.0)
    ibd  = params.get("inbreeding_depression", 0.0)
    spe  = params.get("background_pollinator_efficiency", 0.0)
    dgb  = params.get("direct_pollinator_guide_benefit", 0.0)

    # C1
    if sb - ibd < -0.30:
        failed.append("C1_selfing_net_fitness")
        notes_parts.append(
            f"C1: selfing_benefit({sb:.3f}) - inbreeding_depression({ibd:.3f})"
            f" = {sb - ibd:.3f} < -0.30"
        )

    # C2 — threshold tightened to match literature_grounded upper bounds
    if spe > 0.55 and sb > 0.55:
        failed.append("C2_small_pollinator_vs_selfing_benefit")
        notes_parts.append(
            f"C2: background_pollinator_efficiency({spe:.3f}) > 0.55 AND "
            f"selfing_benefit({sb:.3f}) > 0.55 — simultaneously high "
            f"outcrossing substitute and maximal selfing advantage"
        )

    # C3
    if gc > 0.20 and ob < 0.05 and dgb > 0.80:
        failed.append("C3_guide_cost_outcrossing_inconsistency")
        notes_parts.append(
            f"C3: guide_cost({gc:.3f}) > 0.20 AND "
            f"outcrossing_benefit({ob:.3f}) < 0.05 AND "
            f"direct_pollinator_guide_benefit({dgb:.3f}) > 0.80"
        )

    # C4 — background efficiency must be strictly below primary efficiency (0.80).
    # Larsson 2005 (Oikos 109): halictid pollen transfer 20-55% of Bombus per
    # visit across several plant families.  Values >= 0.80 collapse the functional
    # distinction between the two pollinator guilds.
    if spe >= 0.80:
        failed.append("C4_background_efficiency_exceeds_primary")
        notes_parts.append(
            f"C4: background_pollinator_efficiency({spe:.3f}) >= 0.80 "
            f"(primary_pollinator_efficiency default) — functional distinction "
            f"between guilds collapses; biologically implausible for halictids"
        )

    # C5 — environmental slope parameters must be positive (direction principle).
    # The DIRECTION of each relationship is a universal/directional principle:
    #   Ne decreases with isolation, migration decreases with isolation,
    #   Bombus frequency decreases with isolation.
    # A zero or negative slope would reverse these principles, which is
    # biologically incoherent regardless of system-specific magnitude.
    for slope_key in ("Ne_isolation_slope", "migration_decay_rate", "pollinator_loss_slope"):
        slope_val = params.get(slope_key)
        if slope_val is not None and slope_val <= 0.0:
            failed.append(f"C5_{slope_key}_direction_violated")
            notes_parts.append(
                f"C5: {slope_key}({slope_val:.4f}) <= 0 — violates directional "
                f"principle (isolation must reduce Ne / migration / Bombus). "
                f"The sign is fixed by universal ecological principle."
            )

    valid = len(failed) == 0
    return ConstraintResult(
        valid=valid,
        failed_constraints=tuple(failed),
        notes="; ".join(notes_parts) if notes_parts else "",
    )


def classify_tradeoffs(params: dict[str, float]) -> dict[str, str]:
    """Compute guide and selfing net-benefit classifications (C4, C5).

    Informational annotations only — never causes rejection.
    """

    ob   = params.get("outcrossing_benefit", 0.0)
    dgb  = params.get("direct_pollinator_guide_benefit", 0.0)
    gc   = params.get("guide_cost", 0.0)
    sb   = params.get("selfing_benefit", 0.0)
    cowp = params.get("cost_of_waiting_for_pollinators", 0.0)
    ibd  = params.get("inbreeding_depression", 0.0)

    gnb = ob + dgb - gc
    g_class = (
        "guide_favorable" if gnb > 0.40
        else "guide_intermediate" if gnb >= 0.00
        else "guide_unfavorable"
    )

    snb = sb + cowp - ibd
    s_class = (
        "selfing_favorable" if snb > 0.30
        else "selfing_intermediate" if snb >= -0.10
        else "selfing_unfavorable"
    )

    return {
        "guide_net_benefit": round(gnb, 4),
        "guide_tradeoff_class": g_class,
        "selfing_net_benefit": round(snb, 4),
        "selfing_tradeoff_class": s_class,
    }


# ---------------------------------------------------------------------------
# Batch sampling
# ---------------------------------------------------------------------------

def sample_valid_parameter_sets(
    preset: TradeoffPreset,
    n: int,
    seed: int | None = None,
    max_attempts: int | None = None,
) -> list[dict[str, float]]:
    """Draw n valid parameter sets from a preset under ecological constraints."""

    rng = random.Random(seed)
    limit = max_attempts if max_attempts is not None else 50 * n
    results: list[dict[str, float]] = []
    attempts = 0

    while len(results) < n and attempts < limit:
        attempts += 1
        params = sample_parameters_from_preset(preset, rng)
        check = check_ecological_parameter_constraints(params, preset.name)
        if not check.valid:
            continue
        row: dict[str, float | str] = {
            "parameter_set_id": str(uuid.uuid4()),
            "preset_name": preset.name,
            **params,
            **classify_tradeoffs(params),
            "valid": True,
            "failed_constraints": "",
        }
        results.append(row)

    return results


def sample_all_sets_with_rejection_log(
    preset: TradeoffPreset,
    n_attempts: int,
    seed: int | None = None,
) -> tuple[list[dict], list[dict]]:
    """Draw n_attempts sets and return (accepted, rejected) with full annotation."""

    rng = random.Random(seed)
    accepted: list[dict] = []
    rejected: list[dict] = []

    for _ in range(n_attempts):
        params = sample_parameters_from_preset(preset, rng)
        check = check_ecological_parameter_constraints(params, preset.name)
        classifications = classify_tradeoffs(params)
        row: dict = {
            "parameter_set_id": str(uuid.uuid4()),
            "preset_name": preset.name,
            **params,
            **classifications,
            "valid": check.valid,
            "failed_constraints": "; ".join(check.failed_constraints),
            "constraint_notes": check.notes,
        }
        if check.valid:
            accepted.append(row)
        else:
            rejected.append(row)

    return accepted, rejected
