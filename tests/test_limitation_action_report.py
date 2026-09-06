"""Tests for the prototype limitation-to-action reporting layer."""
from __future__ import annotations

from math import nan

from causal_model.limitation_action_report import (
    CandidateScore,
    SpecificationInput,
    build_limitation_action_report,
    classify_specification,
)


def score(name: str, value: float | None, estimable: bool = True) -> CandidateScore:
    return CandidateScore(candidate=name, estimable=estimable, information_value=value)


def test_full_resolution_stops_without_forcing_candidate_choice():
    status = classify_specification(
        SpecificationInput("base", 0.0, (score("Q1", 0.5),))
    )
    assert status.current_state_status == "estimable"
    assert status.full_mechanism_status == "fully_resolved"
    assert status.declared_target_status == "resolved"
    assert status.candidate_coverage == "not_required"
    assert status.recommendation_status == "not_required"
    assert status.recommended_actions == ("stop_fully_resolved",)


def test_declared_target_can_be_resolved_while_full_entropy_remains():
    status = classify_specification(
        SpecificationInput(
            "graph_done",
            1.2,
            (score("Q1", 0.3),),
            declared_target_resolved=True,
        )
    )
    assert status.full_mechanism_status == "ambiguous"
    assert status.declared_target_status == "resolved"
    assert status.candidate_coverage == "not_required"
    assert status.recommended_actions == (
        "stop_declared_target_resolved_report_residual_ambiguity",
    )


def test_nonestimable_current_state_is_a_separate_axis():
    status = classify_specification(
        SpecificationInput("empty_region", nan, (score("Q1", 0.0),))
    )
    assert status.current_state_status == "nonestimable"
    assert status.full_mechanism_status == "nonestimable"
    assert status.declared_target_status == "nonestimable"
    assert status.candidate_coverage == "not_evaluable"
    assert status.validated_information_status == "not_evaluable"
    assert status.recommended_actions == ("repair_or_reestimate_current_admissible_region",)


def test_complete_positive_candidate_set_is_validated_actionable():
    status = classify_specification(
        SpecificationInput("base", 1.0, (score("Q1", 0.3), score("Q2", 0.1)))
    )
    assert status.declared_target_status == "unresolved"
    assert status.budget_status == "available"
    assert status.candidate_coverage == "complete"
    assert status.validated_information_status == "positive"
    assert status.recommendation_status == "validated_best"
    assert status.best_candidates == ("Q1",)
    assert status.recommended_actions == ("measure_best_candidate",)


def test_budget_exhaustion_does_not_erase_known_best_candidate():
    status = classify_specification(
        SpecificationInput(
            "base", 1.0, (score("Q1", 0.4), score("Q2", 0.1)), budget_remaining=False
        )
    )
    assert status.budget_status == "exhausted"
    assert status.validated_information_status == "positive"
    assert status.recommendation_status == "validated_best"
    assert status.best_candidates == ("Q1",)
    assert status.recommended_actions == (
        "report_budget_limit",
        "retain_best_candidate_for_future_budget",
    )


def test_information_limit_requires_complete_estimability():
    status = classify_specification(
        SpecificationInput("base", 1.0, (score("Q1", 0.0), score("Q2", 0.0)))
    )
    assert status.candidate_coverage == "complete"
    assert status.validated_information_status == "zero"
    assert status.recommendation_status == "unavailable"
    assert status.recommended_actions == (
        "report_information_limit",
        "redesign_or_expand_measurement_vocabulary",
    )


def test_no_estimable_candidate_is_prediction_limited():
    status = classify_specification(
        SpecificationInput(
            "base",
            1.0,
            (score("Q1", None, estimable=False), score("Q2", None, estimable=False)),
        )
    )
    assert status.candidate_coverage == "none_estimable"
    assert status.validated_information_status == "nonestimable"
    assert status.recommendation_status == "unavailable"
    assert status.nonestimable_candidates == ("Q1", "Q2")
    assert status.recommended_actions == ("identify_candidate_outcome_models",)


def test_partial_zero_information_does_not_license_information_limit():
    status = classify_specification(
        SpecificationInput(
            "base",
            1.0,
            (score("Q1", 0.0), score("Q2", None, estimable=False)),
        )
    )
    assert status.candidate_coverage == "partial"
    assert status.validated_information_status == "zero"
    assert status.recommendation_status == "unavailable"
    assert status.recommended_actions == (
        "resolve_nonestimable_candidates_before_global_ranking",
    )


def test_partial_positive_information_is_only_provisional():
    status = classify_specification(
        SpecificationInput(
            "base",
            1.0,
            (score("Q1", 0.4), score("Q2", None, estimable=False)),
        )
    )
    assert status.candidate_coverage == "partial"
    assert status.validated_information_status == "positive"
    assert status.recommendation_status == "provisional_best_among_estimable"
    assert status.best_candidates == ("Q1",)
    assert status.recommended_actions == (
        "resolve_nonestimable_candidates_before_global_ranking",
        "report_provisional_best_among_estimable_candidates",
    )


def test_no_candidate_vocabulary_is_separate_from_zero_information():
    status = classify_specification(SpecificationInput("base", 1.0, ()))
    assert status.candidate_coverage == "none_declared"
    assert status.validated_information_status == "not_available"
    assert status.recommended_actions == ("expand_candidate_vocabulary",)


def test_common_best_candidate_yields_stable_recommendation():
    report = build_limitation_action_report(
        [
            SpecificationInput("s1", 1.0, (score("Q1", 0.4), score("Q2", 0.2))),
            SpecificationInput("s2", 0.8, (score("Q1", 0.3), score("Q2", 0.1))),
        ]
    )
    assert report.full_resolution_stability == "stable_mechanism_ambiguous"
    assert report.target_resolution_stability == "stable_target_unresolved"
    assert report.validated_actionability_stability == "stable_actionable"
    assert report.recommendation_stability == "stable_common_best"
    assert report.common_best_candidates == ("Q1",)


def test_different_best_candidates_yield_specification_sensitive_ranking():
    report = build_limitation_action_report(
        [
            SpecificationInput("strict", 1.0, (score("Q1", 0.5), score("Q2", 0.3))),
            SpecificationInput("loose", 1.0, (score("Q1", 0.2), score("Q2", 0.4))),
        ]
    )
    assert report.validated_actionability_stability == "stable_actionable"
    assert report.recommendation_stability == "specification_sensitive_ranking"
    assert report.common_best_candidates == ()


def test_partial_prediction_makes_validated_actionability_specification_sensitive():
    report = build_limitation_action_report(
        [
            SpecificationInput("complete", 1.0, (score("Q1", 0.4),)),
            SpecificationInput(
                "partial",
                1.0,
                (score("Q1", 0.4), score("Q2", None, estimable=False)),
            ),
        ]
    )
    assert report.validated_actionability_stability == "specification_sensitive"
    assert report.recommendation_stability == "specification_sensitive_actionability"


def test_target_resolution_and_full_resolution_have_separate_stability_axes():
    report = build_limitation_action_report(
        [
            SpecificationInput("full", 0.0, (score("Q1", 0.0),)),
            SpecificationInput(
                "target_only",
                1.0,
                (score("Q1", 0.2),),
                declared_target_resolved=True,
            ),
        ]
    )
    assert report.full_resolution_stability == "specification_sensitive"
    assert report.target_resolution_stability == "stable_target_resolved"
    assert report.validated_actionability_stability == "not_required"
    assert report.recommendation_stability == "not_available"


def test_target_resolution_can_itself_be_specification_sensitive():
    report = build_limitation_action_report(
        [
            SpecificationInput(
                "s1", 1.0, (score("Q1", 0.2),), declared_target_resolved=True
            ),
            SpecificationInput("s2", 1.0, (score("Q1", 0.2),)),
        ]
    )
    assert report.full_resolution_stability == "stable_mechanism_ambiguous"
    assert report.target_resolution_stability == "specification_sensitive"
