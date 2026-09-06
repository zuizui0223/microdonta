"""Regression tests for current resolvability versus evidence gain."""
from __future__ import annotations

from causal_model.prior_evidence_separation_witness import (
    evaluate_prior_evidence_separation,
    evaluate_prior_ranking_sensitivity,
)


def test_nonuniform_baseline_can_have_positive_resolvability_before_observation():
    result = evaluate_prior_evidence_separation()
    assert result.baseline_entropy_bits == 0.469
    assert result.baseline_resolvability == 0.531


def test_candidate_value_is_incremental_information_from_current_state():
    result = evaluate_prior_evidence_separation()
    assert result.signal_information_bits == 0.468996
    assert result.signal_value == 0.469
    assert result.expected_resolvability_after_signal == 1.0
    assert result.noise_information_bits == 0.0
    assert result.noise_value == 0.0


def test_prior_distribution_can_change_candidate_information_ranking():
    result = evaluate_prior_ranking_sensitivity()
    assert result.first_prior_information_bits["observe_A"] == 1.0
    assert result.first_prior_information_bits["observe_B"] == 0.468996
    assert result.first_best == "observe_A"

    assert result.second_prior_information_bits["observe_A"] == 0.468996
    assert result.second_prior_information_bits["observe_B"] == 1.0
    assert result.second_best == "observe_B"
