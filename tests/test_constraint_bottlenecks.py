"""Tests for external constraints and bottleneck identification."""
import math

import pytest

from causal_model.external_constraints import (
    Constraint,
    penalty,
    total_penalty,
    individual_penalties,
    constraint_bottleneck,
)


# ---------------------------------------------------------------------------
# Individual penalty functions
# ---------------------------------------------------------------------------

def test_hard_constraint_zero_inside():
    c = Constraint(name="p", type="hard", lower=0.0, upper=1.0)
    assert penalty(c, 0.5) == 0.0
    assert penalty(c, 0.0) == 0.0
    assert penalty(c, 1.0) == 0.0


def test_hard_constraint_inf_outside():
    c = Constraint(name="p", type="hard", lower=0.0, upper=1.0)
    assert penalty(c, -0.01) == float("inf")
    assert penalty(c, 1.01) == float("inf")


def test_normal_constraint_zero_at_mean():
    c = Constraint(name="w", type="normal", mu=1.0, sigma=0.5)
    assert penalty(c, 1.0) == pytest.approx(0.0)


def test_normal_constraint_grows_with_deviation():
    c = Constraint(name="w", type="normal", mu=0.0, sigma=1.0)
    assert penalty(c, 1.0) == pytest.approx(1.0)  # ((1-0)/1)²
    assert penalty(c, 2.0) == pytest.approx(4.0)  # ((2-0)/1)²
    # monotone in absolute deviation
    assert penalty(c, 3.0) > penalty(c, 2.0) > penalty(c, 1.0)


def test_range_constraint_zero_inside():
    c = Constraint(name="x", type="range", lower=0.0, upper=10.0)
    assert penalty(c, 5.0) == 0.0
    assert penalty(c, 0.0) == 0.0
    assert penalty(c, 10.0) == 0.0


def test_range_constraint_positive_outside():
    c = Constraint(name="x", type="range", lower=0.0, upper=10.0)
    p = penalty(c, 15.0)   # excess = 5, width = 10 → (5/10)² = 0.25
    assert p == pytest.approx(0.25)


def test_soft_constraint_always_zero():
    c = Constraint(name="y", type="soft", weight=2.0)
    assert penalty(c, -100.0) == 0.0
    assert penalty(c, 100.0) == 0.0


# ---------------------------------------------------------------------------
# Total penalty
# ---------------------------------------------------------------------------

def test_total_penalty_sums_individual():
    c1 = Constraint(name="a", type="normal", mu=0.0, sigma=1.0)
    c2 = Constraint(name="b", type="normal", mu=0.0, sigma=1.0)
    vals = {"a": 1.0, "b": 2.0}
    assert total_penalty([c1, c2], vals) == pytest.approx(1.0 + 4.0)


def test_total_penalty_inf_if_any_hard_violated():
    c_hard = Constraint(name="p", type="hard", lower=0.0)
    c_norm = Constraint(name="w", type="normal", mu=0.0, sigma=1.0)
    vals = {"p": -1.0, "w": 0.5}
    assert total_penalty([c_hard, c_norm], vals) == float("inf")


def test_total_penalty_missing_key_uses_mu():
    c = Constraint(name="missing", type="normal", mu=0.0, sigma=1.0)
    # missing key → defaults to mu → penalty = 0
    assert total_penalty([c], {}) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Constraint bottleneck identification
# ---------------------------------------------------------------------------

def test_bottleneck_identifies_highest_penalty_constraint():
    """Among ablated rows, the bottleneck is the constraint with the largest penalty."""
    # Two ablated rows — first row is the min-penalty row (total = 1.0 + 0.0)
    # second row has higher total (9.0 + 0.0)
    ablated = [
        {"a": 1.0, "b": 0.0},   # a penalty = 1, b penalty = 0 → total = 1
        {"a": 3.0, "b": 0.0},   # a penalty = 9, b penalty = 0 → total = 9
    ]
    c_a = Constraint(name="a", type="normal", mu=0.0, sigma=1.0)
    c_b = Constraint(name="b", type="normal", mu=0.0, sigma=1.0)

    bn = constraint_bottleneck([c_a, c_b], ablated)
    # Minimum-cost row is row 0 (total=1). Within row 0: a has penalty 1, b has 0.
    assert bn is not None
    assert bn.name == "a"


def test_bottleneck_returns_none_for_empty_inputs():
    c = Constraint(name="x", type="normal", mu=0.0, sigma=1.0)
    assert constraint_bottleneck([], [{"x": 1.0}]) is None
    assert constraint_bottleneck([c], []) is None


def test_bottleneck_returns_none_for_no_constraints():
    ablated = [{"a": 1.0}]
    assert constraint_bottleneck([], ablated) is None


def test_individual_penalties_dict():
    c1 = Constraint(name="p", type="normal", mu=0.0, sigma=1.0)
    c2 = Constraint(name="q", type="range", lower=0.0, upper=1.0)
    vals = {"p": 2.0, "q": 0.5}
    ind = individual_penalties([c1, c2], vals)
    assert ind["p"] == pytest.approx(4.0)  # (2/1)²
    assert ind["q"] == pytest.approx(0.0)  # inside range
