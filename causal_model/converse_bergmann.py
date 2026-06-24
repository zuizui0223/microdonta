"""Discovery-style Tier-A example: a CONVERSE ecogeographic rule is cryptic.

What is genuinely found here (not a re-derivation of textbook knowledge)
-----------------------------------------------------------------------
The Bergmann examples show RACH recovering a *known* confound. This one produces
a result that contradicts the naive sign-reasoning an ecologist would apply, and
RACH gets it right where intuition gets it wrong.

The pattern is the *converse* Bergmann cline: body size *decreases* with coldness
(common in ectotherms / insects). The naive inference is immediate and wrong:

    "size is smaller where colder  ⟹  selection favours small bodies in the cold
     (or large bodies in the warm); cold-favouring heat-conservation selection is
     therefore ruled out."

RACH, run on a fitness model that also contains a growing-season developmental
constraint (a short cold-climate season caps attainable size), finds three things
that the naive reading misses:

  1. **A converse cline needs no size selection at all.** A pure developmental
     season-length constraint reproduces it, and is statistically confounded with
     genuinely adaptive warm-favouring selection — the cline alone cannot tell an
     adaptive story from a developmental one.

  2. **A converse cline does NOT exclude heat-conservation (cold-favouring)
     selection.** When the season constraint binds, it *masks* selection for large
     size in the cold: the realised cline is converse even though selection
     favours the opposite. So cold-favouring selection stays admissible.

  3. **The two rule directions are not symmetric.** A *Bergmann* cline uniquely
     identifies cold-favouring selection (nothing else makes bodies larger in the
     cold), so it is fully resolved; the *converse* cline is a three-way confound.
     The diagnosticity of an ecogeographic rule depends on its direction.

How the constraint flips the cline (the mechanism of the surprise)
------------------------------------------------------------------
Desired (selective optimum) size ``D(T)`` rises with coldness ``T`` under
cold_selection. Realised size is capped by the season: ``z = min(D(T), cap(T))``
with ``cap(T) = cmin + kappa·(1−T)`` shrinking as it gets colder. When the cap
binds in the cold, realised size *falls* with coldness — converse — while
selection still points the other way.

The resolving observation (and why it is real)
-----------------------------------------------
Rear all populations under a common, *extended* season (a common-garden that
removes the developmental cap), and look at the size cline that remains. This is
exactly the experiment used to test the temperature–size rule, and RACH's NOV
recovers it. Its three outcomes cleanly separate the three explanations:

    cline still converse  → warm-favouring selection (adaptive);
    cline flat            → it was the developmental constraint (non-adaptive);
    cline FLIPS to Bergmann → cold-favouring selection was there all along,
                              cryptic, unmasked by removing the constraint.

That flip — a converse field cline becoming a Bergmann cline in the common garden
— is the concrete, testable, non-obvious prediction RACH yields.

Usage
-----
    python -m causal_model.converse_bergmann --truth cold_masked
    python -m causal_model.converse_bergmann --figure outputs/mee/converse_bergmann.png
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field

_SITES = (0.0, 0.25, 0.5, 0.75, 1.0)        # T = coldness (1 = coldest)
_MECHS = ("cold_selection", "warm_selection", "season_constraint")

_BASE_LO, _BASE_HI = 0.3, 0.9              # baseline desired size (warm-end size)
_COST_LO, _COST_HI = 0.5, 1.5
_B_LO, _B_HI = 0.5, 1.4
_KAPPA_LO, _KAPPA_HI = 0.3, 1.0
_CMIN_LO, _CMIN_HI = 0.0, 0.1
_RULE_TOL = 0.12                            # clearly above the pairwise "≈" band (0.06)


def _switches():
    from causal_model.switch_inference import BiologicalSwitch
    desc = {
        "cold_selection": "Heat conservation: selection favours large body size where colder (Bergmann driver).",
        "warm_selection": "Predation escape / productivity: selection favours large body size where warmer.",
        "season_constraint": "Short cold-climate growing season caps attainable size (developmental, non-adaptive).",
    }
    return [BiologicalSwitch(name=m, pathway_key=m, biological_question="", description=desc[m])
            for m in _MECHS]


def _desired(s: dict, p: dict, T: float) -> float:
    """Selective-optimum ('desired') size before any developmental cap."""
    D = p["base"]
    if s["cold_selection"]:
        D += p["b_cold"] * T
    if s["warm_selection"]:
        D += p["b_warm"] * (1.0 - T)
    return D / (2.0 * p["cost"])


def _realised(s: dict, p: dict, T: float) -> float:
    """Realised wild size: desired size capped by the growing-season constraint."""
    z = _desired(s, p, T)
    if s["season_constraint"]:
        z = min(z, p["cmin"] + p["kappa"] * (1.0 - T))
    return z


def _params(rng: random.Random) -> dict:
    return {
        "base": rng.uniform(_BASE_LO, _BASE_HI),
        "cost": rng.uniform(_COST_LO, _COST_HI),
        "b_cold": rng.uniform(_B_LO, _B_HI),
        "b_warm": rng.uniform(_B_LO, _B_HI),
        "kappa": rng.uniform(_KAPPA_LO, _KAPPA_HI),
        "cmin": rng.uniform(_CMIN_LO, _CMIN_HI),
    }


def _abc_accept(n_attempts: int, seed: int) -> list[dict]:
    """Accept randomised landscapes whose realised wild cline is *converse*
    Bergmann (body size decreases with coldness). Each draw also stores the
    common-garden (constraint-removed) size at the warm and cold extremes.
    """
    rng = random.Random(seed)
    accepted: list[dict] = []
    for _ in range(n_attempts):
        s = {m: (rng.random() < 0.5) for m in _MECHS}
        p = _params(rng)
        z = [_realised(s, p, T) for T in _SITES]
        # observed rule: realised size strictly DECREASES from warm to cold
        if not (z[-1] - z[0] < -_RULE_TOL and z[2] < z[0]):
            continue
        row = dict(s)
        for i, T in enumerate(_SITES):
            row[f"z{i}"] = round(z[i], 4)
        # common garden: remove the season cap, keep selection; cline at extremes
        row["warm_cgsize"] = round(_desired(s, p, 0.0), 4)
        row["cold_cgsize"] = round(_desired(s, p, 1.0), 4)
        accepted.append(row)
    return accepted


# ---------------------------------------------------------------------------
# Candidate observation (NOV): the extended-season common garden
# ---------------------------------------------------------------------------

def _candidate_observations():
    from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome

    def _cg(rel: str):
        return [{
            "type": "pairwise_relation", "variable": "cgsize",
            "left_population": "cold", "right_population": "warm", "relation": rel,
        }]

    cg = CandidateObservation(
        name="extended_season_common_garden",
        description="Rear all populations under a common, extended season (removes the developmental cap); read the residual size cline.",
        target_switches=["cold_selection", "warm_selection", "season_constraint"],
        rationale=("Removing the season constraint reveals the underlying selective cline: still "
                   "converse → warm selection; flat → it was the constraint; flips to Bergmann → "
                   "cryptic cold-favouring selection."),
        pattern_type="pairwise_relation",
        outcomes=[
            CandidateOutcome("cg_bergmann", "Common-garden cline FLIPS to Bergmann (cold-favouring selection revealed).",
                             1 / 3, _cg("cold > warm")),
            CandidateOutcome("cg_converse", "Common-garden cline stays converse (warm-favouring selection).",
                             1 / 3, _cg("cold < warm")),
            CandidateOutcome("cg_flat", "Common-garden cline is flat (developmental constraint, not selection).",
                             1 / 3, _cg("cold ~= warm")),
        ],
    )
    return [cg]


def _truth_overrides(truth: str) -> dict[str, str]:
    """Realised common-garden outcome under an assumed generating mechanism."""
    return {"extended_season_common_garden": {
        "cold_masked": "cg_bergmann",      # cold selection masked by the constraint in the wild
        "warm": "cg_converse",
        "constraint": "cg_flat",
    }[truth]}


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class ConverseBergmannResult:
    switch_names: list[str]
    truth: str
    n_accepted: int
    n_attempts: int
    ca_j: dict[str, float]
    R_expl: float
    explanations: list[tuple[frozenset, float]]
    ca_cold_selection: float                       # the headline: NOT ~0 under converse
    nov_ranking: list[tuple[str, float]]
    explanations_after: list[tuple[frozenset, float]] = field(default_factory=list)
    R_expl_after: float = float("nan")
    cold_selection_after: float = float("nan")


def run_converse_bergmann(truth: str = "cold_masked", n_attempts: int = 60000,
                          seed: int = 1) -> ConverseBergmannResult:
    from causal_model.causal_admissibility import rach_summary
    from causal_model.minimal_explanations import minimal_explanations, explanation_nov
    from causal_model.rach_seq import filter_by_outcome

    switches = _switches()
    names = [sw.name for sw in switches]
    acc = _abc_accept(n_attempts, seed)

    summ = rach_summary(acc, switches)
    ca = {r.switch_name: round(r.CA_j, 4) for r in summ.causal_admissibility}
    dec = minimal_explanations(acc, switches)

    cands = _candidate_observations()
    nov = sorted(((c.name, explanation_nov(c, acc, switches)) for c in cands),
                 key=lambda x: -x[1])

    res = ConverseBergmannResult(
        switch_names=names, truth=truth, n_accepted=len(acc), n_attempts=n_attempts,
        ca_j=ca, R_expl=dec.R_expl,
        explanations=[(e.mechanisms, e.mass) for e in dec.explanations],
        ca_cold_selection=ca["cold_selection"], nov_ranking=nov,
    )

    ov = _truth_overrides(truth)
    cand = cands[0]
    oc = next(o for o in cand.outcomes if o.name == ov[cand.name])
    rows = filter_by_outcome(acc, oc.extra_pattern_rows)
    if len(rows) >= 5:
        summ2 = rach_summary(rows, switches)
        dec2 = minimal_explanations(rows, switches)
        res.explanations_after = [(e.mechanisms, e.mass) for e in dec2.explanations]
        res.R_expl_after = dec2.R_expl
        res.cold_selection_after = round(
            next(r.CA_j for r in summ2.causal_admissibility if r.switch_name == "cold_selection"), 4)
    return res


def _fmt(expl) -> str:
    return "  ".join(("{" + ", ".join(sorted(m)) + "}" if m else "{∅}") + f"={mass:.2f}"
                     for m, mass in expl)


def print_report(res: ConverseBergmannResult) -> None:
    print("=" * 74)
    print("Converse Bergmann is cryptic — a discovery-style worked example")
    print("=" * 74)
    print(f"truth = {res.truth}   accepted (converse cline) = {res.n_accepted}/{res.n_attempts}")
    print("(A) On the converse field cline alone (size DECREASES with coldness):")
    print(f"    R_expl = {res.R_expl}   minimal explanations: {_fmt(res.explanations)}")
    print(f"    *** CA(cold_selection) = {res.ca_cold_selection} — NOT ruled out, though the")
    print(f"        naive reading says 'smaller in cold ⇒ no cold-favouring selection'. ***")
    print("(B) NOV (exact EVSI on R_expl):")
    for name, val in res.nov_ranking:
        print(f"      {name:32s} {val:.3f}")
    if res.explanations_after:
        print(f"(C) After the extended-season common garden (truth={res.truth}):")
        print(f"      R_expl {res.R_expl} → {res.R_expl_after}")
        print(f"      CA(cold_selection) {res.ca_cold_selection} → {res.cold_selection_after}")
        print(f"      minimal explanations: {_fmt(res.explanations_after)}")
        if res.truth == "cold_masked":
            print("      → the wild converse cline FLIPS to Bergmann in the common garden:")
            print("        cold-favouring selection was cryptic, masked by the season constraint.")


def make_figure(res: ConverseBergmannResult, path: str) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib unavailable — skipping figure.")
        return None
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.2))

    ax = axes[0]
    labels = ["{" + ", ".join(sorted(m)) + "}" if m else "{∅}" for m, _ in res.explanations]
    short = [l.replace("cold_selection", "cold-sel").replace("warm_selection", "warm-sel")
              .replace("season_constraint", "season-constraint") for l in labels]
    ax.bar(short, [mass for _, mass in res.explanations], color="#1f77b4")
    ax.set_ylim(0, 1); ax.set_ylabel("posterior mass")
    ax.set_title(f"(A) Converse cline — 3-way confound\nCA(cold-selection)={res.ca_cold_selection} (not excluded)")
    ax.tick_params(axis="x", labelrotation=20)

    ax = axes[1]
    if res.explanations_after:
        la = ["{" + ", ".join(sorted(m)) + "}" for m, _ in res.explanations_after]
        sa = [l.replace("cold_selection", "cold-sel").replace("warm_selection", "warm-sel")
               .replace("season_constraint", "season-con") for l in la]
        ax.bar(sa, [mass for _, mass in res.explanations_after], color="#d62728")
    ax.set_ylim(0, 1); ax.set_ylabel("posterior mass")
    ax.set_title(f"(B) After extended-season common garden\n(truth={res.truth}) R_expl={res.R_expl_after}")
    ax.tick_params(axis="x", labelrotation=20)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Converse-Bergmann cryptic-selection Tier-A example.")
    p.add_argument("--truth", default="cold_masked", choices=["cold_masked", "warm", "constraint"])
    p.add_argument("--n-attempts", type=int, default=60000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_converse_bergmann(truth=args.truth, n_attempts=args.n_attempts, seed=args.seed)
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
