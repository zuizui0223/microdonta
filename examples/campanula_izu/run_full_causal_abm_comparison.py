"""Full stochastic causal ABM comparison for Campanula Izu Islands.

Runs M1-M5 causal structures with full individual-based ABM simulation
for Oshima and Hachijo environments, compares final generation values
against observed pattern targets.

Usage::

    python examples/campanula_izu/run_full_causal_abm_comparison.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from examples.campanula_izu.causal_structures import (
    campanula_causal_structures,
    campanula_pattern_targets,
)
from examples.campanula_izu.proxy_simulation import default_campanula_proxy_environments
from attraction_trait_model.parameters import ModelParameters
from attraction_trait_model.scenario_runner import (
    final_summary as get_final,
    run_causal_structure_simulation,
)
from causal_model.relations import relations_from_final_summaries
from causal_model.scoring import score_simulated_relations

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEEDS = [42, 43, 44, 45, 46]  # 5 independent replicates per structure × environment
GENERATIONS = 50
POPULATION_SIZE = 200

# Summary variables compared between Oshima and Hachijo
VARIABLES = [
    "mean_nectar_guide",
    "selfing_rate",
    "mean_herkogamy",
    "mean_flower_size",
    "Fis_proxy",
]

# Rename simulation keys to match pattern-target variable names
VAR_RENAME: dict[str, str] = {
    "mean_nectar_guide": "nectar_guide",
    "mean_herkogamy": "herkogamy",
    "mean_flower_size": "flower_size",
    "Fis_proxy": "Fis",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mean_final(reps: list[dict]) -> dict:
    """Average numeric fields across replicate summary dicts."""
    keys = [k for k in reps[0] if isinstance(reps[0][k], (int, float))]
    avg: dict = {}
    for k in keys:
        avg[k] = sum(r[k] for r in reps) / len(reps)
    avg["population_name"] = reps[0].get("population_name", "")
    return avg


def _write_csv(path: Path, rows: list[dict]) -> None:
    """Write *rows* to a CSV file at *path*."""
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run() -> None:
    """Execute the full stochastic causal ABM comparison and write CSVs."""

    structures = campanula_causal_structures()
    targets = campanula_pattern_targets()
    environments = default_campanula_proxy_environments()
    params = ModelParameters()

    out_dir = Path(__file__).parent / "outputs"
    out_dir.mkdir(exist_ok=True)

    all_ranking: list[dict] = []
    all_pattern_scores: list[dict] = []
    all_final_values: list[dict] = []
    all_timeseries: list[dict] = []

    for structure in structures:
        rep_finals: dict[str, list[dict]] = {name: [] for name in environments}

        # ----- run replicates ------------------------------------------------
        for pop_name, env in environments.items():
            for seed in SEEDS:
                rows = run_causal_structure_simulation(
                    structure, env, params, GENERATIONS, POPULATION_SIZE, seed
                )
                final = get_final(rows)
                final = dict(final)  # copy so we can annotate
                final["structure"] = structure.name
                final["seed"] = seed
                rep_finals[pop_name].append(final)

                for row in rows:
                    row = dict(row)
                    row["structure"] = structure.name
                    row["seed"] = seed
                    all_timeseries.append(row)

                all_final_values.append(final)

        # ----- average across seeds -----------------------------------------
        pop_names = list(environments.keys())
        left_name, right_name = pop_names[0], pop_names[1]
        left_avg = _mean_final(rep_finals[left_name])
        right_avg = _mean_final(rep_finals[right_name])

        # ----- symbolic relations -------------------------------------------
        relations = relations_from_final_summaries(
            left_avg, right_avg, VARIABLES, tolerance=0.03
        )

        # Rename keys and substitute population labels in relation strings
        left_label = left_avg.get("population_name", left_name)
        right_label = right_avg.get("population_name", right_name)
        renamed: dict[str, str] = {}
        for k, v in relations.items():
            target_key = VAR_RENAME.get(k, k)
            renamed[target_key] = (
                v.replace(left_label, left_name).replace(right_label, right_name)
            )

        # ----- score against pattern targets --------------------------------
        summary, details = score_simulated_relations(
            structure_name=structure.name,
            description=structure.description,
            relations=renamed,
            targets=targets,
            latent_parameters=";".join(structure.latent_parameters),
            edges=";".join(
                f"{e.source}->{e.target}({e.relation})" for e in structure.edges
            ),
        )
        all_ranking.append(summary)
        all_pattern_scores.extend(details)

    # ----- sort ranking by mismatch ----------------------------------------
    ranking_sorted = sorted(
        all_ranking,
        key=lambda r: (
            float(r.get("mean_weighted_mismatch", 1.0)),
            float(r.get("total_mismatch", 1.0)),
        ),
    )

    # ----- write CSVs -------------------------------------------------------
    _write_csv(out_dir / "full_causal_abm_ranking.csv", ranking_sorted)
    _write_csv(out_dir / "full_causal_abm_pattern_scores.csv", all_pattern_scores)
    _write_csv(out_dir / "full_causal_abm_final_values.csv", all_final_values)
    _write_csv(out_dir / "full_causal_abm_generation_timeseries.csv", all_timeseries)

    # ----- console summary --------------------------------------------------
    print("\nFull stochastic causal ABM ranking (Campanula Izu Islands)")
    print("-" * 60)
    cols = ["structure", "mean_weighted_mismatch", "total_mismatch"]
    widths = {
        c: max(len(c), max(len(str(r.get(c, ""))) for r in ranking_sorted))
        for c in cols
    }
    print("  ".join(c.ljust(widths[c]) for c in cols))
    for r in ranking_sorted:
        print("  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))
    print(f"\nOutputs written to {out_dir}/")


if __name__ == "__main__":
    run()
