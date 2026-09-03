"""Decision-theoretic audit for adaptive versus precommitted second measurements.

The scientific utility can be normalized mechanism information, raw conditional
mutual information, or another nonnegative branch-specific score.  The theorem
implemented here is purely about recomputation after a realised first outcome:
adaptivity is valuable exactly when no one remaining candidate is optimal on
every positive-probability branch.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Mapping


@dataclass(frozen=True)
class AdaptiveRecomputationAudit:
    adaptive_expected_value: float
    best_static_expected_value: float
    adaptive_gain: float
    best_static_candidates: tuple[str, ...]
    common_branch_maximizers: tuple[str, ...]
    strict_adaptive_advantage: bool


def _validate(
    branch_probabilities: Mapping[str, float],
    conditional_values: Mapping[str, Mapping[str, float]],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    branches = tuple(branch_probabilities)
    if not branches:
        raise ValueError("at least one branch is required")
    probs = [float(branch_probabilities[b]) for b in branches]
    if any(p < 0 for p in probs):
        raise ValueError("branch probabilities must be nonnegative")
    if not isclose(sum(probs), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("branch probabilities must sum to one")
    positive = tuple(b for b in branches if float(branch_probabilities[b]) > 0)
    if not positive:
        raise ValueError("at least one branch must have positive probability")

    first_candidates = tuple(conditional_values[positive[0]])
    if not first_candidates:
        raise ValueError("at least one remaining candidate is required")
    candidate_set = set(first_candidates)
    for b in positive:
        if b not in conditional_values:
            raise ValueError(f"missing conditional values for branch {b!r}")
        if set(conditional_values[b]) != candidate_set:
            raise ValueError("every positive-probability branch must score the same candidate set")
    return positive, first_candidates


def adaptive_recomputation_audit(
    *,
    branch_probabilities: Mapping[str, float],
    conditional_values: Mapping[str, Mapping[str, float]],
    tolerance: float = 1e-12,
) -> AdaptiveRecomputationAudit:
    """Compare adaptive recomputation with the optimal precommitted candidate.

    Let U_q(x) be the value of candidate q after first-outcome branch x.
    The adaptive second-step value is E[max_q U_q(X)].  The strongest static
    comparator precommits one q before seeing X and achieves max_q E[U_q(X)].

    The adaptive gain is nonnegative.  It is exactly zero iff at least one
    candidate is a branchwise maximizer for every positive-probability branch.
    """
    positive, candidates = _validate(branch_probabilities, conditional_values)

    branch_max: dict[str, float] = {
        b: max(float(conditional_values[b][q]) for q in candidates)
        for b in positive
    }
    adaptive = sum(float(branch_probabilities[b]) * branch_max[b] for b in positive)

    static_values = {
        q: sum(
            float(branch_probabilities[b]) * float(conditional_values[b][q])
            for b in positive
        )
        for q in candidates
    }
    best_static_value = max(static_values.values())
    best_static = tuple(
        q for q in candidates if abs(static_values[q] - best_static_value) <= tolerance
    )

    branch_argmax_sets = []
    for b in positive:
        maximum = branch_max[b]
        branch_argmax_sets.append(
            {q for q in candidates if abs(float(conditional_values[b][q]) - maximum) <= tolerance}
        )
    common = set(candidates)
    for argmax in branch_argmax_sets:
        common &= argmax

    gain = adaptive - best_static_value
    if gain < 0 and abs(gain) <= tolerance:
        gain = 0.0
    if gain < -tolerance:
        raise AssertionError("adaptive value fell below the best static comparator")

    strict = gain > tolerance
    if strict == bool(common):
        raise AssertionError("adaptive strictness disagrees with common-argmax criterion")

    return AdaptiveRecomputationAudit(
        adaptive_expected_value=adaptive,
        best_static_expected_value=best_static_value,
        adaptive_gain=gain,
        best_static_candidates=best_static,
        common_branch_maximizers=tuple(q for q in candidates if q in common),
        strict_adaptive_advantage=strict,
    )
