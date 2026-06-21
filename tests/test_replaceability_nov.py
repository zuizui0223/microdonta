"""Tests for replaceability-aware NOV (expected ΔCRC)."""
import math

import pytest

from causal_model.replaceability_nov import (
    replaceability_nov,
    replaceability_nov_profile,
    replaceability_nov_total,
    rank_candidates_by_replaceability_nov,
)
from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome as ObservationOutcome


class _Sw:
    def __init__(self, name): self.name = name


def _make_candidate(name, outcome_a_rows, outcome_b_rows, p_a=0.5, p_b=0.5):
    """Build a two-outcome CandidateObservation for testing."""
    return CandidateObservation(
        name=name,
        description="",
        target_switches=[],
        rationale="",
        outcomes=[
            ObservationOutcome(
                name="outcome_a",
                description="",
                extra_pattern_rows=outcome_a_rows,
                prior_probability=p_a,
            ),
            ObservationOutcome(
                name="outcome_b",
                description="",
                extra_pattern_rows=outcome_b_rows,
                prior_probability=p_b,
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Basic NOV_CRC properties
# ---------------------------------------------------------------------------

def test_replaceability_nov_is_positive_when_observation_pins_mechanism():
    """An observation that pins j=1 in one outcome increases CRC(j) in that arm."""
    # 100 rows: j=0 (50) and j=1 (50)
    # Outcome A filters to j=1 rows only; Outcome B filters to j=0 rows
    rows = [{"j": True,  "keep_a": True,  "keep_b": False}] * 50 + \
           [{"j": False, "keep_a": False, "keep_b": True}]  * 50

    # Outcome A extra pattern: keep_a must be True → selects j=1 rows
    outcome_a = [{"type": "gradient_slope", "variable": "keep_a",
                  "expected_direction": "positive",
                  "left_population": "", "right_population": ""}]
    # Outcome B extra pattern: selects j=0 rows
    outcome_b = [{"type": "gradient_slope", "variable": "keep_b",
                  "expected_direction": "positive",
                  "left_population": "", "right_population": ""}]

    # Use a simpler approach: build rows where the pattern columns allow filtering
    # Use pairwise_relation type with synthetic pop columns
    rows2 = []
    for i in range(50):
        rows2.append({"j": True, "pop_high_val": 1.0, "pop_low_val": 0.0})
    for i in range(50):
        rows2.append({"j": False, "pop_high_val": 0.0, "pop_low_val": 1.0})

    # Outcome A: pop_high_val > pop_low_val (pairwise) → selects j=True rows
    oa = [{"type": "pairwise_relation", "variable": "val",
           "left_population": "pop_high", "right_population": "pop_low",
           "relation": "pop_high > pop_low"}]
    # Outcome B: pop_low_val > pop_high_val → selects j=False rows
    ob = [{"type": "pairwise_relation", "variable": "val",
           "left_population": "pop_low", "right_population": "pop_high",
           "relation": "pop_low > pop_high"}]

    cand = _make_candidate("test_obs", oa, ob)
    nov = replaceability_nov(cand, "j", rows2)
    # In outcome A (j all True), CRC(j|A) = inf.
    # In outcome B (j all False), CRC(j|B) = 0.
    # NOV = 0.5*(inf_sentinel - 1.0) + 0.5*(0.0 - 1.0) → net positive (inf_sentinel >> 1)
    assert nov > 0.0, f"Expected positive NOV_CRC, got {nov}"


def test_replaceability_nov_zero_for_uninformative_observation():
    """An observation that doesn't change the A_ε composition has NOV ≈ 0."""
    rows = [{"j": True}, {"j": False}] * 100  # 50/50
    # Both outcomes are uninformative (match all rows)
    oa = []  # no filter → selects everything
    ob = []
    cand = _make_candidate("noop", oa, ob)
    nov = replaceability_nov(cand, "j", rows)
    assert abs(nov) < 0.5, f"Uninformative observation should have NOV ≈ 0, got {nov}"


def test_replaceability_nov_profile_covers_all_switches():
    rows = [{"j": True, "k": False}] * 50 + [{"j": False, "k": True}] * 50
    cand = _make_candidate("q", [], [])
    sw = [_Sw("j"), _Sw("k")]
    profile = replaceability_nov_profile(cand, rows, sw)
    assert set(profile.keys()) == {"j", "k"}


def test_replaceability_nov_nan_for_empty_region():
    cand = _make_candidate("q", [], [])
    nov = replaceability_nov(cand, "j", [])
    assert math.isnan(nov)


# ---------------------------------------------------------------------------
# Candidate ranking
# ---------------------------------------------------------------------------

def test_rank_candidates_returns_sorted_list():
    rows = [{"j": True, "pop_high_v": 1.0, "pop_low_v": 0.0}] * 50 + \
           [{"j": False, "pop_high_v": 0.0, "pop_low_v": 1.0}] * 50

    oa = [{"type": "pairwise_relation", "variable": "v",
            "left_population": "pop_high", "right_population": "pop_low",
            "relation": "pop_high > pop_low"}]
    ob = [{"type": "pairwise_relation", "variable": "v",
            "left_population": "pop_low", "right_population": "pop_high",
            "relation": "pop_low > pop_high"}]

    informative = _make_candidate("informative", oa, ob)
    noop = _make_candidate("noop", [], [])

    sw = [_Sw("j")]
    ranking = rank_candidates_by_replaceability_nov([informative, noop], rows, sw)
    assert ranking[0][0] == "informative"
    assert ranking[0][1] >= ranking[1][1]


# ---------------------------------------------------------------------------
# Neutral mechanisms have low NOV_CRC in directional context
# ---------------------------------------------------------------------------

def test_neutral_has_low_replaceability_nov_in_directional_context():
    """In A_ε dominated by directional mechanisms, neutral is redundant (CRC≈0).

    Observing an additional directional pattern won't change CRC(neutral) much,
    so NOV_CRC(neutral) should be small relative to NOV_CRC(directional).
    """
    # 80 rows: directional=True, neutral=False (directional dominates)
    # 10 rows: directional=False, neutral=True
    # 10 rows: directional=True, neutral=True
    rows = (
        [{"directional": True,  "neutral": False, "pop_h_v": 1.0, "pop_l_v": 0.0}] * 80 +
        [{"directional": False, "neutral": True,  "pop_h_v": 0.5, "pop_l_v": 0.5}] * 10 +
        [{"directional": True,  "neutral": True,  "pop_h_v": 1.0, "pop_l_v": 0.0}] * 10
    )
    oa = [{"type": "pairwise_relation", "variable": "v",
           "left_population": "pop_h", "right_population": "pop_l",
           "relation": "pop_h > pop_l"}]
    cand = _make_candidate("directional_obs", oa, [])
    sw = [_Sw("directional"), _Sw("neutral")]

    nov_directional = replaceability_nov(cand, "directional", rows)
    nov_neutral = replaceability_nov(cand, "neutral", rows)
    # Directional observation pins the directional mechanism; neutral gain is small
    assert nov_directional >= nov_neutral
