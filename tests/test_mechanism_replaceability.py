"""Tests for Causal Replaceability Cost (CRC)."""
import math

import pytest

from causal_model.causal_replaceability import (
    causal_replaceability_cost,
    causal_replaceability_cost_full,
    crc_profile,
    CRCResult,
)
from causal_model.external_constraints import Constraint


# ---------------------------------------------------------------------------
# Minimal synthetic admitted regions
# ---------------------------------------------------------------------------

def _rows_always_on(n: int = 100) -> list[dict]:
    """All accepted rows have switch_j = True (mechanism always active)."""
    return [{"j": True, "k": True} for _ in range(n)]


def _rows_always_off(n: int = 100) -> list[dict]:
    """All accepted rows have switch_j = False (mechanism always absent)."""
    return [{"j": False, "k": True} for _ in range(n)]


def _rows_mixed(n_on: int = 50, n_off: int = 50) -> list[dict]:
    """Mix of j=True and j=False rows."""
    return [{"j": True, "k": False} for _ in range(n_on)] + \
           [{"j": False, "k": True} for _ in range(n_off)]


# ---------------------------------------------------------------------------
# Core CRC properties
# ---------------------------------------------------------------------------

def test_crc_is_inf_when_no_ablated_draws_exist():
    rows = _rows_always_on(200)
    crc = causal_replaceability_cost("j", rows)
    assert crc == float("inf"), "Mechanism always active → CRC must be ∞"


def test_crc_is_zero_when_mechanism_is_always_absent():
    rows = _rows_always_off(200)
    crc = causal_replaceability_cost("j", rows)
    assert crc == 0.0, "Mechanism always absent → CRC must be 0 (free to ablate)"


def test_crc_is_nan_for_empty_region():
    crc = causal_replaceability_cost("j", [])
    assert math.isnan(crc), "Empty A_ε → CRC must be NaN"


def test_crc_increases_with_indispensability():
    rows_rare = [{"j": False}] * 10 + [{"j": True}] * 90     # j on 90% → harder to replace
    rows_common = [{"j": False}] * 70 + [{"j": True}] * 30   # j on 30% → easier to replace
    crc_rare = causal_replaceability_cost("j", rows_rare)
    crc_common = causal_replaceability_cost("j", rows_common)
    assert crc_rare > crc_common, "Higher CA_j (j more often active) → higher CRC"


def test_crc_at_half_is_one_bit():
    rows = _rows_mixed(50, 50)
    crc = causal_replaceability_cost("j", rows)
    assert abs(crc - 1.0) < 0.05, "P(j=0)=0.5 → CRC should be ≈ 1 bit"


def test_crc_full_result_fields():
    rows = _rows_mixed(30, 70)
    res = causal_replaceability_cost_full("j", rows)
    assert isinstance(res, CRCResult)
    assert res.n_total == 100
    assert res.n_ablated == 70
    assert abs(res.fraction_ablated - 0.70) < 1e-6
    assert res.CRC == res.info_cost + res.constraint_penalty


# ---------------------------------------------------------------------------
# CRC with explicit constraints
# ---------------------------------------------------------------------------

def test_constraint_penalty_adds_to_informational_cost():
    rows = [{"j": False, "param": 2.0} for _ in range(50)] + \
           [{"j": True,  "param": 0.0} for _ in range(50)]
    # Normal constraint: literature mean = 0.0, sigma = 1.0
    # The j=0 rows all have param=2.0 → penalty = (2/1)² = 4.0
    c = Constraint(name="param", type="normal", mu=0.0, sigma=1.0)
    crc_no_c = causal_replaceability_cost("j", rows, constraints=None)
    crc_with_c = causal_replaceability_cost("j", rows, constraints=[c])
    assert crc_with_c > crc_no_c, "Constraint penalty should increase CRC"
    # Penalty adds at least 4.0 (min penalty in ablated rows)
    assert crc_with_c >= crc_no_c + 3.9


def test_hard_constraint_violation_makes_crc_inf():
    rows = [{"j": False, "rate": -0.5} for _ in range(50)] + \
           [{"j": True,  "rate":  0.5} for _ in range(50)]
    # Hard constraint: rate must be ≥ 0 (probability constraint)
    c = Constraint(name="rate", type="hard", lower=0.0)
    # All j=0 rows have rate=-0.5 → hard violation → no valid replacement
    crc = causal_replaceability_cost("j", rows, constraints=[c])
    assert crc == float("inf"), "Hard constraint violation in all ablated rows → CRC = ∞"


def test_range_constraint_zero_inside_range():
    rows = [{"j": False, "v": 0.5}] * 100
    c = Constraint(name="v", type="range", lower=0.0, upper=1.0)
    crc = causal_replaceability_cost("j", rows, constraints=[c])
    # v=0.5 is inside [0, 1], so constraint_penalty = 0; CRC = info_cost = 0
    assert crc == 0.0


# ---------------------------------------------------------------------------
# Profile function
# ---------------------------------------------------------------------------

class _MockSwitch:
    def __init__(self, name): self.name = name


def test_crc_profile_covers_all_switches():
    rows = [{"j": True, "k": False}, {"j": False, "k": True}] * 100
    switches = [_MockSwitch("j"), _MockSwitch("k")]
    profile = crc_profile(rows, switches)
    assert set(profile.keys()) == {"j", "k"}
    assert all(isinstance(v, float) for v in profile.values())
