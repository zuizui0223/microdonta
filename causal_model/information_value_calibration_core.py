"""Observation-information calibration (MEE Experiment 3).

Validates that observation information value is a calibrated, cheaply computable
preposterior expected gain in mechanism resolvability rather than a heuristic.
Two results are checked:

(1) Exactness / cheapness. For a quantitative observation q = (variable,
population) with true value v, the resolvability gain computed by filtering the
existing admissible region to draws consistent with q≈v equals the gain from a
fresh ABC re-inference that actually adds q=v. Thus the gain can be computed from
the current accepted region without costly re-runs under the deterministic proxy
simulator (and approximately under a stochastic simulator).

(2) Predictive calibration. The preposterior information value of q — the
expectation of the resolvability gain over the predictive distribution of q
across the admissible region — predicts the realised gain obtained when the
observation is taken under a specific true state.

Resolvability-utility form:

    V(q) = Σ_v p(v | A_ε) · [R(A_ε | q=v) − R(A_ε)].

where p(v | A_ε) is the predictive probability of outcome v and R(A_ε | q=v)
is the resolvability of the sub-region consistent with observing v.

Usage
-----
    python -m causal_model.observation_value_calibration \
        --figure outputs/mee/figure3_information_value_calibration.png
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field


_PANEL_VARS = ("nectar_guide", "selfing_rate", "flower_size", "Fis")
_PANEL_POPS = ("Oshima", "Hachijo")


def _truth_states():
    """Representative confound-relevant true states for calibration."""
    from causal_model.switches import PathwaySwitches
    return {
        "S2": PathwaySwitches(selfing_mediation=1.0),
        "S3": PathwaySwitches(island_common_cause=1.0),
        "S2+S3": PathwaySwitches(selfing_mediation=1.0, island_common_cause=1.0),
        "S1+S2": PathwaySwitches(
            direct_pollinator_to_guide=1.0,
            selfing_mediation=1.0,
        ),
    }


@dataclass
class CalibrationResult:
    R0: float
    n_accepted: int
    # (1) exactness: list of (label, cheap_gain, reinference_gain)
    exactness: list[tuple[str, float, float]] = field(default_factory=list)
    # (2) calibration: list of (obs_label, information_value, truth_label, realized)
    calibration: list[tuple[str, float, str, float]] = field(default_factory=list)


def _col(pop: str, var: str) -> str:
    return f"{pop}_{var}"


def _values(accepted: list[dict], pop: str, var: str) -> list[float]:
    c = _col(pop, var)
    return [float(r[c]) for r in accepted if r.get(c) is not None]


def evsi_resolvability(
    accepted: list[dict],
    switches,
    pop: str,
    var: str,
    R0: float,
    n_bins: int = 6,
) -> float | None:
    """Preposterior information value on resolvability from the admissible region."""
    from causal_model.mechanism_region import causal_resolvability

    xs = _values(accepted, pop, var)
    if not xs:
        return None
    lo, hi = min(xs), max(xs)
    if hi - lo < 1e-9:
        return 0.0
    w = (hi - lo) / n_bins
    col = _col(pop, var)
    e = 0.0
    for b in range(n_bins):
        c0, c1 = lo + b * w, lo + (b + 1) * w
        sub = [
            r
            for r in accepted
            if r.get(col) is not None
            and (
                c0 <= float(r[col]) < c1
                or (b == n_bins - 1 and float(r[col]) >= c1 - 1e-12)
            )
        ]
        if not sub:
            continue
        p = len(sub) / len(accepted)
        e += p * (causal_resolvability(sub, switches) - R0)
    return round(e, 4)


def realized_gain_cheap(
    accepted: list[dict],
    switches,
    pop: str,
    var: str,
    true_value: float,
    tol: float,
    R0: float,
) -> float | None:
    """Realised resolvability gain at a true value by filtering accepted rows."""
    from causal_model.mechanism_region import causal_resolvability

    col = _col(pop, var)
    sub = [
        r
        for r in accepted
        if r.get(col) is not None and abs(float(r[col]) - true_value) <= tol
    ]
    if not sub:
        return None
    return round(causal_resolvability(sub, switches) - R0, 4)


def realized_gain_reinference(
    switches,
    pop: str,
    var: str,
    true_value: float,
    tol: float,
    R0: float,
    *,
    preset_name: str,
    acceptance_rule: str,
    n_attempts: int,
    seed: int,
) -> float | None:
    """Realised gain from fresh ABC re-inference after adding q=true_value."""
    from causal_model.switch_inference import run_switch_posterior_inference
    from causal_model.mechanism_region import causal_resolvability

    row = {
        "pattern": f"{var}_{pop}_abs",
        "observation": f"{var}_{pop}_abs",
        "type": "absolute_summary",
        "variable": var,
        "population": pop,
        "observed_value": f"{true_value:.6f}",
        "se": f"{tol:.6f}",
        "scale": f"{tol:.6f}",
        "weight": "1.5",
        "role": "observed_target",
        "left_population": "",
        "right_population": "",
        "populations": "",
        "predictor": "",
        "expected_direction": "",
        "relation": "",
    }
    sp = run_switch_posterior_inference(
        preset_name=preset_name,
        n_attempts=n_attempts,
        acceptance_rule=acceptance_rule,
        seed=seed,
        extra_pattern_rows=[row],
    )
    if not sp.accepted_rows:
        return None
    return round(causal_resolvability(sp.accepted_rows, switches) - R0, 4)


def _tol_for(var: str) -> float:
    return {
        "nectar_guide": 0.04,
        "selfing_rate": 0.10,
        "flower_size": 0.05,
        "Fis": 0.10,
    }.get(var, 0.05)


def run_calibration(
    preset_name: str = "literature_grounded",
    acceptance_rule: str = "strict_all",
    n_attempts: int = 1000,
    seed: int = 7,
) -> CalibrationResult:
    from causal_model.switch_inference import (
        CAMPANULA_SWITCHES,
        run_switch_posterior_inference,
    )
    from causal_model.mechanism_region import causal_resolvability
    from examples.campanula_izu.campanula_phenomenological import (
        default_campanula_gradient_environments,
        simulate_campanula_gradient,
    )

    sp = run_switch_posterior_inference(
        preset_name=preset_name,
        n_attempts=n_attempts,
        acceptance_rule=acceptance_rule,
        seed=seed,
    )
    acc = sp.accepted_rows
    R0 = round(causal_resolvability(acc, CAMPANULA_SWITCHES), 4)
    res = CalibrationResult(R0=R0, n_accepted=len(acc))

    envs = default_campanula_gradient_environments()
    truths = _truth_states()
    truth_vals = {
        tn: simulate_campanula_gradient(sw, environments=envs)
        for tn, sw in truths.items()
    }

    for pop in _PANEL_POPS:
        for var in _PANEL_VARS:
            tol = _tol_for(var)
            value = evsi_resolvability(acc, CAMPANULA_SWITCHES, pop, var, R0)
            if value is None:
                continue
            for tn, outs in truth_vals.items():
                tv = getattr(outs[pop], var, None)
                if tv is None:
                    continue
                real = realized_gain_cheap(
                    acc,
                    CAMPANULA_SWITCHES,
                    pop,
                    var,
                    tv,
                    tol,
                    R0,
                )
                if real is not None:
                    res.calibration.append((f"{var}@{pop}", value, tn, real))

    # Cheap filter versus fresh re-inference at S3-truth values.
    s3_outs = truth_vals["S3"]
    for pop in ("Hachijo", "Oshima"):
        for var in ("nectar_guide", "selfing_rate", "flower_size"):
            tol = _tol_for(var)
            tv = getattr(s3_outs[pop], var, None)
            if tv is None:
                continue
            cheap = realized_gain_cheap(
                acc,
                CAMPANULA_SWITCHES,
                pop,
                var,
                tv,
                tol,
                R0,
            )
            reinf = realized_gain_reinference(
                CAMPANULA_SWITCHES,
                pop,
                var,
                tv,
                tol,
                R0,
                preset_name=preset_name,
                acceptance_rule=acceptance_rule,
                n_attempts=n_attempts,
                seed=seed,
            )
            if cheap is not None and reinf is not None:
                res.exactness.append((f"{var}@{pop}", cheap, reinf))
    return res


def print_report(res: CalibrationResult) -> None:
    print("=" * 68)
    print(
        f"Observation information-value calibration   "
        f"R0={res.R0}  n_accepted={res.n_accepted}"
    )
    print("=" * 68)
    print("(1) Stored-region filter versus fresh re-inference")
    for lab, cheap, reinf in res.exactness:
        flag = "OK" if abs(cheap - reinf) < 1e-6 else f"Δ={cheap-reinf:+.4f}"
        print(f"    {lab:24s} filter={cheap:+.4f}  reinference={reinf:+.4f}  {flag}")
    print()
    print("(2) Predicted information value versus mean realised gain")
    import statistics

    by_obs: dict[str, list[float]] = {}
    value_of: dict[str, float] = {}
    for obs, value, _tn, real in res.calibration:
        by_obs.setdefault(obs, []).append(real)
        value_of[obs] = value
    for obs in by_obs:
        rr = by_obs[obs]
        print(
            f"    {obs:24s} predicted={value_of[obs]:+.4f}  "
            f"mean_realised={statistics.mean(rr):+.4f}"
        )


def make_figure(res: CalibrationResult, path: str) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib unavailable — skipping figure.")
        return None
    import math
    import os
    import statistics

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))

    ax = axes[0]
    if res.exactness:
        cheap = [c for _, c, _ in res.exactness]
        reinf = [r for _, _, r in res.exactness]
        lim = max(max(cheap + reinf), 0.01) * 1.1
        ax.plot([0, lim], [0, lim], "k--", lw=1, label="1:1")
        ax.scatter(cheap, reinf, c="#1f77b4", s=40, zorder=3)
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
    ax.set_xlabel("stored-region ΔR")
    ax.set_ylabel("ΔR from fresh re-inference")
    ax.set_title("(1) Stored-region update is exact\nfor tested deterministic cases")
    ax.legend(fontsize=8)

    ax = axes[1]
    by_obs: dict[str, list[float]] = {}
    value_of: dict[str, float] = {}
    for obs, value, _tn, real in res.calibration:
        by_obs.setdefault(obs, []).append(real)
        value_of[obs] = value
    xs_all, ys_all = [], []
    for obs, rr in by_obs.items():
        value = value_of[obs]
        ax.scatter([value] * len(rr), rr, c="#cccccc", s=18, zorder=2)
        mean_realised = statistics.mean(rr)
        ax.scatter([value], [mean_realised], c="#d62728", s=45, zorder=3)
        xs_all.append(value)
        ys_all.append(mean_realised)
    if xs_all:
        lim = max(max(xs_all + ys_all), 0.01) * 1.15
        ax.plot([0, lim], [0, lim], "k--", lw=1, label="1:1")
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        if len(xs_all) > 2:
            mx, my = statistics.mean(xs_all), statistics.mean(ys_all)
            cov = sum((a - mx) * (b - my) for a, b in zip(xs_all, ys_all))
            sx = math.sqrt(sum((a - mx) ** 2 for a in xs_all))
            sy = math.sqrt(sum((b - my) ** 2 for b in ys_all))
            if sx > 0 and sy > 0:
                ax.set_title(
                    "(2) Predicted vs realised gain\n"
                    f"mean realised correlation r={cov/(sx*sy):.2f}"
                )
    ax.set_xlabel("predicted observation information value")
    ax.set_ylabel("realised ΔR at truth (grey)\nmean over truths (red)")
    if not ax.get_title():
        ax.set_title("(2) Predicted vs realised gain")
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Observation information-value calibration.")
    p.add_argument("--preset", default="literature_grounded")
    p.add_argument("--rule", default="strict_all")
    p.add_argument("--n-attempts", type=int, default=1000)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_calibration(
        preset_name=args.preset,
        acceptance_rule=args.rule,
        n_attempts=args.n_attempts,
        seed=args.seed,
    )
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
