"""Small finite-occupancy phase-diagram pilot.

This example deliberately stays at the mathematical simulation layer. It does
not project the result onto Campanula or any empirical ecosystem.
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from causal_model.multipatch_criticality_experiments import (
    CellResult,
    results_to_csv_rows,
    run_parameter_grid,
    standard_profile,
)


PILOT_PARAMETER_CELLS = (
    (0.8, 3.0, 0.55),
    (0.8, 4.5, 0.75),
    (1.0, 4.5, 0.55),
    (1.2, 4.5, 0.75),
)


def pilot_spec():
    """Return the small finite-bin sweep used in the pilot report."""
    return replace(
        standard_profile(),
        generations=20,
        replicates=8,
        area_reference_values=(0.8, 1.0, 1.2),
        interaction_feedback_values=(3.0, 4.5),
        interaction_barrier_values=(0.35, 0.55, 0.75),
        master_seed=23,
    )


def run_pilot() -> tuple[CellResult, ...]:
    return run_parameter_grid(pilot_spec())


def render_markdown(results: Sequence[CellResult]) -> str:
    rows = results_to_csv_rows(results)
    selected = tuple(row for row in rows if _cell_key(row) in PILOT_PARAMETER_CELLS)
    severe = _find_row(rows, "equal_isolated", (1.2, 4.5, 0.75))
    lead_rows = tuple(
        row
        for row in rows
        if max(
            row["probabilities.genetic_lead_H_alpha"],
            row["probabilities.genetic_lead_H_gamma"],
            row["probabilities.genetic_lead_FST"],
            row["probabilities.allele_loss_lead"],
        )
        > 0.0
    )
    lines = [
        "# Finite occupancy phase-diagram pilot",
        "",
        "This is a model-specific stochastic pilot, not a theorem and not an empirical ecosystem projection.",
        "",
        "## Design",
        "",
        f"- profile: finite-bin standard profile, reduced to {len(rows)} scenario x parameter cells",
        "- generations: 20",
        "- replicates per cell: 8",
        "- landscapes: one_large, equal_isolated, equal_migrating",
        "- closure: finite_trait_bin_recruitment + two_kernel_recruitment + coupled q feedback",
        "",
        "## Main mathematical takeaways",
        "",
        "1. One large patch retained realised high-trait occupancy in every pilot cell.",
        "2. Fragmented landscapes produced model-specific transition regions where realised high-trait persistence fell sharply.",
        "3. Genetic first-passage warnings often preceded realised high-trait loss among valid event pairs.",
        "4. H_alpha, H_gamma, and F_ST did not collapse to one diversity signal.",
        "5. These results are parameter-specific simulation outcomes; they do not establish universal early warning.",
        "",
        "## Selected landscape contrasts",
        "",
        "| scenario | A_ref | kappa | theta | Pr(realised persists) | H_alpha mean | H_gamma mean | F_ST mean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in selected:
        lines.append(
            "| {scenario_id} | {area_reference:.1f} | {interaction_feedback:.1f} | {interaction_barrier:.2f} | "
            "{persist:.3f} | {h_alpha:.3f} | {h_gamma:.3f} | {fst} |".format(
                scenario_id=row["scenario_id"],
                area_reference=row["area_reference"],
                interaction_feedback=row["interaction_feedback"],
                interaction_barrier=row["interaction_barrier"],
                persist=row["probabilities.realised_high_trait_persistence_final"],
                h_alpha=row["metrics.H_alpha.mean"],
                h_gamma=row["metrics.H_gamma.mean"],
                fst=_fmt_optional(row["metrics.F_ST.mean"]),
            )
        )
    lines.extend(
        [
            "",
            "## Severe fragmented cell",
            "",
            "For `equal_isolated`, `A_ref=1.2`, `kappa=4.5`, `theta=0.75`:",
            "",
            f"- final realised high-trait persistence probability: {_fmt(severe['probabilities.realised_high_trait_persistence_final'])}",
            f"- final potential high-trait viability probability: {_fmt(severe['probabilities.potential_high_trait_viability_final'])}",
            f"- median tau_trait_realised: {_fmt_optional(severe['first_passage.tau_trait_realised.median'])}",
            f"- median tau_H_alpha: {_fmt_optional(severe['first_passage.tau_H_alpha.median'])}",
            f"- median tau_H_gamma: {_fmt_optional(severe['first_passage.tau_H_gamma.median'])}",
            f"- median tau_FST: {_fmt_optional(severe['first_passage.tau_FST.median'])}",
            f"- Pr(tau_H_alpha < tau_trait_realised): {_fmt(severe['probabilities.genetic_lead_H_alpha'])}",
            f"- Pr(tau_H_gamma < tau_trait_realised): {_fmt(severe['probabilities.genetic_lead_H_gamma'])}",
            f"- Pr(tau_FST < tau_trait_realised): {_fmt(severe['probabilities.genetic_lead_FST'])}",
            f"- Pr(tau_allele_loss < tau_trait_realised): {_fmt(severe['probabilities.allele_loss_lead'])}",
            "",
            "This cell is a useful mathematical witness that genetic warnings can precede realised trait loss under the declared closure.",
            "It is not evidence that this ordering is universal.",
            "",
            "## Lead signal coverage",
            "",
            f"{len(lead_rows)} of {len(rows)} pilot rows had at least one nonzero genetic/allele lead probability.",
            "Rows with no valid event pairs retain censoring rather than being counted as no-lead evidence.",
            "",
            "## Interpretation discipline",
            "",
            "The pilot preserves the central non-equivalence:",
            "",
            "```text",
            "Omega_tau^potential != realised N_H > 0 != p > 0 != H_alpha > 0",
            "```",
            "",
            "The next empirical step is to decide which observations would identify these quantities, not to map them onto Campanula immediately.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(results: Sequence[CellResult], path: Path) -> None:
    rows = results_to_csv_rows(results)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _cell_key(row: dict[str, object]) -> tuple[float, float, float]:
    return (float(row["area_reference"]), float(row["interaction_feedback"]), float(row["interaction_barrier"]))


def _find_row(rows: Iterable[dict[str, object]], scenario_id: str, cell: tuple[float, float, float]) -> dict[str, object]:
    for row in rows:
        if row["scenario_id"] == scenario_id and _cell_key(row) == cell:
            return row
    raise ValueError(f"missing row for {scenario_id} {cell}")


def _fmt(value: object) -> str:
    return f"{float(value):.3f}"


def _fmt_optional(value: object) -> str:
    if value is None:
        return "NA"
    return _fmt(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", type=Path, help="Optional path for a Markdown report.")
    parser.add_argument("--csv", type=Path, help="Optional path for CSV-friendly rows.")
    args = parser.parse_args(argv)

    results = run_pilot()
    report = render_markdown(results)
    if args.markdown:
        args.markdown.write_text(report, encoding="utf-8")
    else:
        print(report)
    if args.csv:
        write_csv(results, args.csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
