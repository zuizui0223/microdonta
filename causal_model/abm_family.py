"""ABM-family adapter for rule-transition RACH.

This module turns repeated outputs from a stochastic ecological simulator into
``ProgramRun`` objects for ``rule_transition_invariants``.  Robustness is not a
single successful run: a program must reproduce the focal qualitative pattern
at an adequate rate across multiple declared parameter regions.

The caller controls all scientific choices:
- how an ABM output is converted into a qualitative match;
- which motifs the program embodies;
- how parameter space is partitioned into interpretable regions.

This keeps the framework model-family based while avoiding a hidden numerical
notion of robustness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Generic, Hashable, Iterable, Mapping, TypeVar

from causal_model.rule_transition_invariants import ProgramRun

OutputT = TypeVar("OutputT")


@dataclass(frozen=True)
class ABMTrial(Generic[OutputT]):
    """One stochastic ABM replicate.

    ``region_id`` must identify a predeclared coarse parameter / initial-state
    region, not merely a random seed.  Repeated seeds in one region increase
    precision, but do not by themselves establish robustness.
    """

    scenario: str
    program_id: str
    region_id: Hashable
    output: OutputT
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RobustnessPolicy:
    """Transparent rule for classifying a program as robust or fragile.

    Parameters
    ----------
    min_success_rate:
        Minimum mean pattern-match rate across occupied regions.
    min_regions:
        Minimum number of distinct parameter regions with at least one match.
    min_trials_per_region:
        Regions with fewer trials are ignored for rate calculation.  This avoids
        labelling a one-off numerical draw as robust.
    """

    min_success_rate: float = 0.6
    min_regions: int = 2
    min_trials_per_region: int = 1

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_success_rate <= 1.0:
            raise ValueError("min_success_rate must lie in [0, 1].")
        if self.min_regions < 1:
            raise ValueError("min_regions must be at least 1.")
        if self.min_trials_per_region < 1:
            raise ValueError("min_trials_per_region must be at least 1.")


@dataclass(frozen=True)
class ProgramRobustness:
    """Audit record for one scenario/program pair."""

    scenario: str
    program_id: str
    n_trials: int
    n_matching_trials: int
    occupied_regions: int
    mean_region_success_rate: float
    robust: bool


def classify_abm_family(
    trials: Iterable[ABMTrial[OutputT]],
    pattern_matches: Callable[[OutputT], bool],
    motifs_for_program: Callable[[str, str], Iterable[str]],
    policy: RobustnessPolicy = RobustnessPolicy(),
) -> tuple[list[ProgramRun], list[ProgramRobustness]]:
    """Classify simulator families and construct RACH ``ProgramRun`` records.

    A program is robust only when its qualitative observation is reproduced in
    enough independent declared regions and with enough mean within-region
    support.  Programs with at least one success but failing this test remain
    usable as ``robust=False`` fragile explanations. Programs with no successful
    trial are omitted because they are not admissible explanations.
    """

    grouped: dict[tuple[str, str], dict[Hashable, list[bool]]] = {}
    for trial in trials:
        key = (trial.scenario, trial.program_id)
        grouped.setdefault(key, {}).setdefault(trial.region_id, []).append(pattern_matches(trial.output))

    runs: list[ProgramRun] = []
    audits: list[ProgramRobustness] = []
    for (scenario, program_id), regions in sorted(grouped.items()):
        eligible = [values for values in regions.values() if len(values) >= policy.min_trials_per_region]
        n_trials = sum(len(values) for values in regions.values())
        n_matches = sum(sum(values) for values in regions.values())
        occupied = sum(any(values) for values in eligible)
        rates = [sum(values) / len(values) for values in eligible]
        mean_rate = sum(rates) / len(rates) if rates else 0.0
        robust = occupied >= policy.min_regions and mean_rate >= policy.min_success_rate

        audits.append(
            ProgramRobustness(
                scenario=scenario,
                program_id=program_id,
                n_trials=n_trials,
                n_matching_trials=n_matches,
                occupied_regions=occupied,
                mean_region_success_rate=mean_rate,
                robust=robust,
            )
        )
        if n_matches == 0:
            continue

        runs.append(
            ProgramRun(
                scenario=scenario,
                program_id=program_id,
                motifs=frozenset(motifs_for_program(scenario, program_id)),
                robust=robust,
                metadata={
                    "n_trials": n_trials,
                    "n_matching_trials": n_matches,
                    "occupied_regions": occupied,
                    "mean_region_success_rate": mean_rate,
                    "robustness_policy": {
                        "min_success_rate": policy.min_success_rate,
                        "min_regions": policy.min_regions,
                        "min_trials_per_region": policy.min_trials_per_region,
                    },
                },
            )
        )
    return runs, audits
