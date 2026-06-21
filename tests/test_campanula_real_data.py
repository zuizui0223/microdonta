"""Tests for RACH applied to the real published Campanula microdonta record."""
import pytest

from causal_model.campanula_real_data import (
    run_campanula_real,
    _real_y_obs,
    CampanulaRealResult,
)


# ---------------------------------------------------------------------------
# The real y_obs is exactly the two source-confirmed gradients
# ---------------------------------------------------------------------------

def test_real_y_obs_is_the_two_confirmed_gradients():
    yobs = _real_y_obs()
    by_var = {r["variable"]: r for r in yobs}
    assert "selfing_rate" in by_var and by_var["selfing_rate"]["direction"] == "positive"
    assert "flower_size" in by_var and by_var["flower_size"]["direction"] == "negative"
    # nothing pending/planned (guide, Fis, herkogamy) leaks into the ABC targets
    assert "nectar_guide" not in by_var
    assert "Fis" not in by_var


# ---------------------------------------------------------------------------
# On the published record the mechanism is honestly unresolved
# ---------------------------------------------------------------------------

def test_published_record_leaves_s2_s3_confounded():
    res = run_campanula_real(n_attempts=6000, seed=1)
    assert isinstance(res, CampanulaRealResult)
    mins = {m for m, _ in res.explanations}
    assert mins == {frozenset({"selfing_syndrome"}), frozenset({"island_common_cause"})}
    assert res.R_expl < 0.05                       # RACH does not claim resolution
    assert "selfing_syndrome" in res.confound_edge
    assert "island_common_cause" in res.confound_edge


def test_guide_switch_is_left_free_by_the_published_pattern():
    res = run_campanula_real(n_attempts=6000, seed=1)
    # the published gradients say nothing about the nectar guide, so S1 sits near 0.5
    assert abs(res.ca_j["guide_attracts_bombus"] - 0.5) < 0.1


def test_reproducible():
    a = run_campanula_real(n_attempts=4000, seed=2)
    b = run_campanula_real(n_attempts=4000, seed=2)
    assert a.n_accepted == b.n_accepted
    assert a.R_expl == b.R_expl


# ---------------------------------------------------------------------------
# The deliverable: a cost-aware study-design ranking over real experiments
# ---------------------------------------------------------------------------

def test_study_design_uses_real_design_estimates():
    res = run_campanula_real(n_attempts=6000, seed=1)
    bagging = next(r for r in res.study_design
                   if r["real_experiment"] == "bagging_autonomous_selfing")
    # values come straight from future_observations.csv
    assert bagging["design_cost"] == pytest.approx(0.4)
    assert bagging["design_feasibility"] == pytest.approx(0.8)


def test_bagging_experiment_is_the_most_efficient_next_step():
    res = run_campanula_real(n_attempts=6000, seed=1)
    top = res.study_design[0]
    assert top["real_experiment"] == "bagging_autonomous_selfing"
    # a reproductive-assurance assay (near-)fully resolves the explanation (EVSI ≈ 1.0)
    assert top["NOV_EVSI_Rexpl"] > 0.95
    assert top["efficiency"] is not None
    # and it is more efficient than the genetic-marker alternative
    others = {r["real_experiment"]: r for r in res.study_design}
    assert top["efficiency"] > others["neutral_marker_structure"]["efficiency"]


def test_every_candidate_has_a_nov_score():
    res = run_campanula_real(n_attempts=6000, seed=1)
    assert len(res.study_design) >= 3
    for r in res.study_design:
        assert r["NOV_EVSI_Rexpl"] is not None
        assert r["NOV_EVSI_Rexpl"] >= 0.0
