"""Run the preregistered G2 RACH-SEQ benchmark without analysis-time overrides.

The scientific configuration is read only from ``paper/g2_frozen_benchmark_protocol.json``.
The CLI can choose an output directory, but cannot alter seeds, budgets, generator
settings, system counts, or ABC draws. Every output row carries the SHA-256 hash
of the exact protocol bytes so manuscript numbers can be traced to one frozen
configuration.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

from causal_model.generality_sweep import run_budget_sweep

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "paper" / "g2_frozen_benchmark_protocol.json"


def load_protocol() -> tuple[dict, str]:
    raw = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(raw.decode("utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    if protocol.get("status") != "frozen_before_final_run":
        raise RuntimeError("G2 protocol is not in frozen_before_final_run state")
    return protocol, digest


def _sample_sd(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def run_protocol(output_dir: str | Path) -> dict[str, Path]:
    protocol, protocol_hash = load_protocol()
    sweep = protocol["sweep"]
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    per_seed_rows: list[dict] = []
    for seed in sweep["seeds"]:
        summaries = run_budget_sweep(
            budgets=tuple(int(x) for x in sweep["budgets"]),
            n_systems=int(sweep["n_systems_per_seed"]),
            seed=int(seed),
            n_attempts=int(sweep["n_attempts"]),
            K_choices=tuple(int(x) for x in sweep["K_choices"]),
            confound_choices=tuple(int(x) for x in sweep["confound_choices"]),
            min_sub_size=int(sweep["min_sub_size"]),
        )
        for summary in summaries:
            per_seed_rows.append({
                "protocol_id": protocol["protocol_id"],
                "protocol_sha256": protocol_hash,
                "seed": int(seed),
                "budget": summary.budget,
                "n_systems": summary.n_systems,
                "systems_with_edges": summary.systems_with_edges,
                "frac_converged": summary.frac_converged,
                "mean_frac_resolved": summary.mean_frac_resolved,
                "mean_steps": summary.mean_steps,
                "false_exclusion_rate": summary.false_exclusion_rate,
            })

    per_seed_path = out / "g2_budget_by_seed.csv"
    fields = [
        "protocol_id", "protocol_sha256", "seed", "budget", "n_systems",
        "systems_with_edges", "frac_converged", "mean_frac_resolved",
        "mean_steps", "false_exclusion_rate",
    ]
    with per_seed_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(per_seed_rows)

    aggregate_rows: list[dict] = []
    for budget in sweep["budgets"]:
        group = [row for row in per_seed_rows if row["budget"] == int(budget)]
        row = {
            "protocol_id": protocol["protocol_id"],
            "protocol_sha256": protocol_hash,
            "budget": int(budget),
            "n_seeds": len(group),
            "total_systems": sum(int(item["n_systems"]) for item in group),
        }
        for metric in protocol["primary_metrics"]:
            values = [float(item[metric]) for item in group]
            if any(not math.isfinite(value) for value in values):
                raise RuntimeError(f"non-finite {metric} in frozen G2 output")
            row[f"{metric}_mean"] = statistics.mean(values)
            row[f"{metric}_sd"] = _sample_sd(values)
        aggregate_rows.append(row)

    aggregate_path = out / "g2_budget_aggregate.csv"
    aggregate_fields = [
        "protocol_id", "protocol_sha256", "budget", "n_seeds", "total_systems",
    ]
    for metric in protocol["primary_metrics"]:
        aggregate_fields.extend([f"{metric}_mean", f"{metric}_sd"])
    with aggregate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=aggregate_fields)
        writer.writeheader()
        writer.writerows(aggregate_rows)

    snapshot_path = out / "g2_protocol_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {"protocol_sha256": protocol_hash, "protocol": protocol},
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    return {
        "per_seed": per_seed_path,
        "aggregate": aggregate_path,
        "protocol_snapshot": snapshot_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the frozen RACH G2 benchmark.")
    parser.add_argument(
        "--output-dir",
        default="outputs/g2_frozen",
        help="Output directory only; scientific benchmark parameters are frozen in JSON.",
    )
    args = parser.parse_args(argv)
    written = run_protocol(args.output_dir)
    for name, path in written.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
