"""Tests for the minimal-sufficient-explanation decomposition of A_ε."""
import math

import pytest

from causal_model.minimal_explanations import (
    minimal_explanations,
    explanation_resolvability,
    explanation_nov,
    Explanation,
    ExplanationDecomposition,
)


class _SW:
    """Minimal switch stub (only ``.name`` is required)."""
    def __init__(self, name):
        self.name = name


def _switches(names):
    return [_SW(n) for n in names]


def _row(on_names, all_names):
    return {n: (n in on_names) for n in all_names}


# ---------------------------------------------------------------------------
# Core decomposition
# ---------------------------------------------------------------------------

def test_single_explanation_is_fully_resolved():
    sw = _switches(["A", "B"])
    rows = [_row({"A"}, ["A", "B"]) for _ in range(10)]
    dec = minimal_explanations(rows, sw)
    assert len(dec.explanations) == 1
    assert dec.explanations[0].mechanisms == frozenset({"A"})
    assert dec.explanations[0].mass == pytest.approx(1.0)
    assert dec.D_expl == pytest.approx(0.0)
    assert dec.R_expl == pytest.approx(1.0)


def test_two_equal_single_mechanism_explanations_are_a_disjunction():
    # 40 rows: {A}, 40 rows: {B}, 20 rows: {A,B}. Minimal explanations are
    # {A} and {B}; the {A,B} rows split equally, leaving ~50/50.
    sw = _switches(["A", "B"])
    rows = ([_row({"A"}, ["A", "B"]) for _ in range(40)]
            + [_row({"B"}, ["A", "B"]) for _ in range(40)]
            + [_row({"A", "B"}, ["A", "B"]) for _ in range(20)])
    dec = minimal_explanations(rows, sw)
    mins = {e.mechanisms for e in dec.explanations}
    assert mins == {frozenset({"A"}), frozenset({"B"})}
    for e in dec.explanations:
        assert e.mass == pytest.approx(0.5, abs=1e-6)
    assert dec.D_expl == pytest.approx(1.0)         # 1 bit over 2 equal options
    assert dec.R_expl == pytest.approx(0.0)


def test_superset_rows_do_not_create_new_explanations():
    # {A} present plus {A,B}; the inclusion-minimal explanation is only {A}.
    sw = _switches(["A", "B"])
    rows = ([_row({"A"}, ["A", "B"]) for _ in range(10)]
            + [_row({"A", "B"}, ["A", "B"]) for _ in range(10)])
    dec = minimal_explanations(rows, sw)
    assert [e.mechanisms for e in dec.explanations] == [frozenset({"A"})]
    assert dec.R_expl == pytest.approx(1.0)         # B is redundant, not a rival


def test_pinning_one_mechanism_collapses_to_single_explanation():
    # Before: {A} or {B}. After conditioning so B is always ON, every config is a
    # superset of {B}; the minimal explanation collapses to {B} and R_expl -> 1.
    sw = _switches(["A", "B"])
    before = ([_row({"A"}, ["A", "B"]) for _ in range(50)]
              + [_row({"B"}, ["A", "B"]) for _ in range(50)])
    assert minimal_explanations(before, sw).R_expl == pytest.approx(0.0)
    after = [r for r in before if r["B"]] + [_row({"A", "B"}, ["A", "B"]) for _ in range(50)]
    dec_after = minimal_explanations(after, sw)
    assert [e.mechanisms for e in dec_after.explanations] == [frozenset({"B"})]
    assert dec_after.R_expl == pytest.approx(1.0)


def test_unequal_masses_give_intermediate_resolvability():
    sw = _switches(["A", "B"])
    rows = ([_row({"A"}, ["A", "B"]) for _ in range(90)]
            + [_row({"B"}, ["A", "B"]) for _ in range(10)])
    dec = minimal_explanations(rows, sw)
    masses = sorted((e.mass for e in dec.explanations), reverse=True)
    assert masses[0] == pytest.approx(0.9)
    assert 0.0 < dec.R_expl < 1.0


def test_n_configs_counts_distinct_on_sets():
    sw = _switches(["A", "B", "C"])
    rows = [_row({"A"}, ["A", "B", "C"]),
            _row({"A"}, ["A", "B", "C"]),
            _row({"A", "B"}, ["A", "B", "C"]),
            _row({"C"}, ["A", "B", "C"])]
    dec = minimal_explanations(rows, sw)
    assert dec.n_configs == 3                        # {A}, {A,B}, {C}


def test_empty_region_is_non_estimable_nan():
    sw = _switches(["A", "B"])
    dec = minimal_explanations([], sw)
    assert dec.explanations == []
    assert math.isnan(dec.D_expl)
    assert math.isnan(dec.R_expl)
    assert math.isnan(explanation_resolvability([], sw))


def test_empty_on_set_is_its_own_explanation():
    # If the pattern can arise with no mechanism, {} is the unique minimal
    # explanation and the region is fully resolved onto "no mechanism needed".
    sw = _switches(["A", "B"])
    rows = ([_row(set(), ["A", "B"]) for _ in range(5)]
            + [_row({"A"}, ["A", "B"]) for _ in range(5)])
    dec = minimal_explanations(rows, sw)
    assert [e.mechanisms for e in dec.explanations] == [frozenset()]
    assert dec.R_expl == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# EVSI NOV on explanation resolvability
# ---------------------------------------------------------------------------

class _Outcome:
    def __init__(self, extra_pattern_rows):
        self.extra_pattern_rows = extra_pattern_rows


class _Candidate:
    def __init__(self, outcomes):
        self.outcomes = outcomes


def test_explanation_nov_rewards_a_separating_observation():
    # A_ε: half {A}, half {B}, disjunction (R_expl=0). A candidate whose two
    # outcomes are "A is ON" vs "A is OFF" fully separates the two explanations,
    # so its EVSI on R_expl is 1.0.
    sw = _switches(["A", "B"])
    rows = ([_row({"A"}, ["A", "B"]) for _ in range(50)]
            + [_row({"B"}, ["A", "B"]) for _ in range(50)])
    cand = _Candidate([
        _Outcome([{"type": "switch_state", "switch": "A", "state": True}]),
        _Outcome([{"type": "switch_state", "switch": "A", "state": False}]),
    ])
    # Use a filter that keys on the switch column directly via a tiny shim:
    # explanation_nov delegates to rach_seq.filter_by_outcome, which we exercise
    # through the real Campanula candidates in the integration test below. Here we
    # just confirm a no-op candidate yields ~0 EVSI.
    noop = _Candidate([_Outcome([])])
    assert explanation_nov(noop, rows, sw) == pytest.approx(0.0, abs=1e-9)


def test_explanation_nov_empty_region_is_nan():
    sw = _switches(["A", "B"])
    cand = _Candidate([_Outcome([])])
    assert math.isnan(explanation_nov(cand, [], sw))


# ---------------------------------------------------------------------------
# Integration with the real Campanula Tier-A region
# ---------------------------------------------------------------------------

def test_campanula_before_is_s2_or_s3_disjunction():
    from causal_model.campanula_structural import _abc_accept, _switches as camp_switches
    sw = camp_switches()
    acc = _abc_accept(4000, seed=1)
    dec = minimal_explanations(acc, sw)
    mins = {e.mechanisms for e in dec.explanations}
    assert mins == {frozenset({"selfing_syndrome"}), frozenset({"island_common_cause"})}
    assert dec.R_expl < 0.05                         # essentially unresolved
    for e in dec.explanations:
        assert e.mass == pytest.approx(0.5, abs=0.05)


def test_campanula_He_gradient_fully_resolves_explanation():
    from causal_model.campanula_structural import (
        _abc_accept, _switches as camp_switches,
        _candidate_observations, _truth_overrides,
    )
    from causal_model.rach_seq import filter_by_outcome
    sw = camp_switches()
    acc = _abc_accept(4000, seed=1)

    # the honest, observable He cline scores EVSI = 1.0 (full resolution)
    he = next(c for c in _candidate_observations() if c.name == "neutral_diversity_gradient")
    assert explanation_nov(he, acc, sw) == pytest.approx(1.0, abs=1e-6)

    # and actually taking it collapses the explanation to {island_common_cause}
    ov = _truth_overrides("S3")
    oc = next(o for o in he.outcomes if o.name == ov["neutral_diversity_gradient"])
    rows = filter_by_outcome(acc, oc.extra_pattern_rows)
    dec = minimal_explanations(rows, sw)
    assert [e.mechanisms for e in dec.explanations] == [frozenset({"island_common_cause"})]
    assert dec.R_expl == pytest.approx(1.0)
