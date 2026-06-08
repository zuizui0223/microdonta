"""Ecology-principled parameter constraints and trade-off sampling.

Latent benefit/cost parameters should not be sampled independently without
biological logic. This module defines trade-off presets and parameter-to-parameter
constraints based on ecological principles, enabling constrained random sampling
rather than manual parameter tuning.

Research framing:
    Latent costs and benefits were not tuned manually. We defined biologically
    motivated prior ranges and parameter-to-parameter constraints, sampled from
    the resulting constrained trade-off space, and evaluated which causal
    structures and parameter sets could reproduce multiple observed patterns
    simultaneously.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TradeoffPreset:
    """A named set of prior ranges over latent benefit/cost parameters.

    Parameters
    ----------
    name:
        Short identifier (e.g. "reproductive_assurance").
    description:
        Biological motivation for this range configuration.
    ranges:
        Mapping from parameter name to (lower, upper) uniform prior bounds.
    constraints:
        Tuple of constraint names that will be applied to samples drawn from
        this preset (in addition to universal constraints).
    """

    name: str
    description: str
    ranges: dict[str, tuple[float, float]]
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConstraintResult:
    """Outcome of checking ecological parameter constraints.

    Parameters
    ----------
    valid:
        True if all constraints passed.
    failed_constraints:
        Names of constraints that were violated.
    notes:
        Optional diagnostic string describing the rejection reason.
    """

    valid: bool
    failed_constraints: tuple[str, ...] = ()
    notes: str = ""


# ---------------------------------------------------------------------------
# Trade-off presets
# ---------------------------------------------------------------------------

def predefined_tradeoff_presets() -> dict[str, TradeoffPreset]:
    """Return five pre-defined ecological trade-off presets.

    These presets replace manual parameter selection with biologically
    motivated prior ranges. Parameter sets are sampled uniformly within
    each preset, then filtered by ecological parameter constraints.

    Returns
    -------
    dict mapping preset name -> TradeoffPreset
    """

    return {
        "broad_prior": TradeoffPreset(
            name="broad_prior",
            description=(
                "Broad exploratory range covering most biologically conceivable "
                "combinations. Useful for initial sensitivity sweeps before "
                "committing to a more focused preset."
            ),
            ranges={
                "guide_cost":                    (0.00, 0.30),
                "outcrossing_benefit":           (0.00, 1.00),
                "selfing_benefit":               (0.00, 0.80),
                "inbreeding_depression":         (0.00, 0.80),
                "small_pollinator_efficiency":   (0.00, 0.70),
                "drift_strength":                (0.00, 0.25),
                "direct_pollinator_guide_benefit": (0.00, 1.00),
                "cost_of_waiting_for_pollinators": (0.00, 1.00),
            },
        ),

        "reproductive_assurance": TradeoffPreset(
            name="reproductive_assurance",
            description=(
                "Selfing is potentially favoured because pollinator service is "
                "unreliable. Waiting cost is elevated and selfing benefit is "
                "moderate-to-high. Inbreeding depression is constrained to "
                "a moderate range that still allows selfing to spread."
            ),
            ranges={
                "guide_cost":                    (0.03, 0.25),
                "outcrossing_benefit":           (0.10, 0.70),
                "selfing_benefit":               (0.25, 0.80),
                "inbreeding_depression":         (0.00, 0.45),
                "small_pollinator_efficiency":   (0.00, 0.50),
                "drift_strength":                (0.00, 0.20),
                "direct_pollinator_guide_benefit": (0.00, 0.70),
                "cost_of_waiting_for_pollinators": (0.20, 0.90),
            },
        ),

        "outcrossing_benefit": TradeoffPreset(
            name="outcrossing_benefit",
            description=(
                "Outcrossing and pollinator-mediated attraction remain valuable. "
                "Outcrossing benefit and direct guide benefit are elevated. "
                "Inbreeding depression is substantial, preventing easy selfing spread."
            ),
            ranges={
                "guide_cost":                    (0.00, 0.18),
                "outcrossing_benefit":           (0.40, 1.00),
                "selfing_benefit":               (0.00, 0.40),
                "inbreeding_depression":         (0.30, 0.80),
                "small_pollinator_efficiency":   (0.20, 0.70),
                "drift_strength":                (0.00, 0.15),
                "direct_pollinator_guide_benefit": (0.30, 1.00),
                "cost_of_waiting_for_pollinators": (0.00, 0.40),
            },
        ),

        "high_guide_cost": TradeoffPreset(
            name="high_guide_cost",
            description=(
                "Nectar-guide maintenance is costly. Guide loss can be favoured "
                "even when some outcrossing benefit exists. Tests scenarios where "
                "guide cost drives convergent reduction across the island gradient."
            ),
            ranges={
                "guide_cost":                    (0.12, 0.30),
                "outcrossing_benefit":           (0.00, 0.70),
                "selfing_benefit":               (0.10, 0.70),
                "inbreeding_depression":         (0.00, 0.60),
                "small_pollinator_efficiency":   (0.00, 0.60),
                "drift_strength":                (0.00, 0.20),
                "direct_pollinator_guide_benefit": (0.00, 0.80),
                "cost_of_waiting_for_pollinators": (0.10, 0.80),
            },
        ),

        "drift_dominated": TradeoffPreset(
            name="drift_dominated",
            description=(
                "Null-like setting where drift can strongly affect guide state. "
                "Drift strength is elevated. Directional selection parameters are "
                "kept at moderate levels so that any guide change is primarily "
                "attributable to stochastic loss, not selection. "
                "Corresponds to M5_drift_null causal structure."
            ),
            ranges={
                "guide_cost":                    (0.00, 0.20),
                "outcrossing_benefit":           (0.00, 0.60),
                "selfing_benefit":               (0.00, 0.60),
                "inbreeding_depression":         (0.00, 0.60),
                "small_pollinator_efficiency":   (0.00, 0.60),
                "drift_strength":                (0.10, 0.30),
                "direct_pollinator_guide_benefit": (0.00, 0.50),
                "cost_of_waiting_for_pollinators": (0.00, 0.60),
            },
        ),
    }


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def sample_parameters_from_preset(
    preset: TradeoffPreset,
    rng: random.Random,
) -> dict[str, float]:
    """Draw one parameter set uniformly from a preset's prior ranges.

    Parameters
    ----------
    preset:
        The trade-off preset defining prior bounds.
    rng:
        Random number generator (for reproducibility).

    Returns
    -------
    dict mapping parameter name -> sampled float value
    """

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

    Constraints are provisional ecological principles, not final truths.
    Failed constraints are recorded so rejected sets can be diagnosed.

    Hard rejection constraints (return valid=False):
        C1  selfing_benefit - inbreeding_depression >= -0.30
        C2  NOT (small_pollinator_efficiency > 0.55 AND selfing_benefit > 0.75)
        C3  NOT (guide_cost > 0.25 AND outcrossing_benefit < 0.05 AND
                 direct_pollinator_guide_benefit > 0.80)

    Classification (informational, never causes rejection):
        C4  guide_net_benefit classification
        C5  selfing_net_benefit classification

    Parameters
    ----------
    params:
        Parameter dict from sample_parameters_from_preset.
    preset_name:
        Optional: name of the preset used, for context.

    Returns
    -------
    ConstraintResult with valid flag and list of failed constraints.
    """

    failed: list[str] = []
    notes_parts: list[str] = []

    gc   = params.get("guide_cost", 0.0)
    ob   = params.get("outcrossing_benefit", 0.0)
    sb   = params.get("selfing_benefit", 0.0)
    ibd  = params.get("inbreeding_depression", 0.0)
    spe  = params.get("small_pollinator_efficiency", 0.0)
    dgb  = params.get("direct_pollinator_guide_benefit", 0.0)
    cowp = params.get("cost_of_waiting_for_pollinators", 0.0)

    # C1 — selfing net fitness must not be impossibly negative
    if sb - ibd < -0.30:
        failed.append("C1_selfing_net_fitness")
        notes_parts.append(
            f"C1: selfing_benefit({sb:.3f}) - inbreeding_depression({ibd:.3f}) = "
            f"{sb - ibd:.3f} < -0.30 — selfing evolution unlikely"
        )

    # C2 — high small-pollinator efficiency + extreme selfing benefit together
    if spe > 0.55 and sb > 0.75:
        failed.append("C2_small_pollinator_vs_selfing_benefit")
        notes_parts.append(
            f"C2: small_pollinator_efficiency({spe:.3f}) > 0.55 AND "
            f"selfing_benefit({sb:.3f}) > 0.75 — simultaneous alternative "
            f"outcrossing and maximal selfing advantage is unjustified"
        )

    # C3 — internally inconsistent high guide cost + high guide benefit + no outcrossing
    if gc > 0.25 and ob < 0.05 and dgb > 0.80:
        failed.append("C3_guide_cost_outcrossing_inconsistency")
        notes_parts.append(
            f"C3: guide_cost({gc:.3f}) > 0.25 AND outcrossing_benefit({ob:.3f}) < 0.05 "
            f"AND direct_pollinator_guide_benefit({dgb:.3f}) > 0.80 — internally inconsistent"
        )

    valid = len(failed) == 0
    return ConstraintResult(
        valid=valid,
        failed_constraints=tuple(failed),
        notes="; ".join(notes_parts) if notes_parts else "",
    )


def classify_tradeoffs(params: dict[str, float]) -> dict[str, str]:
    """Compute guide and selfing net-benefit classifications (C4, C5).

    These are informational annotations, not rejection criteria.

    Returns
    -------
    dict with keys:
        guide_net_benefit       float
        guide_tradeoff_class    "guide_favorable" | "guide_intermediate" | "guide_unfavorable"
        selfing_net_benefit     float
        selfing_tradeoff_class  "selfing_favorable" | "selfing_intermediate" | "selfing_unfavorable"
    """

    ob   = params.get("outcrossing_benefit", 0.0)
    dgb  = params.get("direct_pollinator_guide_benefit", 0.0)
    gc   = params.get("guide_cost", 0.0)
    sb   = params.get("selfing_benefit", 0.0)
    cowp = params.get("cost_of_waiting_for_pollinators", 0.0)
    ibd  = params.get("inbreeding_depression", 0.0)

    gnb = ob + dgb - gc
    if gnb > 0.40:
        g_class = "guide_favorable"
    elif gnb >= 0.00:
        g_class = "guide_intermediate"
    else:
        g_class = "guide_unfavorable"

    snb = sb + cowp - ibd
    if snb > 0.30:
        s_class = "selfing_favorable"
    elif snb >= -0.10:
        s_class = "selfing_intermediate"
    else:
        s_class = "selfing_unfavorable"

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
    """Draw n valid parameter sets from a preset under ecological constraints.

    Each returned dict includes:
        - all sampled parameter values
        - guide_net_benefit, guide_tradeoff_class
        - selfing_net_benefit, selfing_tradeoff_class
        - parameter_set_id (UUID)
        - preset_name
        - valid = True (only valid sets are returned)
        - failed_constraints = ""

    Parameters
    ----------
    preset:
        Trade-off preset to sample from.
    n:
        Number of valid sets to collect.
    seed:
        RNG seed for reproducibility.
    max_attempts:
        Maximum total draws before giving up (default: 50 * n).

    Returns
    -------
    list of valid annotated parameter dicts (length <= n).
    """

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
    """Draw n_attempts sets and return (accepted, rejected) with full annotation.

    Useful for reporting acceptance rates and diagnosing which constraints
    fail most often.

    Returns
    -------
    (accepted_sets, rejected_sets)
        Each entry is a fully annotated dict including valid, failed_constraints.
    """

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
