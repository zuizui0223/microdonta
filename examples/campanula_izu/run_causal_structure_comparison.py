"""Rank Campanula latent causal structures against observable pattern targets.

This is the Issue #3 Stage 4 runner. It uses a deterministic proxy generator
connected to `attraction_trait_model` probability functions, converts M1-M5
outputs into Oshima/Hachijo pattern relations, and ranks the causal structures
against observable Campanula pattern targets.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from causal_model import (  # noqa: E402
    default_campanula_causal_structures,
    default_campanula_pattern_targets,
    score_simulated_relations,
    simulate_campanula_causal_structure,
)


def main() -> None:
    structures = default_campanula_causal_structures()
    targets = default_campanula_pattern_targets()

    summary_rows: list[dict[str, float | str]] = []
    detail_rows: list[dict[str, float | str]] = []
    value_rows: list[dict[str, float | str]] = []
    for structure in structures:
        relations, outputs = simulate_campanula_causal_structure(structure)
        summary, details = score_simulated_relations(
            structure_name=structure.name,
            description=structure.description,
            relations=relations,
            targets=targets,
            latent_parameters=";".join(structure.latent_parameters),
            edges=";".join(
                f"{edge.source}->{edge.target}({edge.relation})"
                for edge in structure.edges
            ),
        )
        summary_rows.append(summary)
        detail_rows.extend(details)
        for output in outputs:
            value_rows.append(
                {
                    "structure": structure.name,
                    "population": output.population,
                    "nectar_guide": output.nectar_guide,
                    "selfing_rate": output.selfing_rate,
                    "herkogamy": output.herkogamy,
                    "flower_size": output.flower_size,
                    "Fis": output.Fis,
                    "Bombus_frequency": output.Bombus_frequency,
                    "outcrossing_opportunity": output.outcrossing_opportunity,
                }
            )

    ranking = sorted(
        summary_rows,
        key=lambda row: (
            float(row["mean_weighted_mismatch"]),
            float(row["total_mismatch"]),
            str(row["structure"]),
        ),
    )
    details = sorted(
        detail_rows,
        key=lambda row: (str(row["structure"]), str(row["pattern"])),
    )
    values = sorted(
        value_rows,
        key=lambda row: (str(row["structure"]), str(row["population"])),
    )

    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(exist_ok=True)
    ranking_path = out_dir / "causal_structure_ranking.csv"
    details_path = out_dir / "causal_structure_pattern_scores.csv"
    values_path = out_dir / "causal_structure_simulated_values.csv"
    write_csv(ranking_path, ranking)
    write_csv(details_path, details)
    write_csv(values_path, values)

    print("Campanula latent causal structure ranking")
    print_table(
        ranking,
        columns=[
            "structure",
            "mean_weighted_mismatch",
            "total_mismatch",
            "n_predicted_targets",
        ],
    )
    print(f"\nWrote: {ranking_path}")
    print(f"Wrote: {details_path}")
    print(f"Wrote: {values_path}")


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    columns = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def print_table(rows: list[dict[str, float | str]], columns: list[str]) -> None:
    widths = {
        column: max(len(column), *(len(format_cell(row[column])) for row in rows))
        for column in columns
    }
    print(" ".join(column.ljust(widths[column]) for column in columns))
    print(" ".join("-" * widths[column] for column in columns))
    for row in rows:
        print(" ".join(format_cell(row[column]).ljust(widths[column]) for column in columns))


def format_cell(value: float | str) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


if __name__ == "__main__":
    main()
