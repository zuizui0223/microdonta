"""Sequential design for a predeclared target, separate from mechanism MROD.

At each step candidates are ranked by current normalized target information
I(T;Q|A_t)/H(T|A_t).  Only after a candidate is selected is its supplied
realised outcome looked up and used to condition the current admissible region.

This is an optional target-oriented policy.  It does not replace the validated
mechanism-resolving sequential policy in :mod:`causal_model.sequential_design`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from causal_model.mechanism_region import CandidateObservation
from causal_model.sequential_observation import filter_by_outcome
from causal_model.target_observation_value import (
    target_entropy_bits,
    target_observation_information_value,
)


@dataclass(frozen=True)
class TargetSequentialStep:
    step: int
    candidate: str
    realised_outcome: str
    target_entropy_before_bits: float
    normalized_target_value: float
    target_information_bits: float
    n_rows_before: int
    n_rows_after: int
    target_entropy_after_bits: float


@dataclass(frozen=True)
class TargetSequentialDesignResult:
    target_columns: tuple[str, ...]
    initial_target_entropy_bits: float
    final_target_entropy_bits: float
    target_identified: bool
    stop_reason: str
    steps: tuple[TargetSequentialStep, ...]
    final_rows: tuple[dict, ...]


def _outcome(candidate: CandidateObservation, name: str):
    matches = [outcome for outcome in candidate.outcomes if outcome.name == name]
    if len(matches) != 1:
        raise ValueError(
            f"candidate {candidate.name!r} has no unique outcome named {name!r}"
        )
    return matches[0]


def target_sequential_observation_design(
    accepted_rows: Sequence[dict],
    candidates: Sequence[CandidateObservation],
    *,
    target_columns: Sequence[str],
    realised_outcomes: Mapping[str, str],
    budget: int | None = None,
    positive_value_tolerance: float = 1e-15,
) -> TargetSequentialDesignResult:
    """Run a fail-closed target-oriented sequential observation policy.

    Parameters
    ----------
    realised_outcomes:
        Mapping from candidate name to the outcome that would be realised if
        that candidate is selected.  The mapping is *not* consulted for any
        unselected candidate during ranking.
    budget:
        Maximum number of observations. ``None`` permits at most one use of
        every supplied candidate.
    """
    rows = list(accepted_rows)
    if not rows:
        raise ValueError("accepted_rows must be non-empty")
    columns = tuple(target_columns)
    if not columns:
        raise ValueError("target_columns must be non-empty")
    remaining = list(candidates)
    if len({candidate.name for candidate in remaining}) != len(remaining):
        raise ValueError("candidate names must be unique")
    max_steps = len(remaining) if budget is None else int(budget)
    if max_steps < 0:
        raise ValueError("budget must be non-negative or None")

    initial_h = target_entropy_bits(rows, columns)
    steps: list[TargetSequentialStep] = []
    stop_reason = "budget_exhausted" if max_steps == 0 else ""

    while len(steps) < max_steps:
        current_h = target_entropy_bits(rows, columns)
        if current_h <= positive_value_tolerance:
            stop_reason = "target_identified"
            break
        if not remaining:
            stop_reason = "candidate_set_exhausted"
            break

        values = target_observation_information_value(
            rows,
            remaining,
            target_columns=columns,
        )
        estimable = [
            value
            for value in values
            if value.estimable
            and value.normalized_target_value is not None
            and value.normalized_target_value > positive_value_tolerance
        ]
        if not estimable:
            stop_reason = "no_positive_estimable_target_value"
            break

        # target_observation_information_value returns descending value order;
        # candidate name is used only as a deterministic tie-breaker.
        best_value = max(
            estimable,
            key=lambda value: (value.normalized_target_value, -remaining.index(
                next(c for c in remaining if c.name == value.candidate)
            )),
        )
        selected = next(c for c in remaining if c.name == best_value.candidate)

        # Realised outcome is intentionally accessed only after selection.
        if selected.name not in realised_outcomes:
            raise ValueError(
                f"missing realised outcome for selected candidate {selected.name!r}"
            )
        outcome_name = realised_outcomes[selected.name]
        realised = _outcome(selected, outcome_name)
        before_n = len(rows)
        after_rows = filter_by_outcome(rows, realised.extra_pattern_rows)
        if not after_rows:
            raise ValueError(
                f"realised outcome {outcome_name!r} for {selected.name!r} "
                "removed every admissible row"
            )
        after_h = target_entropy_bits(after_rows, columns)
        steps.append(
            TargetSequentialStep(
                step=len(steps) + 1,
                candidate=selected.name,
                realised_outcome=outcome_name,
                target_entropy_before_bits=current_h,
                normalized_target_value=float(best_value.normalized_target_value),
                target_information_bits=float(best_value.mutual_information_bits or 0.0),
                n_rows_before=before_n,
                n_rows_after=len(after_rows),
                target_entropy_after_bits=after_h,
            )
        )
        rows = list(after_rows)
        remaining = [candidate for candidate in remaining if candidate.name != selected.name]
    else:
        stop_reason = "budget_exhausted"

    final_h = target_entropy_bits(rows, columns)
    identified = final_h <= positive_value_tolerance
    if identified and stop_reason == "budget_exhausted":
        stop_reason = "target_identified_at_budget"

    return TargetSequentialDesignResult(
        target_columns=columns,
        initial_target_entropy_bits=initial_h,
        final_target_entropy_bits=final_h,
        target_identified=identified,
        stop_reason=stop_reason,
        steps=tuple(steps),
        final_rows=tuple(dict(row) for row in rows),
    )
