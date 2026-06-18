"""Generality demonstration on a synthetic, non-Campanula system (MEE Exp 2).

The RACH *inference layer* (causal admissibility, degeneracy, resolvability,
observation contribution, EVSI) is simulator-agnostic: it consumes accepted
(theta, s) draws and a switch list, with no Campanula dependency. This module
shows the *same* workflow — confound → degeneracy → quantitative resolution +
EVSI — on a transparent synthetic generative model, demonstrating the method is
not specific to the Campanula ABM.

Synthetic model
---------------
K = 4 binary mechanism switches s = (A, B, C, D). A latent scale theta ∈ [0.8, 1.2].
A trait is observed along a gradient x ∈ {0, 1/3, 2/3, 1}:

    slope(s, theta) = theta * (0.20 * B + 0.50 * C)     # only B and C drive it
    y1_i = slope * x_i                                   # ordinal observable (trend sign)
    y2   = slope                                         # quantitative magnitude (endpoint)

Observed ordinal pattern: y1 increases along the gradient (slope > 0). **B and C
both produce a positive slope** (same ordinal direction) but different magnitude
(0.20 vs 0.50), so they are confounded on the ordinal observable and separable
only by the quantitative magnitude y2 — exactly the structure of the Campanula
S2/S3 confound, in a generic model.

Usage
-----
    python -m causal_model.synthetic_demo --figure outputs/mee/synthetic_demo.png
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field

_SITES = (0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0)
_SLOPE_TOL = 0.05   # ordinal: |slope| must exceed this to call a direction


def _switches():
    from causal_model.switch_inference import BiologicalSwitch
    return [
        BiologicalSwitch(name="A", pathway_key="A", biological_question="", description=""),
        BiologicalSwitch(name="B", pathway_key="B", biological_question="", description=""),
        BiologicalSwitch(name="C", pathway_key="C", biological_question="", description=""),
        BiologicalSwitch(name="D", pathway_key="D", biological_question="", description=""),
    ]


def _slope(s: dict, theta: float) -> float:
    return theta * (0.20 * int(bool(s["B"])) + 0.50 * int(bool(s["C"])))


@dataclass
class SyntheticResult:
    switch_names: list[str]
    n_accepted: int
    ca_j: dict[str, float]
    D_RACH: float
    R_RACH: float
    map_model: tuple
    map_prob: float
    # EVSI for the quantitative magnitude observation
    evsi_y2: float
    # resolution after adding the quantitative observation (truth = C only)
    ca_j_after: dict[str, float] = field(default_factory=dict)
    D_after: float = float("nan")
    R_after: float = field(default=float("nan"))


def _abc_accept(n_attempts: int, seed: int) -> list[dict]:
    """Sample (s, theta) from the prior; accept draws whose ordinal y1 trend is positive."""
    rng = random.Random(seed)
    accepted = []
    for _ in range(n_attempts):
        s = {k: (rng.random() < 0.5) for k in ("A", "B", "C", "D")}
        theta = rng.uniform(0.8, 1.2)
        slope = _slope(s, theta)
        if slope > _SLOPE_TOL:           # observed ordinal pattern: positive trend
            row = dict(s)
            row["theta"] = theta
            row["y2"] = slope            # quantitative magnitude available per draw
            accepted.append(row)
    return accepted


def _evsi_resolvability(accepted, switches, key: str, R0: float, n_bins: int = 6):
    from causal_model.causal_admissibility import causal_resolvability
    xs = [r[key] for r in accepted if r.get(key) is not None]
    if not xs:
        return None
    lo, hi = min(xs), max(xs)
    if hi - lo < 1e-9:
        return 0.0
    w = (hi - lo) / n_bins
    e = 0.0
    for b in range(n_bins):
        c0, c1 = lo + b * w, lo + (b + 1) * w
        sub = [r for r in accepted if c0 <= r[key] < c1 or (b == n_bins - 1 and r[key] >= c1 - 1e-12)]
        if not sub:
            continue
        e += (len(sub) / len(accepted)) * (causal_resolvability(sub, switches) - R0)
    return round(e, 4)


def run_synthetic_demo(n_attempts: int = 4000, seed: int = 1) -> SyntheticResult:
    from causal_model.causal_admissibility import rach_summary, causal_resolvability
    from collections import Counter

    switches = _switches()
    names = [sw.name for sw in switches]
    acc = _abc_accept(n_attempts, seed)

    summ = rach_summary(acc, switches)
    ca = {r.switch_name: round(r.CA_j, 4) for r in summ.causal_admissibility}
    R0 = round(summ.causal_resolvability, 4)
    D0 = round(summ.causal_degeneracy, 4)

    # ABC model choice: MAP switch-combination
    counts = Counter(tuple(int(bool(r[n])) for n in names) for r in acc)
    map_model, c = counts.most_common(1)[0]
    map_prob = round(c / len(acc), 4)

    # EVSI for the quantitative magnitude observation y2
    evsi = _evsi_resolvability(acc, switches, "y2", R0)

    res = SyntheticResult(
        switch_names=names, n_accepted=len(acc), ca_j=ca, D_RACH=D0, R_RACH=R0,
        map_model=map_model, map_prob=map_prob, evsi_y2=evsi or 0.0,
    )

    # Resolution: truth = C only → quantitative magnitude ~ 0.50 (theta~1). Add the
    # quantitative observation by filtering A_eps to draws consistent with it.
    truth_val = 0.50  # C-only slope at theta=1
    tol = 0.08
    sub = [r for r in acc if abs(r["y2"] - truth_val) <= tol]
    if sub:
        summ2 = rach_summary(sub, switches)
        res.ca_j_after = {r.switch_name: round(r.CA_j, 4) for r in summ2.causal_admissibility}
        res.D_after = round(summ2.causal_degeneracy, 4)
        res.R_after = round(causal_resolvability(sub, switches), 4)
    return res


def print_report(res: SyntheticResult) -> None:
    print("=" * 64)
    print("Synthetic generality demo (non-Campanula 4-switch system)")
    print("=" * 64)
    print(f"n_accepted={res.n_accepted}   switch order={res.switch_names}")
    print(f"(A) ABC model choice MAP model {res.map_model}  P={res.map_prob}")
    print(f"(B) RACH: D_RACH={res.D_RACH}/4  R_RACH={res.R_RACH}")
    for n in res.switch_names:
        print(f"      CA_j[{n}] = {res.ca_j[n]}")
    print(f"    → B={res.ca_j['B']} and C={res.ca_j['C']}: confounded on the ordinal trend.")
    print(f"(C) EVSI for the quantitative magnitude observation y2 = {res.evsi_y2:+.4f}")
    if res.ca_j_after:
        print("(D) Resolution — add quantitative magnitude (truth = C only):")
        print(f"      D_RACH {res.D_RACH} → {res.D_after}   R_RACH {res.R_RACH} → {res.R_after}")
        print(f"      CA_j[C] {res.ca_j['C']} → {res.ca_j_after['C']}  (↑ supported)")
        print(f"      CA_j[B] {res.ca_j['B']} → {res.ca_j_after['B']}  (↓ rejected)")
        print("    → same workflow as Campanula, on a generic model: the confound resolves.")


def make_figure(res: SyntheticResult, path: str) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception:
        print("matplotlib unavailable — skipping figure.")
        return None
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    names = res.switch_names

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))

    # Panel 1: degeneracy (B,C confounded)
    ax = axes[0]
    vals = [res.ca_j[n] for n in names]
    colors = ["#d62728" if n in ("B", "C") else "#1f77b4" for n in names]
    ax.bar(names, vals, color=colors)
    ax.axhline(0.5, color="gray", ls="--", lw=1)
    ax.set_ylim(0, 1); ax.set_ylabel("CA_j")
    ax.set_title(f"(A) Synthetic confound\nD={res.D_RACH}/4, R={res.R_RACH}; B,C unresolved")

    # Panel 2: resolution before/after for B and C
    ax = axes[1]
    if res.ca_j_after:
        before = [res.ca_j["B"], res.ca_j["C"]]
        after = [res.ca_j_after["B"], res.ca_j_after["C"]]
        x = np.arange(2); w = 0.38
        ax.bar(x - w/2, before, w, label="ordinal only", color="#bbbbbb")
        ax.bar(x + w/2, after, w, label="+ magnitude", color="#d62728")
        ax.axhline(0.5, color="gray", ls="--", lw=1)
        ax.set_xticks(x); ax.set_xticklabels(["B (weak)", "C (strong)"])
        ax.set_ylim(0, 1); ax.set_ylabel("CA_j")
        ax.set_title(f"(B) Resolution (truth=C)\nD {res.D_RACH}→{res.D_after}, "
                     f"R {res.R_RACH}→{res.R_after}; EVSI(y2)={res.evsi_y2:+.2f}")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Synthetic generality demo (MEE Exp 2).")
    p.add_argument("--n-attempts", type=int, default=4000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_synthetic_demo(n_attempts=args.n_attempts, seed=args.seed)
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
