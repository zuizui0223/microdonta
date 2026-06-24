"""Tests for the converse-Bergmann 'cryptic selection' discovery example.

The non-obvious claims being pinned down:
  * a converse cline (size smaller where colder) does NOT exclude cold-favouring
    selection;
  * the converse cline confounds an adaptive (warm selection) with a non-adaptive
    (developmental constraint) explanation;
  * an extended-season common garden resolves it, and in the cryptic case the
    cline FLIPS from converse to Bergmann.
"""
import pytest

from causal_model.converse_bergmann import (
    run_converse_bergmann,
    _abc_accept,
    _desired,
    _realised,
    _switches,
    _candidate_observations,
    _truth_overrides,
    _SITES,
    _MECHS,
    ConverseBergmannResult,
)


# ---------------------------------------------------------------------------
# The constraint actually flips the cline (mechanism of the surprise)
# ---------------------------------------------------------------------------

def test_constraint_can_flip_cold_selection_to_converse():
    # cold_selection wants large bodies in the cold (Bergmann), but with the
    # season constraint binding, realised size falls with coldness (converse).
    s = {"cold_selection": True, "warm_selection": False, "season_constraint": True}
    p = {"base": 0.5, "cost": 1.0, "b_cold": 1.4, "b_warm": 1.0, "kappa": 0.4, "cmin": 0.0}
    realised = [_realised(s, p, T) for T in _SITES]
    desired = [_desired(s, p, T) for T in _SITES]
    assert desired[-1] > desired[0]          # selection wants BIGGER in the cold
    assert realised[-1] < realised[0]        # realised body size is SMALLER in the cold


def test_reproducible():
    a = _abc_accept(4000, seed=3)
    b = _abc_accept(4000, seed=3)
    assert len(a) == len(b)
    assert a[0] == b[0]


def test_accepted_rows_are_converse():
    acc = _abc_accept(30000, seed=1)
    assert len(acc) > 0
    n = len(_SITES)
    for r in acc[:100]:
        assert r[f"z{n - 1}"] < r["z0"]      # size smaller at the cold end


# ---------------------------------------------------------------------------
# The discovery: converse does not exclude cold-favouring selection
# ---------------------------------------------------------------------------

def test_converse_does_not_exclude_cold_selection():
    res = run_converse_bergmann(truth="cold_masked", n_attempts=60000, seed=1)
    assert isinstance(res, ConverseBergmannResult)
    # the naive reading would put this near 0; RACH keeps it near the prior — the
    # cold-favouring hypothesis is emphatically NOT ruled out by a converse cline.
    assert res.ca_cold_selection > 0.3
    assert res.ca_cold_selection < 0.5


def test_converse_confounds_adaptive_with_developmental():
    res = run_converse_bergmann(truth="cold_masked", n_attempts=60000, seed=1)
    mins = {m for m, _ in res.explanations}
    assert mins == {frozenset({"warm_selection"}), frozenset({"season_constraint"})}
    assert res.R_expl < 0.1                   # essentially unresolved on the cline alone


# ---------------------------------------------------------------------------
# Resolution by the extended-season common garden
# ---------------------------------------------------------------------------

def test_nov_recommends_the_common_garden():
    res = run_converse_bergmann(truth="cold_masked", n_attempts=60000, seed=1)
    assert res.nov_ranking[0][0] == "extended_season_common_garden"
    assert res.nov_ranking[0][1] > 0.0


def test_cryptic_case_flips_to_bergmann_and_reveals_cold_selection():
    res = run_converse_bergmann(truth="cold_masked", n_attempts=80000, seed=1)
    assert res.R_expl_after == pytest.approx(1.0)
    # the common garden reveals that cold-favouring selection was there all along
    assert res.cold_selection_after == pytest.approx(1.0)
    assert [m for m, _ in res.explanations_after] == [
        frozenset({"cold_selection", "season_constraint"})
    ]


def test_warm_truth_resolves_to_warm_selection():
    res = run_converse_bergmann(truth="warm", n_attempts=80000, seed=1)
    assert res.R_expl_after == pytest.approx(1.0)
    assert [m for m, _ in res.explanations_after] == [frozenset({"warm_selection"})]
    assert res.cold_selection_after < 0.35    # cold selection now disfavoured


def test_constraint_truth_resolves_to_developmental_constraint():
    res = run_converse_bergmann(truth="constraint", n_attempts=80000, seed=1)
    assert res.R_expl_after == pytest.approx(1.0)
    assert [m for m, _ in res.explanations_after] == [frozenset({"season_constraint"})]


def test_truth_overrides_cover_the_candidate():
    cand = _candidate_observations()[0]
    for truth in ("cold_masked", "warm", "constraint"):
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
    assert "causal_model.converse_bergmann" in VALIDATED_SIMULATOR_MODULES
    assert evidence_tier("causal_model.converse_bergmann") == TIER_VALIDATED
