"""Minimal scoring helpers for causal pattern comparison."""

from __future__ import annotations


def score_pattern_match(observed_relation: str, simulated_relation: str) -> float:
    """Return 0 for an exact relation match and 1 for a mismatch."""

    observed = observed_relation.strip()
    simulated = simulated_relation.strip()
    return 0.0 if observed == simulated else 1.0


def summarize_structure_support(
    structure_name: str,
    pattern_scores: dict[str, float],
) -> dict[str, float | str]:
    """Summarize mismatch scores for one candidate causal structure."""

    total = float(sum(pattern_scores.values()))
    n_patterns = len(pattern_scores)
    mean = total / n_patterns if n_patterns else 0.0
    return {
        "structure": structure_name,
        "total_mismatch": total,
        "mean_mismatch": mean,
        "n_patterns": float(n_patterns),
    }
