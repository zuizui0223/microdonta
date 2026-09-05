"""Specified-simulator recovery benchmark for mechanism-resolution inference.

The benchmark generates synthetic observations under a declared switch state and
asks whether the same specified inference family recovers that state. It is a
self-consistency / simulator-robustness benchmark, not evidence that any switch
state is the true ecological mechanism in nature.

Historical CSV field names are preserved by the private implementation because
they are part of the frozen G2 validation schema. Publication-facing CLI and
figure labels use the current method vocabulary.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

from . import _compat_known_truth_benchmark as _impl

TRUE_SWITCH_STATES = _impl.TRUE_SWITCH_STATES
SwitchRecovery = _impl.SwitchRecovery
BenchmarkCase = _impl.BenchmarkCase
BenchmarkResult = _impl.BenchmarkResult

generate_synthetic_patterns = _impl.generate_synthetic_patterns
compute_case_metrics = _impl.compute_case_metrics
run_benchmark = _impl.run_benchmark
save_outputs = _impl.save_outputs


def __getattr__(name: str):
    """Delegate historical support symbols to the private benchmark backend."""
    return getattr(_impl, name)


def make_figure(written: dict[str, Path], path: str) -> str | None:
    """Plot specified-simulator recovery with current method labels.

    Panel A shows mean accuracy and F1 versus injected pattern-noise rate. Panel B
    (when a draw-count sweep is present) shows recovery and mechanism
    resolvability ``R`` versus ABC draws. Stored CSV keys retain their frozen
    historical names and are translated only at presentation time.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib unavailable — skipping figure.")
        return None
    import os

    def _read(name: str) -> list[dict[str, str]]:
        p = written.get(name)
        if p is None or not Path(p).exists():
            return []
        with open(p, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _f(rows, key):
        out = []
        for row in rows:
            try:
                out.append(float(row[key]))
            except (KeyError, ValueError):
                out.append(float("nan"))
        return out

    noise = _read("recovery_by_noise.csv")
    sweep = _read("recovery_by_n_attempts.csv")
    has_sweep = len(sweep) > 1

    n_panels = 2 if has_sweep else 1
    fig, axes = plt.subplots(
        1,
        n_panels,
        figsize=(4.6 * n_panels, 3.8),
        squeeze=False,
    )

    ax = axes[0][0]
    xs = _f(noise, "noise_rate")
    ax.plot(xs, _f(noise, "mean_accuracy"), "o-", label="accuracy", color="#2c7fb8")
    ax.plot(xs, _f(noise, "mean_f1"), "s--", label="F1", color="#d95f0e")
    ax.set_xlabel("pattern-noise rate")
    ax.set_ylabel("switch recovery")
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=8)
    ax.set_title("(A) Recovery vs noise\n(specified-simulator self-consistency)")

    if has_sweep:
        ax = axes[0][1]
        xs = _f(sweep, "n_attempts")
        ax.plot(xs, _f(sweep, "mean_accuracy"), "o-", label="accuracy", color="#2c7fb8")
        ax.plot(xs, _f(sweep, "mean_f1"), "s--", label="F1", color="#d95f0e")
        # Frozen files retain the historical column key; display uses current R.
        ax.plot(xs, _f(sweep, "mean_R_RACH"), "^:", label="resolvability R", color="#31a354")
        ax.set_xscale("log")
        ax.set_xlabel("ABC draws (log scale)")
        ax.set_ylim(0, 1.02)
        ax.legend(fontsize=8)
        ax.set_title("(B) Convergence with draws")

    fig.tight_layout()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"figure written: {path}")
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Mechanism-Resolving Observation Design specified-simulator recovery benchmark.\n\n"
            "EPISTEMIC NOTE: this is a recovery/self-consistency benchmark, not a causal "
            "proof about real ecological mechanisms."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--n-attempts", type=int, default=200,
                   help="ABC draws per benchmark case (default: 200)")
    p.add_argument("--noise-rates", type=str, default="0.0,0.1,0.2",
                   help="Comma-separated noise probabilities (default: 0.0,0.1,0.2)")
    p.add_argument("--preset", type=str, default="literature_grounded",
                   choices=["literature_grounded", "broad_prior"],
                   help="θ-prior preset (default: literature_grounded)")
    p.add_argument("--rule", type=str, default="weighted_lax",
                   help="ABC acceptance rule (default: weighted_lax)")
    p.add_argument("--seed", type=int, default=42,
                   help="Base random seed (default: 42)")
    p.add_argument("--output-dir", type=str, default="outputs/known_truth_benchmark",
                   help="Output directory (default: outputs/known_truth_benchmark)")
    p.add_argument("--figure", type=str, default="",
                   help="If set, write a recovery figure to this path")
    p.add_argument("--n-attempts-sweep", type=str, default="",
                   help="Comma-separated draw counts for an optional convergence sweep")
    p.add_argument("--cases", type=str, default="",
                   help="Comma-separated subset of case labels (default: all)")
    p.add_argument("--generator-backend", type=str, default="proxy",
                   choices=["proxy", "abm"],
                   help="Simulator used to generate synthetic observations")
    p.add_argument("--inference-backend", type=str, default="proxy",
                   choices=["proxy", "abm"],
                   help="Simulator used by the inference step")
    p.add_argument("--abm-generations", type=int, default=30,
                   help="ABM generations per run (default: 30)")
    p.add_argument("--abm-population-size", type=int, default=120,
                   help="ABM population size per run (default: 120)")
    p.add_argument("--abm-replicates", type=int, default=2,
                   help="ABM replicates per population per draw (default: 2)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    noise_rates = [float(x) for x in args.noise_rates.split(",") if x.strip()]
    n_att_sweep = (
        [int(x) for x in args.n_attempts_sweep.split(",") if x.strip()]
        if args.n_attempts_sweep else None
    )
    true_states = TRUE_SWITCH_STATES
    if args.cases:
        wanted = {s.strip() for s in args.cases.split(",")}
        true_states = [(label, state) for label, state in TRUE_SWITCH_STATES if label in wanted]
        if not true_states:
            print(f"ERROR: no matching cases for --cases={args.cases}", file=sys.stderr)
            return 1

    print("=" * 68)
    print("Mechanism-Resolving Observation Design: specified-simulator recovery")
    print("=" * 68)
    print(
        "EPISTEMIC NOTE: this benchmark tests recovery under declared synthetic\n"
        "generators. It does NOT constitute a causal proof about real ecological\n"
        "mechanisms.\n"
    )
    backend_pair = f"{args.generator_backend}->{args.inference_backend}"
    self_consistency = args.generator_backend == "proxy" and args.inference_backend == "proxy"
    print(f"  true_states  : {[label for label, _ in true_states]}")
    print(f"  noise_rates  : {noise_rates}")
    print(f"  n_attempts   : {args.n_attempts}")
    print(f"  preset       : {args.preset}")
    print(f"  rule         : {args.rule}")
    print(f"  seed         : {args.seed}")
    print(f"  backend_pair : {backend_pair}  "
          f"({'self-consistency' if self_consistency else 'simulator-robustness'})")
    print(f"  output_dir   : {args.output_dir}")
    if n_att_sweep:
        print(f"  n_att_sweep  : {n_att_sweep}")
    print()

    t_start = time.monotonic()
    result = run_benchmark(
        true_states=true_states,
        noise_rates=noise_rates,
        n_attempts=args.n_attempts,
        preset_name=args.preset,
        acceptance_rule=args.rule,
        seed=args.seed,
        generator_backend=args.generator_backend,
        inference_backend=args.inference_backend,
        abm_generations=args.abm_generations,
        abm_population_size=args.abm_population_size,
        abm_replicates=args.abm_replicates,
        n_attempts_sweep=n_att_sweep,
        verbose=True,
    )
    elapsed = round(time.monotonic() - t_start, 1)

    written = save_outputs(result, args.output_dir)
    print(f"\nDone in {elapsed}s. Files written:")
    for path in written.values():
        print(f"  {path}")
    if args.figure:
        make_figure(written, args.figure)

    print("\n--- Summary by noise rate ---")
    print(f"{'noise':>6}  {'cases':>5}  {'acc':>6}  {'F1':>6}  {'R':>7}")
    groups: dict[float, list] = defaultdict(list)
    for case in result.cases:
        groups[case.noise_rate].append(case)
    for noise in sorted(groups):
        cases = groups[noise]

        def _mean(attr):
            values = [getattr(case, attr) for case in cases if not math.isnan(getattr(case, attr))]
            return sum(values) / len(values) if values else float("nan")

        # The object field keeps its frozen historical name; display uses R.
        print(
            f"{noise:6.2f}  {len(cases):5d}  {_mean('accuracy'):6.3f}  "
            f"{_mean('f1'):6.3f}  {_mean('R_RACH'):7.3f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "BenchmarkCase",
    "BenchmarkResult",
    "SwitchRecovery",
    "TRUE_SWITCH_STATES",
    "compute_case_metrics",
    "generate_synthetic_patterns",
    "make_figure",
    "run_benchmark",
    "save_outputs",
]
