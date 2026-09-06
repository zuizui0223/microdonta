"""Tests for a target T=tau(S) that coarsens the full mechanism world."""
from __future__ import annotations

import pytest

from causal_model.question_relative_mechanism_target_witness import (
    build_question_relative_mechanism_target_witness,
)


def test_question_target_is_a_strict_coarsening_of_full_mechanism_uncertainty():
    witness = build_question_relative_mechanism_target_witness()
    assert witness.full_state_entropy_bits == pytest.approx(3.0)
    assert witness.question_target_entropy_bits == pytest.approx(1.0)
    assert witness.question_target_entropy_bits <= witness.full_state_entropy_bits


def test_deep_measurement_can_win_full_state_information_but_lose_question_target():
    witness = build_question_relative_mechanism_target_witness()

    assert witness.full_state_information_bits["deep_submechanism"] == pytest.approx(2.0)
    assert witness.full_state_information_bits["question_class"] == pytest.approx(1.0)
    assert witness.full_state_best == "deep_submechanism"

    assert witness.question_target_information_bits["deep_submechanism"] == pytest.approx(0.0)
    assert witness.question_target_information_bits["question_class"] == pytest.approx(1.0)
    assert witness.question_target_best == "question_class"

    assert witness.full_state_normalized_values["deep_submechanism"] == pytest.approx(2 / 3, abs=1e-4)
    assert witness.full_state_normalized_values["question_class"] == pytest.approx(1 / 3, abs=1e-4)
    assert witness.question_target_normalized_values["deep_submechanism"] == pytest.approx(0.0)
    assert witness.question_target_normalized_values["question_class"] == pytest.approx(1.0)


def test_data_processing_bound_holds_candidatewise_for_target_coarsening():
    witness = build_question_relative_mechanism_target_witness()
    for candidate, target_bits in witness.question_target_information_bits.items():
        assert target_bits <= witness.full_state_information_bits[candidate] + 1e-12


def test_question_target_can_be_resolved_while_full_mechanism_remains_ambiguous():
    witness = build_question_relative_mechanism_target_witness()
    assert witness.resolved_target_entropy_bits == pytest.approx(0.0)
    assert witness.residual_full_state_entropy_bits_after_target_resolution == pytest.approx(2.0)
