"""Target-aware value of candidate observations over the current admissible region.

The publication-facing MROD score remains mechanism information
I(S;Q|A_epsilon)/K. This module adds a separate prospective score for a
predeclared target T, so mechanism-learning value is not silently treated as
target-licensing value.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from numbers import Number, Rational
from typing import Sequence

from causal_model.mechanism_region import CandidateObservation
from causal_model.sequential_observation import (
    filter_by_outcome,
    predictive_outcome_distribution,
)


@dataclass(frozen=True)
class TargetInformationValueResult:
    candidate: str
    target_columns: tuple[str, ...]
    current_target_entropy_bits: float
    mutual_information_bits: float | None
    normalized_target_value: float | None
    target_already_identified: bool
    estimable: bool
    partition_verified: bool
    probability_source: str
    reason: str


def _target_columns(target_columns: Sequence[str]) -> tuple[str, ...]:
    if isinstance(target_columns, (str, bytes)):
        raise ValueError("target_columns must be a non-empty sequence of column names")
    columns = tuple(target_columns)
    if not columns:
        raise ValueError("target_columns must be non-empty")
    if any(not isinstance(column, str) or not column.strip() for column in columns):
        raise ValueError("target column names must be non-empty strings")
    if len(set(columns)) != len(columns):
        raise ValueError("target column names must be unique")
    return columns


def _check_target_label(value, column: str) -> None:
    """Reject missing/non-finite labels instead of inventing a target category."""
    if value is None:
        raise ValueError(f"target column {column!r} contains a missing value")
    try:
        hash(value)
    except TypeError as exc:
        raise ValueError("target column values must be hashable") from exc
    if isinstance(value, (tuple, frozenset)):
        for item in value:
            _check_target_label(item, column)
        return
    if isinstance(value, Number) and not isinstance(value, Rational):
        try:
            finite = math.isfinite(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"target column {column!r} requires finite real labels") from exc
        if not finite:
            raise ValueError(f"target column {column!r} contains a non-finite value")
    try:
        reflexive = bool(value == value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"target column {column!r} contains a missing/invalid label") from exc
    if not reflexive:
        raise ValueError(f"target column {column!r} contains a missing/invalid label")


def _state(row: dict, target_columns: Sequence[str]) -> tuple:
    values = []
    for column in target_columns:
        if column not in row:
            raise ValueError(f"missing target column {column!r}")
        value = row[column]
        _check_target_label(value, column)
        values.append(value)
    return tuple(values)


def target_entropy_bits(accepted_rows: list[dict], target_columns: Sequence[str]) -> float:
    """Empirical joint entropy on fully declared, finite, non-missing target labels.

    Missing columns or values are input errors, not a shared category with zero
    entropy. Zero entropy concerns the represented pool, not unenumerated worlds.
    """
    columns = _target_columns(target_columns)
    rows = list(accepted_rows)
    if not rows:
        raise ValueError("accepted_rows must be non-empty")
    counts = Counter(_state(row, columns) for row in rows)
    n = len(rows)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def candidate_target_mutual_information_bits(
    accepted_rows: list[dict],
    candidate: CandidateObservation,
    target_columns: Sequence[str],
) -> float | None:
    """Return empirical I(T;Q|A_epsilon) for a verified candidate partition.

    Validate every supplied target before inspecting candidate coverage, so an
    unavailable predictive map cannot mask a missing scientific target.
    """
    columns = _target_columns(target_columns)
    rows = list(accepted_rows)
    for row in rows:
        _state(row, columns)
    if not rows or not candidate.outcomes:
        return None

    distribution = predictive_outcome_distribution(candidate, rows)
    if not distribution.partition_verified:
        return None

    joint: Counter[tuple[tuple, str]] = Counter()
    target_counts: Counter[tuple] = Counter()
    outcome_counts: Counter[str] = Counter()
    for outcome in candidate.outcomes:
        sub = filter_by_outcome(rows, outcome.extra_pattern_rows)
        for row in sub:
            state = _state(row, columns)
            joint[(state, outcome.name)] += 1
            target_counts[state] += 1
            outcome_counts[outcome.name] += 1

    n = len(rows)
    if sum(joint.values()) != n:
        raise RuntimeError(
            "verified predictive partition did not reproduce every admissible row exactly once"
        )

    mi = 0.0
    for (state, outcome_name), count in joint.items():
        p_joint = count / n
        p_target = target_counts[state] / n
        p_outcome = outcome_counts[outcome_name] / n
        mi += p_joint * math.log2(p_joint / (p_target * p_outcome))
    if mi < 0.0 and abs(mi) < 1e-12:
        mi = 0.0
    return mi


def target_observation_information_value(
    accepted_rows: list[dict],
    candidates: Sequence[CandidateObservation],
    *,
    target_columns: Sequence[str],
) -> list[TargetInformationValueResult]:
    """Score candidates for a declared target without replacing MROD's mechanism score."""
    rows = list(accepted_rows)
    columns = _target_columns(target_columns)
    current_h = target_entropy_bits(rows, columns)
    results: list[TargetInformationValueResult] = []

    for candidate in candidates:
        if not candidate.outcomes:
            results.append(
                TargetInformationValueResult(
                    candidate=candidate.name,
                    target_columns=columns,
                    current_target_entropy_bits=current_h,
                    mutual_information_bits=None,
                    normalized_target_value=None,
                    target_already_identified=current_h <= 1e-15,
                    estimable=False,
                    partition_verified=False,
                    probability_source="no_outcomes",
                    reason="candidate has no explicit outcome map",
                )
            )
            continue

        distribution = predictive_outcome_distribution(candidate, rows)
        if not distribution.partition_verified:
            results.append(
                TargetInformationValueResult(
                    candidate=candidate.name,
                    target_columns=columns,
                    current_target_entropy_bits=current_h,
                    mutual_information_bits=None,
                    normalized_target_value=None,
                    target_already_identified=current_h <= 1e-15,
                    estimable=False,
                    partition_verified=False,
                    probability_source=distribution.source,
                    reason=(
                        "outcome maps do not form a verified partition of current A_epsilon"
                    ),
                )
            )
            continue

        mi = candidate_target_mutual_information_bits(rows, candidate, columns)
        if mi is None:
            raise RuntimeError("verified target partition lost its information measure")
        normalized = 0.0 if current_h <= 1e-15 else min(1.0, max(0.0, mi / current_h))
        results.append(
            TargetInformationValueResult(
                candidate=candidate.name,
                target_columns=columns,
                current_target_entropy_bits=current_h,
                mutual_information_bits=mi,
                normalized_target_value=normalized,
                target_already_identified=current_h <= 1e-15,
                estimable=True,
                partition_verified=True,
                probability_source=distribution.source,
                reason="",
            )
        )

    results.sort(
        key=lambda r: (
            r.estimable,
            r.normalized_target_value
            if r.normalized_target_value is not None
            else float("-inf"),
        ),
        reverse=True,
    )
    return results
