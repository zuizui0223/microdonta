from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Hashable, Iterable, Mapping

from causal_model.rule_transition_invariants import ProgramRun


@dataclass(frozen=True)
class SweepRecord:
    """One completed ecological simulation in a parameter sweep."""
    scenario: str
    program_id: str
    parameter_cell: Hashable
    seed: Hashable
    motifs: FrozenSet[str]
    matches_pattern: bool
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RobustnessPolicy:
    min_successes: int = 3
    min_parameter_cells: int = 2
    min_success_fraction: float = 0.20

    def __post_init__(self) -> None:
        if self.min_successes < 1 or self.min_parameter_cells < 1:
            raise ValueError("minimum counts must be positive")
        if not 0.0 < self.min_success_fraction <= 1.0:
            raise ValueError("min_success_fraction must lie in (0, 1]")


def program_runs_from_sweep(
    records: Iterable[SweepRecord],
    policy: RobustnessPolicy | None = None,
) -> list[ProgramRun]:
    """Convert parameter-sweep output to robust or fragile RACH program runs."""
    policy = policy or RobustnessPolicy()
    grouped: dict[tuple[str, str], list[SweepRecord]] = {}
    for record in records:
        grouped.setdefault((record.scenario, record.program_id), []).append(record)
    if not grouped:
        raise ValueError("At least one SweepRecord is required")

    output: list[ProgramRun] = []
    for (scenario, program_id), group in sorted(grouped.items()):
        successes = [record for record in group if record.matches_pattern]
        if not successes:
            continue
        cells = {record.parameter_cell for record in successes}
        fraction = len(successes) / len(group)
        robust = (
            len(successes) >= policy.min_successes
            and len(cells) >= policy.min_parameter_cells
            and fraction >= policy.min_success_fraction
        )
        motifs = frozenset().union(*(record.motifs for record in successes))
        output.append(ProgramRun(
            scenario=scenario,
            program_id=program_id,
            motifs=motifs,
            robust=robust,
            metadata={
                "n_total": len(group),
                "n_success": len(successes),
                "success_fraction": fraction,
                "n_parameter_cells": len(cells),
            },
        ))
    return output
