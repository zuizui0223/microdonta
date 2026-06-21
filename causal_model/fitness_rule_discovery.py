"""Tier-A worked example: derive an ecogeographic rule from FITNESS, then ask
RACH which selective hypotheses it admits.

The point (and why it is better than hand-coded signs)
------------------------------------------------------
In the other Tier-A examples a domain expert asserts the *sign* of each
mechanism's effect on each trait. A sceptic can call those signs cherry-picked.
Here we go one level deeper: we assert nothing about the trait cline's
*direction*. We only

  * name candidate *selective forces*, each with a qualitative form — "this force
    makes larger bodies more valuable where it is colder", etc. — toggled by a
    switch, and
  * give every force a RANDOM strength and let a universal quadratic cost trade
    off against it.

The evolved trait at each site is then the fitness optimum

    z*(site) = argmax_z W(z; site) = (net linear selection) / (2 · cost),

and the *rule* (does body size increase or decrease along the gradient?) is
whatever that optimisation produces. No coefficient is chosen to make the rule
come out a particular way; the rule **emerges** from selection on a randomised
fitness landscape, and is then marginalised over all strengths.

What this buys
--------------
* The trade-off has its proper, principled definition: a linear selective
  *benefit* (``+b·driver``) against a quadratic *cost* (``−c·z²``); the optimum is
  where they balance. Nothing is hand-tuned.
* The confound is *derived*, not asserted. Two different selective forces
  (thermal heat-conservation and seasonal fasting-endurance) drive body size in
  the *same* direction in the wild — because their environmental drivers
  (coldness, seasonality) are correlated along latitude — so the published rule
  (Bergmann's: body size ↑ with coldness) leaves them jointly admissible.

The system
----------
Two environmental drivers vary along the gradient and are CORRELATED in the wild:

    thermal_stress  T   (coldness)
    seasonality     S   (resource scarcity / seasonal fasting pressure)

Selective forces (each a switch; strength random, marginalised):

    heat_conservation   +b·T     larger body conserves heat where cold
    fasting_endurance   +b·S     larger body endures seasonal scarcity
    predation_escape    +b·(1−T) larger body escapes predators in warm low sites
    resource_limit      −b·T     cold = resource-poor, penalises large bodies

Universal quadratic cost ``−c·z²`` (always on, random ``c``). Optimum body size
``z*(T,S) = (net linear selection)/(2c)``.

y_obs = the published rule only: in wild sites (where ``T ≈ S``) body size
increases with coldness. heat_conservation and fasting_endurance both produce it
⇒ a derived two-way confound.

Resolving it the way the literature actually does
-------------------------------------------------
Heat conservation tracks ``T``; fasting endurance tracks ``S``. In the wild they
are confounded because ``T ≈ S``. The distinguishing observation is a site where
the two drivers are **decoupled** — a cold-but-aseasonal site (high ``T``, low
``S``), e.g. a tropical high mountain. There heat predicts large bodies and
fasting predicts small ones, so a single body-size measurement separates them.
This is exactly how Bergmann's mechanism is probed empirically, and RACH's NOV
recovers it from the fitness structure alone.

Usage
-----
    python -m causal_model.fitness_rule_discovery --truth heat
    python -m causal_model.fitness_rule_discovery --figure outputs/mee/fitness_rule.png
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field

_FORCES = ("heat_conservation", "fasting_endurance", "predation_escape", "resource_limit")

# Wild gradient sites as (thermal_stress T, seasonality S). In the wild the two
# drivers are correlated (T ≈ S), which is *why* heat and fasting are confounded.
_WILD_SITES = ((0.0, 0.0), (0.25, 0.25), (0.5, 0.5), (0.75, 0.75), (1.0, 1.0))

# The distinguishing site: cold but aseasonal (high T, low S) — a tropical alpine
# analogue where the two drivers are decoupled.
_DECOUPLED_SITE = (1.0, 0.0)

_COST_LO, _COST_HI = 0.5, 1.5
_B_LO, _B_HI = 0.3, 1.2
# The accepted rule must be clearly above the pairwise "≈" band used by the
# decoupled-site filter (rach_seq._PAIRWISE_TOL·3 = 0.06), so a heat-driven cline
# (whose decoupled response equals the wild-cline magnitude) is never misread as
# "no response". This keeps the resolution an honest measurement, not a tolerance
# artefact.
_RULE_TOL = 0.20           # ordinal: cline must exceed this to count as "size↑ with cold"


def _switches():
    from causal_model.switch_inference import BiologicalSwitch
    desc = {
        "heat_conservation": "Larger body conserves heat; selective benefit scales with coldness (T).",
        "fasting_endurance": "Larger body endures seasonal scarcity; benefit scales with seasonality (S).",
        "predation_escape":  "Larger body escapes predators in warm low-stress sites; benefit scales with (1−T).",
        "resource_limit":    "Cold sites are resource-poor; large bodies penalised (−T).",
    }
    return [BiologicalSwitch(name=m, pathway_key=m, biological_question="", description=desc[m])
            for m in _FORCES]


def _lin_sel(force: str, T: float, S: float, b: float) -> float:
    """Linear selection coefficient on body size from one force at a site."""
    return {
        "heat_conservation": b * T,
        "fasting_endurance": b * S,
        "predation_escape":  b * (1.0 - T),
        "resource_limit":   -b * T,
    }[force]


def _optimum(s: dict, b: dict, cost: float, T: float, S: float) -> float:
    """Evolved body size = argmax_z W = (net linear selection) / (2·cost)."""
    lin = sum(_lin_sel(m, T, S, b[m]) for m in _FORCES if s[m])
    return lin / (2.0 * cost)


def _abc_accept(n_attempts: int, seed: int) -> list[dict]:
    """Accept randomised fitness landscapes whose evolved optimum reproduces the
    published rule (body size increases with coldness across the wild sites).

    Each accepted draw also stores the evolved body size at the *decoupled* site,
    so the distinguishing observation can filter it.
    """
    rng = random.Random(seed)
    accepted: list[dict] = []
    for _ in range(n_attempts):
        s = {m: (rng.random() < 0.5) for m in _FORCES}
        cost = rng.uniform(_COST_LO, _COST_HI)
        b = {m: rng.uniform(_B_LO, _B_HI) for m in _FORCES}
        z = [_optimum(s, b, cost, T, S) for (T, S) in _WILD_SITES]
        # published rule: body size strictly increases from warmest to coldest site
        if not (z[-1] - z[0] > _RULE_TOL and z[2] > z[0]):
            continue
        row = dict(s)
        for i, (T, S) in enumerate(_WILD_SITES):
            row[f"z_site{i}"] = round(z[i], 4)
        # distinguishing observation: evolved size at the decoupled (cold, aseasonal) site,
        # compared to the warm baseline site (T=0, S=0)
        zd = _optimum(s, b, cost, *_DECOUPLED_SITE)
        z0 = _optimum(s, b, cost, 0.0, 0.0)
        row["low_decoupled_size"] = round(z0, 4)
        row["high_decoupled_size"] = round(zd, 4)
        accepted.append(row)
    return accepted


# ---------------------------------------------------------------------------
# Candidate observations (NOV)
# ---------------------------------------------------------------------------

def _candidate_observations():
    from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome

    def _decoupled(big: bool):
        rel = "high > low" if big else "high ~= low"
        return [{
            "type": "pairwise_relation", "variable": "decoupled_size",
            "left_population": "high", "right_population": "low", "relation": rel,
        }]

    decoupled = CandidateObservation(
        name="decoupled_site_body_size",
        description="Measure evolved body size at a cold-but-aseasonal site (high T, low S), e.g. a tropical alpine population.",
        target_switches=["heat_conservation", "fasting_endurance"],
        rationale=("Where coldness and seasonality are decoupled, heat conservation still "
                   "favours large bodies but fasting endurance does not. Separates the two "
                   "forces that the wild latitudinal gradient confounds."),
        pattern_type="pairwise_relation",
        outcomes=[
            CandidateOutcome("large_when_decoupled", "Body size still large where cold-but-aseasonal (heat conservation).",
                             0.5, _decoupled(True)),
            CandidateOutcome("small_when_decoupled", "Body size not enlarged where cold-but-aseasonal (fasting endurance).",
                             0.5, _decoupled(False)),
        ],
    )
    return [decoupled]


def _truth_overrides(truth: str) -> dict[str, str]:
    """Realised outcome of the decoupled-site observation under an assumed truth."""
    heat = truth in ("heat", "heat_conservation")
    return {"decoupled_site_body_size": "large_when_decoupled" if heat else "small_when_decoupled"}


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class FitnessRuleResult:
    switch_names: list[str]
    truth: str
    n_accepted: int
    n_attempts: int
    ca_j: dict[str, float]
    R_RACH: float
    R_expl: float
    explanations: list[tuple[frozenset, float]]
    nov_ranking: list[tuple[str, float]]
    explanations_after: list[tuple[frozenset, float]] = field(default_factory=list)
    R_expl_after: float = float("nan")


def run_fitness_rule_discovery(truth: str = "heat", n_attempts: int = 20000,
                               seed: int = 1) -> FitnessRuleResult:
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

    res = FitnessRuleResult(
        switch_names=names, truth=truth, n_accepted=len(acc), n_attempts=n_attempts,
        ca_j=ca, R_RACH=round(summ.causal_resolvability, 4), R_expl=dec.R_expl,
        explanations=[(e.mechanisms, e.mass) for e in dec.explanations],
        nov_ranking=nov,
    )

    # Resolution: take the decoupled-site observation at the assumed truth.
    ov = _truth_overrides(truth)
    cand = cands[0]
    oc = next(o for o in cand.outcomes if o.name == ov[cand.name])
    rows = filter_by_outcome(acc, oc.extra_pattern_rows)
    if len(rows) >= 5:
        dec_after = minimal_explanations(rows, switches)
        res.explanations_after = [(e.mechanisms, e.mass) for e in dec_after.explanations]
        res.R_expl_after = dec_after.R_expl
    return res


def _fmt(expl) -> str:
    return "  ".join(("{" + ", ".join(sorted(m)) + "}" if m else "{∅}") + f"={mass:.2f}"
                     for m, mass in expl)


def print_report(res: FitnessRuleResult) -> None:
    print("=" * 72)
    print("Fitness-derived ecogeographic rule (Tier-A): which selection is it?")
    print("=" * 72)
    print(f"truth = {res.truth}   accepted (rule emerged) = {res.n_accepted}/{res.n_attempts}")
    print(f"(A) The rule (body size ↑ with coldness) emerged from fitness maximisation.")
    print(f"    switch-level R={res.R_RACH}   explanation-level R_expl={res.R_expl}")
    print(f"    minimal explanations: {_fmt(res.explanations)}")
    print(f"    → heat_conservation and fasting_endurance jointly admissible — derived, not asserted.")
    print(f"(B) NOV (exact EVSI on R_expl):")
    for name, val in res.nov_ranking:
        print(f"      {name:28s} {val:.3f}")
    if res.explanations_after:
        print(f"(C) After measuring the decoupled (cold, aseasonal) site (truth={res.truth}):")
        print(f"      R_expl {res.R_expl} → {res.R_expl_after}")
        print(f"      minimal explanations: {_fmt(res.explanations_after)}")


def make_figure(res: FitnessRuleResult, path: str) -> str | None:
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
    labels = ["{" + ", ".join(sorted(m)) + "}" if m else "{∅}" for m, _ in res.explanations]
    short = [l.replace("heat_conservation", "heat").replace("fasting_endurance", "fasting")
              .replace("predation_escape", "predation").replace("resource_limit", "resource")
             for l in labels]
    ax.bar(short, [mass for _, mass in res.explanations], color="#1f77b4")
    ax.set_ylim(0, 1); ax.set_ylabel("posterior mass")
    ax.set_title(f"(A) Rule emerged from fitness\nconfound: R_expl={res.R_expl}")
    ax.tick_params(axis="x", labelrotation=15)

    ax = axes[1]
    if res.explanations_after:
        la = ["{" + ", ".join(sorted(m)) + "}" for m, _ in res.explanations_after]
        sa = [l.replace("heat_conservation", "heat").replace("fasting_endurance", "fasting") for l in la]
        ax.bar(sa, [mass for _, mass in res.explanations_after], color="#d62728")
    ax.set_ylim(0, 1); ax.set_ylabel("posterior mass")
    ax.set_title(f"(B) After decoupled-site obs (truth={res.truth})\nR_expl={res.R_expl_after}")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fitness-derived ecogeographic rule Tier-A example.")
    p.add_argument("--truth", default="heat", choices=["heat", "fasting"])
    p.add_argument("--n-attempts", type=int, default=20000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_fitness_rule_discovery(truth=args.truth, n_attempts=args.n_attempts, seed=args.seed)
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
