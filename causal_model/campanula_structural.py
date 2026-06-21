"""Tier-A (validated) worked example: the Campanula isolation cline.

This is the *publication-grade* version of the Campanula example. Unlike the
phenomenological model in ``examples/campanula_izu`` — which hand-codes effect
magnitudes (``guide += w·1.30·bombus·…``) and is therefore Tier B (illustrative,
conditional on those numbers) — this module commits ONLY to the *directional
structure* of the competing hypotheses and randomises every magnitude, then
marginalises it out (see ``causal_model.simulator``: TIER_VALIDATED). The
accepted region therefore reflects only the confound logic that a domain expert
can defend qualitatively, not any tuned coefficient.

The biological hypotheses (signs only)
--------------------------------------
Along the mainland→island isolation gradient (Bombus declines, Ne declines):

    S1 guide_attracts_bombus    Bombus loss removes selection for nectar guides
                                ⇒ guide DECLINES with isolation.
    S2 selfing_syndrome         Reproductive-assurance selfing syndrome
                                ⇒ selfing UP, flower size DOWN, herkogamy DOWN.
                                (does NOT itself drive the nectar guide.)
    S3 island_common_cause      Isolation is a single upstream cause shifting
                                everything ⇒ selfing UP, flower DOWN, herkogamy
                                DOWN, guide DOWN, neutral diversity DOWN.
    S5 halictid_substitution    Small pollinators compensate ⇒ SUPPRESSES the
                                selfing increase.

Only the signs above are asserted. Each active mechanism's effect on each trait
gets an independent random positive magnitude per draw, which is then integrated
out by ABC.

The confound it exposes (the whole point)
-----------------------------------------
The published, source-confirmed ordinal pattern is only ``selfing ↑`` and
``flower size ↓`` along the cline. BOTH S2 and S3 produce exactly that, so on the
published pattern alone they are jointly admissible — a disjunction confound
(``at least one of S2, S3``), with high degeneracy and low resolvability. This is
the real Campanula question: is guide/flower change a selfing-syndrome (S2) or an
isolation-common-cause (S3) signature?

What separates them: the nectar-guide cline. S3 drives the guide (and neutral
diversity); S2 does not. So measuring the guide gradient — the highest-NOV
observation — separates S2 from S3 *using only the directional structure*. No
field magnitudes are required for this conclusion; field data later upgrade the
ordinal y_obs to quantitative (see the §4.2 measurement table).

Usage
-----
    python -m causal_model.campanula_structural --figure outputs/mee/campanula_structural.png
    python -m causal_model.campanula_structural --truth S2
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field

# Mechanisms (named hypotheses) and the SIGN of each mechanism's effect on each
# trait's cline slope along increasing isolation. Magnitudes are random per draw.
_MECHANISMS = ("guide_attracts_bombus", "selfing_syndrome",
               "island_common_cause", "halictid_substitution")
_TRAITS = ("nectar_guide", "selfing_rate", "flower_size", "herkogamy", "neutral_diversity")

_SIGNS: dict[str, dict[str, int]] = {
    "guide_attracts_bombus": {"nectar_guide": -1},
    "selfing_syndrome":      {"selfing_rate": +1, "flower_size": -1, "herkogamy": -1},
    "island_common_cause":   {"selfing_rate": +1, "flower_size": -1, "herkogamy": -1,
                              "nectar_guide": -1, "neutral_diversity": -1},
    "halictid_substitution": {"selfing_rate": -1},
}

_MAG_LO, _MAG_HI = 0.30, 0.80
_SLOPE_TOL = 0.05          # ordinal: |net slope| must exceed this to count as directional
_BASE = 0.50               # baseline trait value at the mainland end
_SIG_TOL = 0.10            # tolerance on a mechanism-signature assay

# the two NOV-relevant cline endpoints (most-connected vs most-isolated)
_NEAR, _FAR = "mainland", "Hachijo"


def _switches():
    from causal_model.switch_inference import BiologicalSwitch
    desc = {
        "guide_attracts_bombus": "S1: Bombus loss removes selection for nectar guides.",
        "selfing_syndrome": "S2: reproductive-assurance selfing syndrome.",
        "island_common_cause": "S3: isolation as a single upstream common cause.",
        "halictid_substitution": "S5: small pollinators compensate, suppressing selfing.",
    }
    return [BiologicalSwitch(name=m, pathway_key=m, biological_question="", description=desc[m])
            for m in _MECHANISMS]


def _net_slopes(s: dict, mag: dict) -> dict[str, float]:
    """Net cline slope per trait = Σ over active mechanisms of sign·magnitude."""
    out = {t: 0.0 for t in _TRAITS}
    for m in _MECHANISMS:
        if not s[m]:
            continue
        for t, sign in _SIGNS[m].items():
            out[t] += sign * mag[(m, t)]
    return out


def _abc_accept(n_attempts: int, seed: int) -> list[dict]:
    """Accept draws reproducing the published ordinal pattern (selfing↑, flower↓).

    Each accepted draw stores: mechanism booleans; the two cline endpoints
    ``{near|far}_{trait}`` for every trait (so gradient/pairwise NOV candidates
    can filter it); and per-mechanism signature columns for the ideal assays.
    """
    rng = random.Random(seed)
    accepted: list[dict] = []
    for _ in range(n_attempts):
        s = {m: (rng.random() < 0.5) for m in _MECHANISMS}
        mag = {(m, t): rng.uniform(_MAG_LO, _MAG_HI)
               for m in _MECHANISMS for t in _SIGNS[m]}
        slope = _net_slopes(s, mag)
        # observed published ordinal pattern: selfing increases, flower declines
        if not (slope["selfing_rate"] > _SLOPE_TOL and slope["flower_size"] < -_SLOPE_TOL):
            continue
        row = dict(s)
        for t in _TRAITS:
            row[f"{_NEAR}_{t}"] = round(_BASE, 4)
            row[f"{_FAR}_{t}"] = round(_BASE + slope[t], 4)
            row[f"slope_{t}"] = round(slope[t], 4)
        for m in ("guide_attracts_bombus", "selfing_syndrome", "island_common_cause"):
            row[f"sig_{m}"] = 1.0 if s[m] else 0.0
        accepted.append(row)
    return accepted


# ---------------------------------------------------------------------------
# Candidate observations (NOV)
# ---------------------------------------------------------------------------

def _candidate_observations():
    from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome

    def _grad(var: str, declines: bool):
        rel = f"{_NEAR} > {_FAR}" if declines else f"{_NEAR} ~= {_FAR}"
        return [{
            "type": "pairwise_relation", "variable": var,
            "left_population": _NEAR, "right_population": _FAR, "relation": rel,
        }]

    def _assay(mech: str, present: bool):
        return [{
            "type": "absolute_summary", "variable": f"{mech}", "population": "sig",
            "observed_value": f"{1.0 if present else 0.0:.4f}", "scale": f"{_SIG_TOL/2:.4f}",
        }]

    guide = CandidateObservation(
        name="nectar_guide_gradient",
        description="Quantify the per-population nectar-guide cline (UV reflectance / guide area).",
        target_switches=["guide_attracts_bombus", "island_common_cause"],
        rationale="Only S1/S3 drive the guide; S2 does not — the cheap gradient that separates S2 from S3.",
        pattern_type="pairwise_relation",
        outcomes=[
            CandidateOutcome("guide_declines", "Guide declines with isolation.", 0.5, _grad("nectar_guide", True)),
            CandidateOutcome("guide_flat", "Guide flat across the cline.", 0.5, _grad("nectar_guide", False)),
        ],
    )
    he = CandidateObservation(
        name="neutral_diversity_gradient",
        description="Neutral heterozygosity He cline (microsatellite/SNP).",
        target_switches=["island_common_cause"],
        rationale="Only S3 (common cause via reduced Ne) drives neutral diversity — isolates S3.",
        pattern_type="pairwise_relation",
        outcomes=[
            CandidateOutcome("He_declines", "He declines with isolation.", 0.5, _grad("neutral_diversity", True)),
            CandidateOutcome("He_flat", "He flat across the cline.", 0.5, _grad("neutral_diversity", False)),
        ],
    )
    # ideal mechanism-specific assays (bagging/RA for S2; demographic signature for S3)
    bagging = CandidateObservation(
        name="bagging_RA_assay",
        description="Bagged vs open seed-set (reproductive-assurance) signature of S2.",
        target_switches=["selfing_syndrome"],
        rationale="A reproductive-assurance signature present iff the selfing syndrome (S2) operates.",
        pattern_type="absolute_summary",
        outcomes=[
            CandidateOutcome("S2_present", "RA signature present.", 0.5, _assay("selfing_syndrome", True)),
            CandidateOutcome("S2_absent", "No RA signature.", 0.5, _assay("selfing_syndrome", False)),
        ],
    )
    return [guide, he, bagging]


def _truth_overrides(truth: str) -> dict[str, str]:
    """Realised outcomes of every candidate under an assumed latent truth.

    truth "S3": island common cause ON ⇒ guide & He decline, S2 absent.
    truth "S2": selfing syndrome ON   ⇒ guide & He flat,    S2 present.
    """
    s3 = truth in ("S3", "island_common_cause", "both")
    s2 = truth in ("S2", "selfing_syndrome", "both")
    return {
        "nectar_guide_gradient": "guide_declines" if s3 else "guide_flat",
        "neutral_diversity_gradient": "He_declines" if s3 else "He_flat",
        "bagging_RA_assay": "S2_present" if s2 else "S2_absent",
    }


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class CampanulaResult:
    switch_names: list[str]
    truth: str
    n_accepted: int
    ca_j: dict[str, float]
    D_RACH: float
    R_RACH: float
    confound_edge: str
    nov_ranking: list[tuple[str, float]]      # (candidate, expected edge cuts)
    ca_j_after: dict[str, float] = field(default_factory=dict)
    D_after: float = float("nan")
    R_after: float = float("nan")
    seq_trace: str = ""


def run_campanula_structural(truth: str = "S3", n_attempts: int = 4000,
                             seed: int = 1) -> CampanulaResult:
    from causal_model.causal_admissibility import rach_summary, causal_resolvability
    from causal_model.mechanism_equivalence import mechanism_equivalence_structure
    from causal_model.rach_seq import rach_seq, filter_by_outcome, expected_edge_cuts

    switches = _switches()
    names = [sw.name for sw in switches]
    acc = _abc_accept(n_attempts, seed)

    summ = rach_summary(acc, switches)
    ca = {r.switch_name: round(r.CA_j, 4) for r in summ.causal_admissibility}
    D0, R0 = round(summ.causal_degeneracy, 4), round(summ.causal_resolvability, 4)

    struct = mechanism_equivalence_structure(acc, switches)
    edge = struct.edges[0].describe() if struct.edges else "none"

    cands = _candidate_observations()
    nov = sorted(((c.name, expected_edge_cuts(c, acc, switches, struct, min_sub_size=10))
                  for c in cands), key=lambda x: -x[1])

    res = CampanulaResult(
        switch_names=names, truth=truth, n_accepted=len(acc), ca_j=ca,
        D_RACH=D0, R_RACH=R0, confound_edge=edge, nov_ranking=nov,
    )

    # RACH-SEQ greedy loop
    seq = rach_seq(acc, switches, cands, budget=3, min_sub_size=10, seed=seed,
                   outcome_overrides=_truth_overrides(truth))
    res.seq_trace = seq.describe()

    # Resolution: apply the full realised panel (cheap guide+He gradients AND the
    # S2 assay) at the assumed truth.
    rows = acc
    ov = _truth_overrides(truth)
    for cand in cands:
        oc = next(o for o in cand.outcomes if o.name == ov[cand.name])
        rows = filter_by_outcome(rows, oc.extra_pattern_rows)
    if len(rows) >= 5:
        summ2 = rach_summary(rows, switches)
        res.ca_j_after = {r.switch_name: round(r.CA_j, 4) for r in summ2.causal_admissibility}
        res.D_after = round(summ2.causal_degeneracy, 4)
        res.R_after = round(causal_resolvability(rows, switches), 4)
    return res


def print_report(res: CampanulaResult) -> None:
    print("=" * 70)
    print("Campanula isolation-cline worked example (Tier A: structural, magnitude-free)")
    print("=" * 70)
    print(f"truth = {res.truth}   n_accepted = {res.n_accepted}")
    print(f"(A) RACH on published pattern (selfing↑, flower↓ only):")
    print(f"    D_RACH = {res.D_RACH}/4   R_RACH = {res.R_RACH}")
    for n in res.switch_names:
        print(f"      CA_j[{n:24s}] = {res.ca_j[n]}")
    print(f"    confounding edge: {res.confound_edge}")
    print(f"    → S2 (selfing syndrome) and S3 (island common cause) jointly")
    print(f"      admissible on the published pattern alone — the Campanula confound.")
    print(f"(B) NOV ranking (expected confounding-edge cuts):")
    for name, val in res.nov_ranking:
        print(f"      {name:28s} {val:.3f}")
    if res.ca_j_after:
        print(f"(C) Resolution at truth={res.truth} (guide+He gradients + S2 assay):")
        print(f"      D {res.D_RACH} → {res.D_after}   R {res.R_RACH} → {res.R_after}")
        for n in ("selfing_syndrome", "island_common_cause"):
            print(f"      CA_j[{n:24s}] {res.ca_j[n]} → {res.ca_j_after[n]}")
    print("-" * 70)
    print("RACH-SEQ trace:")
    print(res.seq_trace)


def make_figure(res: CampanulaResult, path: str) -> str | None:
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
    short = {"guide_attracts_bombus": "S1 guide\n←Bombus", "selfing_syndrome": "S2 selfing\nsyndrome",
             "island_common_cause": "S3 island\ncommon cause", "halictid_substitution": "S5 halictid\nsubst."}

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0))

    ax = axes[0]
    vals = [res.ca_j[n] for n in names]
    colors = ["#d62728" if n in ("selfing_syndrome", "island_common_cause") else "#9aa0a6"
              for n in names]
    ax.bar([short[n] for n in names], vals, color=colors)
    ax.axhline(0.5, color="gray", ls="--", lw=1)
    ax.set_ylim(0, 1); ax.set_ylabel("CA_j")
    ax.set_title(f"(A) Campanula confound (published pattern only)\n"
                 f"D={res.D_RACH}/4, R={res.R_RACH}; S2 ≈ S3 unresolved")

    ax = axes[1]
    if res.ca_j_after:
        keys = ["selfing_syndrome", "island_common_cause"]
        before = [res.ca_j[k] for k in keys]
        after = [res.ca_j_after[k] for k in keys]
        x = np.arange(2); w = 0.38
        ax.bar(x - w/2, before, w, label="published cline only", color="#bbbbbb")
        ax.bar(x + w/2, after, w, label="+ guide/He gradients + assay", color="#d62728")
        ax.axhline(0.5, color="gray", ls="--", lw=1)
        ax.set_xticks(x); ax.set_xticklabels(["S2 selfing", "S3 common cause"])
        ax.set_ylim(0, 1); ax.set_ylabel("CA_j")
        ax.set_title(f"(B) Resolution (truth = {res.truth})\n"
                     f"D {res.D_RACH}→{res.D_after}, R {res.R_RACH}→{res.R_after}")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Campanula structural (Tier-A) worked example.")
    p.add_argument("--truth", default="S3", choices=["S2", "S3", "both"])
    p.add_argument("--n-attempts", type=int, default=4000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_campanula_structural(truth=args.truth, n_attempts=args.n_attempts, seed=args.seed)
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
