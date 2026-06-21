"""Convert ecological ABM sweep records into RACH rule-transition runs.

A model family is not called robust merely because one parameter setting works.
This module classifies a program as robust only when the focal qualitative
pattern recurs across independent parameter cells and stochastic replicates.
It then emits ProgramRun objects consumable by rule_transition_invariants.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Mapping

from causal_model.rule_transition_invariants import ProgramRun


@dataclass(frozen=True)
class SweepRecord:
    """One stochastic ABM evaluation.

    `parameter_cell` must identify a distinct sampled parameter / update-rule /
    initial-state cell. Multiple seeds within the same cell are replicates, not
    independent evidence of robustness.
    """

    scenario: str
    program_id: str
    parameter_cell: str
    replicate_id: str
    motifs: FrozenSet[str]
    matches_pattern: bool
    fragile_flags: FrozenSet[str] = field(default_factory=frozenset)
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RobustnessPolicy:
    """Transparent operational definition of robustness for an ABM family."""

    min_parameter_cells: int = 3
    min_cell_success_rate: float = 0.5
    min_successful_cell_fraction: float = 0.6
    disqualifying_fragility_flags: FrozenSet[str] = frozenset(
        {
            "exact_cancellation",
            "boundary_only",
            "exact_initial_alignment",
            "measure_zero_tuning",
        }
    )

    def __post_init__(self) -> None:
        if self.min_parameter_cells < 1:
            raise ValueError("min_parameter_cells must be at least 1.")
        for value, name in (
            (self.min_cell_success_rate, "min_cell_success_rate"),
            (self.min_successful_cell_fraction, "min_successful_cell_fraction"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1.")


@dataclass(frozen=True)
class ProgramRobustnessSummary:
    scenario: str
    program_id: str
    motifs: FrozenSet[str]
    n_cells: int
    n_successful_cells: int
    successful_cell_fraction: float
    robust: bool
    fragility_flags: FrozenSet[str]


def summarise_sweep_records(
    records: Iterable[SweepRecord],
    policy: RobustnessPolicy = RobustnessPolicy(),
) -> tuple[ProgramRobustnessSummary, ...]:
    """Classify each scenario/program pair from parameter-cell-level recurrence.

    A cell is successful when at least `min_cell_success_rate` of its stochastic
    replicates reproduce the focal qualitative pattern. A program is robust when
    it has enough distinct cells, enough successful cells, and no disqualifying
    fragility flag on any successful record.
    """

    grouped: dict[tuple[str, str], list[SweepRecord]] = {}
    for record in records:
        grouped.setdefault((record.scenario, record.program_id), []).append(record)

    summaries: list[ProgramRobustnessSummary] = []
    for (scenario, program_id), rows in sorted(grouped.items()):
        cells: dict[str, list[SweepRecord]] = {}
        for row in rows:
            cells.setdefault(row.parameter_cell, []).append(row)

        successful_cells: list[str] = []
        successful_rows: list[SweepRecord] = []
        for cell_id, cell_rows in cells.items():
            success_rate = sum(row.matches_pattern for row in cell_rows) / len(cell_rows)
            if success_rate >= policy.min_cell_success_rate:
                successful_cells.append(cell_id)
                successful_rows.extend(row for row in cell_rows if row.matches_pattern)

        n_cells = len(cells)
        n_successful = len(successful_cells)
        fraction = n_successful / n_cells if n_cells else 0.0
        flags = frozenset().union(*(row.fragile_flags for row in successful_rows)) if successful_rows else frozenset()
        disqualified = bool(flags & policy.disqualifying_fragility_flags)
        robust = (
            n_cells >= policy.min_parameter_cells
            and fraction >= policy.min_successful_cell_fraction
            and not disqualified
        )

        motif_sets = [row.motifs for row in successful_rows]
        motifs = frozenset.intersection(*motif_sets) if motif_sets else frozenset()
        summaries.append(
            ProgramRobustnessSummary(
                scenario=scenario,
                program_id=program_id,
                motifs=motifs,
                n_cells=n_cells,
                n_successful_cells=n_successful,
                successful_cell_fraction=fraction,
                robust=robust,
                fragility_flags=flags,
            )
        )
    return tuple(summaries)


def program_runs_from_sweep(
    records: Iterable[SweepRecord],
    policy: RobustnessPolicy = RobustnessPolicy(),
) -> tuple[ProgramRun, ...]:
    """Create RACH ProgramRun records with reproducibility metadata."""

    runs: list[ProgramRun] = []
    for summary in summarise_sweep_records(records, policy):
        runs.append(
            ProgramRun(
                scenario=summary.scenario,
                program_id=summary.program_id,
                motifs=summary.motifs,
                robust=summary.robust,
                metadata={
                    "n_cells": summary.n_cells,
                    "n_successful_cells": summary.n_successful_cells,
                    "successful_cell_fraction": summary.successful_cell_fraction,
                    "fragility_flags": sorted(summary.fragility_flags),
                },
            )
        )
    return tuple(runs)
