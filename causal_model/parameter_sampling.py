"""Ecology-principled constrained parameter sampling for CAPOM.

Latent benefit/cost parameters (guide_cost, outcrossing_benefit, etc.) should
not be sampled independently without biological logic. This module provides:

  - Trade-off presets: named prior ranges motivated by ecological hypotheses
  - Ecological parameter constraints: hard filters that reject implausible
    parameter combinations before any simulation is run
  - Constrained sampling: draw valid sets from a preset's prior

Research framing::

    Latent costs and benefits were not tuned manually. We defined biologically
    motivated prior ranges and parameter-to-parameter constraints, sampled from
    the resulting constrained trade-off space, and evaluated which causal
    structures and parameter sets could reproduce multiple observed patterns
    simultaneously.

Japanese::

    隕ｳ蟇溘ヱ繧ｿ繝ｼ繝ｳ縺ｫ蜷医≧繧医≧縺ｫ繝代Λ繝｡繝ｼ繧ｿ繧呈焔蜍戊ｪｿ謨ｴ縺吶ｋ縺ｮ縺ｧ縺ｯ縺ｪ縺上・    逕滓・蟄ｦ逧・↓螯･蠖薙↑蛻ｩ逶翫・繧ｳ繧ｹ繝医・遽・峇縺ｨ繝代Λ繝｡繝ｼ繧ｿ髢灘宛邏・ｒ莠句燕縺ｫ螳夂ｾｩ縺励・    縺昴・蛻ｶ邏・・縺ｧ繝ｩ繝ｳ繝繝繧ｵ繝ｳ繝励Μ繝ｳ繧ｰ繧定｡後＞縲∬､・焚縺ｮ隕ｳ蟇溘ヱ繧ｿ繝ｼ繝ｳ繧貞酔譎ゅ↓
    蜀咲樟縺ｧ縺阪ｋ繝代Λ繝｡繝ｼ繧ｿ繧ｻ繝・ヨ縺縺代ｒ蜿礼炊縺吶ｋ縲・"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TradeoffPreset:
    """A named set of prior ranges over latent benefit/cost parameters.

    Attributes
    ----------
    name:
        Short identifier, e.g. ``"reproductive_assurance"``.
    description:
        Biological motivation for this range configuration.
    ranges:
        Mapping from parameter name to ``(lower, upper)`` uniform prior bounds.
        All bounds are inclusive.
    constraints:
        Names of ecological constraints that apply specifically to this preset,
        in addition to the universal constraints checked by
        :func:`check_ecological_parameter_constraints`.
    """

    name: str
    description: str
    ranges: dict[str, tuple[float, float]]
    constraints: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ConstraintResult:
    """Outcome of checking ecological parameter constraints.

    Attributes
    ----------
    valid:
        True if all checked constraints passed.
    failed_constraints:
        Tuple of constraint identifiers that were violated.
    notes:
        Human-readable explanation of each violation, joined by "; ".
    """

    valid: bool
    failed_constraints: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


# ---------------------------------------------------------------------------
# Trade-off presets
# ---------------------------------------------------------------------------

def predefined_tradeoff_presets() -> dict[str, TradeoffPreset]:
    """Return five ecology-motivated trade-off presets.

    Each preset defines a biologically plausible region of the
    latent parameter space. Parameter sets are sampled uniformly
    within a preset's ranges, then filtered by ecological constraints.

    Returns
    -------
    dict
        Mapping from preset name to :class:`TradeoffPreset`.

    Presets
    -------
    broad_prior
        Wide exploratory ranges; useful for sensitivity sweeps.
    reproductive_assurance
        Selfing may be favoured because pollinator service is unreliable.
    outcrossing_benefit
        Outcrossing and guide-mediated attraction remain valuable.
    high_guide_cost
        Nectar-guide maintenance is metabolically costly.
    drift_dominated
        Drift is the primary driver of guide change (null hypothesis).
    """

    return {
        # 笏笏 1. broad_prior 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
        "broad_prior": TradeoffPreset(
            name="broad_prior",
            description=(
                "Wide exploratory ranges covering most biologically conceivable "
                "combinations. Useful for initial sensitivity sweeps before "
                "committing to a more focused preset."
            ),
            ranges={
                "guide_cost":                      (0.00, 0.30),
                "outcrossing_benefit":             (0.00, 1.00),
                "selfing_benefit":                 (0.00, 0.80),
                "inbreeding_depression":           (0.00, 0.80),
                "small_pollinator_efficiency":     (0.00, 0.70),
                "drift_strength":                  (0.00, 0.25),
                "direct_pollinator_guide_benefit": (0.00, 1.00),
                "cost_of_waiting_for_pollinators": (0.00, 1.00),
            },
        ),

        # 笏笏 2. reproductive_assurance 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
        "reproductive_assurance": TradeoffPreset(
            name="reproductive_assurance",
            description=(
                "Selfing is potentially favoured because pollinator service is "
                "unreliable. Waiting cost is elevated and selfing benefit is "
                "moderate-to-high. Inbreeding depression is constrained to a "
                "moderate range that still allows selfing to spread."
            ),
            ranges={
                "guide_cost":                      (0.03, 0.25),
                "outcrossing_benefit":             (0.10, 0.70),
                "selfing_benefit":                 (0.25, 0.80),
                "inbreeding_depression":           (0.00, 0.45),
                "small_pollinator_efficiency":     (0.00, 0.50),
                "drift_strength":                  (0.00, 0.20),
                "direct_pollinator_guide_benefit": (0.00, 0.70),
                "cost_of_waiting_for_pollinators": (0.20, 0.90),
            },
        ),

        # 笏笏 3. outcrossing_benefit 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
        "outcrossing_benefit": TradeoffPreset(
            name="outcrossing_benefit",
            description=(
                "Outcrossing and pollinator-mediated attraction remain valuable. "
                "Outcrossing benefit and direct guide benefit are elevated. "
                "Inbreeding depression is substantial, preventing easy selfing spread."
            ),
            ranges={
                "guide_cost":                      (0.00, 0.18),
                "outcrossing_benefit":             (0.40, 1.00),
                "selfing_benefit":                 (0.00, 0.40),
                "inbreeding_depression":           (0.30, 0.80),
                "small_pollinator_efficiency":     (0.20, 0.70),
                "drift_strength":                  (0.00, 0.15),
                "direct_pollinator_guide_benefit": (0.30, 1.00),
                "cost_of_waiting_for_pollinators": (0.00, 0.40),
            },
        ),

        # 笏笏 4. high_guide_cost 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
        "high_guide_cost": TradeoffPreset(
            name="high_guide_cost",
            description=(
                "Nectar-guide maintenance is metabolically costly. Guide loss can "
                "be favoured even when some outcrossing benefit exists. Tests "
                "scenarios where guide cost drives convergent reduction across the "
                "island isolation gradient."
            ),
            ranges={
                "guide_cost":                      (0.12, 0.30),
                "outcrossing_benefit":             (0.00, 0.70),
                "selfing_benefit":                 (0.10, 0.70),
                "inbreeding_depression":           (0.00, 0.60),
                "small_pollinator_efficiency":     (0.00, 0.60),
                "drift_strength":                  (0.00, 0.20),
                "direct_pollinator_guide_benefit": (0.00, 0.80),
                "cost_of_waiting_for_pollinators": (0.10, 0.80),
            },
        ),

        # 笏笏 5. drift_dominated 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
        "drift_dominated": TradeoffPreset(
            name="drift_dominated",
            description=(
                "Null-like setting where drift strongly affects guide state. "
                "Drift strength is elevated. Directional selection parameters are "
                "kept moderate so that guide change is primarily attributable to "
                "stochastic loss, not selection. Corresponds to M5_drift_null."
            ),
            ranges={
                "guide_cost":                      (0.00, 0.20),
                "outcrossing_benefit":             (0.00, 0.60),
                "selfing_benefit":                 (0.00, 0.60),
                "inbreeding_depression":           (0.00, 0.60),
                "small_pollinator_efficiency":     (0.00, 0.60),
                "drift_strength":                  (0.10, 0.30),
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
        Trade-off preset defining the prior bounds.
    rng:
        Caller-owned random number generator (enables reproducibility).

    Returns
    -------
    dict
        Mapping from parameter name to sampled float value.
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

    Constraints are *provisional ecological principles*, not final truths.
    All failed constraints are recorded so that rejected sets can be
    diagnosed and reported transparently.

    Hard rejection constraints
    --------------------------
    C1  selfing_benefit - inbreeding_depression >= -0.30
        Rationale: if inbreeding depression is extremely high and selfing
        benefit very low, strong selfing evolution is biologically unlikely.

    C2  NOT (small_pollinator_efficiency > 0.55 AND selfing_benefit > 0.75)
        Rationale: when small pollinators can still maintain reasonably
        efficient outcrossing, extreme reproductive-assurance selfing benefit
        should not be assigned simultaneously without justification.

    C3  NOT (guide_cost > 0.25 AND outcrossing_benefit < 0.05
             AND direct_pollinator_guide_benefit > 0.80)
        Rationale: extremely costly guides with near-zero outcrossing benefit
        and simultaneously very high direct guide benefit is internally
        inconsistent unless explicitly motivated.

    Informational classifications (never cause rejection)
    -----------------------------------------------------
    C4  guide_net_benefit = outcrossing_benefit
                          + direct_pollinator_guide_benefit - guide_cost
        竊・guide_favorable (> 0.40) / guide_intermediate (0窶・.40)
          / guide_unfavorable (< 0)

    C5  selfing_net_benefit = selfing_benefit
                            + cost_of_waiting_for_pollinators
                            - inbreeding_depression
        竊・selfing_favorable (> 0.30) / selfing_intermediate (-0.10窶・.30)
          / selfing_unfavorable (< -0.10)

    Parameters
    ----------
    params:
        Parameter dict, typically from :func:`sample_parameters_from_preset`.
    preset_name:
        Optional preset identifier included in notes for context.

    Returns
    -------
    ConstraintResult
    """

    gc   = params.get("guide_cost",                      0.0)
    ob   = params.get("outcrossing_benefit",             0.0)
    sb   = params.get("selfing_benefit",                 0.0)
    ibd  = params.get("inbreeding_depression",           0.0)
    spe  = params.get("small_pollinator_efficiency",     0.0)
    dgb  = params.get("direct_pollinator_guide_benefit", 0.0)

    failed: list[str] = []
    notes: list[str] = []

    # C1 窶・selfing net fitness must not be implausibly negative
    if sb - ibd < -0.30:
        failed.append("C1_selfing_net_fitness")
        notes.append(
            f"C1: selfing_benefit({sb:.3f}) - inbreeding_depression({ibd:.3f})"
            f" = {sb - ibd:.3f} < -0.30; selfing evolution unlikely under"
            " such strong inbreeding cost"
        )

    # C2 窶・effective alternative outcrossing + extreme selfing benefit together
    if spe > 0.55 and sb > 0.75:
        failed.append("C2_small_pollinator_vs_selfing_benefit")
        notes.append(
            f"C2: small_pollinator_efficiency({spe:.3f}) > 0.55 AND"
            f" selfing_benefit({sb:.3f}) > 0.75; simultaneous high alternative"
            " outcrossing and maximal selfing advantage is unjustified"
        )

    # C3 窶・internally inconsistent high guide cost + no outcrossing + high guide benefit
    if gc > 0.25 and ob < 0.05 and dgb > 0.80:
        failed.append("C3_guide_cost_benefit_inconsistency")
        notes.append(
            f"C3: guide_cost({gc:.3f}) > 0.25 AND outcrossing_benefit({ob:.3f})"
            f" < 0.05 AND direct_pollinator_guide_benefit({dgb:.3f}) > 0.80;"
            " internally inconsistent parameter combination"
        )

    return ConstraintResult(
        valid=len(failed) == 0,
        failed_constraints=tuple(failed),
        notes="; ".join(notes),
    )


def _classify_tradeoffs(params: dict[str, float]) -> dict[str, object]:
    """Compute C4/C5 informational trade-off classifications.

    Not a rejection criterion 窶・purely annotational.

    Returns dict with keys:
        guide_net_benefit, guide_tradeoff_class,
        selfing_net_benefit, selfing_tradeoff_class
    """

    ob   = params.get("outcrossing_benefit",             0.0)
    dgb  = params.get("direct_pollinator_guide_benefit", 0.0)
    gc   = params.get("guide_cost",                      0.0)
    sb   = params.get("selfing_benefit",                 0.0)
    cowp = params.get("cost_of_waiting_for_pollinators", 0.0)
    ibd  = params.get("inbreeding_depression",           0.0)

    gnb = ob + dgb - gc
    g_class = (
        "guide_favorable"    if gnb > 0.40 else
        "guide_intermediate" if gnb >= 0.00 else
        "guide_unfavorable"
    )

    snb = sb + cowp - ibd
    s_class = (
        "selfing_favorable"    if snb > 0.30 else
        "selfing_intermediate" if snb >= -0.10 else
        "selfing_unfavorable"
    )

    return {
        "guide_net_benefit":    round(gnb, 4),
        "guide_tradeoff_class": g_class,
        "selfing_net_benefit":  round(snb, 4),
        "selfing_tradeoff_class": s_class,
    }


# ---------------------------------------------------------------------------
# Batch constrained sampling
# ---------------------------------------------------------------------------

def sample_valid_parameter_sets(
    preset: TradeoffPreset,
    n: int,
    seed: int | None = None,
    max_attempts: int | None = None,
) -> list[dict[str, float | str | bool]]:
    """Draw *n* valid parameter sets from a preset under ecological constraints.

    Each returned dict contains:

    - all sampled parameter values from the preset
    - ``guide_net_benefit``, ``guide_tradeoff_class`` (C4)
    - ``selfing_net_benefit``, ``selfing_tradeoff_class`` (C5)
    - ``parameter_set_id``  窶・UUID string for traceability
    - ``preset_name``
    - ``valid = True``  (only accepted sets are returned)
    - ``failed_constraints = ""``

    Parameters
    ----------
    preset:
        Trade-off preset to sample from.
    n:
        Target number of valid sets to collect.
    seed:
        RNG seed for reproducibility. ``None`` 竊・system entropy.
    max_attempts:
        Maximum total draws before stopping (default: ``50 * n``).
        If exhausted before *n* sets are found, returns fewer than *n*.

    Returns
    -------
    list of valid annotated parameter dicts (length 竕､ n).

    Notes
    -----
    The function logs nothing; callers that need rejection diagnostics
    should use :func:`sample_with_rejection_log` instead.
    """

    rng = random.Random(seed)
    limit = max_attempts if max_attempts is not None else 50 * n
    results: list[dict] = []
    attempts = 0

    while len(results) < n and attempts < limit:
        attempts += 1
        params = sample_parameters_from_preset(preset, rng)
        result = check_ecological_parameter_constraints(params, preset.name)
        if not result.valid:
            continue
        row: dict = {
            "parameter_set_id":  str(uuid.uuid4()),
            "preset_name":       preset.name,
            **params,
            **_classify_tradeoffs(params),
            "valid":             True,
            "failed_constraints": "",
        }
        results.append(row)

    return results


def sample_with_rejection_log(
    preset: TradeoffPreset,
    n_attempts: int,
    seed: int | None = None,
) -> tuple[list[dict], list[dict]]:
    """Draw *n_attempts* sets and return ``(accepted, rejected)`` with full annotation.

    Both lists use the same schema as :func:`sample_valid_parameter_sets` plus
    ``constraint_notes`` for rejected sets.

    Parameters
    ----------
    preset:
        Trade-off preset to sample from.
    n_attempts:
        Total draws from the prior (regardless of acceptance).
    seed:
        RNG seed.

    Returns
    -------
    (accepted_sets, rejected_sets)
    """

    rng = random.Random(seed)
    accepted: list[dict] = []
    rejected: list[dict] = []

    for _ in range(n_attempts):
        params = sample_parameters_from_preset(preset, rng)
        result = check_ecological_parameter_constraints(params, preset.name)
        row: dict = {
            "parameter_set_id":   str(uuid.uuid4()),
            "preset_name":        preset.name,
            **params,
            **_classify_tradeoffs(params),
            "valid":              result.valid,
            "failed_constraints": "; ".join(result.failed_constraints),
            "constraint_notes":   result.notes,
        }
        (accepted if result.valid else rejected).append(row)

    return accepted, rejected


# ---------------------------------------------------------------------------
# Conversion to ModelParameters
# ---------------------------------------------------------------------------

def param_set_to_model_parameters(param_set: dict):
    """Convert a sampled latent parameter dict to ModelParameters.

    Maps the 8 CAPOM latent parameters onto ModelParameters fields.

    Mapping
    -------
    guide_cost                      → mp.guide_cost
    outcrossing_benefit             → mp.outcrossing_benefit
    selfing_benefit                 → mp.selfing_benefit (base)
    inbreeding_depression           → mp.inbreeding_depression
    small_pollinator_efficiency     → mp.small_pollinator_efficiency
    drift_strength                  → mp.base_drift_strength
    direct_pollinator_guide_benefit → mp.bombus_guide_use
    cost_of_waiting_for_pollinators → added to selfing_benefit as reproductive-
                                      assurance modifier (× 0.4, capped at 1.0)
    """

    from attraction_trait_model.parameters import ModelParameters

    guide_cost = float(param_set.get("guide_cost", 0.05))
    outcrossing_benefit = float(param_set.get("outcrossing_benefit", 0.2))
    selfing_benefit_raw = float(param_set.get("selfing_benefit", 0.1))
    inbreeding_depression = float(param_set.get("inbreeding_depression", 0.2))
    small_pollinator_efficiency = float(param_set.get("small_pollinator_efficiency", 0.3))
    drift_strength = float(param_set.get("drift_strength", 0.05))
    direct_pollinator_guide_benefit = float(param_set.get("direct_pollinator_guide_benefit", 0.6))
    cost_of_waiting = float(param_set.get("cost_of_waiting_for_pollinators", 0.1))

    # Reproductive assurance: waiting cost increases effective selfing benefit
    effective_selfing_benefit = min(1.0, selfing_benefit_raw + cost_of_waiting * 0.4)

    return ModelParameters(
        guide_cost=guide_cost,
        outcrossing_benefit=outcrossing_benefit,
        selfing_benefit=effective_selfing_benefit,
        inbreeding_depression=inbreeding_depression,
        small_pollinator_efficiency=small_pollinator_efficiency,
        base_drift_strength=drift_strength,
        bombus_guide_use=direct_pollinator_guide_benefit,
    )