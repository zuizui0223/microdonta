"""Parameter filtering runner for Campanula Izu causal scenarios.

Samples latent benefit/cost parameters from ecology-principled trade-off presets,
checks ecological parameter constraints, runs M1-M5 causal scenarios, and retains
only parameter sets that reproduce observed pattern targets simultaneously.

This implements the research-mode workflow described in Issue #5:

    We did not manually tune parameters to match the observed pattern. Instead,
    we pre-defined biologically plausible trade-off ranges and ecological
    constraints, sampled latent parameters under those constraints, and retained
    only parameter sets that reproduced multiple observed patterns simultaneously.

Usage:
    python examples/campanula_izu/run_parameter_filtering.py

Outputs are written to examples/campanula_izu/outputs/.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from causal_model.parameter_constraints import (
    predefined_tradeoff_presets,
    sample_all_sets_with_rejection_log,
)
from causal_model.parameter_sampling import param_set_to_model_parameters
from causal_model.range_summary import summarize_parameter_ranges
from examples.campanula_izu.causal_structures import campanula_causal_structures
from examples.campanula_izu.proxy_simulation import simulate_campanula_causal_structure


N_ATTEMPTS_PER_PRESET = 400
PRESETS_TO_RUN = [
    "broad_prior",
    "reproductive_assurance",
    "outcrossing_benefit",
    "high_guide_cost",
    "drift_dominated",
]

OBSERVED_RELATIONS: dict[str, str] = {
    "nectar_guide": "Oshima > Hachijo",
    "selfing_rate": "Oshima < Hachijo",
    "herkogamy": "Oshima > Hachijo",
    "flower_size": "Oshima > Hachijo",
    "Fis": "Oshima < Hachijo",
    "Bombus_frequency": "Oshima > Hachijo",
}

LATENT_PARAMS = [
    "guide_cost",
    "outcrossing_benefit",
    "selfing_benefit",
    "inbreeding_depression",
    "small_pollinator_efficiency",
    "drift_strength",
    "direct_pollinator_guide_benefit",
    "cost_of_waiting_for_pollinators",
]


def score_relations(relations: dict[str, str], observed: dict[str, str]) -> tuple[int, int]:
    """Return (matches, total) for ordinal relation scoring."""

    total = len(observed)
    matches = sum(1 for variable, target in observed.items() if relations.get(variable) == target)
    return matches, total


def write_csv(path: Path, rows: list[dict]) -> None:
    """Write rows to CSV, creating an empty file if rows are empty."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def print_table(rows: list[dict], columns: list[str]) -> None:
    if not rows:
        print("(no rows)")
        return
    widths = {col: max(len(col), *(len(_fmt(row.get(col, ""))) for row in rows)) for col in columns}
    print("  ".join(col.ljust(widths[col]) for col in columns))
    print("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  ".join(_fmt(row.get(col, "")).ljust(widths[col]) for col in columns))


def main() -> None:
    presets = predefined_tradeoff_presets()
    structures = campanula_causal_structures()

    all_runs: list[dict] = []
    accepted_runs: list[dict] = []
    rejected_sets: list[dict] = []

    print("=" * 70)
    print("Parameter filtering - Campanula Izu causal scenarios")
    print("Research mode: constrained random sampling, no manual tuning")
    print("=" * 70)

    for preset_name in PRESETS_TO_RUN:
        preset = presets[preset_name]
        print(f"\n[Preset: {preset_name}] {preset.description[:70]}...")

        accepted_params, rejected_params = sample_all_sets_with_rejection_log(
            preset, N_ATTEMPTS_PER_PRESET, seed=42
        )
        rejected_sets.extend(rejected_params)
        print(
            f"  Sampled {N_ATTEMPTS_PER_PRESET} sets -> "
            f"accepted {len(accepted_params)} ({len(accepted_params)/N_ATTEMPTS_PER_PRESET:.1%}), "
            f"rejected {len(rejected_params)}"
        )

        for param_set in accepted_params:
            model_params = param_set_to_model_parameters(param_set)
            for structure in structures:
                try:
                    relations, _outputs = simulate_campanula_causal_structure(
                        structure, params=model_params
                    )
                except Exception as exc:
                    print(f"  Warning: simulation failed for {structure.name}: {exc}")
                    continue

                matches, total = score_relations(relations, OBSERVED_RELATIONS)
                all_matched = matches == total
                row = {
                    "parameter_set_id": param_set.get("parameter_set_id"),
                    "preset_name": preset_name,
                    "structure": structure.name,
                    "pattern_matches": matches,
                    "pattern_total": total,
                    "all_patterns_matched": all_matched,
                    **{name: param_set.get(name) for name in LATENT_PARAMS},
                    "guide_tradeoff_class": param_set.get("guide_tradeoff_class", ""),
                    "selfing_tradeoff_class": param_set.get("selfing_tradeoff_class", ""),
                    "guide_net_benefit": param_set.get("guide_net_benefit", ""),
                    "selfing_net_benefit": param_set.get("selfing_net_benefit", ""),
                    **{key: value for key, value in relations.items()},
                }
                all_runs.append(row)
                if all_matched:
                    accepted_runs.append(row)

    accepted_ranges = summarize_parameter_ranges(accepted_runs, LATENT_PARAMS)

    scenario_summary: list[dict] = []
    for structure in structures:
        rows = [row for row in all_runs if row["structure"] == structure.name]
        if not rows:
            continue
        accepted_count = sum(1 for row in rows if row["all_patterns_matched"])
        scenario_summary.append(
            {
                "structure": structure.name,
                "total_runs": len(rows),
                "accepted_runs": accepted_count,
                "acceptance_rate": round(accepted_count / len(rows), 4),
                "mean_matches": round(
                    sum(float(row["pattern_matches"]) for row in rows) / len(rows), 4
                ),
            }
        )
    scenario_summary.sort(key=lambda row: -row["acceptance_rate"])

    out_dir = Path(__file__).parent / "outputs"
    out_dir.mkdir(exist_ok=True)
    write_csv(out_dir / "parameter_filtering_all_runs.csv", all_runs)
    write_csv(out_dir / "parameter_filtering_accepted_runs.csv", accepted_runs)
    write_csv(out_dir / "parameter_filtering_accepted_ranges.csv", accepted_ranges)
    write_csv(out_dir / "parameter_filtering_scenario_summary.csv", scenario_summary)
    write_csv(out_dir / "parameter_sampling_rejected_sets.csv", rejected_sets)

    print("\n" + "=" * 70)
    print("Causal structure acceptance rates across presets and parameter sets")
    print("=" * 70)
    print_table(scenario_summary, ["structure", "total_runs", "accepted_runs", "acceptance_rate", "mean_matches"])

    print(f"\nAccepted runs (all patterns matched): {len(accepted_runs)}")
    print(f"Total runs: {len(all_runs)}")
    if all_runs:
        print(f"Overall acceptance rate: {len(accepted_runs)/len(all_runs):.1%}")

    if accepted_ranges:
        print("\nAccepted parameter ranges:")
        print_table(accepted_ranges, ["Parameter", "n_accepted", "Min", "q025", "Median", "q975", "Max"])
    else:
        print("\nNo accepted parameter ranges: no run matched all observed relations.")

    print(f"\nOutputs written to {out_dir}/")


if __name__ == "__main__":
    main()
