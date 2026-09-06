"""Controlled tests for the internal horizon-information limitation audit."""
from __future__ import annotations

import pytest

from causal_model.horizon_information_profile import horizon_information_profile


def test_xor_requires_bundle_size_two_even_though_every_singleton_is_zero():
    # Uniform Q1,Q2 with mechanism S = XOR(Q1,Q2).
    q1 = (0, 0, 1, 1)
    q2 = (0, 1, 0, 1)
    states = tuple(a ^ b for a, b in zip(q1, q2))
    profile = horizon_information_profile(
        states,
        {"Q1": q1, "Q2": q2},
        mechanism_bits=1,
    )
    assert profile.mechanism_entropy_bits == pytest.approx(1.0)
    assert profile.best_information_bits_by_horizon == pytest.approx((0.0, 1.0))
    assert profile.best_normalized_value_by_horizon == pytest.approx((0.0, 1.0))
    assert profile.first_positive_bundle_size == 2
    assert profile.full_vector_information_bits == pytest.approx(1.0)
    assert profile.best_bundles_by_horizon[1] == (("Q1", "Q2"),)


def test_three_bit_parity_requires_bundle_size_three():
    q1 = []
    q2 = []
    q3 = []
    states = []
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                q1.append(a)
                q2.append(b)
                q3.append(c)
                states.append(a ^ b ^ c)
    profile = horizon_information_profile(
        tuple(states),
        {"Q1": tuple(q1), "Q2": tuple(q2), "Q3": tuple(q3)},
        mechanism_bits=1,
    )
    assert profile.best_information_bits_by_horizon == pytest.approx((0.0, 0.0, 1.0))
    assert profile.first_positive_bundle_size == 3
    assert profile.full_vector_information_bits == pytest.approx(1.0)


def test_direct_measurement_is_already_actionable_at_bundle_size_one():
    states = (0, 0, 1, 1)
    direct = states
    nuisance = (0, 1, 0, 1)
    profile = horizon_information_profile(
        states,
        {"direct": direct, "nuisance": nuisance},
        mechanism_bits=1,
    )
    assert profile.best_information_bits_by_horizon == pytest.approx((1.0, 1.0))
    assert profile.first_positive_bundle_size == 1
    assert ("direct",) in profile.best_bundles_by_horizon[0]


def test_jointly_uninformative_candidate_vector_has_zero_at_every_horizon():
    # Full Cartesian product makes S independent of the entire Q1,Q2 vector.
    states = []
    q1 = []
    q2 = []
    for s in (0, 1):
        for a in (0, 1):
            for b in (0, 1):
                states.append(s)
                q1.append(a)
                q2.append(b)
    profile = horizon_information_profile(
        tuple(states),
        {"Q1": tuple(q1), "Q2": tuple(q2)},
        mechanism_bits=1,
    )
    assert profile.best_information_bits_by_horizon == pytest.approx((0.0, 0.0))
    assert profile.first_positive_bundle_size is None
    assert profile.full_vector_information_bits == pytest.approx(0.0)


def test_profile_is_monotone_and_bounded_by_current_mechanism_entropy():
    states = (0, 0, 1, 1, 0, 0, 1, 1)
    candidates = {
        "A": (0, 0, 0, 0, 1, 1, 1, 1),
        "B": (0, 0, 1, 1, 0, 0, 1, 1),
        "C": (0, 1, 0, 1, 0, 1, 0, 1),
    }
    profile = horizon_information_profile(states, candidates, mechanism_bits=1)
    values = profile.best_information_bits_by_horizon
    assert all(values[i] <= values[i + 1] + 1e-12 for i in range(len(values) - 1))
    assert all(value <= profile.mechanism_entropy_bits + 1e-12 for value in values)


def test_normalization_does_not_change_first_positive_bundle_size():
    states = (0, 1, 1, 0)
    q1 = (0, 0, 1, 1)
    q2 = (0, 1, 0, 1)
    profile = horizon_information_profile(states, {"Q1": q1, "Q2": q2}, mechanism_bits=4)
    assert profile.first_positive_bundle_size == 2
    assert profile.best_information_bits_by_horizon[1] == pytest.approx(1.0)
    assert profile.best_normalized_value_by_horizon[1] == pytest.approx(0.25)


def test_invalid_alignment_horizon_and_normalization_are_rejected():
    with pytest.raises(ValueError):
        horizon_information_profile((0, 1), {"Q": (0,)}, mechanism_bits=1)
    with pytest.raises(ValueError):
        horizon_information_profile((0, 1), {"Q": (0, 1)}, mechanism_bits=1, max_horizon=2)
    with pytest.raises(ValueError):
        horizon_information_profile((0, 1), {"Q": (0, 1)}, mechanism_bits=0)
    # Four equiprobable states have H(S)=2 bits, inconsistent with K=1.
    with pytest.raises(ValueError, match="entropy exceeds"):
        horizon_information_profile((0, 1, 2, 3), {"Q": (0, 1, 2, 3)}, mechanism_bits=1)
