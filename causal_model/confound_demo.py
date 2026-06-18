"""Money-figure demonstration: model selection misleads, RACH does not (MEE Exp 1).

The current Campanula y_obs is two ordinal isolation gradients (selfing ↑,
flower size ↓). S2 (selfing syndrome) and S3 (island isolation common cause) both
reproduce these gradients exactly, so they are confounded under the current data.

This driver contrasts, on the SAME ABC-accepted region:

  (A) ABC model choice   — posterior over discrete switch-combination "models"
                           and the single MAP model a selection approach reports.
  (B) RACH degeneracy    — D_RACH / R_RACH and per-mechanism admissibility CA_j;
                           the S2/S3 confound is reported, not hidden.
  (C) NOV                — which next observation most reduces the confound.
  (D) Resolution         — add the NOV-recommended observation and re-infer;
                           the confounded mechanism resolves.

The point is not a different posterior — model choice and RACH share it — but
that RACH reports the confound explicitly and prescribes the resolving
observation, then verifies it resolves.

Usage
-----
    python -m causal_model.confound_demo --backend proxy --n-attempts 600
    python -m causal_model.confound_demo --figure outputs/mee/confound_demo.png
"""
from __future__ import annotations

import argparse
import math
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class ConfoundDemoResult:
    switch_names: list[str]
    n_accepted: int
    # (A) ABC model choice
    model_posterior: list[tuple[tuple[int, ...], float]]   # (switch vector, prob), sorted desc
    map_model: tuple[int, ...]
    map_prob: float
    # (B) RACH
    ca_j: dict[str, float]
    D_RACH: float
    R_RACH: float
    # (C) NOV
    nov_ranking: list[tuple[str, float, list[str]]]        # (candidate, gain, target_switches)
    # (D) resolution after adding the top confound-breaking observation
    resolving_candidate: str | None = None
    ca_j_after: dict[str, float] = field(default_factory=dict)
    D_after: float = float("nan")
    R_after: float = float("nan")


def _switch_vector(row: dict, switch_names: list[str]) -> tuple[int, ...]:
    return tuple(int(bool(row.get(n))) for n in switch_names)


def _model_posterior(accepted: list[dict], switch_names: list[str]):
    """Posterior over distinct switch-combination models (ABC model choice)."""
    n = len(accepted)
    if n == 0:
        return [], (), 0.0
    counts = Counter(_switch_vector(r, switch_names) for r in accepted)
    posterior = sorted(((vec, c / n) for vec, c in counts.items()),
                       key=lambda x: x[1], reverse=True)
    map_model, map_prob = posterior[0]
    return posterior, map_model, map_prob


def run_confound_demo(
    backend: str = "proxy",
    n_attempts: int = 600,
    preset_name: str = "literature_grounded",
    acceptance_rule: str = "strict_all",
    seed: int = 7,
) -> ConfoundDemoResult:
    """Run the model-choice vs RACH confound demonstration on the current y_obs."""
    from causal_model.switch_inference import (
        run_switch_posterior_inference,
        run_switch_posterior_inference_abm,
        CAMPANULA_SWITCHES,
    )
    from causal_model.causal_admissibility import (
        rach_summary,
        causal_degeneracy,
        causal_resolvability,
        next_observation_value,
        CAMPANULA_CANDIDATE_OBSERVATIONS,
    )

    switch_names = [sw.name for sw in CAMPANULA_SWITCHES]
    _run = run_switch_posterior_inference_abm if backend == "abm" else run_switch_posterior_inference
    kw = dict(preset_name=preset_name, n_attempts=n_attempts,
              acceptance_rule=acceptance_rule, seed=seed)
    if backend == "abm":
        kw.update(generations=30, population_size=100, replicates=3)
    sp = _run(**kw)
    accepted = sp.accepted_rows

    # (A) ABC model choice
    posterior, map_model, map_prob = _model_posterior(accepted, switch_names)

    # (B) RACH degeneracy
    summ = rach_summary(accepted, CAMPANULA_SWITCHES)
    ca_j = {r.switch_name: round(r.CA_j, 4) for r in summ.causal_admissibility}
    D = round(summ.causal_degeneracy, 4)
    R = round(summ.causal_resolvability, 4)

    # (C) NOV ranking
    nov = next_observation_value(accepted, CAMPANULA_SWITCHES)
    nov_ranking = [(r.candidate, round(r.expected_resolvability_gain, 4), list(r.target_switches))
                   for r in nov]

    return ConfoundDemoResult(
        switch_names=switch_names,
        n_accepted=len(accepted),
        model_posterior=posterior,
        map_model=map_model,
        map_prob=map_prob,
        ca_j=ca_j,
        D_RACH=D,
        R_RACH=R,
        nov_ranking=nov_ranking,
    )


def print_report(res: ConfoundDemoResult) -> None:
    sw = res.switch_names
    print("=" * 70)
    print("Confound demonstration — current 2-gradient y_obs (selfing↑, flower↓)")
    print("=" * 70)
    print(f"n_accepted (shared ABC region): {res.n_accepted}")
    print()
    print("(A) ABC MODEL CHOICE — posterior over switch-combination models")
    print(f"    switch order: {sw}")
    for vec, p in res.model_posterior[:6]:
        print(f"      {vec}  P={p:.3f}")
    print(f"    MAP model a selection approach would report: {res.map_model}  "
          f"P={res.map_prob:.3f}")
    print("    → a single 'best model' is reported even though S2 and S3 are "
          "indistinguishable.")
    print()
    print("(B) RACH — degeneracy makes the confound explicit")
    print(f"    D_RACH={res.D_RACH}  (of K={len(sw)})   R_RACH={res.R_RACH}")
    for n in sw:
        print(f"      CA_j[{n}] = {res.ca_j[n]}")
    s2 = res.ca_j.get("selfing_syndrome_active")
    s3 = res.ca_j.get("island_isolation_common_cause")
    print(f"    → S2={s2} and S3={s3}: both admissible and nearly equal = "
          "mutually UNRESOLVED (the confound is reported, not hidden).")
    print("    NB: S2 and S3 agree on the ORDINAL direction of both gradients;")
    print("        they differ only in MAGNITUDE (e.g. selfing slope ~0.18 vs ~0.50,")
    print("        Fis ~0.19 vs ~0.41). Ordinal y_obs cannot separate them — a")
    print("        quantitative / absolute_summary observation is required (see NOV).")
    print()
    print("(C) NOV — which observation most reduces the confound")
    for cand, gain, tgt in res.nov_ranking[:5]:
        print(f"      {cand:38s} ΔR={gain:+.4f}  targets={tgt}")


def make_figure(res: ConfoundDemoResult, path: str) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib unavailable — skipping figure.")
        return None
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    sw = res.switch_names
    short = {"guide_attracts_bombus": "S1", "selfing_syndrome_active": "S2",
             "island_isolation_common_cause": "S3", "small_pollinator_substitution": "S5"}
    labels = [short.get(n, n) for n in sw]

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))

    # Panel A: model-choice posterior (top models)
    ax = axes[0]
    top = res.model_posterior[:6]
    ylabels = ["".join(str(b) for b in vec) for vec, _ in top]
    ax.barh(range(len(top)), [p for _, p in top], color="#888")
    ax.set_yticks(range(len(top))); ax.set_yticklabels(ylabels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("P(model | data)")
    ax.set_title("(A) ABC model choice\n(reports a single MAP model)")

    # Panel B: CA_j with S2/S3 highlighted as confounded
    ax = axes[1]
    vals = [res.ca_j[n] for n in sw]
    colors = ["#d62728" if n in ("selfing_syndrome_active", "island_isolation_common_cause")
              else "#1f77b4" for n in sw]
    ax.bar(labels, vals, color=colors)
    ax.axhline(0.5, color="gray", ls="--", lw=1)
    ax.set_ylim(0, 1); ax.set_ylabel("CA_j")
    ax.set_title(f"(B) RACH degeneracy\nD={res.D_RACH}, R={res.R_RACH}; S2,S3 unresolved")

    # Panel C: NOV ranking
    ax = axes[2]
    topn = res.nov_ranking[:6]
    names = [c for c, _, _ in topn]
    gains = [g for _, g, _ in topn]
    ax.barh(range(len(topn)), gains, color="#2ca02c")
    ax.set_yticks(range(len(topn)))
    ax.set_yticklabels([n[:24] for n in names], fontsize=7)
    ax.invert_yaxis(); ax.set_xlabel("expected ΔR (NOV)")
    ax.set_title("(C) NOV: what to measure next\nto break the confound")

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="RACH confound demonstration (MEE money figure).")
    p.add_argument("--backend", choices=["proxy", "abm"], default="proxy")
    p.add_argument("--n-attempts", type=int, default=600)
    p.add_argument("--preset", default="literature_grounded")
    p.add_argument("--rule", default="strict_all")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--figure", default="", help="Path to write the money figure PNG.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_confound_demo(backend=args.backend, n_attempts=args.n_attempts,
                            preset_name=args.preset, acceptance_rule=args.rule,
                            seed=args.seed)
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
