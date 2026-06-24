"""Rule-transition invariant discovery with assumptions separated from outcomes.

The invariant is conditional on the declared ABM family. Structural assumptions
and simulated trait-space outcomes are stored separately so an outcome cannot be
"discovered" merely because it was placed in a program motif set.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import FrozenSet, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ProgramRun:
    scenario: str
    program_id: str
    motifs: FrozenSet[str]  # assumptions / structural conditions only
    robust: bool
    metadata: Mapping[str, object] = field(default_factory=dict)
    outcome_motifs: FrozenSet[str] = frozenset()  # derived from simulated records


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    robust_program_ids: tuple[str, ...]
    fragile_program_ids: tuple[str, ...]
    necessary_motifs: FrozenSet[str]
    disjunctive_necessary_clauses: tuple[FrozenSet[str], ...]
    no_common_rule: bool
    necessary_assumption_motifs: FrozenSet[str] = frozenset()
    necessary_outcome_motifs: FrozenSet[str] = frozenset()


@dataclass(frozen=True)
class CrossSystemResult:
    by_scenario: Mapping[str, ScenarioResult]
    cross_system_common_motifs: FrozenSet[str]
    cross_system_common_clauses: tuple[FrozenSet[str], ...]
    no_cross_system_common_rule: bool
    cross_system_common_assumption_motifs: FrozenSet[str] = frozenset()
    cross_system_common_outcome_motifs: FrozenSet[str] = frozenset()


def _minimal_hitting_sets(program_motifs: Sequence[FrozenSet[str]]) -> tuple[FrozenSet[str], ...]:
    """Minimal clauses that intersect every robust program's assumption set."""
    if not program_motifs:
        return ()
    universe = sorted(set().union(*program_motifs))
    candidates: list[FrozenSet[str]] = []
    for size in range(1, len(universe) + 1):
        for combo in combinations(universe, size):
            clause = frozenset(combo)
            if all(clause & motifs for motifs in program_motifs):
                if not any(existing <= clause for existing in candidates):
                    candidates.append(clause)
        if candidates:
            break
    return tuple(candidates)


def _intersect_clauses(clause_sets: Iterable[tuple[FrozenSet[str], ...]]) -> tuple[FrozenSet[str], ...]:
    clause_sets = list(clause_sets)
    if not clause_sets:
        return ()
    common = set(clause_sets[0])
    for clauses in clause_sets[1:]:
        common &= set(clauses)
    return tuple(sorted(common, key=lambda c: (len(c), tuple(sorted(c)))))


def _intersection(sets: Sequence[FrozenSet[str]]) -> FrozenSet[str]:
    return frozenset.intersection(*sets) if sets else frozenset()


def infer_rule_transition_invariants(runs: Iterable[ProgramRun]) -> CrossSystemResult:
    """Infer conditional necessities from robust runs.

    ``motifs`` are assumptions; ``outcome_motifs`` must come from simulated
    outcomes. The legacy combined fields are retained for callers, while the
    separate fields make the provenance of every claim inspectable.
    """
    grouped: dict[str, list[ProgramRun]] = {}
    for run in runs:
        grouped.setdefault(run.scenario, []).append(run)
    if not grouped:
        raise ValueError("At least one ProgramRun is required.")

    by_scenario: dict[str, ScenarioResult] = {}
    scenario_assumptions: list[FrozenSet[str]] = []
    scenario_outcomes: list[FrozenSet[str]] = []
    scenario_clauses: list[tuple[FrozenSet[str], ...]] = []
    for scenario, scenario_runs in sorted(grouped.items()):
        robust_runs = [run for run in scenario_runs if run.robust]
        fragile_runs = [run for run in scenario_runs if not run.robust]
        assumptions = _intersection([run.motifs for run in robust_runs])
        outcomes = _intersection([run.outcome_motifs for run in robust_runs])
        clauses = _minimal_hitting_sets([run.motifs for run in robust_runs]) if robust_runs else ()
        combined = frozenset(assumptions | outcomes)
        summary = ScenarioResult(
            scenario=scenario,
            robust_program_ids=tuple(sorted(run.program_id for run in robust_runs)),
            fragile_program_ids=tuple(sorted(run.program_id for run in fragile_runs)),
            necessary_motifs=combined,
            disjunctive_necessary_clauses=clauses,
            no_common_rule=not bool(combined or clauses),
            necessary_assumption_motifs=assumptions,
            necessary_outcome_motifs=outcomes,
        )
        by_scenario[scenario] = summary
        scenario_assumptions.append(assumptions)
        scenario_outcomes.append(outcomes)
        scenario_clauses.append(clauses)

    common_assumptions = _intersection(scenario_assumptions)
    common_outcomes = _intersection(scenario_outcomes)
    common_clauses = _intersect_clauses(scenario_clauses)
    common = frozenset(common_assumptions | common_outcomes)
    return CrossSystemResult(
        by_scenario=by_scenario,
        cross_system_common_motifs=common,
        cross_system_common_clauses=common_clauses,
        no_cross_system_common_rule=not bool(common or common_clauses),
        cross_system_common_assumption_motifs=common_assumptions,
        cross_system_common_outcome_motifs=common_outcomes,
    )


def explain_result(result: CrossSystemResult) -> dict[str, object]:
    return {
        "cross_system_common_motifs": sorted(result.cross_system_common_motifs),
        "cross_system_common_assumption_motifs": sorted(result.cross_system_common_assumption_motifs),
        "cross_system_common_outcome_motifs": sorted(result.cross_system_common_outcome_motifs),
        "cross_system_common_clauses": [sorted(c) for c in result.cross_system_common_clauses],
        "no_cross_system_common_rule": result.no_cross_system_common_rule,
        "scenarios": {
            name: {
                "robust_program_ids": list(summary.robust_program_ids),
                "fragile_program_ids": list(summary.fragile_program_ids),
                "necessary_motifs": sorted(summary.necessary_motifs),
                "necessary_assumption_motifs": sorted(summary.necessary_assumption_motifs),
                "necessary_outcome_motifs": sorted(summary.necessary_outcome_motifs),
                "disjunctive_necessary_clauses": [sorted(c) for c in summary.disjunctive_necessary_clauses],
                "no_common_rule": summary.no_common_rule,
            }
            for name, summary in result.by_scenario.items()
        },
    }
