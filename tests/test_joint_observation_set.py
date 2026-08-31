"""Tests for the RACH-SET joint observation-set optimizer.

These tests verify the exact behaviour described in Theorem C:
  - in the canonical synergy family every singleton gain is zero,
  - the full elimination set resolves the target mechanism,
  - RACH-SET (brute-force) finds the optimal set,
  - positive-marginal-gain-stopping greedy fails,
  - the submodularity of R_j is correctly reported as violated.
"""
import math

import pytest

from causal_model.rach_set import rach_set, RachSetResult
from causal_model.replaceability_theory import (
    synthetic_synergy_model,
    resolution_indicator,
    _add_nulls,
    StructuralModel,
    Observation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _synergy(n: int):
    """Return (model, baseline, cands, j) for the n-competitor family."""
    return synthetic_synergy_model(n)


# ---------------------------------------------------------------------------
# Core Theorem C facts reproduced via rach_set
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_rach_set_finds_optimal_in_synergy_family(n):
    model, baseline, cands, j = _synergy(n)
    res = rach_set(model, baseline, cands, j, budget=len(cands))
    assert res.optimal_value == 1, "the full elimination set must resolve j"
    assert set(res.optimal_set) == set(cands), (
        "optimal set should be all n witnesses"
    )


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_synergy_warning_is_raised(n):
    """All singleton gains are zero in the canonical family → synergy_warning True."""
    model, baseline, cands, j = _synergy(n)
    res = rach_set(model, baseline, cands, j, budget=len(cands))
    assert res.synergy_warning, (
        "all singletons have zero gain but the set resolves: synergy_warning must be True"
    )


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_greedy_fails_in_synergy_family(n):
    """Positive-marginal-gain-stopping greedy makes no progress."""
    model, baseline, cands, j = _synergy(n)
    res = rach_set(model, baseline, cands, j, budget=len(cands))
    assert res.greedy_value == 0, "greedy should resolve nothing (all singletons have zero gain)"
    assert res.greedy_set == [], "greedy should choose nothing (no positive-gain step exists)"


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_greedy_optimal_ratio_is_zero(n):
    model, baseline, cands, j = _synergy(n)
    res = rach_set(model, baseline, cands, j, budget=len(cands))
    assert res.greedy_optimal_ratio == 0.0


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_submodularity_violated_in_synergy_family(n):
    model, baseline, cands, j = _synergy(n)
    res = rach_set(model, baseline, cands, j, budget=len(cands))
    assert res.submodularity_status == "violated"


# ---------------------------------------------------------------------------
# Budget constraint respected
# ---------------------------------------------------------------------------

def test_budget_limits_search():
    """With budget < n, the optimal set under budget cannot include all witnesses."""
    model, baseline, cands, j = _synergy(4)
    res = rach_set(model, baseline, cands, j, budget=2)
    # budget=2 < 4 competitors: cannot resolve
    assert res.optimal_value == 0


def test_budget_exactly_n_resolves():
    model, baseline, cands, j = _synergy(3)
    res = rach_set(model, baseline, cands, j, budget=3)
    assert res.optimal_value == 1


# ---------------------------------------------------------------------------
# Degenerate / trivial cases
# ---------------------------------------------------------------------------

def test_trivial_one_candidate():
    """With a single candidate (private witness of the only competitor), trivial."""
    model = StructuralModel(
        K=2,
        driver_sets={
            "focal": frozenset({0, 1}),
            "witness_1": frozenset({1}),
        },
    )
    baseline = Observation(present=("focal",))
    res = rach_set(model, baseline, ["witness_1"], 0, budget=1)
    assert res.optimal_value == 1
    assert res.synergy_warning is False   # singleton gain IS positive here
    assert res.submodularity_status == "trivial"


def test_no_resolution_possible():
    """When the target has a private witness (always pinned by the present trait)."""
    model = StructuralModel(
        K=2,
        driver_sets={
            "private_j": frozenset({0}),   # only j drives this
            "focal": frozenset({0, 1}),
        },
    )
    baseline = Observation(present=("private_j",))
    # j is already pinned; no NULLs needed
    res = rach_set(model, baseline, ["focal"], 0, budget=1)
    # baseline already resolves j; optimal is the empty set (encoded as () with base_r=1)
    assert res.optimal_value == 1


def test_n_evaluated_matches_expected():
    """Brute-force should evaluate all non-empty subsets up to budget."""
    from math import comb
    model, baseline, cands, j = _synergy(3)
    budget = 3
    # cands has 3 elements; subsets of size 1,2,3 until a resolving set is found.
    # The only resolving set is all 3; all size-1 and size-2 subsets are tried first.
    res = rach_set(model, baseline, cands, j, budget=budget)
    # C(3,1)=3, C(3,2)=3, C(3,3)=1 → all evaluated = 7 (stops after finding at size 3)
    # because all size-1 and size-2 return 0, and then the size-3 returns 1 → stop
    assert res.n_evaluated == comb(3, 1) + comb(3, 2) + comb(3, 3)


# ---------------------------------------------------------------------------
# Result type and describe() smoke test
# ---------------------------------------------------------------------------

def test_result_type():
    model, baseline, cands, j = _synergy(2)
    res = rach_set(model, baseline, cands, j, budget=2)
    assert isinstance(res, RachSetResult)


def test_describe_runs():
    model, baseline, cands, j = _synergy(3)
    res = rach_set(model, baseline, cands, j, budget=3)
    desc = res.describe()
    assert "RACH-SET" in desc
    assert "synergy" in desc.lower()
    assert "violated" in desc
