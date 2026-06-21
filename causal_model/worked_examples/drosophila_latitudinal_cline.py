"""Flagship real-system re-analysis target: the Drosophila latitudinal cline.

This is the harness for the option-2 re-analysis: take a *famous, genuinely
confounded* adaptive cline and ask, with Causal Replaceability Cost (CRC),
whether the published adaptive explanation is **load-bearing** or **freely
replaceable** by the long-standing demographic alternative.

The system
----------
Latitudinal clines in *Drosophila melanogaster* (body size, pigmentation, Adh,
the In(3R)Payne inversion) are the textbook adaptive-cline system. They are also
the textbook *confound*: a latitudinal trait cline can be produced by

    S_thermal     direct thermal/climatic selection on the trait
    S_demographic demographic structure — secondary contact / admixture /
                  isolation-by-distance — painting the whole genome clinally
                  WITHOUT selection on the focal trait (Endler; Caracristi &
                  Schlötterer; Bergland et al.)
    S_inversion   the trait cline is a *correlated response* to clinal selection
                  on a linked inversion (In(3R)Payne), not direct trait selection

On the *trait cline alone* these are mutually admissible — exactly the "pattern ≠
process" critique. CRC turns that critique into a number.

The two levers (the real Drosophila arguments)
----------------------------------------------
neutral-marker cline (private to S_demographic)
    Demography paints neutral loci clinally; direct trait selection does not. A
    FLAT neutral-marker cline therefore rules demography OUT (CRC(S_demographic)
    → 0); a neutral-marker cline that *is* present pins demography IN
    (CRC(S_demographic) → ∞).

parallelism across independent continents (signature of selection)
    Selection (thermal or via the inversion) reproduces the cline on independent
    continents; neutral demographic history does not align across continents.
    PARALLEL clines therefore rule out the demography-only world; their ABSENCE
    pins demography (CRC(S_demographic) → ∞) and rules out selection. This is the
    same logic as the replicate-transect resolver in ``neutral_adaptive``.

What is asserted vs what is a placeholder
-----------------------------------------
ASSERTED (Tier-A, defensible qualitatively): only the SIGN structure in
``_SIGNS`` — which mechanism moves which observable in which direction.
Magnitudes are randomised and marginalised, so no effect size is hand-chosen.

PLACEHOLDER (must be filled from the real literature before any empirical claim):
every *quantitative* input — the measured body-size cline slope, the neutral Fst
gradient, the documented thermal-selection coefficient, whether parallel clines
are actually observed. These live in ``literature_constraints()`` and the
candidate-outcome realisations, each flagged ``# PLACEHOLDER``. Filling them with
real values from a chosen paper turns this harness into the empirical re-analysis;
until then it reports only the *structure* of the confound and its resolution.

Usage
-----
    python -m causal_model.worked_examples.drosophila_latitudinal_cline
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field

from causal_model.switch_inference import BiologicalSwitch
from causal_model.external_constraints import Constraint


# ---------------------------------------------------------------------------
# Mechanisms and the SIGN of each mechanism's effect on each observable cline
# ---------------------------------------------------------------------------

_MECHANISMS = ("thermal_selection", "demographic_cline", "inversion_hitchhike")

# Cline-valued observables (each gets near/far endpoints + a slope).
_TRAITS = ("body_size", "neutral_marker", "inversion_freq")

_SIGNS: dict[str, dict[str, int]] = {
    # direct thermal selection moves only the focal trait (leaves neutral
    # markers flat; its cross-continent signature is parallelism, handled below)
    "thermal_selection":   {"body_size": +1},
    # demography paints the focal trait AND neutral markers clinally
    "demographic_cline":   {"body_size": +1, "neutral_marker": +1},
    # selection on the inversion drags the trait as a correlated response and
    # leaves an inversion-frequency cline as its private signature
    "inversion_hitchhike": {"body_size": +1, "inversion_freq": +1},
}

# Parallelism across independent continents is the private signature of
# SELECTION (thermal or via the inversion); neutral demography lacks it.
_SELECTION_MECHANISMS = ("thermal_selection", "inversion_hitchhike")

_MAG_LO, _MAG_HI = 0.30, 0.80
_SLOPE_TOL = 0.05
_BASE = 0.50
_SIG_TOL = 0.10

_NEAR, _FAR = "low_lat", "high_lat"


def _switches() -> list[BiologicalSwitch]:
    desc = {
        "thermal_selection": "Direct thermal/climatic selection on the trait.",
        "demographic_cline": "Neutral demographic structure (admixture / IBD) painting the genome clinally.",
        "inversion_hitchhike": "Trait cline as a correlated response to clinal selection on In(3R)Payne.",
    }
    return [BiologicalSwitch(name=m, pathway_key=m, biological_question="", description=desc[m])
            for m in _MECHANISMS]


def literature_constraints() -> list[Constraint]:
    """External effect-size constraints — ALL VALUES ARE PLACEHOLDERS.

    Replace ``mu`` / ``sigma`` with real documented estimates from the chosen
    Drosophila paper(s) before making any empirical claim. The *structure* (which
    coefficient is constrained) is asserted; the *numbers* are not.
    """
    return [
        # PLACEHOLDER: documented neutral Fst latitudinal gradient (demography's
        # reach). A shallow documented gradient makes a steep trait cline hard to
        # attribute to demography → constraint penalty on the demographic coeff.
        Constraint(name="w_demographic", type="normal", mu=0.40, sigma=0.20,
                   description="PLACEHOLDER: documented neutral Fst gradient (fill from literature)"),
        # PLACEHOLDER: documented thermal-selection coefficient on the trait.
        Constraint(name="w_thermal", type="normal", mu=0.60, sigma=0.30,
                   description="PLACEHOLDER: documented thermal-selection effect size (fill from literature)"),
    ]


# ---------------------------------------------------------------------------
# Simulation + ABC acceptance (Tier-A: random magnitudes, marginalised)
# ---------------------------------------------------------------------------

def _net_slopes(s: dict, mag: dict) -> dict[str, float]:
    out = {t: 0.0 for t in _TRAITS}
    for m in _MECHANISMS:
        if not s[m]:
            continue
        for t, sign in _SIGNS[m].items():
            out[t] += sign * mag[(m, t)]
    return out


def _abc_accept(n_attempts: int, seed: int) -> list[dict]:
    """Accept draws reproducing the published pattern: a body-size cline.

    Each accepted draw stores near/far endpoints for every observable (so cline
    candidates can filter it), the per-mechanism coefficients (so literature
    constraints can score them), and the parallelism signature.
    """
    rng = random.Random(seed)
    accepted: list[dict] = []
    for _ in range(n_attempts):
        s = {m: (rng.random() < 0.5) for m in _MECHANISMS}
        mag = {(m, t): rng.uniform(_MAG_LO, _MAG_HI)
               for m in _MECHANISMS for t in _SIGNS[m]}
        slope = _net_slopes(s, mag)
        # published ordinal pattern: the focal trait increases with latitude
        if not (slope["body_size"] > _SLOPE_TOL):
            continue
        row = dict(s)
        for t in _TRAITS:
            row[f"{_NEAR}_{t}"] = round(_BASE, 4)
            row[f"{_FAR}_{t}"] = round(_BASE + slope[t], 4)
            row[f"slope_{t}"] = round(slope[t], 4)
        # parallelism: present iff at least one selection mechanism is active
        row["sig_parallel"] = 1.0 if any(s[m] for m in _SELECTION_MECHANISMS) else 0.0
        # coefficients for the literature-constraint penalty (raw proposals)
        row["w_thermal"] = round(mag.get(("thermal_selection", "body_size"), 0.0), 4)
        row["w_demographic"] = round(mag.get(("demographic_cline", "body_size"), 0.0), 4)
        accepted.append(row)
    return accepted


# ---------------------------------------------------------------------------
# Candidate observations (the levers)
# ---------------------------------------------------------------------------

def _candidate_observations():
    from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome

    def _grad(var: str, present: bool):
        rel = f"{_FAR} > {_NEAR}" if present else f"{_FAR} ~= {_NEAR}"
        return [{
            "type": "pairwise_relation", "variable": var,
            "left_population": _FAR, "right_population": _NEAR, "relation": rel,
        }]

    def _assay(present: bool):
        return [{
            "type": "absolute_summary", "variable": "parallel", "population": "sig",
            "observed_value": f"{1.0 if present else 0.0:.4f}", "scale": f"{_SIG_TOL/2:.4f}",
        }]

    neutral = CandidateObservation(
        name="neutral_marker_cline",
        description="Genotype neutral loci across the latitudinal transect (Fst / allele-freq cline). PLACEHOLDER outcome.",
        target_switches=["demographic_cline"],
        rationale="A neutral-marker cline is the private signature of demography; flat neutral markers rule it out.",
        pattern_type="pairwise_relation",
        outcomes=[
            CandidateOutcome("neutral_cline_present", "Neutral loci show a latitudinal cline.", 0.5, _grad("neutral_marker", True)),
            CandidateOutcome("neutral_flat", "Neutral loci are flat across latitude.", 0.5, _grad("neutral_marker", False)),
        ],
    )
    parallel = CandidateObservation(
        name="parallel_continents",
        description="Test whether the trait cline is reproduced, same-direction, on an independent continent. PLACEHOLDER outcome.",
        target_switches=["thermal_selection", "demographic_cline"],
        rationale="Parallel clines on independent continents are the signature of selection; their absence pins demography.",
        pattern_type="absolute_summary",
        outcomes=[
            CandidateOutcome("parallel_present", "Cline parallel across continents.", 0.5, _assay(True)),
            CandidateOutcome("parallel_absent", "No parallel cline on the second continent.", 0.5, _assay(False)),
        ],
    )
    inversion = CandidateObservation(
        name="inversion_cline",
        description="Score the In(3R)Payne frequency cline along the transect. PLACEHOLDER outcome.",
        target_switches=["inversion_hitchhike"],
        rationale="An inversion-frequency cline is the private signature of the hitchhiking mechanism.",
        pattern_type="pairwise_relation",
        outcomes=[
            CandidateOutcome("inversion_cline_present", "Inversion shows a latitudinal cline.", 0.5, _grad("inversion_freq", True)),
            CandidateOutcome("inversion_flat", "Inversion frequency flat across latitude.", 0.5, _grad("inversion_freq", False)),
        ],
    )
    return [neutral, parallel, inversion]


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

def _crc_str(v: float) -> float | str:
    if v == float("inf"):
        return "∞"
    if v != v:
        return float("nan")
    return round(v, 4)


@dataclass
class DrosophilaClineResult:
    switch_names: list[str]
    n_accepted: int
    n_attempts: int
    ca_j: dict[str, float]
    R_expl: float
    explanations: list[tuple[frozenset, float]]
    crc_published: dict[str, float | str]
    crc_after: dict[str, dict[str, float | str]]      # outcome_name -> CRC profile
    replaceability_nov: list[dict]

    def describe(self) -> str:
        lines = [
            "Drosophila latitudinal cline — CRC re-analysis harness",
            f"  |A_ε| = {self.n_accepted}/{self.n_attempts}   (published y_obs: body-size cline)",
            f"  explanation-level R_expl = {self.R_expl}",
            "  minimal explanations: " + "  ".join(
                ("{" + ", ".join(sorted(m)) + "}") + f"={mass:.2f}"
                for m, mass in self.explanations),
            "",
            "  (A) On the body-size cline ALONE — is adaptation load-bearing?",
            "      CRC: " + "  ".join(
                f"{k.split('_')[0]}:{'∞' if v=='∞' else f'{v:.2f}'}"
                for k, v in self.crc_published.items()),
            "      → all finite & similar: the cline alone does NOT single out",
            "        adaptation. Selection and demography are mutually replaceable.",
            "",
            "  (B) Counterfactual levers (PLACEHOLDER outcomes — fill from real data):",
        ]
        for outcome, prof in self.crc_after.items():
            body = "  ".join(f"{k.split('_')[0]}:{'∞' if v=='∞' else f'{v:.2f}'}"
                             for k, v in prof.items())
            lines.append(f"      if {outcome:24s}: {body}")
        lines += [
            "",
            "  (C) Replaceability-NOV — which measurement to make next:",
        ]
        for r in self.replaceability_nov:
            lines.append(f"      {r['candidate']:22s} NOV_CRC = {r['NOV_CRC_total']:.3f}")
        return "\n".join(lines)


def run_drosophila_cline(n_attempts: int = 12000, seed: int = 1) -> DrosophilaClineResult:
    from causal_model.causal_admissibility import rach_summary
    from causal_model.minimal_explanations import minimal_explanations
    from causal_model.causal_replaceability import crc_profile
    from causal_model.replaceability_nov import replaceability_nov_total
    from causal_model.rach_seq import filter_by_outcome

    switches = _switches()
    names = [sw.name for sw in switches]
    acc = _abc_accept(n_attempts, seed)
    n = len(acc)

    summ = rach_summary(acc, switches)
    ca = {r.switch_name: round(r.CA_j, 4) for r in summ.causal_admissibility}
    dec = minimal_explanations(acc, switches)

    crc_pub = {k: _crc_str(v) for k, v in crc_profile(acc, switches).items()}

    crc_after: dict[str, dict] = {}
    for cand in _candidate_observations():
        for o in cand.outcomes:
            sub = filter_by_outcome(acc, o.extra_pattern_rows)
            crc_after[o.name] = (
                {k: _crc_str(v) for k, v in crc_profile(sub, switches).items()}
                if sub else {}
            )

    nov = []
    for cand in _candidate_observations():
        nov.append({
            "candidate": cand.name,
            "NOV_CRC_total": replaceability_nov_total(cand, acc, switches),
        })
    nov.sort(key=lambda r: (r["NOV_CRC_total"] if r["NOV_CRC_total"] == r["NOV_CRC_total"] else -1),
             reverse=True)

    return DrosophilaClineResult(
        switch_names=names, n_accepted=n, n_attempts=n_attempts,
        ca_j=ca, R_expl=dec.R_expl,
        explanations=[(e.mechanisms, e.mass) for e in dec.explanations],
        crc_published=crc_pub, crc_after=crc_after, replaceability_nov=nov,
    )


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--n-attempts", type=int, default=12000)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args(argv)
    print(run_drosophila_cline(args.n_attempts, args.seed).describe())
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
