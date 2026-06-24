"""Tests for the adaptation-vs-plasticity Tier-A worked example."""
import pytest

from causal_model.adaptation_plasticity import (
    run_adaptation_plasticity,
    _abc_accept,
    _net,
    _candidate_observations,
    _truth_overrides,
    _MECHANISMS,
    _OBSERVABLES,
    _SIGNS,
    AdaptationPlasticityResult,
)


# ---------------------------------------------------------------------------
# Sign structure / acceptance
# ---------------------------------------------------------------------------

def test_only_genetic_drives_cost_and_second_gen():
    mag = {(m, o): 0.5 for m in _MECHANISMS for o in _SIGNS[m]}
    g = _net({m: (m == "genetic_adaptation") for m in _MECHANISMS}, mag)
    assert g["benign_site_cost"] > 0
    assert g["second_gen_diff"] > 0
    assert g["common_garden_diff"] > 0

    p = _net({m: (m == "phenotypic_plasticity") for m in _MECHANISMS}, mag)
    assert p["field_cline"] > 0
    assert p["common_garden_diff"] == 0.0          # plasticity vanishes in common garden
    assert p["second_gen_diff"] == 0.0
    assert p["benign_site_cost"] == 0.0

    mat = _net({m: (m == "maternal_effects") for m in _MECHANISMS}, mag)
    assert mat["common_garden_diff"] > 0           # persists in F1
    assert mat["second_gen_diff"] == 0.0           # gone by F2
    assert mat["benign_site_cost"] == 0.0


def test_accepted_rows_show_field_cline():
    acc = _abc_accept(3000, seed=1)
    assert len(acc) > 0
    for r in acc[:50]:
        assert r["high_field_cline"] > r["low_field_cline"]


def test_reproducible():
    a = _abc_accept(2000, seed=4)
    b = _abc_accept(2000, seed=4)
    assert len(a) == len(b)
    assert a[0] == b[0]


# ---------------------------------------------------------------------------
# The three-way confound on the field cline alone
# ---------------------------------------------------------------------------

def test_field_cline_is_a_three_way_disjunction():
    res = run_adaptation_plasticity(truth="genetic", n_attempts=6000, seed=1)
    assert isinstance(res, AdaptationPlasticityResult)
    mins = {m for m, _ in res.explanations}
    assert mins == {
        frozenset({"genetic_adaptation"}),
        frozenset({"phenotypic_plasticity"}),
        frozenset({"maternal_effects"}),
    }
    # roughly equal masses, essentially unresolved
    for _, mass in res.explanations:
        assert mass == pytest.approx(1 / 3, abs=0.05)
    assert res.R_expl < 0.05


# ---------------------------------------------------------------------------
# NOV: the F1 common garden cannot, by itself, beat the genetic-isolating obs
# ---------------------------------------------------------------------------

def test_nov_ranks_genetic_isolating_observations_above_f1_garden():
    res = run_adaptation_plasticity(truth="genetic", n_attempts=6000, seed=1)
    nov = dict(res.nov_ranking)
    # second-gen garden and the cost assay each isolate genetic adaptation and so
    # carry higher expected resolvability than a single-generation common garden,
    # which leaves the genetic/maternal ambiguity unresolved.
    assert nov["second_gen_common_garden"] > nov["common_garden"]
    assert nov["benign_site_cost_assay"] > nov["common_garden"]
    assert all(v >= 0 for v in nov.values())


# ---------------------------------------------------------------------------
# Sequential resolution recovers whichever process is the truth
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("truth,survivor", [
    ("genetic", frozenset({"genetic_adaptation"})),
    ("plastic", frozenset({"phenotypic_plasticity"})),
    ("maternal", frozenset({"maternal_effects"})),
])
def test_sequential_resolution_recovers_truth(truth, survivor):
    res = run_adaptation_plasticity(truth=truth, n_attempts=6000, seed=1)
    assert res.seq_steps, "expected at least one resolution step"
    final_cand, final_expl, final_R = res.seq_steps[-1]
    assert final_R == pytest.approx(1.0)
    assert [m for m, _ in final_expl] == [survivor]
    assert res.R_expl_after == pytest.approx(1.0)


def test_truth_overrides_cover_every_candidate():
    cands = _candidate_observations()
    for truth in ("genetic", "plastic", "maternal"):
        ov = _truth_overrides(truth)
        for c in cands:
            assert c.name in ov
            assert ov[c.name] in {o.name for o in c.outcomes}


# ---------------------------------------------------------------------------
# Tier-A registration
# ---------------------------------------------------------------------------

def test_is_tier_a_validated():
    from causal_model.simulator import (
        evidence_tier, TIER_VALIDATED, VALIDATED_SIMULATOR_MODULES,
    )
    assert "causal_model.adaptation_plasticity" in VALIDATED_SIMULATOR_MODULES
    assert evidence_tier("causal_model.adaptation_plasticity") == TIER_VALIDATED
