"""Internal exhaustive horizon-information diagnostic for MROD limitations.

This module is deliberately *not* a new sequential-design optimizer. It asks a
narrow diagnostic question after a declared current mechanism state and a coherent
set of candidate-outcome predictions have already been specified:

    how large must a *fixed observation bundle* be before the declared candidate
    vocabulary contains mechanism information?

For candidate set C and bundle horizon b, define

    J_b = max_{B subseteq C, 1 <= |B| <= b} I(S; Q_B) / K.

The exhaustive implementation here is intended only for small controlled audits.
Its cost is combinatorial in the number of candidates. Positive bundle information
does not identify an acquisition order, a minimum adaptive step count, a
cost-optimal policy, or a globally optimal adaptive strategy.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from math import log2
from typing import Hashable, Mapping, Sequence


@dataclass(frozen=True)
class HorizonInformationProfile:
    candidate_names: tuple[str, ...]
    mechanism_entropy_bits: float
    best_information_bits_by_horizon: tuple[float, ...]
    best_normalized_value_by_horizon: tuple[float, ...]
    best_bundles_by_horizon: tuple[tuple[tuple[str, ...], ...], ...]
    first_positive_bundle_size: int | None
    full_vector_information_bits: float


def _entropy_bits(values: Sequence[Hashable]) -> float:
    if not values:
        raise ValueError("at least one state is required")
    counts = Counter(values)
    n = len(values)
    return -sum((count / n) * log2(count / n) for count in counts.values())


def _mutual_information_bits(
    mechanism_states: Sequence[Hashable],
    outcomes: Sequence[Hashable],
) -> float:
    if len(mechanism_states) != len(outcomes):
        raise ValueError("mechanism states and outcomes must have equal length")
    if not mechanism_states:
        raise ValueError("at least one state is required")

    n = len(mechanism_states)
    joint = Counter(zip(mechanism_states, outcomes))
    state_counts = Counter(mechanism_states)
    outcome_counts = Counter(outcomes)
    information = 0.0
    for (state, outcome), count in joint.items():
        p_joint = count / n
        p_state = state_counts[state] / n
        p_outcome = outcome_counts[outcome] / n
        information += p_joint * log2(p_joint / (p_state * p_outcome))
    return information


def horizon_information_profile(
    mechanism_states: Sequence[Hashable],
    candidate_outcomes: Mapping[str, Sequence[Hashable]],
    *,
    mechanism_bits: int,
    max_horizon: int | None = None,
    value_tol: float = 1e-12,
) -> HorizonInformationProfile:
    """Exhaustively compute cumulative best fixed-bundle information through b.

    ``candidate_outcomes`` must be a coherent joint prediction: every candidate
    sequence is aligned to the same accepted-state rows. The returned horizon-b
    value maximizes over all nonempty fixed bundles of size *at most* b. It does
    not optimize an outcome-dependent adaptive acquisition tree.
    """
    if mechanism_bits <= 0:
        raise ValueError("mechanism_bits must be positive")
    if value_tol < 0:
        raise ValueError("value_tol must be non-negative")
    states = tuple(mechanism_states)
    if not states:
        raise ValueError("at least one mechanism state is required")
    names = tuple(sorted(candidate_outcomes))
    if not names:
        raise ValueError("at least one candidate is required")

    aligned: dict[str, tuple[Hashable, ...]] = {}
    for name in names:
        values = tuple(candidate_outcomes[name])
        if len(values) != len(states):
            raise ValueError(f"candidate {name!r} is not aligned to mechanism states")
        aligned[name] = values

    maximum_horizon = len(names) if max_horizon is None else int(max_horizon)
    if maximum_horizon < 1 or maximum_horizon > len(names):
        raise ValueError("max_horizon must be between 1 and the candidate count")

    entropy = _entropy_bits(states)
    if entropy > mechanism_bits + 1e-10:
        raise ValueError(
            "mechanism state entropy exceeds the declared mechanism_bits normalization"
        )

    best_bits: list[float] = []
    best_values: list[float] = []
    best_bundles: list[tuple[tuple[str, ...], ...]] = []
    cumulative_best = -1.0
    cumulative_ties: tuple[tuple[str, ...], ...] = ()

    for horizon in range(1, maximum_horizon + 1):
        exact: list[tuple[tuple[str, ...], float]] = []
        for bundle in combinations(names, horizon):
            joint_outcomes = tuple(
                tuple(aligned[name][row_index] for name in bundle)
                for row_index in range(len(states))
            )
            exact.append((bundle, _mutual_information_bits(states, joint_outcomes)))

        exact_max = max(value for _, value in exact)
        exact_ties = tuple(bundle for bundle, value in exact if abs(value - exact_max) <= value_tol)
        if exact_max > cumulative_best + value_tol:
            cumulative_best = exact_max
            cumulative_ties = exact_ties
        elif abs(exact_max - cumulative_best) <= value_tol:
            cumulative_ties = tuple(sorted(set(cumulative_ties).union(exact_ties)))

        best_bits.append(cumulative_best)
        best_values.append(cumulative_best / mechanism_bits)
        best_bundles.append(cumulative_ties)

    first_positive_bundle_size = next(
        (index + 1 for index, value in enumerate(best_bits) if value > value_tol),
        None,
    )
    full_joint = tuple(tuple(aligned[name][i] for name in names) for i in range(len(states)))
    full_information = _mutual_information_bits(states, full_joint)

    if any(value > entropy + 1e-10 for value in best_bits):
        raise RuntimeError("bundle information exceeded mechanism entropy")

    return HorizonInformationProfile(
        candidate_names=names,
        mechanism_entropy_bits=entropy,
        best_information_bits_by_horizon=tuple(best_bits),
        best_normalized_value_by_horizon=tuple(best_values),
        best_bundles_by_horizon=tuple(best_bundles),
        first_positive_bundle_size=first_positive_bundle_size,
        full_vector_information_bits=full_information,
    )


__all__ = ["HorizonInformationProfile", "horizon_information_profile"]
