"""Prototype reporting layer that turns MROD limitations into explicit actions.

This module does not define a new scientific score. It composes quantities that
MROD already reports and deliberately keeps several axes separate:

* concentration of the full declared mechanism vector;
* completion of a narrower predeclared design target, such as a confounding graph;
* validated candidate-information estimability and actionability;
* observation budget;
* stability of those statements across a declared specification set.

The result is an internal reporting prototype, not a robust-design objective and
not a replacement for the publication-level observation-selection algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class CandidateScore:
    candidate: str
    estimable: bool
    information_value: float | None


@dataclass(frozen=True)
class SpecificationInput:
    name: str
    current_entropy_bits: float
    candidates: tuple[CandidateScore, ...]
    budget_remaining: bool = True
    # Optional narrower stopping target supplied by the analysis, e.g. whether
    # the predeclared confounding graph has been resolved. ``None`` means that
    # only full mechanism-vector resolution (D=0 within tolerance) counts as
    # target resolution for this prototype.
    declared_target_resolved: bool | None = None


@dataclass(frozen=True)
class SpecificationStatus:
    name: str
    current_entropy_bits: float
    full_mechanism_status: str
    declared_target_status: str
    candidate_status: str
    best_candidates: tuple[str, ...]
    max_information_value: float | None
    estimable_candidates: tuple[str, ...]
    nonestimable_candidates: tuple[str, ...]
    recommended_action: str


@dataclass(frozen=True)
class LimitationActionReport:
    per_specification: tuple[SpecificationStatus, ...]
    full_resolution_stability: str
    target_resolution_stability: str
    actionability_stability: str
    recommendation_stability: str
    common_best_candidates: tuple[str, ...]


def _candidate_score_from_object(item) -> CandidateScore:
    """Adapt publication result objects or explicit CandidateScore records."""
    if isinstance(item, CandidateScore):
        return item
    value = getattr(item, "information_value", None)
    return CandidateScore(
        candidate=str(getattr(item, "candidate")),
        estimable=bool(getattr(item, "estimable")),
        information_value=None if value is None else float(value),
    )


def _status(
    spec: SpecificationInput,
    *,
    full_mechanism_status: str,
    declared_target_status: str,
    candidate_status: str,
    best_candidates: tuple[str, ...] = (),
    max_information_value: float | None = None,
    estimable: tuple[CandidateScore, ...] = (),
    nonestimable: tuple[CandidateScore, ...] = (),
    recommended_action: str,
) -> SpecificationStatus:
    return SpecificationStatus(
        name=spec.name,
        current_entropy_bits=spec.current_entropy_bits,
        full_mechanism_status=full_mechanism_status,
        declared_target_status=declared_target_status,
        candidate_status=candidate_status,
        best_candidates=best_candidates,
        max_information_value=max_information_value,
        estimable_candidates=tuple(item.candidate for item in estimable),
        nonestimable_candidates=tuple(item.candidate for item in nonestimable),
        recommended_action=recommended_action,
    )


def classify_specification(
    spec: SpecificationInput,
    *,
    entropy_tol: float = 0.0,
    value_tol: float = 0.0,
) -> SpecificationStatus:
    """Classify one declared current-state specification without hiding why it stops.

    ``full_mechanism_status`` and ``declared_target_status`` are intentionally
    different. A sequential benchmark may resolve a predeclared confounding
    graph while residual entropy in other mechanism dimensions remains positive.

    Candidate actionability is based only on validated information values. An
    explicit compatibility fallback can be reported elsewhere, but it does not
    convert non-estimable mutual information into validated actionability.
    """
    if entropy_tol < 0 or value_tol < 0:
        raise ValueError("tolerances must be non-negative")

    candidates = tuple(_candidate_score_from_object(item) for item in spec.candidates)
    estimable = tuple(item for item in candidates if item.estimable)
    nonestimable = tuple(item for item in candidates if not item.estimable)

    if not math.isfinite(spec.current_entropy_bits) or spec.current_entropy_bits < 0:
        return _status(
            spec,
            full_mechanism_status="nonestimable",
            declared_target_status="nonestimable",
            candidate_status="current_state_nonestimable",
            estimable=estimable,
            nonestimable=nonestimable,
            recommended_action="repair_or_reestimate_current_admissible_region",
        )

    fully_resolved = spec.current_entropy_bits <= entropy_tol
    full_mechanism_status = "fully_resolved" if fully_resolved else "ambiguous"

    # Full mechanism resolution necessarily satisfies any narrower target. When
    # ambiguity remains, the caller may still declare a narrower target resolved.
    target_resolved = fully_resolved or bool(spec.declared_target_resolved)
    declared_target_status = "resolved" if target_resolved else "unresolved"

    if target_resolved:
        action = (
            "stop_fully_resolved"
            if fully_resolved
            else "stop_declared_target_resolved_report_residual_ambiguity"
        )
        return _status(
            spec,
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            candidate_status="not_required",
            estimable=estimable,
            nonestimable=nonestimable,
            recommended_action=action,
        )

    if not spec.budget_remaining:
        return _status(
            spec,
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            candidate_status="budget_limited",
            estimable=estimable,
            nonestimable=nonestimable,
            recommended_action="report_budget_limit",
        )

    if not candidates:
        return _status(
            spec,
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            candidate_status="candidate_limited",
            recommended_action="expand_candidate_vocabulary",
        )

    if not estimable:
        return _status(
            spec,
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            candidate_status="prediction_limited",
            nonestimable=nonestimable,
            recommended_action="identify_candidate_outcome_models",
        )

    values = {
        item.candidate: float(item.information_value or 0.0)
        for item in estimable
    }
    maximum = max(values.values())
    best_verified = tuple(
        sorted(
            name
            for name, value in values.items()
            if abs(value - maximum) <= 1e-12
        )
    )

    if nonestimable:
        return _status(
            spec,
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            candidate_status="partial_prediction_limited",
            best_candidates=best_verified if maximum > value_tol else (),
            max_information_value=maximum,
            estimable=estimable,
            nonestimable=nonestimable,
            recommended_action="resolve_nonestimable_candidates_before_global_ranking",
        )

    if maximum <= value_tol:
        return _status(
            spec,
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            candidate_status="information_limited",
            max_information_value=maximum,
            estimable=estimable,
            recommended_action="report_information_limit",
        )

    return _status(
        spec,
        full_mechanism_status=full_mechanism_status,
        declared_target_status=declared_target_status,
        candidate_status="actionable",
        best_candidates=best_verified,
        max_information_value=maximum,
        estimable=estimable,
        recommended_action="measure_best_candidate",
    )


def _stability_label(values: set[str], *, prefix: str) -> str:
    if len(values) == 1:
        return f"stable_{prefix}_{next(iter(values))}"
    return "specification_sensitive"


def build_limitation_action_report(
    specifications: Sequence[SpecificationInput],
    *,
    entropy_tol: float = 0.0,
    value_tol: float = 0.0,
) -> LimitationActionReport:
    """Return orthogonal limitation and action states across declared specifications."""
    if not specifications:
        raise ValueError("at least one specification is required")

    statuses = tuple(
        classify_specification(spec, entropy_tol=entropy_tol, value_tol=value_tol)
        for spec in specifications
    )

    full_resolution_stability = _stability_label(
        {status.full_mechanism_status for status in statuses}, prefix="mechanism"
    )
    target_resolution_stability = _stability_label(
        {status.declared_target_status for status in statuses}, prefix="target"
    )

    unresolved = [
        status for status in statuses if status.declared_target_status == "unresolved"
    ]
    actionable_flags = {
        status.candidate_status == "actionable" for status in unresolved
    }
    if not unresolved:
        actionability_stability = "not_required"
    elif actionable_flags == {True}:
        actionability_stability = "stable_actionable"
    elif actionable_flags == {False}:
        actionability_stability = "stable_not_actionable"
    else:
        actionability_stability = "specification_sensitive"

    actionable = [status for status in unresolved if status.candidate_status == "actionable"]
    common: set[str] = set(actionable[0].best_candidates) if actionable else set()
    for status in actionable[1:]:
        common &= set(status.best_candidates)

    if not unresolved or not actionable:
        recommendation_stability = "not_available"
    elif len(actionable) != len(unresolved):
        recommendation_stability = "specification_sensitive_actionability"
    elif common:
        recommendation_stability = "stable_common_best"
    else:
        recommendation_stability = "specification_sensitive_ranking"

    return LimitationActionReport(
        per_specification=statuses,
        full_resolution_stability=full_resolution_stability,
        target_resolution_stability=target_resolution_stability,
        actionability_stability=actionability_stability,
        recommendation_stability=recommendation_stability,
        common_best_candidates=tuple(sorted(common)),
    )


__all__ = [
    "CandidateScore",
    "SpecificationInput",
    "SpecificationStatus",
    "LimitationActionReport",
    "classify_specification",
    "build_limitation_action_report",
]
