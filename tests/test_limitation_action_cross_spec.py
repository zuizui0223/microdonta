"""Cross-specification guards for the limitation-to-action prototype."""
from __future__ import annotations

from math import nan

from causal_model.limitation_action_report import (
    CandidateScore,
    SpecificationInput,
    build_limitation_action_report,
)


def score(name: str, value: float) -> CandidateScore:
    return CandidateScore(candidate=name, estimable=True, information_value=value)


def test_resolved_and_unresolved_target_states_block_common_recommendation():
    report = build_limitation_action_report(
        [
            SpecificationInput(
                "resolved_spec",
                1.0,
                (score("Q1", 0.4),),
                declared_target_resolved=True,
            ),
            SpecificationInput("unresolved_spec", 1.0, (score("Q1", 0.4),)),
        ]
    )
    assert report.target_resolution_stability == "specification_sensitive"
    assert report.validated_actionability_stability == "specification_sensitive_target_state"
    assert report.recommendation_stability == "specification_sensitive_target_state"
    assert report.common_best_candidates == ()


def test_nonestimable_and_unresolved_target_states_block_common_recommendation():
    report = build_limitation_action_report(
        [
            SpecificationInput("nonestimable", nan, (score("Q1", 0.4),)),
            SpecificationInput("unresolved", 1.0, (score("Q1", 0.4),)),
        ]
    )
    assert report.target_resolution_stability == "specification_sensitive"
    assert report.validated_actionability_stability == "specification_sensitive_target_state"
    assert report.recommendation_stability == "specification_sensitive_target_state"
    assert report.common_best_candidates == ()


def test_all_nonestimable_target_states_are_not_evaluable():
    report = build_limitation_action_report(
        [
            SpecificationInput("a", nan, (score("Q1", 0.4),)),
            SpecificationInput("b", nan, (score("Q1", 0.4),)),
        ]
    )
    assert report.target_resolution_stability == "stable_target_nonestimable"
    assert report.validated_actionability_stability == "not_evaluable"
    assert report.recommendation_stability == "not_evaluable"
