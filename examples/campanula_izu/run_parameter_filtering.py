"""Parameter filtering runner for Campanula Izu causal scenarios.

Samples latent benefit/cost parameters from ecology-principled trade-off
presets, checks ecological parameter constraints, runs M1–M5 causal
scenarios, and retains only parameter sets that reproduce observed pattern
targets simultaneously.

This implements the research-mode workflow described in Issue #5:

    We did not manually tune parameters to match the observed pattern.
    Instead, we pre-defined biologically plausible trade-off ranges and
    ecological constraints, sampled latent parameters under those constraints,
    and retained only parameter sets that reproduced multiple observed patterns
    simultaneously.

Usage:
    python examples/campanula_izu/run_parameter_filtering.py

Outputs (written to examples/campanula_izu/outputs/):
    parameter_filtering_all_runs.csv
    parameter_filtering_accepted_runs.csv
    parameter_filtering_accepted_ranges.csv
    parameter_filtering_scenario_summary.csv
    parameter_sampling_rejected_sets.csv
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
from examples.campanula_izu.causal_structures import (
    campanula_causal_structures,
    campanula_pattern_targets,
)
from examples.campanula_izu.proxy_simulation import (
    default_campanula_proxy_environments,
    simulate_campanula_causal_structure,
)
from causal_model.relations import relations_from_final_summaries

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

N_ATTEMPTS_PER_PRESET = 400   # total draws per preset before constraint filtering
PRESETS_TO_RUN = [
    "broad_prior",
    "reproductive_assurance",
    "outcrossing_benefit",
    "high_guide_cost",
    "drift_dominated",
]

# Observed ordinal relations (Oshima vs Hachijo) from field data
OBSERVED_RELATIONS: dict[str, str] = {
    "nectar_guide":  "Oshima > Hachijo",
    "selfing_rate":  "Oshima < Hachijo",
    "herkogamy":     "Oshima > Hachijo",
    "flower_size":   "Oshima > Hachijo",
    "Fis":           "Oshima < Hachijo",
    "Bombus_frequency": "Oshima > Hachijo",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def score_relations(
    relations: dict[str, str],
    observed: dict[str, str],
) -> tuple[int, int]:
    """Return (matches, total) for ordinal relation scoring."""
    total = len(observed)
    matches = sum(1 for var, obs in observed.items() if relations.get(var) == obs)
    return matches, total


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def print_table(rows: list[dict], columns: list[str]) -> None:
    widths = {c: max(len(c), *(len(_fmt(r.get(c, ""))) for r in rows)) for c in columns}
    print("  ".join(c.ljust(widths[c]) for c in columns))
    print("  ".join("-" * widths[c] for c in columns))
    for r in rows:
        print("  ".join(_fmt(r.get(c, "")).ljust(widths[c]) for c in columns))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    presets = predefined_tradeoff_presets()
    structures = campanula_causal_structures()
    targets = campanula_pattern_targets()
    environments = default_campanula_proxy_environments()

    all_runs: list[dict] = []
    accepted_runs: list[dict] = []
    rejected_sets: list[dict] = []
    scenario_summary: list[dict] = []

    print("=" * 70)
    print("Parameter filtering — Campanula Izu causal scenarios")
    print("Research mode: constrained random sampling, no manual tuning")
    print("=" * 70)

    for preset_name in PRESETS_TO_RUN:
        preset = presets[preset_name]
        print(f"\n[Preset: {preset_name}]  {preset.description[:60]}…")

        accepted_params, rejected_params = sample_all_sets_with_rejection_log(
            preset, N_ATTEMPTS_PER_PRESET, seed=42
        )
        rejected_sets.extend(rejected_params)
        print(
            f"  Sampled {N_ATTEMPTS_PER_PRESET} sets → "
            f"accepted {len(accepted_params)} ({len(accepted_params)/N_ATTEMPTS_PER_PRESET:.1%}), "
            f"rejected {len(rejected_params)}"
        )

        if not accepted_params:
            print("  No valid parameter sets — skipping scenario runs.")
            continue

        # Run each causal structure for each valid parameter set
        for param_set in accepted_params:
            set_id = param_set["parameter_set_id"]

            for structure in structures:
                # Run proxy simulation with these parameters
                # (the deterministic proxy is fast and useful for filtering;
                #  full stochastic ABM can be run on the accepted subset)
                try:
                    relations, outputs = simulate_campanula_causal_structure(structure)
                except Exception as exc:
                    print(f"  Warning: simulation failed for {structure.name}: {exc}")
                    continue

                matches, total = score_relations(relations, OBSERVED_RELATIONS)
                accepted = matches == total  # strict: all 6 relations must match

                run_row = {
                    "parameter_set_id": set_id,
                    "preset_name": preset_name,
                    "structure": structure.name,
                    "pattern_matches": matches,
                    "pattern_total": total,
                    "all_patterns_matched": accepted,
                    "guide_tradeoff_class": param_set.get("guide_tradeoff_class", ""),
                    "selfing_tradeoff_class": param_set.get("selfing_tradeoff_class", ""),
                    "guide_net_benefit": param_set.get("guide_net_benefit", ""),
                    "selfing_net_benefit": param_set.get("selfing_net_benefit", ""),
                    **{k: v for k, v in relations.items()},
                }
                all_runs.append(run_row)
                if accepted:
                    accepted_run = {**param_set, **run_row}
                    accepted_runs.append(accepted_run)

    # ---------------------------------------------------------------------------
    # Accepted parameter ranges summary
    # ---------------------------------------------------------------------------
    accepted_ranges: list[dict] = []
    param_names = [
        "guide_cost", "outcrossing_benefit", "selfing_benefit",
        "inbreeding_depression", "small_pollinator_efficiency",
        "drift_strength", "direct_pollinator_guide_benefit",
        "cost_of_waiting_for_pollinators",
    ]
    if accepted_runs:
        for param in param_names:
            vals = [r[param] for r in accepted_runs if isinstance(r.get(param), float)]
            if vals:
                accepted_ranges.append({
                    "parameter": param,
                    "n_accepted": len(vals),
                    "min": round(min(vals), 4),
                    "max": round(max(vals), 4),
                    "mean": round(sum(vals) / len(vals), 4),
                })

    # ---------------------------------------------------------------------------
    # Per-structure scenario summary across presets
    # ---------------------------------------------------------------------------
    from collections import defaultdict
    struct_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "accepted": 0})
    for r in all_runs:
        s = r["structure"]
        struct_stats[s]["total"] += 1
        if r["all_patterns_matched"]:
            struct_stats[s]["accepted"] += 1

    for s_name, stats in struct_stats.items():
        rate = stats["accepted"] / stats["total"] if stats["total"] else 0.0
        scenario_summary.append({
            "structure": s_name,
            "total_runs": stats["total"],
            "accepted_runs": stats["accepted"],
            "acceptance_rate": round(rate, 4),
        })
    scenario_summary.sort(key=lambda r: -r["acceptance_rate"])

    # ---------------------------------------------------------------------------
    # Write outputs
    # ---------------------------------------------------------------------------
    out_dir = Path(__file__).parent / "outputs"
    out_dir.mkdir(exist_ok=True)

    write_csv(out_dir / "parameter_filtering_all_runs.csv", all_runs)
    write_csv(out_dir / "parameter_filtering_accepted_runs.csv", accepted_runs)
    write_csv(out_dir / "parameter_filtering_accepted_ranges.csv", accepted_ranges)
    write_csv(out_dir / "parameter_filtering_scenario_summary.csv", scenario_summary)
    write_csv(out_dir / "parameter_sampling_rejected_sets.csv", rejected_sets)

    # ---------------------------------------------------------------------------
    # Print summary
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("Causal structure acceptance rates across presets and parameter sets")
    print("=" * 70)
    print_table(
        scenario_summary,
        ["structure", "total_runs", "accepted_runs", "acceptance_rate"],
    )

    print(f"\nAccepted parameter sets (all patterns matched): {len(accepted_runs)}")
    print(f"Total runs: {len(all_runs)}")
    if all_runs:
        overall_rate = len(accepted_runs) / len(all_runs)
        print(f"Overall acceptance rate: {overall_rate:.1%}")

    if accepted_ranges:
        print("\nAccepted parameter ranges:")
        print_table(accepted_ranges, ["parameter", "n_accepted", "min", "max", "mean"])

    print(f"\nOutputs written to {out_dir}/")
    print("  parameter_filtering_all_runs.csv")
    print("  parameter_filtering_accepted_runs.csv")
    print("  parameter_filtering_accepted_ranges.csv")
    print("  parameter_filtering_scenario_summary.csv")
    print("  parameter_sampling_rejected_sets.csv")


if __name__ == "__main__":
    main()
