"""Regression tests for the post-data candidate reprioritization witness."""
from __future__ import annotations

import math

from causal_model.postdata_reprioritization_witness import (
    current_rows,
    evaluate_reprioritization,
    prior_rows,
)


def test_current_evidence_restricts_only_A_and_leaves_B_balanced():
    before = prior_rows(repeats_per_state=7)
    after = current_rows(before)
    assert len(before) == 28
    assert len(after) == 14
    assert all(row["A"] is False for row in after)
    assert sum(bool(row["B"]) for row in after) == 7


def test_predata_and_postdata_candidate_ranking_reverses():
    result = evaluate_reprioritization(repeats_per_state=20)

    assert result.prior_best == "observe_A"
    assert result.current_best == "observe_B_when_A0"

    assert result.prior_information_bits["observe_A"] == 1.0
    assert result.current_information_bits["observe_A"] == 0.0
    assert result.current_information_bits["observe_B_when_A0"] == 1.0

    expected_conditional_prior_bits = -(
        0.25 * math.log2(0.25) + 0.75 * math.log2(0.75)
    )
    assert abs(
        result.prior_information_bits["observe_B_when_A0"]
        - expected_conditional_prior_bits
    ) < 1e-6


def test_normalized_mrod_values_change_with_current_region():
    result = evaluate_reprioritization(repeats_per_state=20)

    # K=2 binary mechanism coordinates, so one bit corresponds to V=0.5.
    assert result.prior_values["observe_A"] == 0.5
    assert result.prior_values["observe_B_when_A0"] == 0.4056
    assert result.current_values["observe_A"] == 0.0
    assert result.current_values["observe_B_when_A0"] == 0.5


def test_witness_is_not_sensitive_to_duplicate_monte_carlo_rows():
    small = evaluate_reprioritization(repeats_per_state=1)
    large = evaluate_reprioritization(repeats_per_state=50)
    assert small.prior_information_bits == large.prior_information_bits
    assert small.current_information_bits == large.current_information_bits
    assert small.prior_best == large.prior_best
    assert small.current_best == large.current_best
