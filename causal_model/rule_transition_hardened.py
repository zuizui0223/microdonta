"""Outcome-aware adapter for rule-transition RACH.

This module protects the invariant layer from a legacy failure mode: an outcome
label such as ``trait_space_contraction`` may appear in a caller-supplied program
motif set, but it is never treated as evidence. Trait-space outcomes are derived
only from the actual ``trait_space_primary`` metadata emitted by each simulator.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from causal_model.abm_family_adapter import (
    ProgramSweepSummary,
    RobustnessPolicy,
    SweepRecord,
    summarise_sweep,
)
from causal_model.rule_transition_invariants import ProgramRun

OUTCOME_PRIMARIES = frozenset({
    "contraction", "fragmentation", "shift", "expansion", "collapse", "conserved",
})
RECONFIGURING_PRIMARIES = frozenset({"contraction", "fragmentation", "shift", "collapse"})
OUTCOME_MOTIFS = frozenset({f"trait_space_{name}" for name in OUTCOME_PRIMARIES} | {
    "trait_space_reconfiguration",
})


@dataclass(frozen=True)
class OutcomeAwareSweep:
    sweep_summary: tuple[ProgramSweepSummary, ...]
    program_runs: tuple[ProgramRun, ...]


def outcome_motifs_from_primary(primary: object) -> frozenset[str]:
    """Return outcome labels only when a simulator actually supplied a valid result."""
    if primary not in OUTCOME_PRIMARIES:
        return frozenset()
    motifs = {f"trait_space_{primary}"}
    if primary in RECONFIGURING_PRIMARIES:
        motifs.add("trait_space_reconfiguration")
    return frozenset(motifs)


def _record_key(record: SweepRecord) -> tuple[str, str, frozenset[str]]:
    return record.scenario, record.program_id, frozenset(record.motifs)


def _assumption_motifs(motifs: frozenset[str]) -> frozenset[str]:
    """Remove any legacy outcome labels from caller-provided program assumptions."""
    return frozenset(m for m in motifs if m not in OUTCOME_MOTIFS)


def program_runs_from_observed_sweep(
    records: Iterable[SweepRecord],
    policy: RobustnessPolicy = RobustnessPolicy(),
) -> OutcomeAwareSweep:
    """Build invariant inputs without allowing fixed outcome motifs to leak in.

    A run contributes an outcome only from matching simulation records. With more
    than one accepted outcome, the intersection is used, so a specific geometry is
    reported only if it recurs across all accepted simulations in that program.
    """
    rows = tuple(records)
    summaries = summarise_sweep(rows, policy)
    grouped: dict[tuple[str, str, frozenset[str]], list[SweepRecord]] = {}
    for row in rows:
        grouped.setdefault(_record_key(row), []).append(row)

    runs: list[ProgramRun] = []
    for summary in summaries:
        if summary.classification not in {"robust", "fragile"}:
            continue
        key = (summary.scenario, summary.program_id, summary.motifs)
        matching = [row for row in grouped[key] if row.pattern_matched]
        per_record_outcomes = [
            outcome_motifs_from_primary(row.metadata.get("trait_space_primary"))
            for row in matching
        ]
        observed_outcomes = (
            frozenset.intersection(*per_record_outcomes)
            if per_record_outcomes and all(per_record_outcomes)
            else frozenset()
        )
        primary_counts = Counter(
            str(row.metadata.get("trait_space_primary"))
            for row in matching
            if row.metadata.get("trait_space_primary") in OUTCOME_PRIMARIES
        )
        runs.append(ProgramRun(
            scenario=summary.scenario,
            program_id=summary.program_id,
            motifs=_assumption_motifs(summary.motifs),
            robust=summary.classification == "robust",
            outcome_motifs=observed_outcomes,
            metadata={
                "n_replicates": summary.n_replicates,
                "n_matches": summary.n_matches,
                "match_fraction": summary.match_fraction,
                "classification": summary.classification,
                "fragility_reasons": sorted(summary.fragility_reasons),
                "observed_outcome_counts": dict(sorted(primary_counts.items())),
                "outcome_provenance": "matching_simulation_metadata.trait_space_primary",
                "robustness_policy": {
                    "min_replicates": policy.min_replicates,
                    "min_match_fraction": policy.min_match_fraction,
                    "fragile_max_fraction": policy.fragile_max_fraction,
                },
            },
        ))
    return OutcomeAwareSweep(sweep_summary=summaries, program_runs=tuple(runs))
