"""Tests for the method-comparison section (CRC/CSM vs established summaries)."""
import math

import pytest

from causal_model.method_comparison import (
    model_posteriors,
    marginal_posteriors,
    compare_methods,
    compare_on_constraint_separated,
    MethodComparison,
)


class _Sw:
    def __init__(self, name): self.name = name


# ---------------------------------------------------------------------------
# The established summaries behave as expected
# ---------------------------------------------------------------------------

def test_model_posteriors_sum_to_one():
    rows = (
        [{"a": True, "b": False}] * 30 +
        [{"a": False, "b": True}] * 30 +
        [{"a": True, "b": True}]  * 40
    )
    sw = [_Sw("a"), _Sw("b")]
    mp = model_posteriors(rows, sw)
    assert abs(sum(mp.values()) - 1.0) < 1e-9
    assert mp[frozenset({"a", "b"})] == pytest.approx(0.4)


def test_marginal_posteriors_are_inclusion_probabilities():
    rows = [{"a": True, "b": False}] * 70 + [{"a": False, "b": True}] * 30
    sw = [_Sw("a"), _Sw("b")]
    cp = marginal_posteriors(rows, sw)
    assert cp["a"] == pytest.approx(0.70)
    assert cp["b"] == pytest.approx(0.30)


# ---------------------------------------------------------------------------
# The headline: only CRC-with-constraints separates thermal vs resource
# ---------------------------------------------------------------------------

def test_only_crc_with_constraints_separates_the_symmetric_pair():
    comp, verdict = compare_on_constraint_separated(n_attempts=30000, seed=1)
    # the three data-only summaries TIE the two mechanisms
    assert verdict["model_selection_BMA"] is False
    assert verdict["marginal_posterior"] is False
    assert verdict["CRC_data_only"] is False
    # only CRC with external constraints separates them
    assert verdict["CRC_with_constraints"] is True


def test_comparison_numbers_are_consistent():
    comp, _ = compare_on_constraint_separated(n_attempts=30000, seed=1)
    # marginal posteriors nearly equal (informational symmetry)
    assert abs(comp.marginal_posteriors["thermal"] - comp.marginal_posteriors["resource"]) < 0.03
    # CRC with constraints widely separated
    crc_t = comp.crc_constrained["thermal"]
    crc_r = comp.crc_constrained["resource"]
    assert crc_r > crc_t + 10.0


def test_separates_handles_infinite_crc():
    """The separates() helper must treat ∞ vs finite as a separation."""
    rows = [{"j": True, "k": False}] * 50 + [{"j": False, "k": True}] * 50
    sw = [_Sw("j"), _Sw("k")]
    comp = compare_methods(rows, sw, constraints=None)
    # synthesise an infinite CRC by hand to exercise the branch
    comp.crc_constrained["j"] = float("inf")
    comp.crc_constrained["k"] = 1.0
    verdict = comp.separates("j", "k")
    assert verdict["CRC_with_constraints"] is True


# ---------------------------------------------------------------------------
# CSM exposes structure the marginal summaries cannot
# ---------------------------------------------------------------------------

def test_csm_present_in_comparison():
    rows = [{"a": True, "b": False}] * 50 + [{"a": False, "b": True}] * 50
    sw = [_Sw("a"), _Sw("b")]
    comp = compare_methods(rows, sw)
    # CSM has off-diagonal entries that the marginal posterior (a single number
    # per mechanism) structurally cannot represent
    assert ("a", "b") in comp.csm
    assert ("b", "a") in comp.csm


def test_result_type():
    comp, verdict = compare_on_constraint_separated(n_attempts=8000, seed=1)
    assert isinstance(comp, MethodComparison)
    assert set(verdict.keys()) == {
        "model_selection_BMA", "marginal_posterior",
        "CRC_data_only", "CRC_with_constraints",
    }
