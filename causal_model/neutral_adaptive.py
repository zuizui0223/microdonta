"""The unifying generative principle: neutral by default, forces born from x_obs.

This module makes explicit the principle the other Tier-A examples were quietly
instances of:

  * **Neutral is the default.** With no selective force, a trait drifts; its
    relationship to the environment is whatever genetic drift happens to produce.
  * **A selective force is *born* from the background environment.** Each axis of
    the observed context ``x_obs`` (temperature, seasonality, …) can host a force;
    a switch ``s_k`` says whether selection is coupled to that axis. No
    environmental signal ⇒ no force ⇒ that axis stays neutral.
  * **Evolution climbs fitness to the benefit = cost balance.** A present force
    adds a benefit linear in the trait and scaled by its environmental driver;
    a universal quadratic cost opposes it. The evolved optimum is the balance
    point ``z* = (Σ active benefits) / (2·cost)`` — the trade-off as a
    conservation condition (marginal benefit equals marginal cost), not a
    hand-picked second sign.
  * Realised trait = ``z*(x)`` + neutral drift.

The question RACH then answers is the central one in evolutionary biology: **is an
observed environmental cline selection or drift, and if selection, on which
environmental axis?**

Why neutral is a *separate* null, not an empty explanation
----------------------------------------------------------
"No force" is the empty switch set ``∅``, which is a subset of every other
configuration. Folding it into the minimal-sufficient-explanation antichain would
make it the unique minimal element and collapse everything onto it. Neutrality is
therefore tracked as a distinguished hypothesis with its own posterior

    P(neutral | A_ε) = fraction of the admissible region with NO force active,

not as a member of the explanation antichain. This posterior behaves exactly as
it should: a weak cline leaves neutrality admissible; a strong, consistent cline
drives ``P(neutral)`` toward zero — a force becomes necessary.

Distinguishing selection from drift
-----------------------------------
The signature of selection is *parallelism*: an environmentally-coupled optimum
reproduces the same cline on independent transects, whereas drift does not. The
resolving observation is therefore a replicate transect; observing a parallel
replicate drives ``P(neutral)`` down (selection), a non-parallel one drives it up
(drift). RACH's NOV recovers this.

(The two forces themselves — thermal vs seasonal — remain confounded on the wild
cline because their drivers are correlated along latitude; separating them is the
decoupled-site observation of ``fitness_rule_discovery``.)

Usage
-----
    python -m causal_model.neutral_adaptive --truth thermal
    python -m causal_model.neutral_adaptive --figure outputs/mee/neutral_adaptive.png
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field

_SITES = (0.0, 0.25, 0.5, 0.75, 1.0)        # environmental gradient (e.g. coldness T)
_FORCES = ("thermal_force", "seasonal_force")  # forces that can be born on x_obs axes

_COST_LO, _COST_HI = 0.5, 1.5
_B_LO, _B_HI = 0.5, 1.4
_DRIFT_LO, _DRIFT_HI = 0.05, 0.25
_RULE_TOL = 0.15            # observed wild cline must rise by at least this much
_REP_TOL = 0.05            # a replicate transect counts as parallel if it rises by this


def _switches():
    from causal_model.switch_inference import BiologicalSwitch
    desc = {
        "thermal_force": "Selection coupled to the temperature axis of x_obs (born only if that signal is present).",
        "seasonal_force": "Selection coupled to the seasonality axis of x_obs (correlated with temperature in the wild).",
    }
    return [BiologicalSwitch(name=m, pathway_key=m, biological_question="", description=desc[m])
            for m in _FORCES]


def _optimum(s: dict, p: dict, T: float) -> float:
    """Benefit = cost balance point: z* = (active benefits)/(2·cost)."""
    benefit = 0.0
    if s["thermal_force"]:
        benefit += p["b_th"] * T
    if s["seasonal_force"]:
        benefit += p["b_se"] * T          # seasonality ≈ T along the wild gradient
    return benefit / (2.0 * p["cost"])


def _transect(s: dict, p: dict, rng: random.Random) -> list[float]:
    """One realised transect: optimum at each site plus independent neutral drift."""
    return [_optimum(s, p, T) + rng.gauss(0.0, p["drift"]) for T in _SITES]


def _params(rng: random.Random) -> dict:
    return {
        "cost": rng.uniform(_COST_LO, _COST_HI),
        "b_th": rng.uniform(_B_LO, _B_HI),
        "b_se": rng.uniform(_B_LO, _B_HI),
        "drift": rng.uniform(_DRIFT_LO, _DRIFT_HI),
    }


def _is_cline(v: list[float], tol: float) -> bool:
    return v[-1] - v[0] >= tol and v[2] > v[0]


def _abc_accept(n_attempts: int, seed: int, rule_tol: float = _RULE_TOL) -> list[dict]:
    """Accept draws whose wild transect shows the observed increasing cline. Each
    draw stores whether an INDEPENDENT replicate transect is parallel (the
    selection-vs-drift signature) and whether it is neutral (no force active).
    """
    rng = random.Random(seed)
    accepted: list[dict] = []
    for _ in range(n_attempts):
        s = {m: (rng.random() < 0.5) for m in _FORCES}
        p = _params(rng)
        v = _transect(s, p, rng)
        if not _is_cline(v, rule_tol):
            continue
        v2 = _transect(s, p, rng)                  # independent replicate
        row = dict(s)
        for i, _ in enumerate(_SITES):
            row[f"z{i}"] = round(v[i], 4)
        row["neutral"] = (not s["thermal_force"]) and (not s["seasonal_force"])
        row["rep_parallel"] = 1.0 if _is_cline(v2, _REP_TOL) else 0.0
        accepted.append(row)
    return accepted


def _p_neutral(rows: list[dict]) -> float:
    return sum(r["neutral"] for r in rows) / len(rows) if rows else float("nan")


# ---------------------------------------------------------------------------
# Candidate observation (NOV): the replicate transect
# ---------------------------------------------------------------------------

def _candidate_observations():
    from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome

    def _rep(parallel: bool):
        return [{
            "type": "absolute_summary", "variable": "parallel", "population": "rep",
            "observed_value": f"{1.0 if parallel else 0.0:.1f}", "scale": "0.25",
        }]

    rep = CandidateObservation(
        name="replicate_transect",
        description="Sample an independent replicate transect along the same gradient; test whether the cline is parallel.",
        target_switches=list(_FORCES),
        rationale=("An environmentally-coupled (selective) optimum reproduces the cline on independent "
                   "transects; drift does not. Parallelism is the selection-vs-neutral signature."),
        pattern_type="absolute_summary",
        outcomes=[
            CandidateOutcome("parallel", "Replicate cline is parallel (selection).", 0.5, _rep(True)),
            CandidateOutcome("not_parallel", "Replicate cline is not parallel (drift).", 0.5, _rep(False)),
        ],
    )
    return [rep]


def _truth_overrides(truth: str) -> dict[str, str]:
    """Realised replicate outcome under an assumed truth (neutral vs a force)."""
    return {"replicate_transect": "not_parallel" if truth == "neutral" else "parallel"}


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class NeutralAdaptiveResult:
    switch_names: list[str]
    truth: str
    n_accepted: int
    n_attempts: int
    ca_j: dict[str, float]
    p_neutral: float
    nov_ranking: list[tuple[str, float]]      # NOV as ΔP(neutral) magnitude
    p_neutral_after: float = float("nan")
    n_after: int = 0
    # P(neutral) as a function of required cline strength (the central curve)
    p_neutral_by_strength: list[tuple[float, float]] = field(default_factory=list)


def _nov_on_neutral(cand, acc: list[dict]) -> float:
    """Expected reduction in uncertainty about neutrality from a candidate:
    Σ_outcome p(outcome)·|P(neutral|outcome) − P(neutral)|."""
    from causal_model.rach_seq import filter_by_outcome
    n = len(acc)
    if n == 0:
        return float("nan")
    p0 = _p_neutral(acc)
    val = 0.0
    for outcome in cand.outcomes:
        sub = filter_by_outcome(acc, outcome.extra_pattern_rows)
        if not sub:
            continue
        val += (len(sub) / n) * abs(_p_neutral(sub) - p0)
    return round(val, 4)


def run_neutral_adaptive(truth: str = "thermal", n_attempts: int = 80000,
                         seed: int = 1) -> NeutralAdaptiveResult:
    from causal_model.causal_admissibility import rach_summary
    from causal_model.rach_seq import filter_by_outcome

    switches = _switches()
    names = [sw.name for sw in switches]
    acc = _abc_accept(n_attempts, seed)

    summ = rach_summary(acc, switches)
    ca = {r.switch_name: round(r.CA_j, 4) for r in summ.causal_admissibility}

    cands = _candidate_observations()
    nov = sorted(((c.name, _nov_on_neutral(c, acc)) for c in cands), key=lambda x: -x[1])

    res = NeutralAdaptiveResult(
        switch_names=names, truth=truth, n_accepted=len(acc), n_attempts=n_attempts,
        ca_j=ca, p_neutral=round(_p_neutral(acc), 4), nov_ranking=nov,
    )

    # P(neutral) vs how strong a cline we demand (the central curve)
    for tol in (0.05, 0.15, 0.30, 0.45):
        sub = _abc_accept(n_attempts, seed, rule_tol=tol)
        if sub:
            res.p_neutral_by_strength.append((tol, round(_p_neutral(sub), 4)))

    # Resolution: take the replicate-transect observation at the assumed truth.
    ov = _truth_overrides(truth)
    cand = cands[0]
    oc = next(o for o in cand.outcomes if o.name == ov[cand.name])
    rows = filter_by_outcome(acc, oc.extra_pattern_rows)
    if rows:
        res.p_neutral_after = round(_p_neutral(rows), 4)
        res.n_after = len(rows)
    return res


def print_report(res: NeutralAdaptiveResult) -> None:
    print("=" * 74)
    print("Neutral by default, forces born from x_obs — the unifying principle")
    print("=" * 74)
    print(f"truth = {res.truth}   accepted (cline) = {res.n_accepted}/{res.n_attempts}")
    print("(A) Is the observed cline selection or drift?")
    print(f"    P(neutral | A_ε) = {res.p_neutral}")
    print(f"    CA_j (forces, confounded on the wild cline): {res.ca_j}")
    print("    P(neutral) vs required cline strength (stronger pattern ⇒ neutral excluded):")
    for tol, pn in res.p_neutral_by_strength:
        print(f"      cline ≥ {tol:.2f}   P(neutral) = {pn}")
    print("(B) NOV — expected shift in P(neutral):")
    for name, val in res.nov_ranking:
        print(f"      {name:24s} {val:.3f}")
    print(f"(C) After the replicate transect (truth={res.truth}, n={res.n_after}):")
    print(f"      P(neutral) {res.p_neutral} → {res.p_neutral_after}")
    if res.truth == "neutral":
        print("      → a non-parallel replicate REVEALS drift: P(neutral) jumps up.")
    else:
        print("      → a parallel replicate CONFIRMS selection: P(neutral) collapses.")


def make_figure(res: NeutralAdaptiveResult, path: str) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib unavailable — skipping figure.")
        return None
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))

    ax = axes[0]
    if res.p_neutral_by_strength:
        xs = [t for t, _ in res.p_neutral_by_strength]
        ys = [p for _, p in res.p_neutral_by_strength]
        ax.plot(xs, ys, "o-", color="#1f77b4")
    ax.set_xlabel("required cline strength"); ax.set_ylabel("P(neutral | A_ε)")
    ax.set_ylim(0, max(0.2, (res.p_neutral_by_strength[0][1] if res.p_neutral_by_strength else 0.2) * 1.2))
    ax.set_title("(A) Stronger cline ⇒ neutral excluded")

    ax = axes[1]
    ax.bar(["A_ε", f"+ replicate\n({res.truth})"], [res.p_neutral, res.p_neutral_after],
           color=["#9aa0a6", "#d62728"])
    ax.set_ylabel("P(neutral)")
    ax.set_title(f"(B) Replicate transect resolves\nselection vs drift")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Neutral-vs-adaptive unifying-principle Tier-A example.")
    p.add_argument("--truth", default="thermal", choices=["thermal", "seasonal", "neutral"])
    p.add_argument("--n-attempts", type=int, default=80000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_neutral_adaptive(truth=args.truth, n_attempts=args.n_attempts, seed=args.seed)
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
