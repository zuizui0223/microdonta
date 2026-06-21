"""Tier-A worked example: is a trait cline genetic adaptation or plasticity?

Why this example
----------------
This is the single most widely understood causal degeneracy in ecology, and it
makes the RACH primitives — *constraint*, *trade-off*, *confound*, *NOV* —
concrete in terms every ecologist already knows.

A quantitative trait (metal tolerance, body size, flowering time, …) is observed
to track an environmental gradient in the wild. That field cline is uncontested.
Its *mechanism* is not — at least three processes each produce the same field
cline and are therefore confounded on it:

    genetic_adaptation     local genetic differentiation under selection;
    phenotypic_plasticity  one genotype expressing different phenotypes;
    maternal_effects       transgenerational (maternal) environmental carry-over.

What "ecological constraint" and "trade-off" mean here (read this)
-----------------------------------------------------------------
In a Tier-A RACH model you do NOT commit to effect *magnitudes*. The ecological
knowledge you commit to is only:

  * a **constraint** = a *sign / feasibility* statement a field biologist can
    defend qualitatively — "mechanism M makes observable O go up / down", or
    "these mechanisms are mutually exclusive / at least one must hold". It is the
    sign structure below (``_SIGNS``), nothing more. No coefficient is tuned.

  * a **trade-off** = a single mechanism that pushes two observables in
    *opposite* (or otherwise costly) directions. Here genetic_adaptation does not
    only raise tolerance along the cline; the locally adapted genotype also
    *underperforms in the benign environment* (``benign_site_cost``) — the classic
    cost of adaptation (Bradshaw 1991; Antonovics et al. 1971). The trade-off is
    represented simply by giving that mechanism a second, oppositely-valued
    observable; you never hand-pick how big the cost is.

This is the whole point of Tier A: the constraint is the *direction*, the
trade-off is a *second directional consequence*, and every magnitude is drawn at
random and integrated out. The old Campanula ``parameter_constraints`` grammar
(C1–C5 over ``selfing_benefit``/``guide_cost``/…) constrained *magnitudes* and
belongs to the deprecated Tier-B ABM; it plays no role here.

The observables
---------------
    field_cline          trait tracks the gradient in the wild      (the y_obs)
    common_garden_diff   population difference PERSISTS when grown in a common
                         garden (F1)
    second_gen_diff      difference persists into the F2 (second garden generation)
    benign_site_cost     adapted genotype underperforms in the benign environment

Sign structure (the only thing asserted):

    genetic_adaptation    field_cline+ , common_garden_diff+ , second_gen_diff+ , benign_site_cost+
    phenotypic_plasticity field_cline+
    maternal_effects      field_cline+ , common_garden_diff+

The confound and its resolution
-------------------------------
y_obs is only ``field_cline+``. All three mechanisms produce it, so the minimal
sufficient explanations are ``{genetic}``, ``{plastic}``, ``{maternal}`` — a
three-way disjunction with high degeneracy.

The resolving observations are exactly the textbook ones, and RACH's NOV recovers
their ordering from the structure alone:

  * a **common garden** separates plasticity (difference vanishes) from
    {genetic, maternal} (difference persists) — the single most informative step;
  * a **second-generation common garden** then separates maternal carry-over
    (gone by F2) from genetic adaptation (persists);
  * measuring the **benign-site cost** (the trade-off) independently confirms
    genetic adaptation.

Because these are *observables*, not direct reads of the latent mechanism, the
explanation-level resolvability ``R_expl`` goes to 1 honestly — no idealised
switch-readout assay is required.

Usage
-----
    python -m causal_model.adaptation_plasticity --truth genetic
    python -m causal_model.adaptation_plasticity --figure outputs/mee/adapt_plast.png
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field

_MECHANISMS = ("genetic_adaptation", "phenotypic_plasticity", "maternal_effects")
_OBSERVABLES = ("field_cline", "common_garden_diff", "second_gen_diff", "benign_site_cost")

#: The ecological constraint: the SIGN of each mechanism's effect on each
#: observable. Magnitudes are random per draw and marginalised out.
_SIGNS: dict[str, dict[str, int]] = {
    "genetic_adaptation":    {"field_cline": +1, "common_garden_diff": +1,
                              "second_gen_diff": +1, "benign_site_cost": +1},
    "phenotypic_plasticity": {"field_cline": +1},
    "maternal_effects":      {"field_cline": +1, "common_garden_diff": +1},
}

_MAG_LO, _MAG_HI = 0.30, 0.80
_TOL = 0.05               # ordinal: |net effect| must exceed this to count as present
_BASE = 0.50             # baseline ("low" pseudo-population) value


def _switches():
    from causal_model.switch_inference import BiologicalSwitch
    desc = {
        "genetic_adaptation": "Local genetic differentiation under selection (heritable cline).",
        "phenotypic_plasticity": "One genotype, environment-dependent expression (no differentiation).",
        "maternal_effects": "Transgenerational maternal environmental carry-over.",
    }
    return [BiologicalSwitch(name=m, pathway_key=m, biological_question="", description=desc[m])
            for m in _MECHANISMS]


def _net(s: dict, mag: dict) -> dict[str, float]:
    out = {o: 0.0 for o in _OBSERVABLES}
    for m in _MECHANISMS:
        if not s[m]:
            continue
        for o, sign in _SIGNS[m].items():
            out[o] += sign * mag[(m, o)]
    return out


def _abc_accept(n_attempts: int, seed: int) -> list[dict]:
    """Accept draws reproducing the published field cline (trait tracks gradient).

    Each accepted draw stores, for every observable, a ``low_*`` / ``high_*``
    pseudo-population pair so the candidate observations (common garden, etc.)
    can filter it by a directional relation — exactly as a real study compares
    source populations.
    """
    rng = random.Random(seed)
    accepted: list[dict] = []
    for _ in range(n_attempts):
        s = {m: (rng.random() < 0.5) for m in _MECHANISMS}
        mag = {(m, o): rng.uniform(_MAG_LO, _MAG_HI)
               for m in _MECHANISMS for o in _SIGNS[m]}
        net = _net(s, mag)
        if not (net["field_cline"] > _TOL):           # observed field cline present
            continue
        row = dict(s)
        for o in _OBSERVABLES:
            row[f"low_{o}"] = round(_BASE, 4)
            row[f"high_{o}"] = round(_BASE + net[o], 4)
            row[f"net_{o}"] = round(net[o], 4)
        accepted.append(row)
    return accepted


# ---------------------------------------------------------------------------
# Candidate observations (NOV)
# ---------------------------------------------------------------------------

def _candidate_observations():
    from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome

    def _persists(obs: str, present: bool):
        rel = "high > low" if present else "high ~= low"
        return [{
            "type": "pairwise_relation", "variable": obs,
            "left_population": "high", "right_population": "low", "relation": rel,
        }]

    common_garden = CandidateObservation(
        name="common_garden",
        description="Grow source populations in a common environment; test if the trait difference persists (F1).",
        target_switches=["phenotypic_plasticity", "genetic_adaptation", "maternal_effects"],
        rationale="Plasticity vanishes in a common garden; genetic & maternal differences persist. Separates plasticity from the rest.",
        pattern_type="pairwise_relation",
        outcomes=[
            CandidateOutcome("cg_persists", "Difference persists in common garden.", 0.5,
                             _persists("common_garden_diff", True)),
            CandidateOutcome("cg_vanishes", "Difference vanishes (plasticity).", 0.5,
                             _persists("common_garden_diff", False)),
        ],
    )
    second_gen = CandidateObservation(
        name="second_gen_common_garden",
        description="Raise a second common-garden generation (F2); test if the difference still persists.",
        target_switches=["maternal_effects", "genetic_adaptation"],
        rationale="Maternal carry-over decays by F2; genetic differences persist. Separates maternal effects from genetic adaptation.",
        pattern_type="pairwise_relation",
        outcomes=[
            CandidateOutcome("f2_persists", "Difference persists to F2 (genetic).", 0.5,
                             _persists("second_gen_diff", True)),
            CandidateOutcome("f2_vanishes", "Difference gone by F2 (maternal).", 0.5,
                             _persists("second_gen_diff", False)),
        ],
    )
    benign_cost = CandidateObservation(
        name="benign_site_cost_assay",
        description="Measure the adapted genotype's performance in the benign environment (cost of adaptation).",
        target_switches=["genetic_adaptation"],
        rationale="Only genetic adaptation incurs the trade-off cost at the benign site. Confirms genetic adaptation.",
        pattern_type="pairwise_relation",
        outcomes=[
            CandidateOutcome("cost_present", "Adapted genotype underperforms at benign site.", 0.5,
                             _persists("benign_site_cost", True)),
            CandidateOutcome("cost_absent", "No benign-site cost.", 0.5,
                             _persists("benign_site_cost", False)),
        ],
    )
    return [common_garden, second_gen, benign_cost]


def _truth_overrides(truth: str) -> dict[str, str]:
    """Realised outcome of every candidate under an assumed latent truth."""
    genetic = truth in ("genetic", "genetic_adaptation")
    plastic = truth in ("plastic", "phenotypic_plasticity")
    maternal = truth in ("maternal", "maternal_effects")
    cg_persist = genetic or maternal           # plasticity vanishes; others persist (F1)
    f2_persist = genetic                        # only genetic persists to F2
    cost = genetic                              # only genetic pays the benign-site cost
    return {
        "common_garden": "cg_persists" if cg_persist else "cg_vanishes",
        "second_gen_common_garden": "f2_persists" if f2_persist else "f2_vanishes",
        "benign_site_cost_assay": "cost_present" if cost else "cost_absent",
    }


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class AdaptationPlasticityResult:
    switch_names: list[str]
    truth: str
    n_accepted: int
    ca_j: dict[str, float]
    D_RACH: float
    R_RACH: float
    R_expl: float
    explanations: list[tuple[frozenset, float]]
    nov_ranking: list[tuple[str, float]]            # (candidate, EVSI on R_expl)
    # sequential resolution: explanation set + R_expl after each cumulative step
    seq_steps: list[tuple[str, list[tuple[frozenset, float]], float]] = field(default_factory=list)
    R_expl_after: float = float("nan")


def run_adaptation_plasticity(truth: str = "genetic", n_attempts: int = 6000,
                              seed: int = 1) -> AdaptationPlasticityResult:
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
    # NOV uses the exact preposterior EVSI on explanation-level resolvability.
    nov = sorted(((c.name, explanation_nov(c, acc, switches)) for c in cands),
                 key=lambda x: -x[1])

    res = AdaptationPlasticityResult(
        switch_names=names, truth=truth, n_accepted=len(acc), ca_j=ca,
        D_RACH=round(summ.causal_degeneracy, 4),
        R_RACH=round(summ.causal_resolvability, 4),
        R_expl=dec.R_expl,
        explanations=[(e.mechanisms, e.mass) for e in dec.explanations],
        nov_ranking=nov,
    )

    # Sequential resolution: take observations in NOV order, accumulating the
    # cheap A_ε filter, and record how the minimal explanations collapse.
    ov = _truth_overrides(truth)
    by_name = {c.name: c for c in cands}
    rows = acc
    for cand_name, _ in nov:
        cand = by_name[cand_name]
        oc = next(o for o in cand.outcomes if o.name == ov[cand_name])
        rows = filter_by_outcome(rows, oc.extra_pattern_rows)
        if len(rows) < 5:
            break
        d = minimal_explanations(rows, switches)
        res.seq_steps.append((cand_name, [(e.mechanisms, e.mass) for e in d.explanations], d.R_expl))
    if res.seq_steps:
        res.R_expl_after = res.seq_steps[-1][2]
    return res


def _fmt_expl(expl) -> str:
    return "  ".join(("{" + ", ".join(sorted(m)) + "}" if m else "{∅}") + f"={mass:.2f}"
                     for m, mass in expl)


def print_report(res: AdaptationPlasticityResult) -> None:
    print("=" * 72)
    print("Adaptation vs. plasticity vs. maternal effects (Tier-A worked example)")
    print("=" * 72)
    print(f"truth = {res.truth}   n_accepted = {res.n_accepted}")
    print(f"(A) On the field cline alone (the only y_obs):")
    print(f"    switch-level D={res.D_RACH}/3  R={res.R_RACH}")
    print(f"    explanation-level R_expl={res.R_expl}")
    print(f"    minimal explanations: {_fmt_expl(res.explanations)}")
    print(f"    → a three-way confound: the cline alone cannot say which process.")
    print(f"(B) NOV (exact EVSI on R_expl):")
    for name, val in res.nov_ranking:
        print(f"      {name:28s} {val:.3f}")
    print(f"(C) Sequential resolution (taking observations in NOV order, truth={res.truth}):")
    for cand_name, expl, r in res.seq_steps:
        print(f"      + {cand_name:26s} R_expl={r:.3f}   {_fmt_expl(expl)}")


def make_figure(res: AdaptationPlasticityResult, path: str) -> str | None:
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

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))

    # Panel A: minimal-explanation masses before (the 3-way confound)
    ax = axes[0]
    labels = ["{" + ", ".join(sorted(m)) + "}" if m else "{∅}" for m, _ in res.explanations]
    masses = [mass for _, mass in res.explanations]
    short = [l.replace("genetic_adaptation", "genetic")
              .replace("phenotypic_plasticity", "plastic")
              .replace("maternal_effects", "maternal") for l in labels]
    ax.bar(short, masses, color="#1f77b4")
    ax.set_ylim(0, 1); ax.set_ylabel("posterior mass")
    ax.set_title(f"(A) Field cline only — 3-way confound\nR_expl={res.R_expl}")
    ax.tick_params(axis="x", labelrotation=20)

    # Panel B: R_expl rising as observations are added in NOV order
    ax = axes[1]
    xs = ["cline\nonly"] + [c.replace("_", "\n") for c, _, _ in res.seq_steps]
    ys = [res.R_expl] + [r for _, _, r in res.seq_steps]
    ax.plot(range(len(xs)), ys, "o-", color="#d62728")
    ax.set_xticks(range(len(xs))); ax.set_xticklabels(xs, fontsize=8)
    ax.set_ylim(0, 1.05); ax.set_ylabel("R_expl")
    ax.set_title(f"(B) Resolution in NOV order (truth={res.truth})")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Adaptation vs. plasticity Tier-A worked example.")
    p.add_argument("--truth", default="genetic",
                   choices=["genetic", "plastic", "maternal"])
    p.add_argument("--n-attempts", type=int, default=6000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_adaptation_plasticity(truth=args.truth, n_attempts=args.n_attempts, seed=args.seed)
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
