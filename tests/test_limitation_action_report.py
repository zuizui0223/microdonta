"""Tests for the prototype limitation-to-action reporting layer."""
from __future__ import annotations

from causal_model.limitation_action_report import (
    CandidateScore,
    SpecificationInput,
    build_limitation_action_report,
    classify_specification,
)


def score(name: str, value: float | None, estimable: bool = True) -> CandidateScore:
    return CandidateScore(candidate=name, estimable=estimable, information_value=value)


def test_resolved_state_stops_without_forcing_candidate_choice():
    status = classify_specification(
        SpecificationInput("base", 0.0, (score("Q1", 0.5),))
    )
    assert status.mechanism_status == "resolved"
    assert status.candidate_status == "not_required"
    assert status.best_candidates == ()
    assert status.recommended_action == "stop_resolved"


def test_unresolved_positive_value_is_actionable():
    status = classify_specification(
        SpecificationInput("base", 1.0, (score("Q1", 0.3), score("Q2", 0.1)))
    )
    assert status.mechanism_status == "unresolved"
    assert status.candidate_status == "actionable"
    assert status.best_candidates == ("Q1",)
    assert status.max_information_value == 0.3
    assert status.recommended_action == "measure_best_candidate"


def test_unresolved_zero_values_are_information_limited():
    status = classify_specification(
        SpecificationInput("base", 1.0, (score("Q1", 0.0), score("Q2", 0.0)))
    )
    assert status.candidate_status == "information_limited"
    assert status.best_candidates == ()
    assert status.recommended_action == "report_information_limit"


def test_no_estimable_candidate_is_prediction_limited():
    status = classify_specification(
        SpecificationInput(
            "base",
            1.0,
            (score("Q1", None, estimable=False), score("Q2", None, estimable=False)),
        )
    )
    assert status.candidate_status == "prediction_limited"
    assert status.nonestimable_candidates == ("Q1", "Q2")
    assert status.recommended_action == "identify_candidate_outcome_models"


def test_no_candidate_is_candidate_limited():
    status = classify_specification(SpecificationInput("base", 1.0, ()))
    assert status.candidate_status == "candidate_limited"
    assert status.recommended_action == "expand_candidate_vocabulary"


def test_budget_limit_remains_distinct_from_information_limit():
    status = classify_specification(
        SpecificationInput("base", 1.0, (score("Q1", 0.4),), budget_remaining=False)
    )
    assert status.candidate_status == "budget_limited"
    assert status.recommended_action == "report_budget_limit"


def test_common_best_candidate_yields_stable_recommendation():
    report = build_limitation_action_report(
        [
            SpecificationInput("s1", 1.0, (score("Q1", 0.4), score("Q2", 0.2))),
            SpecificationInput("s2", 0.8, (score("Q1", 0.3), score("Q2", 0.1))),
        ]
    )
    assert report.resolution_stability == "stable_unresolved"
    assert report.actionability_stability == "stable_actionable"
    assert report.recommendation_stability == "stable_common_best"
    assert report.common_best_candidates == ("Q1",)


def test_different_best_candidates_yield_specification_sensitive_ranking():
    report = build_limitation_action_report(
        [
            SpecificationInput("strict", 1.0, (score("Q1", 0.5), score("Q2", 0.3))),
            SpecificationInput("loose", 1.0, (score("Q1", 0.2), score("Q2", 0.4))),
        ]
    )
    assert report.recommendation_stability == "specification_sensitive_ranking"
    assert report.common_best_candidates == ()


def test_actionability_can_itself_be_specification_sensitive():
    report = build_limitation_action_report(
        [
            SpecificationInput("s1", 1.0, (score("Q1", 0.4),)),
            SpecificationInput("s2", 1.0, (score("Q1", 0.0),)),
        ]
    )
    assert report.actionability_stability == "specification_sensitive"
    assert report.recommendation_stability == "specification_sensitive_actionability"


def test_resolution_can_itself_be_specification_sensitive():
    report = build_limitation_action_report(
        [
            SpecificationInput("s1", 0.0, (score("Q1", 0.0),)),
            SpecificationInput("s2", 1.0, (score("Q1", 0.2),)),
        ]
    )
    assert report.resolution_stability == "specification_sensitive"
