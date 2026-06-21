"""One-call pipeline from ecological ABM sweeps to RACH rule-transition results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from causal_model.abm_family_adapter import (
    ProgramSweepSummary,
    RobustnessPolicy,
    SweepRecord,
    program_runs_from_sweep,
    summarise_sweep,
)
from causal_model.rule_transition_invariants import CrossSystemResult, infer_rule_transition_invariants


@dataclass(frozen=True)
class RuleTransitionAnalysis:
    sweep_summary: tuple[ProgramSweepSummary, ...]
    invariant_result: CrossSystemResult


def analyse_rule_transitions(
    records: Iterable[SweepRecord],
    policy: RobustnessPolicy = RobustnessPolicy(),
) -> RuleTransitionAnalysis:
    """Classify ABM families and infer robust cross-system rule transitions.

    The result preserves rejected and insufficient families in ``sweep_summary``
    while only robust/fragile matching families enter the invariant calculation.
    """
    records = tuple(records)
    summary = summarise_sweep(records, policy)
    runs = program_runs_from_sweep(records, policy)
    if not runs:
        raise ValueError("No robust or fragile program reproduced the focal qualitative pattern.")
    return RuleTransitionAnalysis(
        sweep_summary=summary,
        invariant_result=infer_rule_transition_invariants(runs),
    )
