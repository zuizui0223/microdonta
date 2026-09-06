"""Tests for the Boundary -> MROD controlled screening witness."""
from __future__ import annotations

from causal_model.structural_mechanism_screen_demo import (
    build_witness_rows,
    structural_vs_mechanism_witness,
)


def _by_name(results):
    return {result.candidate: result for result in results}


def test_witness_current_fibre_balances_mechanism_and_nuisance():
    rows = build_witness_rows(n_per_cell=10)
    assert len(rows) == 40
    assert all(abs(row["x0"] + row["x1"]) < 1e-12 for row in rows)
    for switch_on in (False, True):
        sub = [row for row in rows if bool(row["S"]) is switch_on]
        assert {row["x2"] for row in sub} == {-1.0, 1.0}
        assert sum(row["x2"] > 0 for row in sub) == len(sub) // 2


def test_structural_rank_screen_is_necessary_but_not_sufficient_for_mechanism_information():
    results, _ = structural_vs_mechanism_witness(n_per_cell=20)
    got = _by_name(results)

    # Existing observation direction: guaranteed zero value.
    assert got["redundant"].rank_gain == 0
    assert got["redundant"].mutual_information_bits == 0.0
    assert got["redundant"].information_value == 0.0

    # New structural direction, but it only measures nuisance x2.
    assert got["nuisance_new"].rank_gain == 1
    assert got["nuisance_new"].mutual_information_bits == 0.0
    assert got["nuisance_new"].information_value == 0.0

    # New structural direction that partitions the mechanism switch exactly.
    assert got["mechanism_new"].rank_gain == 1
    assert got["mechanism_new"].mutual_information_bits == 1.0
    assert got["mechanism_new"].information_value == 1.0


def test_mrod_information_screen_resolves_rank_gain_tie():
    _, policy = structural_vs_mechanism_witness(n_per_cell=20)

    # Uniform random choice among all three spends 2/3 of selections on zero-value Q.
    assert abs(policy.random_all_expected_information - 1.0 / 3.0) < 1e-12

    # Boundary-style structural screening removes the redundant row, but leaves
    # one nuisance-new and one mechanism-new candidate tied by rank gain.
    assert abs(policy.structural_filter_uniform_tie_expected_information - 0.5) < 1e-12

    # MROD's mechanism-targeted value breaks that tie deterministically.
    assert policy.mrod_selected_candidate == "mechanism_new"
    assert policy.mrod_max_information == 1.0
    assert policy.mrod_max_information > policy.structural_filter_uniform_tie_expected_information
