"""Governance tests for the preregistered G2 v2 benchmark configuration."""
import inspect
from pathlib import Path

from paper.run_g2_frozen_benchmark import load_protocol, run_protocol

ROOT = Path(__file__).resolve().parents[1]


def test_g2_protocol_v2_is_frozen_truth_peek_free_and_auditable():
    protocol, digest = load_protocol()
    assert protocol["protocol_id"] == "rach-g2-truth-peek-free-v2"
    assert protocol["status"] == "frozen_before_final_run"
    assert protocol["supersedes"] == "rach-g2-truth-peek-free-v1"
    assert protocol["generator"]["truth_peek_free"] is True
    assert protocol["generator"]["hidden_truth_use"] == (
        "materialise_realised_outcome_after_candidate_selection_only"
    )
    assert len(digest) == 64
    assert (ROOT / "paper/archive/g2_frozen_benchmark_protocol_v1_pre_execution.json").exists()
    assert (ROOT / "paper/archive/g2_protocol_v1_supersession.md").exists()


def test_g2_protocol_fixes_submission_scale_before_results():
    protocol, _ = load_protocol()
    sweep = protocol["sweep"]
    assert sweep["seeds"] == [0, 1, 2, 3, 4]
    assert sweep["n_systems_per_seed"] == 200
    assert sweep["n_attempts"] == 1500
    assert sweep["K_choices"] == [4, 5, 6]
    assert sweep["confound_choices"] == [1, 2]
    assert sweep["budgets"] == [0, 1, 2, 3, 4]
    assert sweep["min_sub_size"] == 8


def test_coefficient_sampling_range_satisfies_declared_separability():
    protocol, _ = load_protocol()
    sampling = protocol["generator"]["driver_coefficient_sampling"]
    ratio_lo, ratio_hi = sampling["b_over_a_uniform"]
    assert ratio_lo > 1.5
    assert ratio_hi < 2.0


def test_selection_challenge_is_predeclared():
    protocol, _ = load_protocol()
    distractors = protocol["generator"]["distractor_candidates"]
    selection = protocol["selection_validation"]
    assert distractors["count"] == 2
    assert distractors["intended_mechanism_information"] == "none_by_construction"
    assert selection["policies"] == ["rach_seq", "random_order"]
    assert selection["same_systems_truths_candidates_and_budgets_across_policies"] is True
    assert selection["policy_comparison_is_descriptive_not_acceptance_gate"] is True


def test_g2_protocol_has_no_favourable_performance_gate():
    protocol, _ = load_protocol()
    assert protocol["reporting"]["performance_acceptance_thresholds"] == (
        "none_report_all_frozen_outcomes"
    )
    assert protocol["reporting"]["policy_contrast_rows_required"] is True


def test_frozen_runner_has_no_scientific_parameter_arguments():
    # The callable can choose only where to write results. Scientific parameters
    # must come from the frozen JSON, not analysis-time function arguments.
    signature = inspect.signature(run_protocol)
    assert list(signature.parameters) == ["output_dir"]
