"""Prototype reporting layer that turns MROD limitations into explicit actions.

No new scientific score is defined here. The module composes existing MROD
quantities into orthogonal reporting axes so that different reasons for stopping
or continuing are not collapsed into one generic limitation label.

The axes distinguish:

* whether the current mechanism-information state is estimable;
* full mechanism-vector ambiguity versus a narrower declared design target;
* observation budget;
* coverage of the declared candidate vocabulary by validated predictive models;
* whether any single candidate has positive immediate mechanism information;
* whether joint/bundle information has been audited when all singleton values are zero;
* whether a global best single candidate is identified;
* stability of those statements over a declared specification set.

Compatibility fallbacks are outside the validated-information axis and must remain
separately labelled.  Likewise, zero immediate information for every singleton
candidate is a one-step greedy stopping condition, not by itself a proof that
candidate combinations contain no mechanism information.
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
    declared_target_resolved: bool | None = None
    joint_candidate_information_value: float | None = None


@dataclass(frozen=True)
class SpecificationStatus:
    name: str
    current_entropy_bits: float
    current_state_status: str
    full_mechanism_status: str
    declared_target_status: str
    budget_status: str
    candidate_coverage: str
    validated_information_status: str
    joint_information_status: str
    recommendation_status: str
    best_candidates: tuple[str, ...]
    max_information_value: float | None
    estimable_candidates: tuple[str, ...]
    nonestimable_candidates: tuple[str, ...]
    recommended_actions: tuple[str, ...]


@dataclass(frozen=True)
class LimitationActionReport:
    per_specification: tuple[SpecificationStatus, ...]
    full_resolution_stability: str
    target_resolution_stability: str
    validated_actionability_stability: str
    recommendation_stability: str
    common_best_candidates: tuple[str, ...]


def _candidate_score_from_object(item) -> CandidateScore:
    if isinstance(item, CandidateScore):
        return item
    value = getattr(item, "information_value", None)
    return CandidateScore(
        candidate=str(getattr(item, "candidate")),
        estimable=bool(getattr(item, "estimable")),
        information_value=None if value is None else float(value),
    )


def _joint_information_status(value: float | None, *, value_tol: float) -> str:
    if value is None:
        return "not_audited"
    if not math.isfinite(value) or value < 0:
        raise ValueError("joint_candidate_information_value must be finite and non-negative")
    return "positive" if value > value_tol else "zero"


def classify_specification(
    spec: SpecificationInput,
    *,
    entropy_tol: float = 0.0,
    value_tol: float = 0.0,
) -> SpecificationStatus:
    """Return orthogonal status axes for one declared specification."""
    if entropy_tol < 0 or value_tol < 0:
        raise ValueError("tolerances must be non-negative")

    candidates = tuple(_candidate_score_from_object(item) for item in spec.candidates)
    names = [item.candidate for item in candidates]
    if len(names) != len(set(names)):
        raise ValueError("candidate names must be unique")
    for item in candidates:
        if item.estimable:
            if item.information_value is None:
                raise ValueError(f"estimable candidate {item.candidate!r} has no information value")
            if not math.isfinite(float(item.information_value)) or float(item.information_value) < 0:
                raise ValueError("estimable candidate information values must be finite and non-negative")

    estimable = tuple(item for item in candidates if item.estimable)
    nonestimable = tuple(item for item in candidates if not item.estimable)
    estimable_names = tuple(item.candidate for item in estimable)
    nonestimable_names = tuple(item.candidate for item in nonestimable)
    budget_status = "available" if spec.budget_remaining else "exhausted"

    if not math.isfinite(spec.current_entropy_bits) or spec.current_entropy_bits < 0:
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            current_state_status="nonestimable",
            full_mechanism_status="nonestimable",
            declared_target_status="nonestimable",
            budget_status=budget_status,
            candidate_coverage="not_evaluable",
            validated_information_status="not_evaluable",
            joint_information_status="not_evaluable",
            recommendation_status="not_evaluable",
            best_candidates=(),
            max_information_value=None,
            estimable_candidates=estimable_names,
            nonestimable_candidates=nonestimable_names,
            recommended_actions=("repair_or_reestimate_current_admissible_region",),
        )

    fully_resolved = spec.current_entropy_bits <= entropy_tol
    full_mechanism_status = "fully_resolved" if fully_resolved else "ambiguous"
    target_resolved = fully_resolved or bool(spec.declared_target_resolved)
    declared_target_status = "resolved" if target_resolved else "unresolved"

    if target_resolved:
        action = (
            "stop_fully_resolved"
            if fully_resolved
            else "stop_declared_target_resolved_report_residual_ambiguity"
        )
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            current_state_status="estimable",
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            budget_status=budget_status,
            candidate_coverage="not_required",
            validated_information_status="not_required",
            joint_information_status="not_required",
            recommendation_status="not_required",
            best_candidates=(),
            max_information_value=None,
            estimable_candidates=estimable_names,
            nonestimable_candidates=nonestimable_names,
            recommended_actions=(action,),
        )

    actions: list[str] = []
    if budget_status == "exhausted":
        actions.append("report_budget_limit")

    if not candidates:
        actions.append("expand_candidate_vocabulary")
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            current_state_status="estimable",
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            budget_status=budget_status,
            candidate_coverage="none_declared",
            validated_information_status="not_available",
            joint_information_status="not_available",
            recommendation_status="unavailable",
            best_candidates=(),
            max_information_value=None,
            estimable_candidates=(),
            nonestimable_candidates=(),
            recommended_actions=tuple(actions),
        )

    if not estimable:
        actions.append("identify_candidate_outcome_models")
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            current_state_status="estimable",
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            budget_status=budget_status,
            candidate_coverage="none_estimable",
            validated_information_status="nonestimable",
            joint_information_status="not_evaluable",
            recommendation_status="unavailable",
            best_candidates=(),
            max_information_value=None,
            estimable_candidates=(),
            nonestimable_candidates=nonestimable_names,
            recommended_actions=tuple(actions),
        )

    values = {item.candidate: float(item.information_value) for item in estimable}
    maximum = max(values.values())
    best_verified = tuple(
        sorted(
            name
            for name, value in values.items()
            if abs(value - maximum) <= 1e-12
        )
    )
    information_status = "positive" if maximum > value_tol else "zero"

    if nonestimable:
        actions.append("resolve_nonestimable_candidates_before_global_ranking")
        if information_status == "positive":
            actions.append("report_provisional_best_among_estimable_candidates")
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            current_state_status="estimable",
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            budget_status=budget_status,
            candidate_coverage="partial",
            validated_information_status=information_status,
            joint_information_status="not_evaluable",
            recommendation_status=(
                "provisional_best_among_estimable"
                if information_status == "positive"
                else "unavailable"
            ),
            best_candidates=best_verified if information_status == "positive" else (),
            max_information_value=maximum,
            estimable_candidates=estimable_names,
            nonestimable_candidates=nonestimable_names,
            recommended_actions=tuple(actions),
        )

    joint_status = _joint_information_status(
        spec.joint_candidate_information_value,
        value_tol=value_tol,
    )
    if spec.joint_candidate_information_value is not None:
        if float(spec.joint_candidate_information_value) + 1e-12 < maximum:
            raise ValueError("joint candidate information cannot be below a singleton information value")

    if information_status == "zero":
        if joint_status == "not_audited":
            actions.extend(
                (
                    "report_zero_singleton_values",
                    "audit_joint_candidate_information_before_sequence_limit",
                )
            )
            recommendation_status = "unavailable"
        elif joint_status == "zero":
            actions.extend(
                (
                    "report_sequence_information_limit",
                    "redesign_or_expand_measurement_vocabulary",
                )
            )
            recommendation_status = "unavailable"
        else:
            actions.extend(
                (
                    "report_joint_information_despite_zero_singletons",
                    "use_nonmyopic_bundle_or_sequence_design",
                )
            )
            recommendation_status = "nonmyopic_bundle_required"
        return SpecificationStatus(
            name=spec.name,
            current_entropy_bits=spec.current_entropy_bits,
            current_state_status="estimable",
            full_mechanism_status=full_mechanism_status,
            declared_target_status=declared_target_status,
            budget_status=budget_status,
            candidate_coverage="complete",
            validated_information_status="zero",
            joint_information_status=joint_status,
            recommendation_status=recommendation_status,
            best_candidates=(),
            max_information_value=maximum,
            estimable_candidates=estimable_names,
            nonestimable_candidates=(),
            recommended_actions=tuple(actions),
        )

    if budget_status == "available":
        actions.append("measure_best_candidate")
    else:
        actions.append("retain_best_candidate_for_future_budget")
    return SpecificationStatus(
        name=spec.name,
        current_entropy_bits=spec.current_entropy_bits,
        current_state_status="estimable",
        full_mechanism_status=full_mechanism_status,
        declared_target_status=declared_target_status,
        budget_status=budget_status,
        candidate_coverage="complete",
        validated_information_status="positive",
        joint_information_status=joint_status,
        recommendation_status="validated_best",
        best_candidates=best_verified,
        max_information_value=maximum,
        estimable_candidates=estimable_names,
        nonestimable_candidates=(),
        recommended_actions=tuple(actions),
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
    """Combine single-specification axes without replacing them by one score."""
    if not specifications:
        raise ValueError("at least one specification is required")

    statuses = tuple(
        classify_specification(spec, entropy_tol=entropy_tol, value_tol=value_tol)
        for spec in specifications
    )

    full_resolution_stability = _stability_label(
        {status.full_mechanism_status for status in statuses}, prefix="mechanism"
    )
    target_states = {status.declared_target_status for status in statuses}
    target_resolution_stability = _stability_label(target_states, prefix="target")

    # Recommendation comparison is downstream of the target state itself. Do not
    # ignore specifications in which the target is resolved or non-estimable.
    if target_states == {"resolved"}:
        validated_actionability_stability = "not_required"
        recommendation_stability = "not_available"
        common: set[str] = set()
    elif target_states == {"nonestimable"}:
        validated_actionability_stability = "not_evaluable"
        recommendation_stability = "not_evaluable"
        common = set()
    elif target_states != {"unresolved"}:
        validated_actionability_stability = "specification_sensitive_target_state"
        recommendation_stability = "specification_sensitive_target_state"
        common = set()
    else:
        unresolved = list(statuses)
        # This axis intentionally describes the current positive-singleton greedy
        # policy. A zero-singleton/joint-positive specification can be sequence-
        # actionable while still not being one-step actionable.
        fully_actionable = [
            status
            for status in unresolved
            if status.candidate_coverage == "complete"
            and status.validated_information_status == "positive"
        ]

        if len(fully_actionable) == len(unresolved):
            validated_actionability_stability = "stable_actionable"
        elif not fully_actionable:
            validated_actionability_stability = "stable_not_fully_actionable"
        else:
            validated_actionability_stability = "specification_sensitive"

        common = set(fully_actionable[0].best_candidates) if fully_actionable else set()
        for status in fully_actionable[1:]:
            common &= set(status.best_candidates)

        if not fully_actionable:
            recommendation_stability = "not_available"
        elif len(fully_actionable) != len(unresolved):
            recommendation_stability = "specification_sensitive_actionability"
        elif common:
            recommendation_stability = "stable_common_best"
        else:
            recommendation_stability = "specification_sensitive_ranking"

    return LimitationActionReport(
        per_specification=statuses,
        full_resolution_stability=full_resolution_stability,
        target_resolution_stability=target_resolution_stability,
        validated_actionability_stability=validated_actionability_stability,
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
