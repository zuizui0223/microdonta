"""Ecology-principled constrained parameter sampling for CAPOM.

IMPORTANT — single source of truth for constraints:
    Ecological parameter constraints (C1, C2, C3, literature-grounded ranges,
    and preset definitions) are AUTHORITATIVE in ``parameter_constraints.py``.
    This module contains a parallel implementation of some checks (used during
    TradeoffPreset sampling) that MUST remain consistent with that module.
    Any change to a constraint threshold must be applied in both files.
    Current agreed values: C2 threshold = sb > 0.55 (selfing_benefit).


This module defines the research-mode sampling logic for latent benefit/cost
parameters. These parameters should not be tuned manually or sampled as fully
independent sliders. Instead, users choose an ecology-motivated trade-off preset,
then draw parameter sets from that constrained space.

Research framing:
    Latent costs and benefits were not tuned manually. We defined biologically
    motivated prior ranges and parameter-to-parameter constraints, sampled from
    the resulting constrained trade-off space, and evaluated which causal
    structures and parameter sets could reproduce multiple observed patterns
    simultaneously.

The Japanese manuscript framing is intentionally kept in project documentation
rather than in this source file to avoid encoding problems in deployed apps.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TradeoffPreset:
    """A named set of prior ranges over latent benefit/cost parameters."""

    name: str
    description: str
    ranges: dict[str, tuple[float, float]]
    constraints: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ConstraintResult:
    """Outcome of checking ecological parameter constraints."""

    valid: bool
    failed_constraints: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


def predefined_tradeoff_presets() -> dict[str, TradeoffPreset]:
    """Return ecology-motivated trade-off presets.

    Each preset defines a biologically plausible region of latent parameter
    space. Parameter sets are sampled uniformly within a preset's ranges, then
    filtered by ecological constraints.
    """

    return {
        # ------------------------------------------------------------------
        # 1. Literature-calibrated baseline — PRIMARY ANALYSIS
        # ------------------------------------------------------------------
        "literature_grounded": TradeoffPreset(
            name="literature_grounded",
            description=(
                "Izu Islands Campanula punctata literature-calibrated ranges "
                "(Inoue 1986 field data; Larsson 2005 halictid efficiency; "
                "Darwin 1876 / Charlesworth & Charlesworth 1987 inbreeding). "
                "Use as the primary analysis preset. "
                "Compare with broad_prior to quantify prior sensitivity."
            ),
            ranges={
                "guide_cost":                     (0.02, 0.12),
                "outcrossing_benefit":             (0.30, 0.80),
                "selfing_benefit":                 (0.10, 0.55),
                "inbreeding_depression":           (0.10, 0.50),
                "background_pollinator_efficiency":(0.15, 0.45),
                "drift_strength":                  (0.02, 0.15),
                "direct_pollinator_guide_benefit": (0.25, 0.80),
                "cost_of_waiting_for_pollinators": (0.10, 0.55),
            },
        ),
        # ------------------------------------------------------------------
        # 2. Broad prior — SENSITIVITY / EXPLORATION
        # ------------------------------------------------------------------
        "broad_prior": TradeoffPreset(
            name="broad_prior",
            description=(
                "Maximally wide exploratory ranges covering most biologically "
                "conceivable parameter combinations. Use for sensitivity sweeps "
                "and to confirm that results are not prior-dependent."
            ),
            ranges={
                "guide_cost":                     (0.00, 0.30),
                "outcrossing_benefit":             (0.00, 1.00),
                "selfing_benefit":                 (0.00, 0.80),
                "inbreeding_depression":           (0.00, 0.80),
                "background_pollinator_efficiency":(0.00, 0.70),
                "drift_strength":                  (0.00, 0.25),
                "direct_pollinator_guide_benefit": (0.00, 1.00),
                "cost_of_waiting_for_pollinators": (0.00, 1.00),
            },
        ),
        # ------------------------------------------------------------------
        # 3. Guide–pollinator link (S1 scenario)
        # ------------------------------------------------------------------
        "guide_pollinator_link": TradeoffPreset(
            name="guide_pollinator_link",
            description=(
                "Nectar guides strongly attract Bombus and outcrossing has high "
                "value. Conditions under which guide retention/loss is primarily "
                "driven by Bombus presence (S1: guide_attracts_bombus). "
                "Selfing benefit is low so the selfing-syndrome pathway (S2) "
                "is not independently active."
            ),
            ranges={
                "guide_cost":                     (0.00, 0.10),
                "outcrossing_benefit":             (0.45, 0.90),
                "selfing_benefit":                 (0.00, 0.30),
                "inbreeding_depression":           (0.25, 0.70),
                "background_pollinator_efficiency":(0.10, 0.45),
                "drift_strength":                  (0.00, 0.10),
                "direct_pollinator_guide_benefit": (0.40, 1.00),
                "cost_of_waiting_for_pollinators": (0.00, 0.35),
            },
        ),
        # ------------------------------------------------------------------
        # 4. Reproductive assurance / selfing syndrome (S2 scenario)
        # ------------------------------------------------------------------
        "reproductive_assurance": TradeoffPreset(
            name="reproductive_assurance",
            description=(
                "Pollinator scarcity makes selfing advantageous and triggers "
                "convergent selfing-syndrome evolution (reduced herkogamy, "
                "flower size, guide co-evolved with selfing rate). "
                "Corresponds to S2: selfing_syndrome_active. "
                "Inbreeding depression is moderate-to-low (allows selfing to spread)."
            ),
            ranges={
                "guide_cost":                     (0.03, 0.20),
                "outcrossing_benefit":             (0.10, 0.65),
                "selfing_benefit":                 (0.30, 0.80),
                "inbreeding_depression":           (0.00, 0.40),
                "background_pollinator_efficiency":(0.00, 0.45),
                "drift_strength":                  (0.00, 0.15),
                "direct_pollinator_guide_benefit": (0.00, 0.60),
                "cost_of_waiting_for_pollinators": (0.25, 0.90),
            },
        ),
        # ------------------------------------------------------------------
        # 5. Drift null (S4/S5 scenario)
        # ------------------------------------------------------------------
        "drift_null": TradeoffPreset(
            name="drift_null",
            description=(
                "Genetic drift in small island populations causes stochastic guide "
                "loss without a full selfing syndrome. Directional selection is "
                "weak; drift strength is elevated. "
                "Corresponds to S4: drift_drives_guide_loss (null model). "
                "Use to test whether observed guide loss can be explained without "
                "invoking adaptive mechanisms."
            ),
            ranges={
                "guide_cost":                     (0.00, 0.15),
                "outcrossing_benefit":             (0.00, 0.55),
                "selfing_benefit":                 (0.00, 0.45),
                "inbreeding_depression":           (0.05, 0.55),
                "background_pollinator_efficiency":(0.00, 0.55),
                "drift_strength":                  (0.10, 0.30),
                "direct_pollinator_guide_benefit": (0.00, 0.45),
                "cost_of_waiting_for_pollinators": (0.00, 0.50),
            },
        ),
    }


def sample_parameters_from_preset(
    preset: TradeoffPreset,
    rng: random.Random,
) -> dict[str, float]:
    """Draw one parameter set uniformly from a preset's prior ranges."""

    return {name: rng.uniform(lo, hi) for name, (lo, hi) in preset.ranges.items()}


def check_ecological_parameter_constraints(
    params: dict[str, float],
    preset_name: str | None = None,
) -> ConstraintResult:
    """Check a parameter set against provisional ecological constraints.

    Hard rejection constraints:
    - C1: selfing_benefit - inbreeding_depression >= -0.30
    - C2: avoid simultaneous high small-pollinator efficiency and extreme selfing benefit
    - C3: avoid high guide cost + no outcrossing benefit + extreme guide benefit
    """

    guide_cost = params.get("guide_cost", 0.0)
    outcrossing_benefit = params.get("outcrossing_benefit", 0.0)
    selfing_benefit = params.get("selfing_benefit", 0.0)
    inbreeding_depression = params.get("inbreeding_depression", 0.0)
    background_pollinator_efficiency = params.get("background_pollinator_efficiency", 0.0)
    direct_pollinator_guide_benefit = params.get("direct_pollinator_guide_benefit", 0.0)

    failed: list[str] = []
    notes: list[str] = []

    if selfing_benefit - inbreeding_depression < -0.30:
        failed.append("C1_selfing_net_fitness")
        notes.append(
            "C1: selfing_benefit - inbreeding_depression is below -0.30; "
            "strong selfing evolution is unlikely under such inbreeding cost."
        )

    # C2 — threshold unified with parameter_constraints.py (sb > 0.55).
    # Ecological rationale: if background pollinators adequately substitute
    # for primary pollinators, reproductive-assurance selfing pressure is
    # relieved, so simultaneously high background_pollinator_efficiency AND
    # high selfing_benefit is ecologically inconsistent.
    if background_pollinator_efficiency > 0.55 and selfing_benefit > 0.55:
        failed.append("C2_small_pollinator_vs_selfing_benefit")
        notes.append(
            "C2: background_pollinator_efficiency > 0.55 AND selfing_benefit > 0.55 — "
            "high outcrossing substitute and high selfing advantage cannot both be "
            "extreme simultaneously (reproductive-assurance logic)."
        )

    if (
        guide_cost > 0.25
        and outcrossing_benefit < 0.05
        and direct_pollinator_guide_benefit > 0.80
    ):
        failed.append("C3_guide_cost_benefit_inconsistency")
        notes.append(
            "C3: high guide cost, near-zero outcrossing benefit, and extreme direct "
            "guide benefit form an internally inconsistent combination."
        )

    # C4 — background efficiency must be below primary efficiency (0.80).
    # Unified with parameter_constraints.py. Larsson 2005: halictid per-visit
    # efficiency 20-55% of Bombus. Values >= 0.80 collapse the guild distinction.
    if background_pollinator_efficiency >= 0.80:
        failed.append("C4_background_efficiency_exceeds_primary")
        notes.append(
            "C4: background_pollinator_efficiency >= 0.80 (primary efficiency default) "
            "— functional distinction between pollinator guilds collapses."
        )

    return ConstraintResult(
        valid=len(failed) == 0,
        failed_constraints=tuple(failed),
        notes="; ".join(notes),
    )


def classify_tradeoffs(params: dict[str, float]) -> dict[str, float | str]:
    """Compute informational guide/selfing net-benefit classifications."""

    guide_net_benefit = (
        params.get("outcrossing_benefit", 0.0)
        + params.get("direct_pollinator_guide_benefit", 0.0)
        - params.get("guide_cost", 0.0)
    )
    if guide_net_benefit > 0.40:
        guide_class = "guide_favorable"
    elif guide_net_benefit >= 0.00:
        guide_class = "guide_intermediate"
    else:
        guide_class = "guide_unfavorable"

    selfing_net_benefit = (
        params.get("selfing_benefit", 0.0)
        + params.get("cost_of_waiting_for_pollinators", 0.0)
        - params.get("inbreeding_depression", 0.0)
    )
    if selfing_net_benefit > 0.30:
        selfing_class = "selfing_favorable"
    elif selfing_net_benefit >= -0.10:
        selfing_class = "selfing_intermediate"
    else:
        selfing_class = "selfing_unfavorable"

    return {
        "guide_net_benefit": round(guide_net_benefit, 4),
        "guide_tradeoff_class": guide_class,
        "selfing_net_benefit": round(selfing_net_benefit, 4),
        "selfing_tradeoff_class": selfing_class,
    }


# Backward-compatible private alias used by older draft code.
_classify_tradeoffs = classify_tradeoffs


def _annotate_parameter_set(
    params: dict[str, float],
    preset_name: str,
    check: ConstraintResult,
) -> dict[str, Any]:
    """Return one sampled parameter row with metadata and trade-off annotations."""

    return {
        "parameter_set_id": str(uuid.uuid4()),
        "preset_name": preset_name,
        **params,
        **classify_tradeoffs(params),
        "valid": check.valid,
        "failed_constraints": "; ".join(check.failed_constraints),
        "constraint_notes": check.notes,
    }


def sample_valid_parameter_sets(
    preset: TradeoffPreset,
    n: int,
    seed: int | None = None,
    max_attempts: int | None = None,
) -> list[dict[str, Any]]:
    """Draw n valid parameter sets from a preset under ecological constraints."""

    rng = random.Random(seed)
    limit = max_attempts if max_attempts is not None else 50 * n
    results: list[dict[str, Any]] = []
    attempts = 0

    while len(results) < n and attempts < limit:
        attempts += 1
        params = sample_parameters_from_preset(preset, rng)
        check = check_ecological_parameter_constraints(params, preset.name)
        if check.valid:
            results.append(_annotate_parameter_set(params, preset.name, check))

    return results


def sample_with_rejection_log(
    preset: TradeoffPreset,
    n_attempts: int,
    seed: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Draw n_attempts sets and return accepted/rejected rows with annotations."""

    rng = random.Random(seed)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for _ in range(n_attempts):
        params = sample_parameters_from_preset(preset, rng)
        check = check_ecological_parameter_constraints(params, preset.name)
        row = _annotate_parameter_set(params, preset.name, check)
        if check.valid:
            accepted.append(row)
        else:
            rejected.append(row)

    return accepted, rejected


# Backward-compatible public alias used in streamlit_app and older notes.
sample_all_sets_with_rejection_log = sample_with_rejection_log


def param_set_to_model_parameters(param_set: dict[str, float]):
    """Convert a sampled latent parameter dict to ModelParameters.

    Mapping:
    - guide_cost -> ModelParameters.guide_cost
    - outcrossing_benefit -> ModelParameters.outcrossing_benefit
    - selfing_benefit -> ModelParameters.selfing_benefit
    - inbreeding_depression -> ModelParameters.inbreeding_depression
    - background_pollinator_efficiency -> ModelParameters.background_pollinator_efficiency
    - drift_strength -> ModelParameters.base_drift_strength
    - direct_pollinator_guide_benefit -> ModelParameters.primary_pollinator_guide_response
    - cost_of_waiting_for_pollinators -> added weakly to effective selfing benefit
    """

    from attraction_trait_model.parameters import ModelParameters

    selfing_benefit_raw = float(param_set.get("selfing_benefit", 0.1))
    cost_of_waiting = float(param_set.get("cost_of_waiting_for_pollinators", 0.1))
    effective_selfing_benefit = min(1.0, selfing_benefit_raw + cost_of_waiting * 0.4)

    return ModelParameters(
        guide_cost=float(param_set.get("guide_cost", 0.05)),
        outcrossing_benefit=float(param_set.get("outcrossing_benefit", 0.2)),
        selfing_benefit=effective_selfing_benefit,
        inbreeding_depression=float(param_set.get("inbreeding_depression", 0.2)),
        background_pollinator_efficiency=float(param_set.get("background_pollinator_efficiency", 0.3)),
        base_drift_strength=float(param_set.get("drift_strength", 0.05)),
        primary_pollinator_guide_response=float(param_set.get("direct_pollinator_guide_benefit", 0.6)),
    )
