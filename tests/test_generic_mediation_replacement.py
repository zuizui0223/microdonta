"""Tests for the generic mediation replacement worked example.

Two headline tests that validate the CRC framework's core claims:

  Case A (Z gradient only):
      S1 (direct) and S2 (mediated) are interchangeable — similar CRC.

  Case B (Z gradient + M gradient):
      Observing M pins S2 as irreplaceable; CRC(S2) rises sharply.
"""
import math

import pytest

from causal_model.worked_examples.generic_mediation_replacement import (
    run_generic_mediation,
    _abc_accept,
    _switches,
    GenericMediationResult,
)
from causal_model.causal_replaceability import causal_replaceability_cost
from causal_model.causal_substitution import causal_substitution_matrix


# ---------------------------------------------------------------------------
# Case A: direct and mediated mechanisms are interchangeable
# ---------------------------------------------------------------------------

def test_direct_mediated_have_similar_crc_in_case_a():
    """With only Z gradient as y_obs, direct and mediated are freely substitutable."""
    res = run_generic_mediation(n_attempts=10000, seed=1, case="A")
    crc_d = res.crc["direct"]
    crc_m = res.crc["mediated"]
    # Both finite (neither is indispensable alone)
    assert crc_d < float("inf"), "direct should not be indispensable in Case A"
    assert crc_m < float("inf"), "mediated should not be indispensable in Case A"
    # CRCs within 0.6 bits of each other (symmetric interchangeability)
    assert abs(crc_d - crc_m) < 0.6, (
        f"Case A: CRC(direct)={crc_d:.3f}, CRC(mediated)={crc_m:.3f} — "
        f"should be similar (interchangeable)"
    )


def test_csm_direct_to_mediated_positive_in_case_a():
    """When direct is ablated in Case A, mediated substitutes."""
    acc = _abc_accept(10000, seed=1, case="A")
    sw = _switches()
    entries = causal_substitution_matrix(acc, sw)
    entry = next((e for e in entries if e.ablated == "direct" and e.target == "mediated"), None)
    assert entry is not None
    assert entry.delta > 0.0, (
        f"CSM[direct→mediated] should be positive (mediated substitutes for direct), "
        f"got {entry.delta:.4f}"
    )


def test_neutral_does_not_substitute_well_in_case_a():
    """Neutral drift is not a good substitute for directional mechanisms."""
    acc = _abc_accept(10000, seed=1, case="A")
    sw = _switches()
    entries = causal_substitution_matrix(acc, sw)
    d_to_n = next((e for e in entries if e.ablated == "direct" and e.target == "neutral"), None)
    assert d_to_n is not None
    # Neutral should NOT strongly compensate for directional loss (CSM ≤ direct-to-mediated)
    d_to_m = next((e for e in entries if e.ablated == "direct" and e.target == "mediated"), None)
    assert d_to_n.delta <= d_to_m.delta + 0.05, (
        "Neutral should not be a better substitute than mediated for direct"
    )


# ---------------------------------------------------------------------------
# Case B: observing M gradient pins the mediated mechanism
# ---------------------------------------------------------------------------

def test_mediated_crc_increases_after_observing_M_gradient():
    """Observing M↑ with x makes the mediated mechanism irreplaceable (CRC rises)."""
    res_a = run_generic_mediation(n_attempts=10000, seed=1, case="A")
    res_b = run_generic_mediation(n_attempts=10000, seed=1, case="B")
    crc_m_a = res_a.crc["mediated"]
    crc_m_b = res_b.crc["mediated"]
    assert crc_m_b > crc_m_a, (
        f"CRC(mediated) should increase from Case A ({crc_m_a:.3f}) to Case B ({crc_m_b:.3f}) "
        f"because observing M gradient pins the mediated mechanism"
    )


def test_mediated_is_indispensable_in_case_b():
    """In Case B, NO accepted draw has mediated=False (CRC(mediated) = ∞)."""
    acc_b = _abc_accept(10000, seed=1, case="B")
    crc_mediated = causal_replaceability_cost("mediated", acc_b)
    # M↑ can only be produced by S2; so mediated must be active in every accepted draw
    assert crc_mediated == float("inf"), (
        f"CRC(mediated) should be ∞ in Case B (M gradient pins S2), got {crc_mediated}"
    )


def test_direct_remains_replaceable_in_case_b():
    """Once mediated is pinned by M gradient, direct is redundant and CRC(direct) is finite."""
    acc_b = _abc_accept(10000, seed=1, case="B")
    crc_direct = causal_replaceability_cost("direct", acc_b)
    assert crc_direct < float("inf"), (
        "CRC(direct) should be finite in Case B (direct is optional when mediated is always on)"
    )


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

def test_reproducible():
    a = run_generic_mediation(n_attempts=6000, seed=42, case="A")
    b = run_generic_mediation(n_attempts=6000, seed=42, case="A")
    assert a.n_accepted == b.n_accepted
    assert a.crc == b.crc


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

def test_result_is_generic_mediation_result():
    res = run_generic_mediation(n_attempts=4000, seed=1, case="A")
    assert isinstance(res, GenericMediationResult)
    assert res.n_accepted > 0
    assert set(res.crc.keys()) == {"direct", "mediated", "neutral"}
    assert 0.0 <= res.p_neutral <= 1.0
