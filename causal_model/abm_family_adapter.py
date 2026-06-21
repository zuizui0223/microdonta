"""Convert ecological ABM parameter sweeps into RACH rule-transition runs.

The adapter deliberately does not declare one parameter setting to be the
answer. A causal program is robust only when the focal qualitative pattern
appears repeatedly across its sampled admissible parameter / initial-state
region. Programs that match only rarely are retained as fragile explanations.

The sampling design is supplied by the caller. Therefore the resulting claim is
conditional on the declared ABM family, constraints, and sampled admissible
region.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Mapping, Sequence

from causal_model.rule_transition_invariants import ProgramRun


@dataclass(frozen=True)
class SweepRecord:
    """One stochastic replicate or parameter draw from an ecological ABM family."""

    scenario: str
    program_id: str
    motifs: FrozenSet[str]
    pattern_matched: bool
    parameters: Mapping[str, float] = field(default_factory=dict)
    initial_state: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RobustnessPolicy:
    """Pre-registered rule for classifying a program from sweep replicates.

    min_replicates prevents a program from being called robust after one lucky
    match. min_match_fraction is the required fraction of successful samples.
    fragile_max_fraction separates rare matches from robust matches.
    """

    min_replicates: int = 20
    min_match_fraction: float = 0.20
    fragile_max_fraction: float = 0.05

    def __post_init__(self) -> None:
        if self.min_replicates < 1:
            raise ValueError("min_replicates must be at least 1")
        if not 0.0 <= self.fragile_max_fraction <= self.min_match_fraction <= 1.0:
            raise ValueError("Require 0 <= fragile_max_fraction <= min_match_fraction <= 1")


@dataclass(frozen=True)
class ProgramSweepSummary:
    scenario: str
    program_id: str
    motifs: FrozenSet[str]
    n_replicates: int
    n_matches: int
    match_fraction: float
    classification: str  # robust | fragile | rejected | insufficient


def summarise_sweep(
    records: Iterable[SweepRecord],
    policy: RobustnessPolicy = RobustnessPolicy(),
) -> tuple[ProgramSweepSummary, ...]:
    """Classify every (scenario, program) family from its parameter-sweep records."""

    grouped: dict[tuple[str, str, FrozenSet[str]], list[SweepRecord]] = {}
    for record in records:
        key = (record.scenario, record.program_id, record.motifs)
        grouped.setdefault(key, []).append(record)

    summaries: list[ProgramSweepSummary] = []
    for (scenario, program_id, motifs), group in sorted(grouped.items()):
        n_replicates = len(group)
        n_matches = sum(record.pattern_matched for record in group)
        fraction = n_matches / n_replicates

        if n_replicates < policy.min_replicates:
            classification = "insufficient"
        elif fraction >= policy.min_match_fraction:
            classification = "robust"
        elif 0.0 < fraction <= policy.fragile_max_fraction:
            classification = "fragile"
        else:
            classification = "rejected"

        summaries.append(
            ProgramSweepSummary(
                scenario=scenario,
                program_id=program_id,
                motifs=motifs,
                n_replicates=n_replicates,
                n_matches=n_matches,
                match_fraction=fraction,
                classification=classification,
            )
        )
    return tuple(summaries)


def program_runs_from_sweep(
    records: Iterable[SweepRecord],
    policy: RobustnessPolicy = RobustnessPolicy(),
) -> tuple[ProgramRun, ...]:
    """Build ProgramRun objects for the rule-transition invariant layer.

    Rejected and insufficient programs are excluded: they either do not explain
    the focal pattern in the declared family or lack enough coverage to assess.
    Fragile programs are retained with ``robust=False`` for transparent reporting.
    """

    runs: list[ProgramRun] = []
    for summary in summarise_sweep(records, policy):
        if summary.classification not in {"robust", "fragile"}:
            continue
        runs.append(
            ProgramRun(
                scenario=summary.scenario,
                program_id=summary.program_id,
                motifs=summary.motifs,
                robust=summary.classification == "robust",
                metadata={
                    "n_replicates": summary.n_replicates,
                    "n_matches": summary.n_matches,
                    "match_fraction": summary.match_fraction,
                    "classification": summary.classification,
                    "robustness_policy": {
                        "min_replicates": policy.min_replicates,
                        "min_match_fraction": policy.min_match_fraction,
                        "fragile_max_fraction": policy.fragile_max_fraction,
                    },
                },
            )
        )
    return tuple(runs)
