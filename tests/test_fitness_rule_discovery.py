"""Tests for the fitness-derived ecogeographic-rule worked example.

The distinguishing property of this example is that the trait cline's *direction*
is not asserted — it emerges from argmax of a randomised fitness landscape — and
the heat/fasting confound is therefore *derived*, not hand-coded.
"""
import pytest

from causal_model.fitness_rule_discovery import (
    run_fitness_rule_discovery,
    _abc_accept,
    _optimum,
    _lin_sel,
    _switches,
    _candidate_observations,
    _truth_overrides,
    _WILD_SITES,
    _DECOUPLED_SITE,
    _FORCES,
    FitnessRuleResult,
)


# ---------------------------------------------------------------------------
# Fitness optimum / selection structure
# ---------------------------------------------------------------------------

def test_optimum_balances_benefit_against_quadratic_cost():
    # heat only, at the coldest site: z* = (b*T)/(2c) > 0
    s = {m: (m == "heat_conservation") for m in _FORCES}
    b = {m: 0.8 for m in _FORCES}
    z = _optimum(s, b, cost=1.0, T=1.0, S=0.0)
    assert z == pytest.approx(0.8 / 2.0)


def test_fasting_does_nothing_at_the_decoupled_site():
    # the whole identifiability hinges on this: fasting tracks seasonality S,
    # which is 0 at the decoupled (cold, aseasonal) site.
    T, S = _DECOUPLED_SITE
    assert S == 0.0
    assert _lin_sel("fasting_endurance", T, S, 1.0) == 0.0
    assert _lin_sel("heat_conservation", T, S, 1.0) > 0.0


def test_reproducible():
    a = _abc_accept(3000, seed=2)
    b = _abc_accept(3000, seed=2)
    assert len(a) == len(b)
    assert a[0] == b[0]


# ---------------------------------------------------------------------------
# The rule emerges and the confound is derived
# ---------------------------------------------------------------------------

def test_rule_emerges_from_fitness():
    acc = _abc_accept(20000, seed=1)
    assert len(acc) > 0
    # every accepted draw reproduces the published rule: body size increases
    # from the warmest wild site to the coldest
    n_sites = len(_WILD_SITES)
    for r in acc[:100]:
        assert r[f"z_site{n_sites - 1}"] - r["z_site0"] > 0.0


def test_heat_fasting_confound_is_derived_not_asserted():
    res = run_fitness_rule_discovery(truth="heat", n_attempts=30000, seed=1)
    assert isinstance(res, FitnessRuleResult)
    mins = {m for m, _ in res.explanations}
    assert mins == {frozenset({"heat_conservation"}), frozenset({"fasting_endurance"})}
    for _, mass in res.explanations:
        assert mass == pytest.approx(0.5, abs=0.05)
    assert res.R_expl < 0.05


def test_opposing_forces_are_disfavoured():
    # predation_escape and resource_limit push against the rule, so their CA_j
    # sits below the prior 0.5.
    res = run_fitness_rule_discovery(truth="heat", n_attempts=30000, seed=1)
    assert res.ca_j["predation_escape"] < 0.45
    assert res.ca_j["resource_limit"] < 0.45
    assert res.ca_j["heat_conservation"] > 0.6
    assert res.ca_j["fasting_endurance"] > 0.6


# ---------------------------------------------------------------------------
# Resolution by the decoupled-site observation (honest, symmetric, no artefact)
# ---------------------------------------------------------------------------

def test_nov_recommends_the_decoupled_site():
    res = run_fitness_rule_discovery(truth="heat", n_attempts=30000, seed=1)
    assert res.nov_ranking[0][0] == "decoupled_site_body_size"
    assert res.nov_ranking[0][1] > 0.0


@pytest.mark.parametrize("truth,survivor", [
    ("heat", frozenset({"heat_conservation"})),
    ("fasting", frozenset({"fasting_endurance"})),
])
def test_decoupled_site_resolves_symmetrically(truth, survivor):
    res = run_fitness_rule_discovery(truth=truth, n_attempts=40000, seed=1)
    assert res.R_expl_after == pytest.approx(1.0)
    assert [m for m, _ in res.explanations_after] == [survivor]


def test_truth_overrides_cover_the_candidate():
    cand = _candidate_observations()[0]
    for truth in ("heat", "fasting"):
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
    assert "causal_model.fitness_rule_discovery" in VALIDATED_SIMULATOR_MODULES
    assert evidence_tier("causal_model.fitness_rule_discovery") == TIER_VALIDATED
