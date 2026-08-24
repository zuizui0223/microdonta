"""Governance tests for the preregistered G2 benchmark configuration."""
import inspect

from paper.run_g2_frozen_benchmark import load_protocol, run_protocol


def test_g2_protocol_is_frozen_and_truth_peek_free():
    protocol, digest = load_protocol()
    assert protocol["status"] == "frozen_before_final_run"
    assert protocol["generator"]["truth_peek_free"] is True
    assert protocol["generator"]["hidden_truth_use"] == (
        "materialise_realised_outcome_after_candidate_ranking_only"
    )
    assert len(digest) == 64


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


def test_frozen_runner_has_no_scientific_parameter_arguments():
    # The callable can choose only where to write results. Scientific parameters
    # must come from the frozen JSON, not analysis-time function arguments.
    signature = inspect.signature(run_protocol)
    assert list(signature.parameters) == ["output_dir"]
