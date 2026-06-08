"""Minimal scoring helpers for causal pattern comparison."""

from __future__ import annotations

from .pattern_targets import PatternTarget
from .structures import CausalStructure


def score_pattern_match(observed_relation: str, simulated_relation: str) -> float:
    """Return 0 for an exact relation match and 1 for a mismatch."""

    observed = observed_relation.strip()
    simulated = simulated_relation.strip()
    return 0.0 if observed == simulated else 1.0


def expected_pattern_relations(structure: CausalStructure) -> dict[str, str]:
    """Parse ``variable: relation`` expectations from one causal structure."""

    relations: dict[str, str] = {}
    for pattern in structure.expected_patterns:
        if ":" not in pattern:
            continue
        variable, relation = pattern.split(":", 1)
        relations[variable.strip()] = relation.strip()
    return relations


def score_causal_structure(
    structure: CausalStructure,
    targets: list[PatternTarget],
) -> tuple[dict[str, float | str], list[dict[str, float | str]]]:
    """Score a causal structure against observable pattern targets.

    This is a Stage 3 schema-level comparison. It asks whether the candidate
    causal structure explicitly predicts each target relation. It does not yet
    run the biological generator; Stage 4 should replace these expected
    relations with simulation-derived relations.
    """

    predicted = expected_pattern_relations(structure)
    return score_simulated_relations(
        structure_name=structure.name,
        description=structure.description,
        relations=predicted,
        targets=targets,
        latent_parameters=";".join(structure.latent_parameters),
        edges=";".join(
            f"{edge.source}->{edge.target}({edge.relation})"
            for edge in structure.edges
        ),
    )


def score_simulated_relations(
    structure_name: str,
    description: str,
    relations: dict[str, str],
    targets: list[PatternTarget],
    latent_parameters: str = "",
    edges: str = "",
) -> tuple[dict[str, float | str], list[dict[str, float | str]]]:
    """Score simulation-derived relations against observable pattern targets."""

    detail_rows: list[dict[str, float | str]] = []
    total = 0.0
    weight_sum = sum(target.weight for target in targets) or 1.0

    for target in targets:
        simulated_relation = relations.get(target.variable, "")
        raw_mismatch = score_pattern_match(
            observed_relation=target.expected_relation,
            simulated_relation=simulated_relation,
        )
        weighted_mismatch = target.weight * raw_mismatch
        total += weighted_mismatch
        detail_rows.append(
            {
                "structure": structure_name,
                "pattern": target.name,
                "variable": target.variable,
                "observed_relation": target.expected_relation,
                "predicted_relation": simulated_relation or "not_predicted",
                "weight": target.weight,
                "raw_mismatch": raw_mismatch,
                "weighted_mismatch": weighted_mismatch,
            }
        )

    summary = {
        "structure": structure_name,
        "description": description,
        "total_mismatch": total,
        "mean_weighted_mismatch": total / weight_sum,
        "n_targets": float(len(targets)),
        "n_predicted_targets": float(
            sum(1 for target in targets if target.variable in relations)
        ),
        "latent_parameters": latent_parameters,
        "edges": edges,
    }
    return summary, detail_rows


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
