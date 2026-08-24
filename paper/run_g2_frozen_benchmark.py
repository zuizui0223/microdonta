"""Run the preregistered G2 selection benchmark without analysis-time overrides.

The scientific configuration is read only from
``paper/g2_frozen_benchmark_protocol.json``. The CLI can choose an output
directory, but cannot alter seeds, budgets, candidate vocabulary, policies,
system counts, or ABC draws. Every output row carries the SHA-256 hash of the
exact protocol bytes.

Protocol v2 evaluates RACH-SEQ and a uniform random candidate-order baseline on
the same seed-defined system family, candidate vocabulary, hidden truths, and
observation budgets. Policy contrasts are descriptive outputs only; no sign or
magnitude is required for software acceptance.
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


def _finite_values(rows: list[dict], metric: str) -> list[float]:
    values = [float(row[metric]) for row in rows]
    if not values or any(not math.isfinite(value) for value in values):
        raise RuntimeError(f"non-finite or missing {metric} in frozen G2 output")
    return values


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_protocol(output_dir: str | Path) -> dict[str, Path]:
    protocol, protocol_hash = load_protocol()
    sweep = protocol["sweep"]
    selection = protocol["selection_validation"]
    n_distractors = int(protocol["generator"]["distractor_candidates"]["count"])
    policies = tuple(str(policy) for policy in selection["policies"])
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
            n_distractors=n_distractors,
            policies=policies,
        )
        for summary in summaries:
            per_seed_rows.append({
                "protocol_id": protocol["protocol_id"],
                "protocol_sha256": protocol_hash,
                "seed": int(seed),
                "policy": summary.policy,
                "budget": summary.budget,
                "n_systems": summary.n_systems,
                "systems_with_edges": summary.systems_with_edges,
                "frac_converged": summary.frac_converged,
                "mean_frac_resolved": summary.mean_frac_resolved,
                "mean_steps": summary.mean_steps,
                "false_exclusion_rate": summary.false_exclusion_rate,
                "mean_distractors_selected": summary.mean_distractors_selected,
            })

    per_seed_path = out / "g2_budget_by_seed_policy.csv"
    per_seed_fields = [
        "protocol_id",
        "protocol_sha256",
        "seed",
        "policy",
        "budget",
        "n_systems",
        "systems_with_edges",
        "frac_converged",
        "mean_frac_resolved",
        "mean_steps",
        "false_exclusion_rate",
        "mean_distractors_selected",
    ]
    _write_csv(per_seed_path, per_seed_fields, per_seed_rows)

    # Aggregate each policy/budget separately; preserve the baseline instead of
    # collapsing policies before the scientific comparison is visible.
    aggregate_rows: list[dict] = []
    aggregate_metrics = [
        *protocol["primary_metrics"],
        "mean_distractors_selected",
    ]
    for policy in policies:
        for budget in sweep["budgets"]:
            group = [
                row
                for row in per_seed_rows
                if row["policy"] == policy and row["budget"] == int(budget)
            ]
            if len(group) != len(sweep["seeds"]):
                raise RuntimeError(
                    f"missing seed rows for policy={policy!r}, budget={budget}"
                )
            row = {
                "protocol_id": protocol["protocol_id"],
                "protocol_sha256": protocol_hash,
                "policy": policy,
                "budget": int(budget),
                "n_seeds": len(group),
                "total_systems": sum(int(item["n_systems"]) for item in group),
            }
            for metric in aggregate_metrics:
                values = _finite_values(group, metric)
                row[f"{metric}_mean"] = statistics.mean(values)
                row[f"{metric}_sd"] = _sample_sd(values)
            aggregate_rows.append(row)

    aggregate_path = out / "g2_budget_policy_aggregate.csv"
    aggregate_fields = [
        "protocol_id",
        "protocol_sha256",
        "policy",
        "budget",
        "n_seeds",
        "total_systems",
    ]
    for metric in aggregate_metrics:
        aggregate_fields.extend([f"{metric}_mean", f"{metric}_sd"])
    _write_csv(aggregate_path, aggregate_fields, aggregate_rows)

    # Direct within-seed contrasts use exactly the same seed and budget. Positive
    # deltas are not declared successes; even an adverse contrast is retained.
    contrast_source_metrics = [
        "frac_converged",
        "mean_frac_resolved",
        "mean_steps",
        "false_exclusion_rate",
        "mean_distractors_selected",
    ]
    contrast_rows: list[dict] = []
    for seed in sweep["seeds"]:
        for budget in sweep["budgets"]:
            pair = {
                row["policy"]: row
                for row in per_seed_rows
                if row["seed"] == int(seed) and row["budget"] == int(budget)
            }
            if set(pair) != set(policies):
                raise RuntimeError(
                    f"incomplete policy pair for seed={seed}, budget={budget}: {sorted(pair)}"
                )
            rach = pair["rach_seq"]
            random_order = pair["random_order"]
            row = {
                "protocol_id": protocol["protocol_id"],
                "protocol_sha256": protocol_hash,
                "seed": int(seed),
                "budget": int(budget),
            }
            for metric in contrast_source_metrics:
                left = float(rach[metric])
                right = float(random_order[metric])
                if not (math.isfinite(left) and math.isfinite(right)):
                    raise RuntimeError(
                        f"non-finite policy contrast source: {metric}, seed={seed}, budget={budget}"
                    )
                row[f"rach_seq_minus_random_order_{metric}"] = left - right
            contrast_rows.append(row)

    contrast_path = out / "g2_policy_contrast_by_seed.csv"
    contrast_fields = ["protocol_id", "protocol_sha256", "seed", "budget"] + [
        f"rach_seq_minus_random_order_{metric}"
        for metric in contrast_source_metrics
    ]
    _write_csv(contrast_path, contrast_fields, contrast_rows)

    contrast_aggregate_rows: list[dict] = []
    contrast_metrics = [field for field in contrast_fields if field.startswith("rach_seq_minus")]
    for budget in sweep["budgets"]:
        group = [row for row in contrast_rows if row["budget"] == int(budget)]
        row = {
            "protocol_id": protocol["protocol_id"],
            "protocol_sha256": protocol_hash,
            "budget": int(budget),
            "n_seeds": len(group),
        }
        for metric in contrast_metrics:
            values = _finite_values(group, metric)
            row[f"{metric}_mean"] = statistics.mean(values)
            row[f"{metric}_sd"] = _sample_sd(values)
        contrast_aggregate_rows.append(row)

    contrast_aggregate_path = out / "g2_policy_contrast_aggregate.csv"
    contrast_aggregate_fields = [
        "protocol_id",
        "protocol_sha256",
        "budget",
        "n_seeds",
    ]
    for metric in contrast_metrics:
        contrast_aggregate_fields.extend([f"{metric}_mean", f"{metric}_sd"])
    _write_csv(
        contrast_aggregate_path,
        contrast_aggregate_fields,
        contrast_aggregate_rows,
    )

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
        "per_seed_policy": per_seed_path,
        "policy_aggregate": aggregate_path,
        "contrast_by_seed": contrast_path,
        "contrast_aggregate": contrast_aggregate_path,
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
