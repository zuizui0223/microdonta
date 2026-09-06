"""Executable claim ceiling for zero singleton observation values."""
from __future__ import annotations

from math import isclose

from causal_model.zero_singleton_synergy_witness import evaluate_zero_singleton_synergy


def test_xor_has_zero_singleton_but_positive_joint_information():
    result = evaluate_zero_singleton_synergy()
    assert set(result.singleton_information_bits) == {"observe_Q1", "observe_Q2"}
    assert all(isclose(value, 0.0, abs_tol=1e-12) for value in result.singleton_information_bits.values())
    assert all(isclose(value, 0.0, abs_tol=1e-12) for value in result.singleton_values.values())
    assert isclose(result.joint_information_bits, 1.0, abs_tol=1e-12)
    assert result.greedy_positive_only_stops


def test_chain_rule_exposes_information_after_zero_value_first_observation():
    result = evaluate_zero_singleton_synergy()
    assert isclose(result.expected_conditional_second_information_bits, 1.0, abs_tol=1e-12)
    q1_bits = result.singleton_information_bits["observe_Q1"]
    assert isclose(
        q1_bits + result.expected_conditional_second_information_bits,
        result.joint_information_bits,
        abs_tol=1e-12,
    )


def test_witness_is_replication_invariant():
    small = evaluate_zero_singleton_synergy(repeats_per_cell=1)
    large = evaluate_zero_singleton_synergy(repeats_per_cell=50)
    assert small.singleton_information_bits == large.singleton_information_bits
    assert isclose(small.joint_information_bits, large.joint_information_bits, abs_tol=1e-12)
    assert isclose(
        small.expected_conditional_second_information_bits,
        large.expected_conditional_second_information_bits,
        abs_tol=1e-12,
    )
