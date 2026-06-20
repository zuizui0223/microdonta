"""Tests for degeneracy estimation: Miller–Madow bias correction and the
empty-A_ε → non-estimable (nan) convention."""
import math

import pytest

from causal_model.causal_admissibility import (
    _joint_entropy,
    causal_degeneracy,
    causal_resolvability,
    causal_admissibility,
    rach_summary,
)


class _SW:
    def __init__(self, name):
        self.name = name
        self.biological_question = ""
        self.prior_on_prob = 0.5


def _switches(names):
    return [_SW(n) for n in names]


def _rows(combos):
    """combos: list of tuples of 0/1 → accepted rows over switches A,B,..."""
    names = [chr(ord("A") + i) for i in range(len(combos[0]))]
    return [{n: bool(v) for n, v in zip(names, c)} for c in combos], _switches(names)


# ---------------------------------------------------------------------------
# Miller–Madow correction
# ---------------------------------------------------------------------------

def test_miller_madow_adds_positive_correction():
    # two equiprobable cells over 1 switch: plug-in H = 1 bit
    vectors = [(0,)] * 50 + [(1,)] * 50
    h_plugin = _joint_entropy(vectors)
    h_mm = _joint_entropy(vectors, bias_correction="miller_madow")
    assert h_plugin == pytest.approx(1.0, abs=1e-9)
    # correction = (m-1)/(2 N ln2) = (2-1)/(2*100*ln2)
    expected = (2 - 1) / (2 * 100 * math.log(2))
    assert h_mm - h_plugin == pytest.approx(expected, abs=1e-9)


def test_miller_madow_correction_grows_with_cells():
    # more occupied cells (m) at fixed N → larger correction
    n = 256
    two_cell = [(0, 0)] * (n // 2) + [(1, 1)] * (n // 2)
    four_cell = ([(0, 0)] * (n // 4) + [(0, 1)] * (n // 4)
                 + [(1, 0)] * (n // 4) + [(1, 1)] * (n // 4))
    c2 = _joint_entropy(two_cell, "miller_madow") - _joint_entropy(two_cell)
    c4 = _joint_entropy(four_cell, "miller_madow") - _joint_entropy(four_cell)
    assert c4 > c2


def test_miller_madow_negligible_for_small_k_large_n():
    # K=2, N large: correction must be < 0.01 bit
    rows, sw = _rows([(0, 0)] * 1000 + [(1, 1)] * 1000)
    d_plugin = causal_degeneracy(rows, sw)
    d_mm = causal_degeneracy(rows, sw, bias_correction="miller_madow")
    assert abs(d_mm - d_plugin) < 0.01


def test_causal_degeneracy_clamps_corrected_value_to_K():
    # tiny N, many cells → correction could overshoot; must clamp to K
    rows, sw = _rows([(0, 0, 0), (1, 1, 1), (0, 1, 0), (1, 0, 1)])
    d_mm = causal_degeneracy(rows, sw, bias_correction="miller_madow")
    assert 0.0 <= d_mm <= 3.0


def test_unknown_bias_correction_raises():
    with pytest.raises(ValueError):
        _joint_entropy([(0,), (1,)], bias_correction="bogus")


def test_resolvability_accepts_bias_correction():
    rows, sw = _rows([(0, 0)] * 500 + [(1, 1)] * 500)
    r = causal_resolvability(rows, sw, bias_correction="miller_madow")
    assert 0.0 <= r <= 1.0


# ---------------------------------------------------------------------------
# Empty A_ε → non-estimable (nan)
# ---------------------------------------------------------------------------

def test_empty_degeneracy_is_nan():
    sw = _switches(["A", "B"])
    assert math.isnan(causal_degeneracy([], sw))


def test_empty_resolvability_is_nan():
    sw = _switches(["A", "B"])
    assert math.isnan(causal_resolvability([], sw))


def test_empty_admissibility_ca_is_nan():
    sw = _switches(["A", "B"])
    res = causal_admissibility([], sw)
    assert all(math.isnan(r.CA_j) for r in res)
    assert all(r.Bayes_factor is None for r in res)


def test_empty_rach_summary_is_nan():
    sw = _switches(["A", "B"])
    summ = rach_summary([], sw)
    assert math.isnan(summ.causal_degeneracy)
    assert math.isnan(summ.causal_resolvability)


def test_nonempty_still_numeric():
    rows, sw = _rows([(1, 1)] * 10)
    # single combination → fully resolved, finite
    assert causal_degeneracy(rows, sw) == 0.0
    assert causal_resolvability(rows, sw) == 1.0
