from __future__ import annotations

import json
from pathlib import Path

from paper.run_static_information_supplement import (
    POLICIES,
    SUPPLEMENT_ID,
    run_supplement,
)

ROOT = Path(__file__).resolve().parents[1]


def test_supplement_does_not_modify_frozen_g2_policy_contract():
    protocol = json.loads(
        (ROOT / "paper" / "g2_frozen_benchmark_protocol.json").read_text(encoding="utf-8")
    )
    assert protocol["protocol_id"] == "rach-g2-truth-peek-free-v2"
    assert protocol["selection_validation"]["policies"] == ["rach_seq", "random_order"]
    assert "static_initial_information" not in protocol["selection_validation"]["policies"]
    assert POLICIES == ("rach_seq", "static_initial_information", "random_order")


def test_small_supplement_is_matched_and_truth_peek_free():
    payload = run_supplement(
        seeds=(17, 29),
        budgets=(0, 1, 2),
        n_systems_per_seed=12,
        n_attempts=300,
        K_choices=(4, 5),
        confound_choices=(1, 2),
        min_sub_size=8,
        n_distractors=2,
    )

    assert payload["supplement_id"] == SUPPLEMENT_ID
    assert payload["status"] == "post_frozen_not_part_of_preregistered_g2"
    assert payload["policies"] == list(POLICIES)

    rows = payload["per_seed"]
    for seed in payload["seeds"]:
        for budget in payload["budgets"]:
            cell = [row for row in rows if row["seed"] == seed and row["budget"] == budget]
            assert {row["policy"] for row in cell} == set(POLICIES)
            # Every policy is evaluated on exactly the same prepared system count.
            assert len({row["n_systems"] for row in cell}) == 1
            # Hidden truth is never used for candidate ranking and should never be
            # silently excluded in this controlled family.
            assert all(row["false_exclusion_rate"] == 0.0 for row in cell)

    # Budget zero is a policy-neutral sanity check.
    budget_zero = [row for row in rows if row["budget"] == 0]
    for seed in payload["seeds"]:
        cell = [row for row in budget_zero if row["seed"] == seed]
        assert len({row["frac_converged"] for row in cell}) == 1
        assert len({row["mean_frac_resolved"] for row in cell}) == 1
        assert len({row["mean_steps"] for row in cell}) == 1


def test_static_policy_is_nonadaptive_by_construction():
    source = (ROOT / "paper" / "run_static_information_supplement.py").read_text(
        encoding="utf-8"
    )
    function = source.split("def _run_static_initial_information", 1)[1].split(
        "def _record_for_policy", 1
    )[0]
    # Scores are computed before the observation loop and never recomputed in it.
    assert function.count("sequential_candidate_value(") == 1
    loop = function.split("for score, _, candidate in ranked:", 1)[1]
    assert "sequential_candidate_value(" not in loop
    assert "ranked.sort" in function
    assert "score <= 0.0" in function
