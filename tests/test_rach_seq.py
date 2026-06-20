"""Tests for RACH-SEQ: sequential mechanism equivalence class reduction."""
from causal_model.rach_seq import (
    rach_seq,
    filter_by_outcome,
    expected_edge_cuts,
    SeqResult,
    SeqStep,
    _row_matches_pattern,
)
from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome


class _SW:
    def __init__(self, name):
        self.name = name


def _switches(names):
    return [_SW(n) for n in names]


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _disjunction_rows(n_per_combo=20):
    """A, B in disjunction: (0,0) absent. C pinned ON, D pinned OFF.

    Each row also carries pop1_trait: high when A=1, low otherwise.
    This lets filter_by_outcome distinguish A=1 rows.
    """
    rows = []
    for a, b in [(1, 0), (0, 1), (1, 1)]:
        for _ in range(n_per_combo):
            rows.append({
                "A": a, "B": b, "C": True, "D": False,
                "pop1_trait": 0.75 if a else 0.25,
                "pop2_trait": 0.50,
            })
    return rows


def _candidate_pins_A(name="confirm_A"):
    """Candidate with one outcome that filters to A=1 rows via absolute_summary."""
    return CandidateObservation(
        name=name,
        description="Observe trait at pop1 to confirm A is active.",
        target_switches=["A"],
        rationale="High pop1_trait implies A=1.",
        outcomes=[
            CandidateOutcome(
                name="A_active",
                description="pop1_trait is high → A is active",
                prior_probability=0.67,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "trait",
                    "population": "pop1",
                    "observed_value": "0.75",
                    "scale": "0.05",
                }],
            ),
            CandidateOutcome(
                name="A_inactive",
                description="pop1_trait is low → A inactive",
                prior_probability=0.33,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "trait",
                    "population": "pop1",
                    "observed_value": "0.25",
                    "scale": "0.05",
                }],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# filter_by_outcome
# ---------------------------------------------------------------------------

def test_filter_absolute_summary_selects_matching_rows():
    rows = [
        {"pop1_val": 0.80, "A": True},
        {"pop1_val": 0.20, "A": False},
        {"pop1_val": 0.75, "A": True},
    ]
    pattern = [{
        "type": "absolute_summary",
        "variable": "val",
        "population": "pop1",
        "observed_value": "0.75",
        "scale": "0.05",
    }]
    kept = filter_by_outcome(rows, pattern)
    # |0.80-0.75|=0.05 ≤ 0.10 → in; |0.20-0.75|=0.55 > 0.10 → out
    assert len(kept) == 2
    assert all(r["A"] for r in kept)


def test_filter_pairwise_relation_less_than():
    rows = [
        {"pop1_x": 0.1, "pop2_x": 0.9},  # pop1 < pop2 ✓
        {"pop1_x": 0.8, "pop2_x": 0.2},  # pop1 > pop2 ✗
        {"pop1_x": 0.3, "pop2_x": 0.6},  # pop1 < pop2 ✓
    ]
    pattern = [{"type": "pairwise_relation", "variable": "x",
                "left_population": "pop1", "right_population": "pop2",
                "relation": "pop1 < pop2"}]
    kept = filter_by_outcome(rows, pattern)
    assert len(kept) == 2


def test_filter_gradient_slope_negative():
    rows = [
        {"mainland_y": 0.9, "Oshima_y": 0.6, "Hachijo_y": 0.3},  # negative ✓
        {"mainland_y": 0.2, "Oshima_y": 0.5, "Hachijo_y": 0.8},  # positive ✗
    ]
    pattern = [{"type": "gradient_slope", "variable": "y",
                "expected_direction": "negative"}]
    kept = filter_by_outcome(rows, pattern)
    assert len(kept) == 1
    assert kept[0]["mainland_y"] == 0.9


def test_filter_unknown_type_passes_all():
    rows = [{"x": 1}, {"x": 2}]
    kept = filter_by_outcome(rows, [{"type": "unknown_future_type", "variable": "x"}])
    assert len(kept) == 2


def test_filter_missing_column_passes_row():
    rows = [{"pop1_val": 0.9}, {"other_col": 0.1}]
    pattern = [{"type": "absolute_summary", "variable": "val",
                "population": "pop1", "observed_value": "0.1", "scale": "0.01"}]
    kept = filter_by_outcome(rows, pattern)
    # Row without column → included conservatively
    assert {"other_col": 0.1} in kept


# ---------------------------------------------------------------------------
# _row_matches_pattern edge cases
# ---------------------------------------------------------------------------

def test_rank_order_decreasing():
    row = {"mainland_z": 1.0, "Oshima_z": 0.7, "Hachijo_z": 0.3}
    pat = {"type": "rank_order", "variable": "z", "expected_direction": "decreasing"}
    assert _row_matches_pattern(row, pat)


def test_rank_order_decreasing_fails_when_ascending():
    row = {"mainland_z": 0.3, "Oshima_z": 0.7, "Hachijo_z": 1.0}
    pat = {"type": "rank_order", "variable": "z", "expected_direction": "decreasing"}
    assert not _row_matches_pattern(row, pat)


# ---------------------------------------------------------------------------
# expected_edge_cuts
# ---------------------------------------------------------------------------

def test_expected_edge_cuts_returns_positive_for_edge_candidate():
    rows = _disjunction_rows()
    sw = _switches(["A", "B", "C", "D"])
    from causal_model.mechanism_equivalence import mechanism_equivalence_structure
    structure = mechanism_equivalence_structure(rows, sw)
    assert len(structure.edges) >= 1   # sanity check

    cand = _candidate_pins_A()
    ec = expected_edge_cuts(cand, rows, sw, structure)
    assert ec > 0


def test_expected_edge_cuts_zero_when_no_edges():
    from causal_model.mechanism_equivalence import EquivalenceStructure
    sw = _switches(["A"])
    empty_structure = EquivalenceStructure(
        n_accepted=10, ca_j={"A": 0.5},
        pinned_on=[], pinned_off=[], free=["A"],
        edges=[], n_admissible_configs=2, n_total_configs=2,
    )
    cand = _candidate_pins_A()
    assert expected_edge_cuts(cand, [], sw, empty_structure) == 0.0


def test_expected_edge_cuts_heuristic_for_no_outcomes():
    rows = _disjunction_rows()
    sw = _switches(["A", "B", "C", "D"])
    from causal_model.mechanism_equivalence import mechanism_equivalence_structure
    structure = mechanism_equivalence_structure(rows, sw)

    cand = CandidateObservation(
        name="heuristic_cand", description="no outcomes", target_switches=["A", "B"],
        rationale="test", outcomes=[],
    )
    ec = expected_edge_cuts(cand, rows, sw, structure)
    # Heuristic: ≥ 1 edge involves A or B, discounted by 0.4
    assert ec > 0


# ---------------------------------------------------------------------------
# rach_seq — core algorithm
# ---------------------------------------------------------------------------

def test_rach_seq_empty_region_returns_immediately():
    result = rach_seq([], _switches(["A", "B"]), [], budget=3)
    assert isinstance(result, SeqResult)
    assert result.converged   # no edges → trivially converged
    assert len(result.steps) == 1   # only step 0
    assert result.observations_taken == []


def test_rach_seq_converges_when_edge_is_cut():
    """A↔B disjunction edge disappears after observing high pop1_trait (A=1 confirmed)."""
    rows = _disjunction_rows(n_per_combo=30)
    sw = _switches(["A", "B", "C", "D"])
    cand = _candidate_pins_A()

    result = rach_seq(
        rows, sw, [cand], budget=3,
        outcome_overrides={"confirm_A": "A_active"},   # force the A=1 outcome
    )
    assert isinstance(result, SeqResult)
    # After pinning A=1, the A↔B coupling disappears (A always ON, B free)
    assert result.converged
    assert "confirm_A" in result.observations_taken
    assert len(result.edges_resolved) >= 1


def test_rach_seq_no_budget_exhausted_when_converged():
    rows = _disjunction_rows(n_per_combo=30)
    sw = _switches(["A", "B", "C", "D"])
    cand = _candidate_pins_A()

    result = rach_seq(rows, sw, [cand], budget=5,
                      outcome_overrides={"confirm_A": "A_active"})
    assert result.converged
    assert not result.budget_exhausted


def test_rach_seq_budget_exhausted_flag():
    """Budget runs out with edges remaining when no candidate can help."""
    rows = _disjunction_rows()
    sw = _switches(["A", "B", "C", "D"])
    # Candidate with no outcomes → heuristic value only; won't actually cut edges
    # because filter_by_outcome returns unchanged rows (no patterns to filter on)
    cand = CandidateObservation(
        name="weak_cand", description="", target_switches=["A"],
        rationale="", outcomes=[
            CandidateOutcome(
                name="no_signal",
                description="no filter",
                prior_probability=1.0,
                extra_pattern_rows=[],   # empty patterns → no filtering → structure unchanged
            ),
        ],
    )
    result = rach_seq(rows, sw, [cand], budget=1)
    # Edge survives: no filtering occurred
    assert result.budget_exhausted or not result.converged


def test_rach_seq_step_structure():
    rows = _disjunction_rows(n_per_combo=30)
    sw = _switches(["A", "B", "C", "D"])
    cand = _candidate_pins_A()

    result = rach_seq(rows, sw, [cand], budget=3,
                      outcome_overrides={"confirm_A": "A_active"})

    # step 0 is always present with no observation
    assert result.steps[0].step == 0
    assert result.steps[0].observation_taken is None
    assert result.steps[0].outcome_observed is None

    # subsequent steps record the candidate and outcome
    taken_steps = [s for s in result.steps if s.step > 0]
    assert len(taken_steps) >= 1
    s = taken_steps[0]
    assert s.observation_taken == "confirm_A"
    assert s.outcome_observed == "A_active"
    assert isinstance(s.candidate_ranking, list)
    assert s.candidate_ranking[0][0] == "confirm_A"


def test_rach_seq_describe_runs():
    rows = _disjunction_rows()
    sw = _switches(["A", "B", "C", "D"])
    cand = _candidate_pins_A()
    result = rach_seq(rows, sw, [cand], budget=2, seed=0)
    text = result.describe()
    assert "RACH-SEQ" in text
    assert "converged" in text


def test_rach_seq_independent_switches_no_action_needed():
    """Balanced, uncorrelated A and B — no confounding edges, trivially converged."""
    rows = []
    for a in (0, 1):
        for b in (0, 1):
            for _ in range(25):
                rows.append({"A": a, "B": b})
    sw = _switches(["A", "B"])
    result = rach_seq(rows, sw, [], budget=3)
    assert result.converged
    assert result.edges_resolved == []
    assert result.edges_unresolved == []


def test_rach_seq_respects_outcome_override_raises_on_unknown():
    rows = _disjunction_rows()
    sw = _switches(["A", "B", "C", "D"])
    cand = _candidate_pins_A()
    import pytest
    with pytest.raises(ValueError, match="not found"):
        rach_seq(rows, sw, [cand], budget=1,
                 outcome_overrides={"confirm_A": "nonexistent_outcome"})
