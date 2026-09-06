"""Numerical/reporting obligations for the internal target-limitation example."""
import json
import math
from copy import deepcopy

import pytest

from examples.target_limitation_report import _candidate, build_demo, build_target_report
from causal_model.mechanism_region import CandidateObservation


def _by_name(report):
    return {row["candidate"]: row for row in report["candidates"]}


def test_three_program_example_reports_partial_progress_and_each_outcome():
    report = build_demo()["current"]
    assert report["n_rows"] == 12
    assert report["target_entropy_bits"] == pytest.approx(math.log2(3))
    assert not report["target_identified_in_pool"]
    assert len(report["target_values"]) == 3
    assert report["unresolved_witness"]["target_values"][0] != report["unresolved_witness"]["target_values"][1]
    info = _by_name(report)
    for name in ("contact_channel", "physiology_channel"):
        value = info[name]
        assert value["information_bits"] == pytest.approx(math.log2(3) - 2/3)
        assert value["expected_remaining_target_entropy_bits"] == pytest.approx(2/3)
        assert not value["complete_repair_in_pool"]
        assert sorted(o["probability"] for o in value["outcomes"]) == pytest.approx([1/3, 2/3])
    assert info["deep_submechanism"]["information_bits"] == pytest.approx(0.0)
    assert not info["deep_submechanism"]["complete_repair_in_pool"]


def test_incomplete_predictions_are_not_zero_or_global_recommendations():
    report = build_demo()["current"]
    assert report["predictive_coverage"] == "partial"
    assert report["recommendation_scope"] == "estimable_subset_only"
    assert report["best_positive_candidates"] == ["contact_channel", "physiology_channel"]
    assert report["next_action"] == "provisional_selection_and_complete_predictions"
    assert report["nonestimable_candidates"] == ["unmodelled_followup"]
    missing = _by_name(report)["unmodelled_followup"]
    assert missing["information_bits"] is None
    assert missing["complete_repair_in_pool"] is None
    assert report["sequence_information_limit"] is None


def test_observed_branch_changes_the_remaining_question_and_next_action():
    demo = build_demo()
    resolved = demo["conditional_contact_branches"]["0"]
    unresolved = demo["conditional_contact_branches"]["1"]
    assert resolved["target_identified_in_pool"]
    assert resolved["n_rows"] == 4
    assert resolved["target_values"] == [("abiotic_only",)]
    assert resolved["best_positive_candidates"] == []
    assert unresolved["n_rows"] == 8
    assert unresolved["target_entropy_bits"] == pytest.approx(1.0)
    assert unresolved["best_positive_candidates"] == ["physiology_channel"]
    assert _by_name(unresolved)["physiology_channel"]["complete_repair_in_pool"]
    assert demo["explicit_joint_bundle"]["candidates"][0]["complete_repair_in_pool"]


def test_zero_singletons_do_not_become_a_sequence_impossibility_claim():
    rows = [{"T": p ^ a, "pop_p": p, "pop_a": a} for p in (0, 1) for a in (0, 1)]
    report = build_target_report(rows, [_candidate("p", "p", (0, 1)), _candidate("a", "a", (0, 1))], target_columns=["T"])
    assert report["one_step_stop_within_tolerance"]
    assert report["next_action"] == "audit_joint_information_before_changing_vocabulary"
    assert report["sequence_information_limit"] is None


def test_missing_candidate_maps_and_empty_vocabulary_have_distinct_actions():
    rows = [{"T": 0}, {"T": 1}]
    empty = build_target_report(rows, [], target_columns=["T"])
    unknown = CandidateObservation(name="unknown", description="", target_switches=[], rationale="", outcomes=[])
    missing = build_target_report(rows, [unknown], target_columns=["T"])
    assert empty["next_action"] == "declare_candidate_observations"
    assert missing["next_action"] == "build_candidate_predictive_models"
    assert not empty["one_step_stop_within_tolerance"]
    assert not missing["one_step_stop_within_tolerance"]


def test_partial_coverage_with_only_zero_known_values_is_not_a_one_step_certificate():
    rows = [{"T": t, "pop_noise": n} for t in (0, 1) for n in (0, 1)]
    noise = _candidate("noise", "noise", (0, 1))
    missing = CandidateObservation(name="unknown", description="", target_switches=[], rationale="", outcomes=[])
    report = build_target_report(rows, [noise, missing], target_columns=["T"])
    assert report["next_action"] == "complete_predictions_before_one_step_stop"
    assert not report["one_step_stop_within_tolerance"]


def test_zero_probability_outcomes_do_not_falsify_current_pool_repair():
    rows = [{"T": i, "pop_q": i} for i in (0, 1)]
    report = build_target_report(rows, [_candidate("q", "q", (0, 1, 2))], target_columns=["T"])
    candidate = report["candidates"][0]
    assert candidate["complete_repair_in_pool"]
    impossible = candidate["outcomes"][2]
    assert impossible["probability"] == 0.0
    assert impossible["target_identified_in_pool"] is None


def test_large_information_tolerance_does_not_manufacture_target_identification():
    rows = [{"T": i, "pop_q": i} for i in (0, 1)]
    report = build_target_report(rows, [_candidate("q", "q", (0, 1))], target_columns=["T"], information_tolerance=2.0)
    assert not report["target_identified_in_pool"]
    assert report["one_step_stop_within_tolerance"]
    assert report["candidates"][0]["complete_repair_in_pool"]


def test_report_rejects_invalid_inputs_instead_of_inventing_resolution():
    with pytest.raises(ValueError, match="missing target column"):
        build_target_report([{}, {}], [], target_columns=["T"])
    q = _candidate("q", "q", (0, 1))
    rows = [{"T": i, "pop_q": i} for i in (0, 1)]
    with pytest.raises(ValueError, match="candidate names"):
        build_target_report(rows, [q, q], target_columns=["T"])
    q.outcomes[1].name = q.outcomes[0].name
    with pytest.raises(ValueError, match="outcome names"):
        build_target_report(rows, [q], target_columns=["T"])
    for tolerance in (-1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="information_tolerance"):
            build_target_report(rows, [], target_columns=["T"], information_tolerance=tolerance)


def test_report_is_json_serializable_and_does_not_consult_truth_or_mutate_rows():
    rows = [{"T": i, "pop_q": i} for i in (0, 1)]
    before = deepcopy(rows)
    report = build_target_report(rows, [_candidate("q", "q", (0, 1))], target_columns=["T"])
    json.dumps(report, allow_nan=False)
    json.dumps(build_demo(), allow_nan=False)
    assert rows == before
    assert report["feasible_domain_exhaustiveness"] == "not_certified"
