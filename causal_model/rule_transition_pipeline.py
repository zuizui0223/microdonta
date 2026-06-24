"""One-call, outcome-aware pipeline from ecological ABM sweeps to RACH results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from causal_model.abm_family_adapter import ProgramSweepSummary, RobustnessPolicy, SweepRecord
from causal_model.rule_transition_hardened import program_runs_from_observed_sweep
from causal_model.rule_transition_invariants import CrossSystemResult, infer_rule_transition_invariants


@dataclass(frozen=True)
class RuleTransitionAnalysis:
    sweep_summary: tuple[ProgramSweepSummary, ...]
    invariant_result: CrossSystemResult


def analyse_rule_transitions(
    records: Iterable[SweepRecord],
    policy: RobustnessPolicy = RobustnessPolicy(),
) -> RuleTransitionAnalysis:
    """Classify sweeps and infer conditional invariants from simulated outcomes.

    Legacy caller motifs remain usable as assumption labels, but trait-space outcome
    labels are stripped and re-derived from each matching simulation's metadata.
    """
    observed = program_runs_from_observed_sweep(tuple(records), policy)
    if not observed.program_runs:
        raise ValueError("No robust or fragile program reproduced the focal qualitative pattern.")
    return RuleTransitionAnalysis(
        sweep_summary=observed.sweep_summary,
        invariant_result=infer_rule_transition_invariants(observed.program_runs),
    )
