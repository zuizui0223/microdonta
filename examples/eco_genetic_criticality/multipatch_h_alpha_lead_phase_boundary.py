"""Plot H_alpha lead-probability phase boundaries for the multipatch pilot.

This example stays at the mathematical simulation layer. It compares fixed
total-area landscapes without projecting the result onto Campanula or any other
empirical ecosystem.
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eco_genetic_criticality.multipatch_criticality_experiments import (
    CellResult,
    ExperimentSpec,
    results_to_csv_rows,
    run_parameter_grid,
    standard_profile,
)


LEAD_PROBABILITY_KEY = "probabilities.genetic_lead_H_alpha"
SCENARIO_ORDER = ("one_large", "equal_isolated", "equal_migrating")


def phase_boundary_spec() -> ExperimentSpec:
    """Return the reproducible finite-bin sweep used for the boundary figure."""
    return replace(
        standard_profile(),
        experiment_id="h_alpha_lead_phase_boundary",
        generations=20,
        replicates=8,
        area_reference_values=(0.8, 1.0, 1.2),
        interaction_feedback_values=(3.0, 4.5),
        interaction_barrier_values=(0.35, 0.55, 0.75),
        master_seed=23,
    )


def run_phase_boundary() -> tuple[CellResult, ...]:
    return run_parameter_grid(phase_boundary_spec())


def phase_boundary_rows(results: Sequence[CellResult]) -> tuple[dict[str, object], ...]:
    rows = results_to_csv_rows(results)
    return tuple(sorted(rows, key=_row_sort_key))


def heatmap_matrix(
    rows: Iterable[Mapping[str, object]],
    *,
    scenario_id: str,
    interaction_feedback: float,
) -> tuple[tuple[float, ...], tuple[float, ...], list[list[float | None]]]:
    """Return A_ref values, theta values, and the H_alpha lead-probability grid."""
    selected = tuple(
        row
        for row in rows
        if row["scenario_id"] == scenario_id
        and float(row["interaction_feedback"]) == float(interaction_feedback)
    )
    area_values = tuple(sorted({float(row["area_reference"]) for row in selected}))
    theta_values = tuple(sorted({float(row["interaction_barrier"]) for row in selected}))
    matrix: list[list[float | None]] = [[None for _ in theta_values] for _ in area_values]
    area_index = {value: index for index, value in enumerate(area_values)}
    theta_index = {value: index for index, value in enumerate(theta_values)}
    for row in selected:
        matrix[area_index[float(row["area_reference"])]][theta_index[float(row["interaction_barrier"])]] = float(row[LEAD_PROBABILITY_KEY])
    return area_values, theta_values, matrix


def render_phase_boundary_svg(rows: Sequence[Mapping[str, object]], path: Path) -> None:
    """Write a faceted SVG heatmap for Pr(tau_H_alpha < tau_trait_realised)."""
    feedback_values = tuple(sorted({float(row["interaction_feedback"]) for row in rows}))
    cell = 42
    panel_gap_x = 62
    panel_gap_y = 70
    left = 90
    top = 62
    legend_width = 110
    panel_width = cell * 3
    panel_height = cell * 3
    width = left + len(feedback_values) * panel_width + (len(feedback_values) - 1) * panel_gap_x + legend_width
    height = top + len(SCENARIO_ORDER) * panel_height + (len(SCENARIO_ORDER) - 1) * panel_gap_y + 45
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,sans-serif;font-size:12px}.small{font-size:10px}.title{font-size:14px;font-weight:bold}</style>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="18" y="26" class="title">Pr(tau_H_alpha &lt; tau_trait_realised) phase boundary</text>',
    ]
    for row_index, scenario_id in enumerate(SCENARIO_ORDER):
        for col_index, feedback in enumerate(feedback_values):
            area_values, theta_values, matrix = heatmap_matrix(
                rows,
                scenario_id=scenario_id,
                interaction_feedback=feedback,
            )
            panel_x = left + col_index * (panel_width + panel_gap_x)
            panel_y = top + row_index * (panel_height + panel_gap_y)
            parts.append(f'<text x="{panel_x}" y="{panel_y - 18}" class="small">interaction_feedback={feedback:.1f}</text>')
            if col_index == 0:
                parts.append(f'<text x="14" y="{panel_y + panel_height / 2 - 8}" class="small">{scenario_id}</text>')
                parts.append(f'<text x="14" y="{panel_y + panel_height / 2 + 8}" class="small">A_ref</text>')
            for area_i in range(len(area_values)):
                for theta_i in range(len(theta_values)):
                    value = matrix[area_i][theta_i]
                    x = panel_x + theta_i * cell
                    y = panel_y + (len(area_values) - 1 - area_i) * cell
                    fill = "#eeeeee" if value is None else _viridis_like(value)
                    label = "NA" if value is None else f"{value:.2f}"
                    text_color = "white" if value is not None and value > 0.55 else "black"
                    parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" stroke="#ffffff"/>')
                    parts.append(f'<text x="{x + cell / 2}" y="{y + cell / 2 + 4}" text-anchor="middle" fill="{text_color}" class="small">{label}</text>')
            for theta_i, theta in enumerate(theta_values):
                x = panel_x + theta_i * cell + cell / 2
                parts.append(f'<text x="{x}" y="{panel_y + panel_height + 16}" text-anchor="middle" class="small">{theta:.2f}</text>')
            for area_i, area in enumerate(area_values):
                y = panel_y + (len(area_values) - 1 - area_i) * cell + cell / 2 + 4
                parts.append(f'<text x="{panel_x - 8}" y="{y}" text-anchor="end" class="small">{area:.1f}</text>')
            if row_index == len(SCENARIO_ORDER) - 1:
                parts.append(f'<text x="{panel_x + panel_width / 2}" y="{panel_y + panel_height + 34}" text-anchor="middle" class="small">theta</text>')
    legend_x = width - 82
    legend_y = top
    parts.append(f'<text x="{legend_x}" y="{legend_y - 18}" class="small">lead probability</text>')
    for index in range(11):
        value = index / 10
        y = legend_y + (10 - index) * 14
        parts.append(f'<rect x="{legend_x}" y="{y}" width="20" height="14" fill="{_viridis_like(value)}"/>')
        if index in {0, 5, 10}:
            parts.append(f'<text x="{legend_x + 28}" y="{y + 11}" class="small">{value:.1f}</text>')
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def render_markdown(rows: Sequence[Mapping[str, object]], figure_path: Path) -> str:
    severe = _find_row(rows, "equal_isolated", area_reference=1.2, interaction_feedback=4.5, theta=0.75)
    strongest = max(rows, key=lambda row: float(row[LEAD_PROBABILITY_KEY]))
    lines = [
        "# H_alpha lead-probability phase boundary",
        "",
        "This is a model-specific phase-boundary pilot, not a theorem and not an ecosystem projection.",
        "Campanula mapping is deliberately deferred until the mathematical conclusions are sharper.",
        "",
        f"![H_alpha lead phase boundary]({figure_path.as_posix()})",
        "",
        "## Design",
        "",
        "- landscapes: one_large, equal_isolated, equal_migrating under fixed total area",
        "- panel columns: `interaction_feedback`, the extended simulator parameter",
        "- panel x-axis: `theta`",
        "- panel y-axis: `A_ref`",
        "- color: `Pr(tau_H_alpha < tau_trait_realised)` among valid event pairs",
        "- censoring: rows without valid event pairs are not converted into no-lead evidence",
        "",
        "## Interpretation discipline",
        "",
        "`interaction_feedback` is not the canonical logistic theorem parameter `kappa`.",
        "The figure is therefore evidence about the declared extended closure, not a proof of the canonical threshold.",
        "",
        "The plotted quantity connects H1-H3 only as a simulation witness:",
        "",
        "```text",
        "fixed total area landscape -> interaction/occupancy dynamics -> Pr(tau_H_alpha < tau_trait_realised)",
        "```",
        "",
        "It keeps the key non-equivalence explicit:",
        "",
        "```text",
        "Omega_tau^potential != realised N_H > 0 != p > 0 != H_alpha > 0",
        "```",
        "",
        "## Witness cells",
        "",
        "- strongest H_alpha lead row: "
        f"`{strongest['scenario_id']}`, A_ref={float(strongest['area_reference']):.1f}, "
        f"interaction_feedback={float(strongest['interaction_feedback']):.1f}, "
        f"theta={float(strongest['interaction_barrier']):.2f}, "
        f"Pr={float(strongest[LEAD_PROBABILITY_KEY]):.3f}",
        "- severe fragmented cell: "
        "`equal_isolated`, A_ref=1.2, interaction_feedback=4.5, theta=0.75, "
        f"Pr={float(severe[LEAD_PROBABILITY_KEY]):.3f}",
        "",
    ]
    return "\n".join(lines)


def write_csv(rows: Sequence[Mapping[str, object]], path: Path) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _row_sort_key(row: Mapping[str, object]) -> tuple[str, float, float, float]:
    return (
        str(row["scenario_id"]),
        float(row["area_reference"]),
        float(row["interaction_feedback"]),
        float(row["interaction_barrier"]),
    )


def _find_row(
    rows: Iterable[Mapping[str, object]],
    scenario_id: str,
    *,
    area_reference: float,
    interaction_feedback: float,
    theta: float,
) -> Mapping[str, object]:
    for row in rows:
        if (
            row["scenario_id"] == scenario_id
            and float(row["area_reference"]) == float(area_reference)
            and float(row["interaction_feedback"]) == float(interaction_feedback)
            and float(row["interaction_barrier"]) == float(theta)
        ):
            return row
    raise ValueError("missing requested phase-boundary row")


def _viridis_like(value: float) -> str:
    clamped = max(0.0, min(1.0, value))
    stops = (
        (0.00, (68, 1, 84)),
        (0.25, (59, 82, 139)),
        (0.50, (33, 145, 140)),
        (0.75, (94, 201, 98)),
        (1.00, (253, 231, 37)),
    )
    for (left_v, left_rgb), (right_v, right_rgb) in zip(stops, stops[1:]):
        if left_v <= clamped <= right_v:
            span = right_v - left_v
            weight = 0.0 if span == 0 else (clamped - left_v) / span
            rgb = tuple(round(left_rgb[i] * (1.0 - weight) + right_rgb[i] * weight) for i in range(3))
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    return "#fde725"


def _relative_path(path: Path, base: Path) -> Path:
    try:
        return path.resolve().relative_to(base.resolve())
    except ValueError:
        return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg", type=Path, default=Path("docs/figures/h_alpha_lead_phase_boundary.svg"))
    parser.add_argument("--markdown", type=Path, default=Path("docs/eco_genetic_criticality/h_alpha_lead_phase_boundary.md"))
    parser.add_argument("--csv", type=Path, help="Optional path for CSV-friendly rows.")
    args = parser.parse_args(argv)

    rows = phase_boundary_rows(run_phase_boundary())
    render_phase_boundary_svg(rows, args.svg)
    figure_link = _relative_path(args.svg, args.markdown.parent)
    report = render_markdown(rows, figure_link)
    args.markdown.write_text(report, encoding="utf-8")
    if args.csv:
        write_csv(rows, args.csv)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
