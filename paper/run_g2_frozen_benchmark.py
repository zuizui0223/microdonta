"""Run the preregistered G2 selection benchmark without analysis-time overrides.

The scientific configuration is read only from
``paper/g2_frozen_benchmark_protocol.json``. The CLI can choose an output
directory, but cannot alter seeds, budgets, candidate vocabulary, policies,
system counts, or prior/ABC draws.

Every output row carries two provenance keys:

- SHA-256 of the exact frozen protocol bytes;
- the exact clean Git commit SHA whose code produced the result.

Protocol v2 evaluates RACH-SEQ and a uniform random candidate-order baseline on
the same seed-defined system family, candidate vocabulary, hidden truths and
observation budgets. Policy contrasts are descriptive outputs only; no sign or
magnitude is required for software acceptance.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
from pathlib import Path

from causal_model.generality_sweep import run_generality_sweep

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "paper" / "g2_frozen_benchmark_protocol.json"


def load_protocol() -> tuple[dict, str]:
    raw = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(raw.decode("utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    if protocol.get("status") != "frozen_before_final_run":
        raise RuntimeError("G2 protocol is not in frozen_before_final_run state")
    return protocol, digest


def _code_revision() -> str:
    """Return the exact clean repository commit used for the frozen run."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("cannot determine Git revision for frozen G2 run") from exc
    if dirty:
        raise RuntimeError(
            "frozen G2 run requires a clean Git worktree; commit all code/protocol changes first"
        )
    env_sha = os.environ.get("GITHUB_SHA")
    if env_sha and env_sha != sha:
        raise RuntimeError(
            f"GITHUB_SHA ({env_sha}) does not match checked-out HEAD ({sha})"
        )
    if len(sha) != 40:
        raise RuntimeError(f"unexpected Git commit SHA: {sha!r}")
    return sha


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


def _system_signature(record) -> tuple:
    """Pre-outcome system identity used to verify matched policy evaluation."""
    return (
        record.K,
        record.n_confounds,
        record.n_initial_edges,
        record.driver_coeff_a,
        record.driver_coeff_b,
        record.n_distractors,
    )


def run_protocol(output_dir: str | Path) -> dict[str, Path]:
    protocol, protocol_hash = load_protocol()
    code_sha = _code_revision()
    sweep = protocol["sweep"]
    selection = protocol["selection_validation"]
    n_distractors = int(protocol["generator"]["distractor_candidates"]["count"])
    policies = tuple(str(policy) for policy in selection["policies"])
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    per_seed_rows: list[dict] = []
    system_rows: list[dict] = []

    # Exact record signatures are retained per seed and checked across every
    # policy/budget cell before any aggregate is accepted.
    reference_signatures: dict[int, list[tuple]] = {}

    for seed in sweep["seeds"]:
        for policy in policies:
            for budget in sweep["budgets"]:
                result = run_generality_sweep(
                    n_systems=int(sweep["n_systems_per_seed"]),
                    seed=int(seed),
                    n_attempts=int(sweep["n_attempts"]),
                    K_choices=tuple(int(x) for x in sweep["K_choices"]),
                    confound_choices=tuple(int(x) for x in sweep["confound_choices"]),
                    budget=int(budget),
                    min_sub_size=int(sweep["min_sub_size"]),
                    n_distractors=n_distractors,
                    policy=policy,  # type: ignore[arg-type]
                )

                signatures = [_system_signature(record) for record in result.records]
                if int(seed) not in reference_signatures:
                    reference_signatures[int(seed)] = signatures
                elif signatures != reference_signatures[int(seed)]:
                    raise RuntimeError(
                        "policy/budget cells did not evaluate identical generated systems "
                        f"for seed={seed}, policy={policy}, budget={budget}"
                    )

                per_seed_rows.append({
                    "protocol_id": protocol["protocol_id"],
                    "protocol_sha256": protocol_hash,
                    "code_commit_sha": code_sha,
                    "seed": int(seed),
                    "policy": policy,
                    "budget": int(budget),
                    "n_systems": len(result.records),
                    "systems_with_edges": result.systems_with_edges,
                    "frac_converged": result.frac_converged,
                    "mean_frac_resolved": result.mean_frac_resolved,
                    "mean_steps": result.mean_steps,
                    "false_exclusion_rate": result.false_exclusion_rate,
                    "mean_distractors_selected": result.mean_distractors_selected,
                })

                for record_index, record in enumerate(result.records):
                    system_rows.append({
                        "protocol_id": protocol["protocol_id"],
                        "protocol_sha256": protocol_hash,
                        "code_commit_sha": code_sha,
                        "seed": int(seed),
                        "policy": policy,
                        "budget": int(budget),
                        "record_index": record_index,
                        "K": record.K,
                        "n_confounds": record.n_confounds,
                        "n_initial_edges": record.n_initial_edges,
                        "n_resolved": record.n_resolved,
                        "n_unresolved": record.n_unresolved,
                        "converged": record.converged,
                        "steps_taken": record.steps_taken,
                        "R0": record.R0,
                        "R_final": record.R_final,
                        "truth_retained": record.truth_retained,
                        "truth_peek_free": record.truth_peek_free,
                        "driver_coeff_a": record.driver_coeff_a,
                        "driver_coeff_b": record.driver_coeff_b,
                        "n_distractors": record.n_distractors,
                        "distractors_selected": record.distractors_selected,
                    })

    system_path = out / "g2_system_records.csv"
    system_fields = [
        "protocol_id",
        "protocol_sha256",
        "code_commit_sha",
        "seed",
        "policy",
        "budget",
        "record_index",
        "K",
        "n_confounds",
        "n_initial_edges",
        "n_resolved",
        "n_unresolved",
        "converged",
        "steps_taken",
        "R0",
        "R_final",
        "truth_retained",
        "truth_peek_free",
        "driver_coeff_a",
        "driver_coeff_b",
        "n_distractors",
        "distractors_selected",
    ]
    _write_csv(system_path, system_fields, system_rows)

    per_seed_path = out / "g2_budget_by_seed_policy.csv"
    per_seed_fields = [
        "protocol_id",
        "protocol_sha256",
        "code_commit_sha",
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
                "code_commit_sha": code_sha,
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
        "code_commit_sha",
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
                "code_commit_sha": code_sha,
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
    contrast_fields = [
        "protocol_id",
        "protocol_sha256",
        "code_commit_sha",
        "seed",
        "budget",
    ] + [
        f"rach_seq_minus_random_order_{metric}"
        for metric in contrast_source_metrics
    ]
    _write_csv(contrast_path, contrast_fields, contrast_rows)

    contrast_aggregate_rows: list[dict] = []
    contrast_metrics = [
        field for field in contrast_fields if field.startswith("rach_seq_minus")
    ]
    for budget in sweep["budgets"]:
        group = [row for row in contrast_rows if row["budget"] == int(budget)]
        row = {
            "protocol_id": protocol["protocol_id"],
            "protocol_sha256": protocol_hash,
            "code_commit_sha": code_sha,
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
        "code_commit_sha",
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
            {
                "protocol_sha256": protocol_hash,
                "code_commit_sha": code_sha,
                "protocol": protocol,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    return {
        "system_records": system_path,
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
