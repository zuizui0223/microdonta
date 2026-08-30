"""Build manuscript Figure 2 from the frozen G2 v2 summary.

This script is deliberately downstream of the frozen benchmark. It never reruns
systems and accepts no scientific benchmark parameters; it only visualizes the
protocol/code-tagged result bundle committed at
``paper/results/g2_frozen_v2_summary.json``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT = ROOT / "paper" / "results" / "g2_frozen_v2_summary.json"


def load_rows(path: Path) -> tuple[dict, dict[tuple[str, int], dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("protocol_id") != "rach-g2-truth-peek-free-v2":
        raise RuntimeError("Figure 2 requires the frozen G2 v2 result bundle")
    rows = {
        (str(row["policy"]), int(row["budget"])): row
        for row in payload["policy_budget_aggregate"]
    }
    for policy in ("rach_seq", "random_order"):
        for budget in range(5):
            if (policy, budget) not in rows:
                raise RuntimeError(f"missing frozen row: {policy}, budget={budget}")
    return payload, rows


def nuisance_contrast(
    rows: dict[tuple[str, int], dict], *, budget: int = 4
) -> tuple[float, float, float, float]:
    """Return frozen absolute values, random/RACH ratio and relative reduction."""
    rach = float(rows[("rach_seq", budget)]["mean_distractors_selected_mean"])
    random = float(rows[("random_order", budget)]["mean_distractors_selected_mean"])
    if rach <= 0 or random <= 0:
        raise RuntimeError("nuisance-selection fold contrast requires positive means")
    ratio = random / rach
    reduction = 1.0 - rach / random
    return rach, random, ratio, reduction


def make_figure(result_path: Path, output_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    payload, rows = load_rows(result_path)
    budgets = list(range(5))
    policies = [
        ("rach_seq", "RACH-SEQ"),
        ("random_order", "random order"),
    ]

    metrics = [
        ("frac_converged", "Converged systems", "fraction"),
        ("mean_frac_resolved", "Initial confounding edges resolved", "fraction"),
        ("mean_steps", "Observations used", "count"),
        (
            "mean_distractors_selected",
            "Mechanism-independent nuisance measurements",
            "count",
        ),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(9.0, 7.0), sharex=True)
    axes = axes.ravel()

    for ax, (metric, title, kind) in zip(axes, metrics):
        for policy, label in policies:
            means = [float(rows[(policy, b)][f"{metric}_mean"]) for b in budgets]
            sds = [float(rows[(policy, b)][f"{metric}_sd"]) for b in budgets]
            ax.errorbar(budgets, means, yerr=sds, marker="o", capsize=3, label=label)
        ax.set_title(title)
        ax.set_xlabel("Observation budget")
        ax.set_xticks(budgets)
        if kind == "fraction":
            ax.set_ylim(-0.03, 1.05)
        else:
            ax.set_ylim(bottom=-0.05)
        ax.grid(alpha=0.2)

    axes[0].set_ylabel("Fraction")
    axes[1].set_ylabel("Fraction")
    axes[2].set_ylabel("Mean count")
    axes[3].set_ylabel("Mean count")
    axes[0].legend(frameon=False)

    rach4, random4, ratio4, reduction4 = nuisance_contrast(rows, budget=4)
    axes[3].text(
        0.03,
        0.96,
        "Budget 4\n"
        f"random / RACH-SEQ = {random4:.3f} / {rach4:.3f}\n"
        f"= {ratio4:.1f}×  ({100.0 * reduction4:.1f}% reduction)",
        transform=axes[3].transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.85},
    )

    protocol_short = payload["protocol_sha256"][:12]
    code_short = payload["code_commit_sha"][:12]
    fig.suptitle(
        "RACH-SEQ selects resolving measurements under a limited budget\n"
        "Frozen G2 v2: 5 seeds × 200 systems; error bars = sample SD across seeds",
        y=0.99,
    )
    fig.text(
        0.5,
        0.012,
        "Hidden-truth false exclusion = 0 in every policy × budget cell. "
        f"Protocol {protocol_short}…; code {code_short}…",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build frozen G2 manuscript Figure 2")
    parser.add_argument("--result", default=str(DEFAULT_RESULT))
    parser.add_argument("--output", default="outputs/mee/figure2_g2_frozen_v2.png")
    args = parser.parse_args(argv)
    output = make_figure(Path(args.result), Path(args.output))
    print(f"figure written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
