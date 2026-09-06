"""Pareto comparison of mechanism-learning and target-resolving observations.

MROD deliberately keeps mechanism information and declared-target information as
separate task-indexed utilities.  This module does not invent a weighted scalar
objective.  It reports the two-dimensional value pair and the non-dominated
candidate set.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .mechanism_region import CandidateObservation
from .observation_value import observation_information_value
from .target_observation_value import target_observation_information_value


@dataclass(frozen=True)
class TaskParetoResult:
    candidate: str
    mechanism_value: float | None
    target_value: float | None
    mechanism_estimable: bool
    target_estimable: bool
    jointly_estimable: bool
    dominated_by: tuple[str, ...]
    pareto_nondominated: bool


def task_pareto_values(
    accepted_rows: list[dict],
    switches,
    candidates: Sequence[CandidateObservation],
    *,
    target_columns: Sequence[str],
    tolerance: float = 1e-12,
) -> tuple[TaskParetoResult, ...]:
    """Return the mechanism/target value pair and Pareto status for candidates.

    A candidate is Pareto-dominated only when another *jointly estimable*
    candidate is no worse on both declared utilities and strictly better on at
    least one.  Non-estimable dimensions are never replaced by zero.
    """
    if tolerance < 0.0:
        raise ValueError("tolerance must be non-negative")
    candidate_list = list(candidates)
    mechanism = {
        row.candidate: row
        for row in observation_information_value(
            accepted_rows,
            switches,
            candidate_list,
        )
    }
    target = {
        row.candidate: row
        for row in target_observation_information_value(
            accepted_rows,
            candidate_list,
            target_columns=target_columns,
        )
    }

    raw: list[tuple[str, float | None, float | None, bool, bool]] = []
    for candidate in candidate_list:
        m = mechanism[candidate.name]
        t = target[candidate.name]
        m_value = m.information_value if m.estimable else None
        t_value = t.normalized_target_value if t.estimable else None
        raw.append((candidate.name, m_value, t_value, m.estimable, t.estimable))

    results: list[TaskParetoResult] = []
    for name, m_value, t_value, m_ok, t_ok in raw:
        joint = m_ok and t_ok and m_value is not None and t_value is not None
        dominators: list[str] = []
        if joint:
            for other_name, om, ot, om_ok, ot_ok in raw:
                if other_name == name or not (om_ok and ot_ok):
                    continue
                if om is None or ot is None:
                    continue
                no_worse = om + tolerance >= m_value and ot + tolerance >= t_value
                strictly_better = om > m_value + tolerance or ot > t_value + tolerance
                if no_worse and strictly_better:
                    dominators.append(other_name)
        results.append(
            TaskParetoResult(
                candidate=name,
                mechanism_value=m_value,
                target_value=t_value,
                mechanism_estimable=m_ok,
                target_estimable=t_ok,
                jointly_estimable=joint,
                dominated_by=tuple(sorted(dominators)),
                pareto_nondominated=joint and not dominators,
            )
        )

    results.sort(
        key=lambda row: (
            not row.pareto_nondominated,
            not row.jointly_estimable,
            row.candidate,
        )
    )
    return tuple(results)


def pareto_front_candidates(results: Sequence[TaskParetoResult]) -> tuple[str, ...]:
    """Return candidate names on the jointly-estimable Pareto front."""
    return tuple(row.candidate for row in results if row.pareto_nondominated)
