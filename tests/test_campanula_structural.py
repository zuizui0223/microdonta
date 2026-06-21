"""Tests for the Tier-A (structural, magnitude-free) Campanula worked example."""
import pytest

from causal_model.campanula_structural import (
    run_campanula_structural,
    _abc_accept,
    _net_slopes,
    _switches,
    _candidate_observations,
    _truth_overrides,
    _MECHANISMS,
    _TRAITS,
    CampanulaResult,
)


# ---------------------------------------------------------------------------
# Sign structure / propagation
# ---------------------------------------------------------------------------

def test_net_slopes_only_active_mechanisms_contribute():
    s = {m: False for m in _MECHANISMS}
    mag = {(m, t): 0.5 for m in _MECHANISMS for t in _net_slopes.__globals__["_SIGNS"][m]}
    slopes = _net_slopes(s, mag)
    assert all(v == 0.0 for v in slopes.values())


def test_s2_does_not_drive_guide():
    # S2 alone: selfing up, flower down, but NO guide effect (key identifiability)
    s = {m: (m == "selfing_syndrome") for m in _MECHANISMS}
    mag = {(m, t): 0.5 for m in _MECHANISMS for t in _net_slopes.__globals__["_SIGNS"][m]}
    slopes = _net_slopes(s, mag)
    assert slopes["selfing_rate"] > 0
    assert slopes["flower_size"] < 0
    assert slopes["nectar_guide"] == 0.0
    assert slopes["neutral_diversity"] == 0.0


def test_s3_drives_guide_and_neutral_diversity():
    s = {m: (m == "island_common_cause") for m in _MECHANISMS}
    mag = {(m, t): 0.5 for m in _MECHANISMS for t in _net_slopes.__globals__["_SIGNS"][m]}
    slopes = _net_slopes(s, mag)
    assert slopes["nectar_guide"] < 0          # S3 drives guide
    assert slopes["neutral_diversity"] < 0     # S3 drives He


# ---------------------------------------------------------------------------
# ABC acceptance
# ---------------------------------------------------------------------------

def test_accepted_rows_match_published_pattern():
    from causal_model.campanula_structural import _NEAR, _FAR
    acc = _abc_accept(2000, seed=1)
    assert len(acc) > 0
    for r in acc:
        # selfing up, flower down at the far (isolated) end
        assert r[f"{_FAR}_selfing_rate"] > r[f"{_NEAR}_selfing_rate"]
        assert r[f"{_FAR}_flower_size"] < r[f"{_NEAR}_flower_size"]


def test_accepted_rows_require_s2_or_s3():
    # the pattern's only drivers of selfing/flower are S2 and S3, so the all-off
    # cell must be (almost) absent — a disjunction confound
    acc = _abc_accept(3000, seed=1)
    both_off = sum(1 for r in acc
                   if not r["selfing_syndrome"] and not r["island_common_cause"])
    assert both_off / len(acc) < 0.02


def test_reproducible():
    a = _abc_accept(1500, seed=5)
    b = _abc_accept(1500, seed=5)
    assert len(a) == len(b)
    assert a[0] == b[0]


# ---------------------------------------------------------------------------
# Confound + resolution
# ---------------------------------------------------------------------------

def test_s2_s3_confounded_on_published_pattern():
    res = run_campanula_structural(truth="S3", n_attempts=4000, seed=1)
    assert isinstance(res, CampanulaResult)
    # both driving mechanisms elevated above 0.5 and close to each other
    assert res.ca_j["selfing_syndrome"] > 0.6
    assert res.ca_j["island_common_cause"] > 0.6
    assert abs(res.ca_j["selfing_syndrome"] - res.ca_j["island_common_cause"]) < 0.1
    # S1 (guide) correctly left free near 0.5 — not driven by the published pattern
    assert abs(res.ca_j["guide_attracts_bombus"] - 0.5) < 0.1
    assert res.R_RACH < 0.3                      # low resolvability on pattern alone


def test_confound_edge_is_s2_s3():
    res = run_campanula_structural(truth="S3", n_attempts=4000, seed=1)
    assert "selfing_syndrome" in res.confound_edge
    assert "island_common_cause" in res.confound_edge


def test_resolution_truth_s3():
    res = run_campanula_structural(truth="S3", n_attempts=4000, seed=1)
    assert res.ca_j_after["island_common_cause"] > 0.9
    assert res.ca_j_after["selfing_syndrome"] < 0.1
    assert res.R_after > res.R_RACH


def test_resolution_truth_s2_is_symmetric():
    res = run_campanula_structural(truth="S2", n_attempts=4000, seed=1)
    assert res.ca_j_after["selfing_syndrome"] > 0.9
    assert res.ca_j_after["island_common_cause"] < 0.1


def test_nov_ranks_a_separating_gradient_first():
    res = run_campanula_structural(truth="S3", n_attempts=4000, seed=1)
    top = res.nov_ranking[0][0]
    # the top NOV must be a cline gradient that separates S2 from S3
    assert top in ("neutral_diversity_gradient", "nectar_guide_gradient")
    assert res.nov_ranking[0][1] > 0


def test_truth_overrides_cover_all_candidates():
    cands = _candidate_observations()
    ov = _truth_overrides("S3")
    for c in cands:
        assert c.name in ov
        assert ov[c.name] in {o.name for o in c.outcomes}


def test_is_tier_a_validated():
    from causal_model.simulator import evidence_tier, TIER_VALIDATED, VALIDATED_SIMULATOR_MODULES
    # the structural Campanula is a Tier-A simulator; register & check
    assert "causal_model.campanula_structural" in VALIDATED_SIMULATOR_MODULES
    assert evidence_tier("causal_model.campanula_structural") == TIER_VALIDATED
