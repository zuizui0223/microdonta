"""Publication-facing calibration checks for observation information value.

The numerical experiment is inherited unchanged from the frozen validation
backend. This module provides descriptive reporting and figure labels for the
active method vocabulary.
"""
from __future__ import annotations

import argparse
import math
import os
import statistics

from .information_value_calibration_core import CalibrationResult, run_calibration


def print_report(res: CalibrationResult) -> None:
    print("=" * 68)
    print(f"Observation information-value calibration   R0={res.R0}  n={res.n_accepted}")
    print("=" * 68)
    print("(1) Stored-region filter versus fresh re-inference")
    for label, cheap, reinf in res.exactness:
        flag = "OK" if abs(cheap - reinf) < 1e-6 else f"difference={cheap-reinf:+.4f}"
        print(f"    {label:24s} filter={cheap:+.4f}  reinference={reinf:+.4f}  {flag}")
    print("(2) Predicted information value versus mean realised gain")
    by_obs: dict[str, list[float]] = {}
    predicted: dict[str, float] = {}
    for obs, value, _truth, realised in res.calibration:
        by_obs.setdefault(obs, []).append(realised)
        predicted[obs] = value
    for obs, realised in by_obs.items():
        print(
            f"    {obs:24s} predicted={predicted[obs]:+.4f}  "
            f"mean_realised={statistics.mean(realised):+.4f}"
        )


def make_figure(res: CalibrationResult, path: str) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib unavailable — skipping figure.")
        return None

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))

    ax = axes[0]
    if res.exactness:
        filtered = [c for _, c, _ in res.exactness]
        reinferred = [r for _, _, r in res.exactness]
        lim = max(max(filtered + reinferred), 0.01) * 1.1
        ax.plot([0, lim], [0, lim], "k--", lw=1, label="1:1")
        ax.scatter(filtered, reinferred, s=40, zorder=3)
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
    ax.set_xlabel("resolvability gain from filtering current region")
    ax.set_ylabel("resolvability gain from fresh re-inference")
    ax.set_title("(1) Stored-region conditioning is exact\nin the deterministic validation model")
    ax.legend(fontsize=8)

    ax = axes[1]
    by_obs: dict[str, list[float]] = {}
    predicted: dict[str, float] = {}
    for obs, value, _truth, realised in res.calibration:
        by_obs.setdefault(obs, []).append(realised)
        predicted[obs] = value
    xs, ys = [], []
    for obs, realised in by_obs.items():
        value = predicted[obs]
        ax.scatter([value] * len(realised), realised, s=18, zorder=2)
        mean_realised = statistics.mean(realised)
        ax.scatter([value], [mean_realised], s=45, zorder=3)
        xs.append(value)
        ys.append(mean_realised)
    if xs:
        lim = max(max(xs + ys), 0.01) * 1.15
        ax.plot([0, lim], [0, lim], "k--", lw=1, label="1:1")
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        if len(xs) > 2:
            mx, my = statistics.mean(xs), statistics.mean(ys)
            cov = sum((a-mx)*(b-my) for a, b in zip(xs, ys))
            sx = math.sqrt(sum((a-mx)**2 for a in xs))
            sy = math.sqrt(sum((b-my)**2 for b in ys))
            if sx > 0 and sy > 0:
                ax.set_title(
                    "(2) Observation information-value calibration\n"
                    f"mean realised vs predicted (r={cov/(sx*sy):.2f})"
                )
    ax.set_xlabel("predicted observation information value")
    ax.set_ylabel("realised resolvability gain")
    if not ax.get_title():
        ax.set_title("(2) Observation information-value calibration")
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Observation information-value calibration")
    parser.add_argument("--preset", default="literature_grounded")
    parser.add_argument("--rule", default="strict_all")
    parser.add_argument("--n-attempts", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--figure", default="")
    args = parser.parse_args(argv)
    result = run_calibration(
        preset_name=args.preset,
        acceptance_rule=args.rule,
        n_attempts=args.n_attempts,
        seed=args.seed,
    )
    print_report(result)
    if args.figure:
        out = make_figure(result, args.figure)
        if out:
            print(f"Figure written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
