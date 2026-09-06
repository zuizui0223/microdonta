"""Prototype reporting layer that turns MROD limitations into explicit actions.

This module does not define a new scientific score. It composes quantities that
MROD already reports: current mechanism entropy, whether candidate observation
values are estimable, whether any candidate has positive mechanism information,
and whether the identity of the best candidate is stable across a declared
specification set.

The result deliberately preserves several axes instead of collapsing every
limitation into one number. Stability labels are descriptive sensitivity labels,
not robust-design objectives.
"""
from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class SpecificationStatus:
    name: str
    current_entropy_bits: float
    mechanism_status: str
    candidate_status: str
    best_candidates: tuple[str, ...]
    max_information_value: float | None
    estimable_candidates: tuple[str, ...]
    nonestimable_candidates: tuple[str, ...]
    recommended_action: str


@dataclass(frozen=True)
class LimitationActionReport:
    per_specification: tuple[SpecificationStatus, ...]
    resolution_stability: str
    actionability_stability: str
    recommendation_stability: str
    common_best_candidates: tuple[str, ...]


def _candidate_score_from_object(item) -> CandidateScore:
    """Adapt publication result objects or explicit CandidateScore records."""
    if isinstance(item, CandidateScore):
        return item
    return CandidateScore(
        candidate=str(getattr(item, "candidate")),
        estimable=bool(getattr(item, "estimable")),
        information_value=(
            None
            if getattr(item, "information_value", None) is None
            else float(getattr(item, "information_value"))
        ),
    )


def classify_specification(
    spec: SpecificationInput,
    *,
    entropy_tol: float = 0.0,
    value_tol: float = 0.0,
) -> SpecificationStatus:
    """Classify one declared current-state specification without hiding why it stops."""
    if entropy_tol < 0 or value_tol < 0:
        raise ValueError("tolerances must be non-negative")

    candidates = tuple(_candidate_score_from_object(item) for item in spec.candidates)
    estimable = tuple(item for item in candidates if item.estimable)
    nonestimable = tuple(item for item in candidates if not item.estimable)

    if spec.current_entropy_bits <= entropy_tol:
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            mechanism_status="resolved",
            candidate_status="not_required",
            best_candidates=(),
            max_information_value=None,
            estimable_candidates=tuple(item.candidate for item in estimable),
            nonestimable_candidates=tuple(item.candidate for item in nonestimable),
            recommended_action="stop_resolved",
        )

    if not spec.budget_remaining:
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            mechanism_status="unresolved",
            candidate_status="budget_limited",
            best_candidates=(),
            max_information_value=None,
            estimable_candidates=tuple(item.candidate for item in estimable),
            nonestimable_candidates=tuple(item.candidate for item in nonestimable),
            recommended_action="report_budget_limit",
        )

    if not candidates:
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            mechanism_status="unresolved",
            candidate_status="candidate_limited",
            best_candidates=(),
            max_information_value=None,
            estimable_candidates=(),
            nonestimable_candidates=(),
            recommended_action="expand_candidate_vocabulary",
        )

    if not estimable:
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            mechanism_status="unresolved",
            candidate_status="prediction_limited",
            best_candidates=(),
            max_information_value=None,
            estimable_candidates=(),
            nonestimable_candidates=tuple(item.candidate for item in nonestimable),
            recommended_action="identify_candidate_outcome_models",
        )

    values = {
        item.candidate: float(item.information_value or 0.0)
        for item in estimable
    }
    maximum = max(values.values())
    if maximum <= value_tol:
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            mechanism_status="unresolved",
            candidate_status="information_limited",
            best_candidates=(),
            max_information_value=maximum,
            estimable_candidates=tuple(item.candidate for item in estimable),
            nonestimable_candidates=tuple(item.candidate for item in nonestimable),
            recommended_action="report_information_limit",
        )

    best = tuple(
        sorted(
            name
            for name, value in values.items()
            if abs(value - maximum) <= 1e-12
        )
    )
    return SpecificationStatus(
        name=spec.name,
        current_entropy_bits=spec.current_entropy_bits,
        mechanism_status="unresolved",
        candidate_status="actionable",
        best_candidates=best,
        max_information_value=maximum,
        estimable_candidates=tuple(item.candidate for item in estimable),
        nonestimable_candidates=tuple(item.candidate for item in nonestimable),
        recommended_action="measure_best_candidate",
    )


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
        classify_specification(
            spec, entropy_tol=entropy_tol, value_tol=value_tol
        )
        for spec in specifications
    )

    resolved_flags = {status.mechanism_status == "resolved" for status in statuses}
    if resolved_flags == {True}:
        resolution_stability = "stable_resolved"
    elif resolved_flags == {False}:
        resolution_stability = "stable_unresolved"
    else:
        resolution_stability = "specification_sensitive"

    unresolved = [status for status in statuses if status.mechanism_status == "unresolved"]
    actionable_flags = {
        status.candidate_status == "actionable" for status in unresolved
    }
    if not actionable_flags:
        actionability_stability = "not_required"
    elif actionable_flags == {True}:
        actionability_stability = "stable_actionable"
    elif actionable_flags == {False}:
        actionability_stability = "stable_not_actionable"
    else:
        actionability_stability = "specification_sensitive"

    actionable = [
        status for status in statuses if status.candidate_status == "actionable"
    ]
    common: set[str] = (
        set(actionable[0].best_candidates) if actionable else set()
    )
    for status in actionable[1:]:
        common &= set(status.best_candidates)

    if not actionable:
        recommendation_stability = "not_available"
    elif len(actionable) != len(unresolved):
        recommendation_stability = "specification_sensitive_actionability"
    elif common:
        recommendation_stability = "stable_common_best"
    else:
        recommendation_stability = "specification_sensitive_ranking"

    return LimitationActionReport(
        per_specification=statuses,
        resolution_stability=resolution_stability,
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
