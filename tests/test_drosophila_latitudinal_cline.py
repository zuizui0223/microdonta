"""Tests for the Drosophila latitudinal-cline CRC re-analysis harness.

These verify the STRUCTURE of the confound and its resolution (the asserted,
sign-only content). They do not test any quantitative empirical claim — those
inputs are placeholders to be filled from a real paper.
"""
import math

import pytest

from causal_model.worked_examples.drosophila_latitudinal_cline import (
    run_drosophila_cline,
    literature_constraints,
    _abc_accept,
    _switches,
    DrosophilaClineResult,
)
from causal_model.causal_replaceability import causal_replaceability_cost
from causal_model.rach_seq import filter_by_outcome
from causal_model.worked_examples.drosophila_latitudinal_cline import _candidate_observations


# ---------------------------------------------------------------------------
# (A) The published cline alone leaves adaptation NOT load-bearing
# ---------------------------------------------------------------------------

def test_body_size_cline_alone_does_not_single_out_adaptation():
    res = run_drosophila_cline(n_attempts=16000, seed=1)
    # all three mechanisms mutually replaceable: finite, similar CRC; R_expl≈0
    crcs = res.crc_published
    assert all(v != "∞" for v in crcs.values())
    vals = list(crcs.values())
    assert max(vals) - min(vals) < 0.3, f"CRCs should be similar, got {crcs}"
    assert res.R_expl < 0.05


# ---------------------------------------------------------------------------
# (B) The two real Drosophila levers resolve it
# ---------------------------------------------------------------------------

def test_neutral_marker_cline_pins_demography():
    """A neutral-marker cline is the private signature of demography → CRC→∞."""
    res = run_drosophila_cline(n_attempts=16000, seed=1)
    assert res.crc_after["neutral_cline_present"]["demographic_cline"] == "∞"


def test_flat_neutral_markers_rule_out_demography():
    """Flat neutral markers make demography freely droppable (CRC→0)."""
    res = run_drosophila_cline(n_attempts=16000, seed=1)
    assert res.crc_after["neutral_flat"]["demographic_cline"] == 0.0


def test_absence_of_parallelism_pins_demography_and_rules_out_selection():
    """No parallel cline on an independent continent ⇒ selection off, demography
    irreplaceable (the replicate-transect resolver, CRC form)."""
    res = run_drosophila_cline(n_attempts=16000, seed=1)
    prof = res.crc_after["parallel_absent"]
    assert prof["demographic_cline"] == "∞"
    assert prof["thermal_selection"] == 0.0
    assert prof["inversion_hitchhike"] == 0.0


def test_inversion_cline_pins_the_hitchhiking_mechanism():
    res = run_drosophila_cline(n_attempts=16000, seed=1)
    assert res.crc_after["inversion_cline_present"]["inversion_hitchhike"] == "∞"


def test_direct_ablation_matches_the_structure():
    """Cross-check via direct ablation: neutral-cline rows always have demography on."""
    acc = _abc_accept(16000, seed=1)
    cand = next(c for c in _candidate_observations() if c.name == "neutral_marker_cline")
    present = next(o for o in cand.outcomes if o.name == "neutral_cline_present")
    sub = filter_by_outcome(acc, present.extra_pattern_rows)
    assert sub, "there should be neutral-cline-present rows"
    assert all(r.get("demographic_cline") for r in sub), (
        "a neutral-marker cline can only arise when demography is active"
    )
    assert causal_replaceability_cost("demographic_cline", sub) == float("inf")


# ---------------------------------------------------------------------------
# (C) Replaceability-NOV ranks the private-signature measurements highest
# ---------------------------------------------------------------------------

def test_replaceability_nov_ranks_private_signature_observations_top():
    res = run_drosophila_cline(n_attempts=16000, seed=1)
    top_two = {r["candidate"] for r in res.replaceability_nov[:2]}
    # the private-signature measurements (neutral markers, inversion) carry the
    # most replaceability information; parallelism alone pins nothing to ∞
    assert "neutral_marker_cline" in top_two or "inversion_cline" in top_two
    assert res.replaceability_nov[-1]["candidate"] == "parallel_continents"


# ---------------------------------------------------------------------------
# Constraints are flagged placeholders; reproducibility; registration
# ---------------------------------------------------------------------------

def test_literature_constraints_are_flagged_placeholders():
    cons = literature_constraints()
    assert all("PLACEHOLDER" in c.description for c in cons)
    names = {c.name for c in cons}
    assert {"w_demographic", "w_thermal"} <= names


def test_reproducible():
    a = run_drosophila_cline(n_attempts=8000, seed=3)
    b = run_drosophila_cline(n_attempts=8000, seed=3)
    assert a.n_accepted == b.n_accepted
    assert a.crc_published == b.crc_published


def test_is_tier_a_validated():
    from causal_model.simulator import (
        evidence_tier, TIER_VALIDATED, VALIDATED_SIMULATOR_MODULES,
    )
    mod = "causal_model.worked_examples.drosophila_latitudinal_cline"
    assert mod in VALIDATED_SIMULATOR_MODULES
    assert evidence_tier(mod) == TIER_VALIDATED


def test_result_type():
    res = run_drosophila_cline(n_attempts=6000, seed=1)
    assert isinstance(res, DrosophilaClineResult)
    assert set(res.ca_j.keys()) == {
        "thermal_selection", "demographic_cline", "inversion_hitchhike",
    }
