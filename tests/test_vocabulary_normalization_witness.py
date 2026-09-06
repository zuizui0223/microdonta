"""Regression tests for deterministic redundant mechanism coordinates."""
from __future__ import annotations

from causal_model.vocabulary_normalization_witness import (
    evaluate_vocabulary_normalization,
)


def test_raw_entropy_is_invariant_to_deterministic_redundant_switch():
    result = evaluate_vocabulary_normalization()
    assert result.original_entropy_bits == 2.0
    assert result.redundant_entropy_bits == 2.0


def test_raw_mutual_information_is_invariant_to_redundant_switch():
    result = evaluate_vocabulary_normalization()
    assert result.original_information_bits == result.redundant_information_bits
    assert result.original_information_bits["observe_A"] == 1.0
    assert result.original_information_bits["observe_A_and_B"] == 0.811278


def test_K_normalized_magnitudes_change_under_redundant_switch():
    result = evaluate_vocabulary_normalization()
    assert result.original_resolvability == 0.0
    assert result.redundant_resolvability == 0.3333

    assert result.original_values["observe_A"] == 0.5
    assert result.redundant_values["observe_A"] == 0.3333
    assert result.original_values["observe_A_and_B"] == 0.4056
    assert result.redundant_values["observe_A_and_B"] == 0.2704


def test_candidate_ranking_and_zero_structure_are_preserved():
    result = evaluate_vocabulary_normalization()
    assert result.original_ranking == ("observe_A", "observe_A_and_B")
    assert result.redundant_ranking == result.original_ranking


def test_witness_is_invariant_to_duplicate_monte_carlo_rows():
    small = evaluate_vocabulary_normalization(repeats_per_state=1)
    large = evaluate_vocabulary_normalization(repeats_per_state=50)
    assert small.original_entropy_bits == large.original_entropy_bits
    assert small.redundant_entropy_bits == large.redundant_entropy_bits
    assert small.original_information_bits == large.original_information_bits
    assert small.redundant_information_bits == large.redundant_information_bits
    assert small.original_ranking == large.original_ranking
    assert small.redundant_ranking == large.redundant_ranking
