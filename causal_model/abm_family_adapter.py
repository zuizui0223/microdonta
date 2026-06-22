"""ABM-sweep classification — the single entry point for rule-transition RACH.

This module is the ONE place that turns ecological ABM-family output into
``robust`` / ``fragile`` / ``rejected`` / ``insufficient`` verdicts and the
``ProgramRun`` records consumed by :mod:`causal_model.rule_transition_invariants`.

A causal program is never robust because one parameter setting happens to work:
robustness means the focal *qualitative* pattern recurs across the declared
admissible parameter / initial-state / region space. Programs that match only
rarely, or only through fine numerical tuning (exact cancellation, boundary-only
values, exact initial-condition alignment, measure-zero tuning), are retained as
*fragile* explanations with their fragility reasons recorded — they are not
silently dropped, and they are never promoted to robust.

The sampling design is supplied by the caller, so every verdict is conditional on
the declared ABM family, constraints, and sampled admissible region.

Four input shapes are supported, all classified here so callers have a single
import home:

* ``SweepRecord`` + :func:`summarise_sweep` / :func:`program_runs_from_sweep`
  — the primary fraction-based 4-way classifier (robust/fragile/rejected/insufficient).
* ``ABMTrial`` + :func:`classify_abm_family` — region-coverage classifier
  (robust requires success across several declared parameter regions).
* ``CellSweepRecord`` + :func:`summarise_sweep_records` /
  :func:`program_runs_from_cell_sweep` — parameter-cell recurrence classifier
  with disqualifying fragility flags.
* ``SweepRun`` + :func:`classify_sweep_runs` — context-coverage classifier over a
  generic, user-supplied output type and qualitative-match predicate.

The thin modules ``abm_family``, ``abm_robustness`` and ``robust_abm_search``
remain as backward-compatible shims that re-export from here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, FrozenSet, Generic, Hashable, Iterable, Mapping, TypeVar

from causal_model.rule_transition_invariants import ProgramRun

OutputT = TypeVar("OutputT")


#: Fragility reasons that disqualify a program from a *robust* verdict: a match
#: that survives only through these is tuning-dependent, not robust.
DISQUALIFYING_FRAGILITY_FLAGS: FrozenSet[str] = frozenset(
    {
        "exact_cancellation",
        "boundary_only",
        "exact_initial_alignment",
        "measure_zero_tuning",
    }
)


# ---------------------------------------------------------------------------
# Primary classifier: fraction-based 4-way verdict (the canonical entry point)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SweepRecord:
    """One stochastic replicate or parameter draw from an ecological ABM family.

    ``fragile_flags`` records why a *match* would be fragile (e.g.
    ``exact_cancellation``); any flag in :data:`DISQUALIFYING_FRAGILITY_FLAGS`
    prevents a robust verdict. ``region_id`` / ``seed`` let the classifier report
    when matches concentrate in a single declared region or seed.
    """

    scenario: str
    program_id: str
    motifs: FrozenSet[str]
    pattern_matched: bool
    parameters: Mapping[str, float] = field(default_factory=dict)
    initial_state: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)
    region_id: Hashable | None = None
    seed: Hashable | None = None
    fragile_flags: FrozenSet[str] = frozenset()


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
    fragility_reasons: FrozenSet[str] = frozenset()


def _fragility_reasons(matching: list[SweepRecord]) -> tuple[set[str], set[str]]:
    """Return (all_flags, disqualifying_flags) gathered from matching records."""
    flags: set[str] = set()
    for record in matching:
        flags |= set(record.fragile_flags)
    return flags, flags & DISQUALIFYING_FRAGILITY_FLAGS


def summarise_sweep(
    records: Iterable[SweepRecord],
    policy: RobustnessPolicy = RobustnessPolicy(),
) -> tuple[ProgramSweepSummary, ...]:
    """Classify every (scenario, program) family from its parameter-sweep records.

    A program that would be robust by match fraction but whose matches carry a
    disqualifying fragility flag (exact cancellation, boundary-only, exact
    initial alignment, measure-zero tuning) is downgraded to ``fragile``. For any
    non-robust program the recorded ``fragility_reasons`` also note when matches
    came from a single region (``single_region``) or single seed
    (``single_seed``).
    """

    grouped: dict[tuple[str, str, FrozenSet[str]], list[SweepRecord]] = {}
    for record in records:
        key = (record.scenario, record.program_id, record.motifs)
        grouped.setdefault(key, []).append(record)

    summaries: list[ProgramSweepSummary] = []
    for (scenario, program_id, motifs), group in sorted(grouped.items()):
        n_replicates = len(group)
        matching = [record for record in group if record.pattern_matched]
        n_matches = len(matching)
        fraction = n_matches / n_replicates

        if n_replicates < policy.min_replicates:
            classification = "insufficient"
        elif fraction >= policy.min_match_fraction:
            classification = "robust"
        elif 0.0 < fraction <= policy.fragile_max_fraction:
            classification = "fragile"
        else:
            classification = "rejected"

        flags, disqualifying = _fragility_reasons(matching)
        if classification == "robust" and disqualifying:
            classification = "fragile"

        reasons: set[str] = set()
        if classification != "robust":
            reasons |= flags
            regions = {r.region_id for r in matching if r.region_id is not None}
            if regions and len(regions) == 1:
                reasons.add("single_region")
            seeds = {r.seed for r in matching if r.seed is not None}
            if seeds and len(seeds) == 1:
                reasons.add("single_seed")

        summaries.append(
            ProgramSweepSummary(
                scenario=scenario,
                program_id=program_id,
                motifs=motifs,
                n_replicates=n_replicates,
                n_matches=n_matches,
                match_fraction=fraction,
                classification=classification,
                fragility_reasons=frozenset(reasons),
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
    Fragile programs are retained with ``robust=False`` and their fragility
    reasons preserved in ``metadata['fragility_reasons']`` for transparent
    reporting.
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
                    "fragility_reasons": sorted(summary.fragility_reasons),
                    "robustness_policy": {
                        "min_replicates": policy.min_replicates,
                        "min_match_fraction": policy.min_match_fraction,
                        "fragile_max_fraction": policy.fragile_max_fraction,
                    },
                },
            )
        )
    return tuple(runs)


# ---------------------------------------------------------------------------
# Region-coverage classifier (was causal_model.abm_family)
# ---------------------------------------------------------------------------

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
class RegionRobustnessPolicy:
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
    """Audit record for one scenario/program pair (region-coverage classifier)."""

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
    policy: RegionRobustnessPolicy = RegionRobustnessPolicy(),
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


# ---------------------------------------------------------------------------
# Parameter-cell recurrence classifier (was causal_model.abm_robustness)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CellSweepRecord:
    """One stochastic ABM evaluation, tagged by parameter cell and replicate.

    ``parameter_cell`` must identify a distinct sampled parameter / update-rule /
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
class CellRobustnessPolicy:
    """Transparent operational definition of robustness for an ABM family."""

    min_parameter_cells: int = 3
    min_cell_success_rate: float = 0.5
    min_successful_cell_fraction: float = 0.6
    disqualifying_fragility_flags: FrozenSet[str] = DISQUALIFYING_FRAGILITY_FLAGS

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
    records: Iterable[CellSweepRecord],
    policy: CellRobustnessPolicy = CellRobustnessPolicy(),
) -> tuple[ProgramRobustnessSummary, ...]:
    """Classify each scenario/program pair from parameter-cell-level recurrence.

    A cell is successful when at least ``min_cell_success_rate`` of its stochastic
    replicates reproduce the focal qualitative pattern. A program is robust when
    it has enough distinct cells, enough successful cells, and no disqualifying
    fragility flag on any successful record.
    """

    grouped: dict[tuple[str, str], list[CellSweepRecord]] = {}
    for record in records:
        grouped.setdefault((record.scenario, record.program_id), []).append(record)

    summaries: list[ProgramRobustnessSummary] = []
    for (scenario, program_id), rows in sorted(grouped.items()):
        cells: dict[str, list[CellSweepRecord]] = {}
        for row in rows:
            cells.setdefault(row.parameter_cell, []).append(row)

        successful_cells: list[str] = []
        successful_rows: list[CellSweepRecord] = []
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


def program_runs_from_cell_sweep(
    records: Iterable[CellSweepRecord],
    policy: CellRobustnessPolicy = CellRobustnessPolicy(),
) -> tuple[ProgramRun, ...]:
    """Create RACH ProgramRun records with parameter-cell reproducibility metadata."""

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


# ---------------------------------------------------------------------------
# Context-coverage classifier (was causal_model.robust_abm_search)
# ---------------------------------------------------------------------------

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
