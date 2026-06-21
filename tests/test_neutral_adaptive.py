"""Tests for the neutral-by-default / forces-born-from-x_obs unifying example."""
import math

import pytest

from causal_model.neutral_adaptive import (
    run_neutral_adaptive,
    _abc_accept,
    _optimum,
    _p_neutral,
    _switches,
    _candidate_observations,
    _truth_overrides,
    _FORCES,
    NeutralAdaptiveResult,
)


# ---------------------------------------------------------------------------
# Benefit = cost balance optimum
# ---------------------------------------------------------------------------

def test_optimum_is_benefit_over_twice_cost():
    s = {"thermal_force": True, "seasonal_force": False}
    p = {"cost": 1.0, "b_th": 0.8, "b_se": 1.0, "drift": 0.0}
    assert _optimum(s, p, T=1.0) == pytest.approx(0.8 / 2.0)


def test_no_force_means_zero_optimum_everywhere():
    s = {"thermal_force": False, "seasonal_force": False}
    p = {"cost": 1.0, "b_th": 0.8, "b_se": 1.0, "drift": 0.0}
    assert all(_optimum(s, p, T) == 0.0 for T in (0.0, 0.5, 1.0))


def test_reproducible():
    a = _abc_accept(4000, seed=2)
    b = _abc_accept(4000, seed=2)
    assert len(a) == len(b)
    assert a[0] == b[0]


# ---------------------------------------------------------------------------
# Neutral as a first-class null
# ---------------------------------------------------------------------------

def test_neutral_flagged_iff_no_force_active():
    acc = _abc_accept(20000, seed=1)
    for r in acc[:200]:
        expected = (not r["thermal_force"]) and (not r["seasonal_force"])
        assert r["neutral"] == expected


def test_stronger_cline_excludes_neutral_monotonically():
    res = run_neutral_adaptive(truth="thermal", n_attempts=60000, seed=1)
    curve = res.p_neutral_by_strength
    assert len(curve) >= 3
    pn = [p for _, p in curve]
    # P(neutral) strictly decreases as the required cline strengthens
    assert all(pn[i] > pn[i + 1] for i in range(len(pn) - 1))
    assert pn[0] > pn[-1]


def test_forces_are_confounded_on_the_wild_cline():
    res = run_neutral_adaptive(truth="thermal", n_attempts=60000, seed=1)
    assert res.ca_j["thermal_force"] > 0.55
    assert res.ca_j["seasonal_force"] > 0.55
    assert abs(res.ca_j["thermal_force"] - res.ca_j["seasonal_force"]) < 0.05


# ---------------------------------------------------------------------------
# Replicate transect resolves selection vs drift (in both directions)
# ---------------------------------------------------------------------------

def test_parallel_replicate_confirms_selection():
    res = run_neutral_adaptive(truth="thermal", n_attempts=80000, seed=1)
    assert res.p_neutral_after < res.p_neutral          # neutral becomes less plausible
    assert res.p_neutral_after < 0.05


def test_nonparallel_replicate_reveals_drift():
    res = run_neutral_adaptive(truth="neutral", n_attempts=80000, seed=1)
    # observing a non-parallel replicate sharply raises the probability of drift
    assert res.p_neutral_after > res.p_neutral
    assert res.p_neutral_after > 5 * res.p_neutral


def test_nov_is_positive_for_the_replicate_transect():
    res = run_neutral_adaptive(truth="thermal", n_attempts=60000, seed=1)
    assert res.nov_ranking[0][0] == "replicate_transect"
    assert res.nov_ranking[0][1] > 0.0


def test_truth_overrides_cover_the_candidate():
    cand = _candidate_observations()[0]
    for truth in ("thermal", "seasonal", "neutral"):
        ov = _truth_overrides(truth)
        assert cand.name in ov
        assert ov[cand.name] in {o.name for o in cand.outcomes}


# ---------------------------------------------------------------------------
# Tier-A registration
# ---------------------------------------------------------------------------

def test_is_tier_a_validated():
    from causal_model.simulator import (
        evidence_tier, TIER_VALIDATED, VALIDATED_SIMULATOR_MODULES,
    )
    assert "causal_model.neutral_adaptive" in VALIDATED_SIMULATOR_MODULES
    assert evidence_tier("causal_model.neutral_adaptive") == TIER_VALIDATED
