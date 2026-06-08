"""Pattern matching and scenario ranking."""

from __future__ import annotations

from dataclasses import dataclass

from .patterns import ObservablePattern


@dataclass(frozen=True)
class PatternMatchResult:
    scenario: str
    total_distance: float
    pattern_distances: dict[str, float]


def compare_patterns(
    scenario: str,
    observed: list[ObservablePattern],
    simulated: dict[str, float | str | list[str]],
) -> PatternMatchResult:
    """Compare simulated outputs with observed CAPOM patterns."""

    distances: dict[str, float] = {}
    for pattern in observed:
        if pattern.name not in simulated:
            distances[pattern.name] = float("inf")
            continue
        distances[pattern.name] = pattern.weight * pattern.distance(simulated[pattern.name])
    return PatternMatchResult(
        scenario=scenario,
        total_distance=sum(distances.values()),
        pattern_distances=distances,
    )


def rank_scenarios(results: list[PatternMatchResult]) -> list[PatternMatchResult]:
    """Return scenario matches from best to worst."""

    return sorted(results, key=lambda result: result.total_distance)
