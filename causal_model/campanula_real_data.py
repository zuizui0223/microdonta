"""RACH applied to the REAL published *Campanula microdonta* (Izu Islands) data.

This is the empirical application, not a simulation with an assumed truth. It runs
the Tier-A structural engine on the *actually source-confirmed* observations and
reports the only honest conclusion the published record supports: the mechanism is
**not resolved**, and here is the cost-aware list of which real field experiment to
do next.

What is real here (and what is not)
-----------------------------------
y_obs — the ABC acceptance targets — are the two directional gradients that are
source-confirmed in the Inoue series:

    selfing rate INCREASES with isolation     (Inoue 1990)
    flower size  DECREASES with isolation      (Inoue & Amano 1986)

Everything else in the data tables (per-population nectar-guide intensity, Fis,
herkogamy, exact numeric rates) is explicitly *excluded*: it is either planned
own-field data, a theory-derived prediction, or pending PDF transcription. We do
NOT feed any of it to acceptance. (See examples/campanula_izu/observed_data.py for
the role bookkeeping.) x_obs — the fixed context — is the documented
Bombus→halictid pollinator transition along the gradient (Inoue & Amano 1986).

The candidate mechanisms (signs only; magnitudes randomised, Tier A)
--------------------------------------------------------------------
    S1 guide_attracts_bombus   Bombus loss removes selection for nectar guides
    S2 selfing_syndrome        reproductive-assurance selfing syndrome
    S3 island_common_cause     isolation as a single upstream common cause
    S5 halictid_substitution   small pollinators compensate, suppressing selfing

The honest result
-----------------
On the two published gradients alone, S2 and S3 both reproduce "selfing↑,
flower↓" and are jointly admissible — a disjunction confound with R_expl ≈ 0. RACH
cannot, and does not, claim to know which is the driver. Its deliverable is the
study design: each candidate observation is scored by its exact EVSI on
explanation-level resolvability, then combined with the *design* cost and
feasibility recorded in future_observations.csv to rank which real experiment buys
the most resolution per unit effort.

Note the cost/feasibility numbers are design estimates (expert priors for study
planning), not measurements; they are labelled as such.

Usage
-----
    python -m causal_model.campanula_real_data
    python -m causal_model.campanula_real_data --figure outputs/mee/campanula_real.png
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field

# The Tier-A structural engine is shared with the worked example; here we drive it
# from the real published pattern and never assume a latent truth.
from causal_model.campanula_structural import (
    _abc_accept, _switches, _candidate_observations, _NEAR, _FAR,
)

# Map each structural NOV candidate to the real, costed field experiment(s) in
# examples/campanula_izu/data/future_observations.csv.
_CANDIDATE_TO_EXPERIMENT = {
    "bagging_RA_assay": "bagging_autonomous_selfing",
    "neutral_diversity_gradient": "neutral_marker_structure",
    "nectar_guide_gradient": "guide_removal_experiment",
}


@dataclass
class CampanulaRealResult:
    y_obs: list[dict]
    switch_names: list[str]
    n_accepted: int
    n_attempts: int
    ca_j: dict[str, float]
    R_expl: float
    explanations: list[tuple[frozenset, float]]
    confound_edge: str
    study_design: list[dict] = field(default_factory=list)


def _real_y_obs() -> list[dict]:
    """The source-confirmed ABC target gradients (role == observed_target)."""
    try:
        from examples.campanula_izu.observed_data import observed_target_patterns
        rows = observed_target_patterns()
    except Exception:
        rows = []
    if not rows:                       # provenance fallback (kept in sync with the CSV)
        rows = [
            {"variable": "selfing_rate", "expected_direction": "positive",
             "predictor": "distance_from_mainland", "source": "field/Inoue1990"},
            {"variable": "flower_size", "expected_direction": "negative",
             "predictor": "distance_from_mainland", "source": "field/InoueAmano1986"},
        ]
    return [{"variable": r["variable"], "direction": r["expected_direction"],
             "predictor": r.get("predictor", ""), "source": r.get("source", "")}
            for r in rows]


def _design_estimates() -> dict[str, dict]:
    try:
        from examples.campanula_izu.observed_data import load_future_observations
        return {r["candidate"]: r for r in load_future_observations()}
    except Exception:
        return {}


def run_campanula_real(n_attempts: int = 6000, seed: int = 1) -> CampanulaRealResult:
    from causal_model.causal_admissibility import rach_summary
    from causal_model.mechanism_equivalence import mechanism_equivalence_structure
    from causal_model.minimal_explanations import minimal_explanations, explanation_nov

    switches = _switches()
    names = [sw.name for sw in switches]
    acc = _abc_accept(n_attempts, seed)            # accepts the real pattern: selfing↑, flower↓

    summ = rach_summary(acc, switches)
    ca = {r.switch_name: round(r.CA_j, 4) for r in summ.causal_admissibility}
    dec = minimal_explanations(acc, switches)
    struct = mechanism_equivalence_structure(acc, switches)
    edge = struct.edges[0].describe() if struct.edges else "none"

    res = CampanulaRealResult(
        y_obs=_real_y_obs(), switch_names=names,
        n_accepted=len(acc), n_attempts=n_attempts, ca_j=ca,
        R_expl=dec.R_expl,
        explanations=[(e.mechanisms, e.mass) for e in dec.explanations],
        confound_edge=edge,
    )

    # Study design: EVSI on R_expl per candidate, combined with real design cost/feasibility.
    design = _design_estimates()
    for cand in _candidate_observations():
        nov = explanation_nov(cand, acc, switches)
        exp_name = _CANDIDATE_TO_EXPERIMENT.get(cand.name)
        d = design.get(exp_name, {})
        cost = d.get("cost")
        feas = d.get("feasibility")
        # efficiency: resolution bought per unit effort, weighted by feasibility
        eff = None
        if nov is not None and cost not in (None, 0) and feas is not None:
            eff = round(nov * feas / cost, 4)
        res.study_design.append({
            "candidate": cand.name,
            "real_experiment": exp_name or "(unmapped)",
            "targets": ", ".join(cand.target_switches),
            "NOV_EVSI_Rexpl": nov,
            "design_cost": cost,
            "design_feasibility": feas,
            "efficiency": eff,
        })
    # rank by efficiency when available, else by raw NOV
    res.study_design.sort(
        key=lambda r: (r["efficiency"] if r["efficiency"] is not None else -1,
                       r["NOV_EVSI_Rexpl"] or 0),
        reverse=True,
    )
    return res


def print_report(res: CampanulaRealResult) -> None:
    print("=" * 76)
    print("RACH on the REAL Campanula microdonta (Izu Islands) published record")
    print("=" * 76)
    print("y_obs — source-confirmed ABC targets:")
    for r in res.y_obs:
        arrow = "↑" if r["direction"] == "positive" else "↓"
        print(f"    {r['variable']:12s} {arrow} with {r['predictor']}   [{r['source']}]")
    print(f"\n(A) On the published gradients alone (|A_ε| = {res.n_accepted}/{res.n_attempts}):")
    print(f"    explanation-level R_expl = {res.R_expl}")
    em = "  ".join(("{" + ", ".join(sorted(m)) + "}") + f"={mass:.2f}" for m, mass in res.explanations)
    print(f"    minimal explanations: {em}")
    print(f"    confounding edge: {res.confound_edge}")
    print("    → the published record CANNOT distinguish the selfing-syndrome (S2)")
    print("      from the island-common-cause (S3) explanation. RACH does not guess.")
    print("\n(B) Study design — which real experiment to run next")
    print("    (NOV = exact EVSI on R_expl; cost/feasibility are design estimates, not data):")
    print(f"    {'experiment':30s} {'targets':24s} {'NOV':>6s} {'cost':>5s} {'feas':>5s} {'eff':>6s}")
    for r in res.study_design:
        nov = "n/a" if r["NOV_EVSI_Rexpl"] is None else f"{r['NOV_EVSI_Rexpl']:.3f}"
        cost = "n/a" if r["design_cost"] is None else f"{r['design_cost']:.2f}"
        feas = "n/a" if r["design_feasibility"] is None else f"{r['design_feasibility']:.2f}"
        eff = "n/a" if r["efficiency"] is None else f"{r['efficiency']:.3f}"
        print(f"    {r['real_experiment']:30s} {r['targets'][:24]:24s} {nov:>6s} {cost:>5s} {feas:>5s} {eff:>6s}")
    top = res.study_design[0]
    print(f"\n    → highest resolution-per-effort: {top['real_experiment']} "
          f"(targets {top['targets']}).")


def make_figure(res: CampanulaRealResult, path: str) -> str | None:
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
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.2))

    ax = axes[0]
    labels = ["{" + ", ".join(sorted(m)) + "}" if m else "{∅}" for m, _ in res.explanations]
    short = [l.replace("selfing_syndrome", "S2 selfing").replace("island_common_cause", "S3 common-cause")
             for l in labels]
    ax.bar(short, [mass for _, mass in res.explanations], color="#1f77b4")
    ax.set_ylim(0, 1); ax.set_ylabel("posterior mass")
    ax.set_title(f"(A) Published record — S2/S3 confound\nR_expl={res.R_expl}")
    ax.tick_params(axis="x", labelrotation=10)

    ax = axes[1]
    rows = [r for r in res.study_design if r["efficiency"] is not None]
    if rows:
        names = [r["real_experiment"].replace("_", "\n") for r in rows]
        ax.barh(range(len(rows)), [r["efficiency"] for r in rows], color="#d62728")
        ax.set_yticks(range(len(rows))); ax.set_yticklabels(names, fontsize=8)
        ax.invert_yaxis(); ax.set_xlabel("resolution per effort (NOV·feas/cost)")
        ax.set_title("(B) Which real experiment to run next")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="RACH on the real Campanula microdonta record.")
    p.add_argument("--n-attempts", type=int, default=6000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_campanula_real(n_attempts=args.n_attempts, seed=args.seed)
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
