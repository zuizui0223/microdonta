"""Bridge ecological ABM sweeps to rule-transition RACH.

A single successful ABM run is not evidence of a robust ecological rule.
This module groups runs by causal program, tests a user-supplied qualitative
pattern predicate, and creates ProgramRun records for rule-transition invariant
inference.

Robustness is empirical and declared: a program is robust when the focal
qualitative pattern occurs in at least ``min_success_rate`` of valid runs and in
at least ``min_distinct_contexts`` distinct contexts.  Otherwise a program that
succeeds at least once is labelled fragile.  Programs with no successful runs
are omitted because they do not explain the target pattern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Hashable, Iterable, Mapping

from causal_model.rule_transition_invariants import ProgramRun


@dataclass(frozen=True)
class SweepRun:
    """One completed ABM/simulator evaluation.

    ``output`` is intentionally generic so this adapter works with existing
    system-specific RACH simulators.  ``context_id`` should distinguish broad
    parameter or environmental regions, not merely random seeds.
    """

    scenario: str
    program_id: str
    motifs: frozenset[str]
    context_id: Hashable
    output: Any
    valid: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RobustnessSummary:
    scenario: str
    program_id: str
    n_valid: int
    n_matching: int
    success_rate: float
    n_matching_contexts: int
    robust: bool
    motifs: frozenset[str]


def classify_sweep_runs(
    runs: Iterable[SweepRun],
    matches_target: Callable[[Any], bool],
    *,
    min_success_rate: float = 0.2,
    min_distinct_contexts: int = 2,
) -> tuple[list[ProgramRun], list[RobustnessSummary]]:
    """Convert ABM sweep output into robust/fragile ProgramRun records.

    Parameters
    ----------
    runs:
        Completed simulator evaluations grouped by scenario and causal program.
    matches_target:
        Predicate returning True iff the simulator output reproduces the focal
        *qualitative* pattern. This keeps numerical distance choices outside the
        invariant layer.
    min_success_rate:
        Minimum matching fraction among valid runs for a robust explanation.
    min_distinct_contexts:
        Minimum number of broad contexts with at least one match. Requiring
        contexts prevents a program from being called robust merely because one
        locally tuned region was sampled many times.

    Returns
    -------
    program_runs:
        ProgramRun records suitable for infer_rule_transition_invariants.
        Non-explanatory programs (zero matching runs) are excluded.
    summaries:
        Diagnostic statistics for every evaluated program.
    """
    if not 0 < min_success_rate <= 1:
        raise ValueError("min_success_rate must be in (0, 1].")
    if min_distinct_contexts < 1:
        raise ValueError("min_distinct_contexts must be >= 1.")

    grouped: dict[tuple[str, str], list[SweepRun]] = {}
    for run in runs:
        grouped.setdefault((run.scenario, run.program_id), []).append(run)

    program_runs: list[ProgramRun] = []
    summaries: list[RobustnessSummary] = []

    for (scenario, program_id), group in sorted(grouped.items()):
        valid = [item for item in group if item.valid]
        matched = [item for item in valid if matches_target(item.output)]
        n_valid = len(valid)
        n_matching = len(matched)
        success_rate = n_matching / n_valid if n_valid else 0.0
        matching_contexts = {item.context_id for item in matched}
        motifs = frozenset().union(*(item.motifs for item in group)) if group else frozenset()
        robust = (
            n_matching > 0
            and success_rate >= min_success_rate
            and len(matching_contexts) >= min_distinct_contexts
        )

        summary = RobustnessSummary(
            scenario=scenario,
            program_id=program_id,
            n_valid=n_valid,
            n_matching=n_matching,
            success_rate=success_rate,
            n_matching_contexts=len(matching_contexts),
            robust=robust,
            motifs=motifs,
        )
        summaries.append(summary)

        if n_matching == 0:
            continue
        program_runs.append(
            ProgramRun(
                scenario=scenario,
                program_id=program_id,
                motifs=motifs,
                robust=robust,
                metadata={
                    "n_valid": n_valid,
                    "n_matching": n_matching,
                    "success_rate": success_rate,
                    "n_matching_contexts": len(matching_contexts),
                    "min_success_rate": min_success_rate,
                    "min_distinct_contexts": min_distinct_contexts,
                },
            )
        )

    return program_runs, summaries
