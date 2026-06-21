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


# ---------------------------------------------------------------------------
# Causal Replaceability read of the same published admissible region
# ---------------------------------------------------------------------------

def test_published_record_makes_S2_S3_mutually_replaceable():
    """On the published gradients, S2 and S3 each have finite, similar CRC:
    each can stand in for the other (the disjunction confound in CRC terms)."""
    res = run_campanula_real(n_attempts=8000, seed=1)
    crc_s2 = res.crc_published["selfing_syndrome"]
    crc_s3 = res.crc_published["island_common_cause"]
    # both finite (neither indispensable) and close (mutually replaceable)
    assert crc_s2 != "∞" and crc_s3 != "∞"
    assert abs(crc_s2 - crc_s3) < 0.3, (
        f"S2/S3 should be mutually replaceable: CRC(S2)={crc_s2}, CRC(S3)={crc_s3}"
    )


def test_flat_guide_makes_selfing_syndrome_irreplaceable():
    """A flat nectar guide rules out the common cause (S3 forces guide↓),
    so the selfing syndrome S2 becomes irreplaceable: CRC(S2)→∞."""
    res = run_campanula_real(n_attempts=8000, seed=1)
    assert res.crc_after_guide_flat.get("selfing_syndrome") == "∞"
    # and the common cause becomes freely droppable
    assert res.crc_after_guide_flat.get("island_common_cause") == 0.0


def test_declining_guide_raises_but_does_not_pin_the_common_cause():
    """A declining guide is consistent with S1 (Bombus loss) OR S3, so CRC(S3)
    rises above its published value but stays finite (honest non-resolution)."""
    res = run_campanula_real(n_attempts=8000, seed=1)
    crc_s3_pub = res.crc_published["island_common_cause"]
    crc_s3_dec = res.crc_after_guide_declines["island_common_cause"]
    assert crc_s3_dec != "∞", "a declining guide should NOT prove S3 (S1 can drive it too)"
    assert crc_s3_dec > crc_s3_pub, "a declining guide should still raise suspicion on S3"


def test_replaceability_nov_ranks_every_candidate():
    res = run_campanula_real(n_attempts=8000, seed=1)
    assert len(res.replaceability_nov) >= 3
    vals = [r["NOV_CRC_total"] for r in res.replaceability_nov]
    # sorted descending
    assert vals == sorted(vals, reverse=True)
    # the neutral-diversity gradient (isolates S3 cleanly) is a top-value observation
    assert res.replaceability_nov[0]["candidate"] in (
        "neutral_diversity_gradient", "bagging_RA_assay"
    )
