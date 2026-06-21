"""RACH rule-transition invariant discovery.

This module takes qualitative runs from ecological model families and extracts
rule-transition motifs that remain necessary across robust explanations.
A fragile run reproduces a pattern only through special tuning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import FrozenSet, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ProgramRun:
    scenario: str
    program_id: str
    motifs: FrozenSet[str]
    robust: bool
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    robust_program_ids: tuple[str, ...]
    fragile_program_ids: tuple[str, ...]
    necessary_motifs: FrozenSet[str]
    disjunctive_necessary_clauses: tuple[FrozenSet[str], ...]
    no_common_rule: bool


@dataclass(frozen=True)
class CrossSystemResult:
    by_scenario: Mapping[str, ScenarioResult]
    cross_system_common_motifs: FrozenSet[str]
    cross_system_common_clauses: tuple[FrozenSet[str], ...]
    no_cross_system_common_rule: bool


def _minimal_hitting_sets(program_motifs: Sequence[FrozenSet[str]]) -> tuple[FrozenSet[str], ...]:
    """Minimal clauses that intersect every robust program's motif set."""
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


def infer_rule_transition_invariants(runs: Iterable[ProgramRun]) -> CrossSystemResult:
    """Infer motifs and disjunctive clauses necessary across robust runs.

    The returned claim is conditional: no robust admissible program in the
    specified model family reproduces the supplied pattern without the motif or
    clause. It is not a claim of universal truth in nature.
    """
    grouped: dict[str, list[ProgramRun]] = {}
    for run in runs:
        grouped.setdefault(run.scenario, []).append(run)
    if not grouped:
        raise ValueError("At least one ProgramRun is required.")

    by_scenario: dict[str, ScenarioResult] = {}
    scenario_necessary: list[FrozenSet[str]] = []
    scenario_clauses: list[tuple[FrozenSet[str], ...]] = []
    for scenario, scenario_runs in sorted(grouped.items()):
        robust_runs = [run for run in scenario_runs if run.robust]
        fragile_runs = [run for run in scenario_runs if not run.robust]
        if robust_runs:
            necessary = frozenset.intersection(*(run.motifs for run in robust_runs))
            clauses = _minimal_hitting_sets([run.motifs for run in robust_runs])
        else:
            necessary, clauses = frozenset(), ()
        summary = ScenarioResult(
            scenario=scenario,
            robust_program_ids=tuple(sorted(run.program_id for run in robust_runs)),
            fragile_program_ids=tuple(sorted(run.program_id for run in fragile_runs)),
            necessary_motifs=necessary,
            disjunctive_necessary_clauses=clauses,
            no_common_rule=not bool(necessary or clauses),
        )
        by_scenario[scenario] = summary
        scenario_necessary.append(necessary)
        scenario_clauses.append(clauses)

    common_motifs = frozenset.intersection(*scenario_necessary)
    common_clauses = _intersect_clauses(scenario_clauses)
    return CrossSystemResult(
        by_scenario=by_scenario,
        cross_system_common_motifs=common_motifs,
        cross_system_common_clauses=common_clauses,
        no_cross_system_common_rule=not bool(common_motifs or common_clauses),
    )


def explain_result(result: CrossSystemResult) -> dict[str, object]:
    return {
        "cross_system_common_motifs": sorted(result.cross_system_common_motifs),
        "cross_system_common_clauses": [sorted(c) for c in result.cross_system_common_clauses],
        "no_cross_system_common_rule": result.no_cross_system_common_rule,
        "scenarios": {
            name: {
                "robust_program_ids": list(summary.robust_program_ids),
                "fragile_program_ids": list(summary.fragile_program_ids),
                "necessary_motifs": sorted(summary.necessary_motifs),
                "disjunctive_necessary_clauses": [sorted(c) for c in summary.disjunctive_necessary_clauses],
                "no_common_rule": summary.no_common_rule,
            }
            for name, summary in result.by_scenario.items()
        },
    }
