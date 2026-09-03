from __future__ import annotations

import math
from collections import Counter
from itertools import product

from causal_model.adaptive_recomputation import adaptive_recomputation_audit


def entropy(values):
    n = len(values)
    counts = Counter(values)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def deterministic_conditional_mi(states, q_values):
    """For deterministic Q=f(S) on equally weighted distinct states, I(S;Q)=H(Q)."""
    assert len(states) == len(q_values)
    return entropy(q_values)


def test_adaptive_value_and_common_argmax_criterion_exhaustive_small_tables():
    probabilities = {"left": 0.4, "right": 0.6}
    candidates = ("a", "b", "c")
    levels = (0.0, 1.0, 2.0)

    for flat in product(levels, repeat=6):
        values = {
            "left": dict(zip(candidates, flat[:3])),
            "right": dict(zip(candidates, flat[3:])),
        }
        audit = adaptive_recomputation_audit(
            branch_probabilities=probabilities,
            conditional_values=values,
        )
        assert audit.adaptive_expected_value + 1e-12 >= audit.best_static_expected_value

        left_max = max(values["left"].values())
        right_max = max(values["right"].values())
        common = {
            q for q in candidates
            if values["left"][q] == left_max and values["right"][q] == right_max
        }
        assert bool(audit.common_branch_maximizers) == bool(common)
        assert audit.strict_adaptive_advantage == (not bool(common))
        assert (audit.adaptive_gain > 1e-12) == (not bool(common))


def test_unique_branchwise_rank_reversal_forces_strict_adaptive_advantage():
    audit = adaptive_recomputation_audit(
        branch_probabilities={"x0": 0.5, "x1": 0.5},
        conditional_values={
            "x0": {"q1": 1.0, "q2": 0.0},
            "x1": {"q1": 0.0, "q2": 1.0},
        },
    )
    assert audit.strict_adaptive_advantage
    assert audit.common_branch_maximizers == ()
    assert audit.adaptive_expected_value == 1.0
    assert audit.best_static_expected_value == 0.5
    assert audit.adaptive_gain == 0.5


def test_common_best_candidate_is_exact_equality_case():
    audit = adaptive_recomputation_audit(
        branch_probabilities={"x0": 0.25, "x1": 0.75},
        conditional_values={
            "x0": {"q1": 2.0, "q2": 1.0, "q3": 2.0},
            "x1": {"q1": 3.0, "q2": 4.0, "q3": 4.0},
        },
    )
    # q3 is branchwise optimal everywhere, although rankings/ties change.
    assert audit.common_branch_maximizers == ("q3",)
    assert not audit.strict_adaptive_advantage
    assert abs(audit.adaptive_gain) < 1e-12


def test_four_world_mutual_information_witness_beats_optimal_static_second_choice():
    states = ("a", "b", "c", "d")
    branches = {"x0": (0, 1), "x1": (2, 3)}
    q1 = (0, 1, 0, 0)
    q2 = (0, 0, 0, 1)

    values = {}
    for branch, ids in branches.items():
        branch_states = tuple(states[i] for i in ids)
        values[branch] = {
            "q1": deterministic_conditional_mi(branch_states, tuple(q1[i] for i in ids)),
            "q2": deterministic_conditional_mi(branch_states, tuple(q2[i] for i in ids)),
        }

    assert values == {
        "x0": {"q1": 1.0, "q2": 0.0},
        "x1": {"q1": 0.0, "q2": 1.0},
    }
    audit = adaptive_recomputation_audit(
        branch_probabilities={"x0": 0.5, "x1": 0.5},
        conditional_values=values,
    )
    assert audit.adaptive_expected_value == 1.0
    assert audit.best_static_expected_value == 0.5
    # X itself identifies which two-state branch holds, so H(X)=1 bit.
    assert 1.0 + audit.adaptive_expected_value == 2.0
    assert 1.0 + audit.best_static_expected_value == 1.5


def test_three_world_two_branch_deterministic_design_cannot_have_strict_branch_switch_advantage():
    states = (0, 1, 2)
    # Up to branch relabeling, every nontrivial two-branch partition has sizes 2 and 1.
    branch_ids = {"pair": (0, 1), "singleton": (2,)}

    binary_functions = tuple(product((0, 1), repeat=3))
    for q1 in binary_functions:
        for q2 in binary_functions:
            values = {}
            for branch, ids in branch_ids.items():
                branch_states = tuple(states[i] for i in ids)
                values[branch] = {
                    "q1": deterministic_conditional_mi(branch_states, tuple(q1[i] for i in ids)),
                    "q2": deterministic_conditional_mi(branch_states, tuple(q2[i] for i in ids)),
                }
            audit = adaptive_recomputation_audit(
                branch_probabilities={"pair": 2 / 3, "singleton": 1 / 3},
                conditional_values=values,
            )
            assert not audit.strict_adaptive_advantage
            assert audit.common_branch_maximizers


def test_zero_probability_branches_do_not_affect_the_condition():
    audit = adaptive_recomputation_audit(
        branch_probabilities={"seen": 1.0, "impossible": 0.0},
        conditional_values={
            "seen": {"q1": 1.0, "q2": 0.0},
            # The impossible branch is intentionally absent from conditional_values.
        },
    )
    assert audit.common_branch_maximizers == ("q1",)
    assert not audit.strict_adaptive_advantage
