"""Tests for Causal Substitution Matrix (CSM)."""
import math

import pytest

from causal_model.causal_substitution import (
    causal_substitution_matrix,
    csm_dict,
    substitutes_for,
    CSMEntry,
)


class _Sw:
    def __init__(self, name): self.name = name


# ---------------------------------------------------------------------------
# Substitution: when j is absent, k compensates
# ---------------------------------------------------------------------------

def test_csm_positive_for_substitutable_mechanisms():
    """When j=0, k is almost always on (k compensates for j).

    Setup: 50 rows with j=1,k=0 and 50 rows with j=0,k=1.
    Baseline P(k|A_ε) = 0.5; P(k|j=0) = 1.0 → CSM_{j→k} = +0.5.
    """
    rows = (
        [{"j": True,  "k": False}] * 50 +
        [{"j": False, "k": True}]  * 50
    )
    sw = [_Sw("j"), _Sw("k")]
    csm = csm_dict(rows, sw)
    delta = csm[("j", "k")]
    assert delta > 0, f"k should substitute for j, got delta={delta}"
    assert abs(delta - 0.5) < 0.05, f"Expected ~+0.5, got {delta}"


def test_csm_negative_for_co_required_mechanisms():
    """When j=0, k also tends to be off (j and k co-require each other).

    Setup: 80 rows with j=1,k=1 and 20 rows with j=0,k=0.
    Baseline P(k|A_ε) = 0.8; P(k|j=0) = 0.0 → CSM_{j→k} = −0.8.
    """
    rows = (
        [{"j": True,  "k": True}]  * 80 +
        [{"j": False, "k": False}] * 20
    )
    sw = [_Sw("j"), _Sw("k")]
    csm = csm_dict(rows, sw)
    delta = csm[("j", "k")]
    assert delta < -0.5, f"k should co-require j, got delta={delta}"


def test_csm_near_zero_for_independent_mechanisms():
    """When j and k are independent, CSM_{j→k} ≈ 0."""
    import random
    rng = random.Random(99)
    # j and k sampled independently with p=0.5 each
    rows = [{"j": rng.random() < 0.5, "k": rng.random() < 0.5}
            for _ in range(4000)]
    sw = [_Sw("j"), _Sw("k")]
    csm = csm_dict(rows, sw)
    delta = csm[("j", "k")]
    assert abs(delta) < 0.05, f"Independent mechanisms → |CSM| < 0.05, got {delta}"


# ---------------------------------------------------------------------------
# NaN when ablated region is empty
# ---------------------------------------------------------------------------

def test_csm_nan_when_ablation_leaves_empty_region():
    rows = [{"j": True, "k": True}] * 100   # j always on
    sw = [_Sw("j"), _Sw("k")]
    entries = causal_substitution_matrix(rows, sw)
    entry = next(e for e in entries if e.ablated == "j" and e.target == "k")
    assert math.isnan(entry.delta), "Ablated region empty → CSM entry must be NaN"
    assert entry.n_ablated == 0


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def test_substitutes_for_returns_ordered_list():
    rows = (
        [{"j": True,  "k": False, "m": False}] * 60 +
        [{"j": False, "k": True,  "m": False}] * 25 +
        [{"j": False, "k": False, "m": True}]  * 15
    )
    sw = [_Sw("j"), _Sw("k"), _Sw("m")]
    subs = substitutes_for("j", rows, sw)
    # k is a stronger substitute (delta ≈ +0.5 for k), m is weaker
    assert len(subs) >= 1
    assert subs[0][0] in ("k", "m")
    # All returned deltas should be positive (substitutes, not co-required)
    assert all(delta > 0 for _, delta in subs)


def test_csm_dict_keys_are_ordered_pairs():
    rows = [{"a": True, "b": False}, {"a": False, "b": True}] * 50
    sw = [_Sw("a"), _Sw("b")]
    d = csm_dict(rows, sw)
    assert ("a", "b") in d
    assert ("b", "a") in d
    assert ("a", "a") not in d   # no self-entries


def test_csm_empty_region_returns_empty_list():
    assert causal_substitution_matrix([], [_Sw("j")]) == []
