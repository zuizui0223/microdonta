"""Regression tests for tolerance-sensitive next-observation ranking."""
from __future__ import annotations

from causal_model.tolerance_sensitivity_witness import (
    LOOSE_EPSILON,
    STRICT_EPSILON,
    accepted_rows,
    evaluate_tolerance_sensitivity,
    evaluated_rows,
)


def test_strict_region_is_nested_in_loose_region():
    pool = evaluated_rows()
    strict = accepted_rows(pool, STRICT_EPSILON)
    loose = accepted_rows(pool, LOOSE_EPSILON)
    assert len(strict) == 10
    assert len(loose) == 18
    assert all(row in loose for row in strict)


def test_candidate_information_ranking_reverses_with_tolerance():
    result = evaluate_tolerance_sensitivity()

    assert result.strict_best == "observe_A"
    assert result.loose_best == "observe_B"
    assert result.common_best == ()

    assert result.strict_information_bits["observe_A"] == 1.0
    assert result.strict_information_bits["observe_B"] == 0.721928
    assert result.loose_information_bits["observe_A"] == 0.852405
    assert result.loose_information_bits["observe_B"] == 0.991076


def test_normalized_information_values_follow_same_reversal():
    result = evaluate_tolerance_sensitivity()
    assert result.strict_values["observe_A"] == 0.5
    assert result.strict_values["observe_B"] == 0.361
    assert result.loose_values["observe_A"] == 0.4262
    assert result.loose_values["observe_B"] == 0.4955


def test_witness_is_invariant_to_duplicate_rows():
    small = evaluate_tolerance_sensitivity(repeats=1)
    large = evaluate_tolerance_sensitivity(repeats=20)
    assert small.strict_information_bits == large.strict_information_bits
    assert small.loose_information_bits == large.loose_information_bits
    assert small.strict_values == large.strict_values
    assert small.loose_values == large.loose_values
    assert small.strict_best == large.strict_best
    assert small.loose_best == large.loose_best
    assert small.common_best == large.common_best
