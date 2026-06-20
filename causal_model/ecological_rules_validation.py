"""Validation against established ecological rules ("照合 against ecology").

Where the generality sweep (``generality_sweep``) shows that RACH-SEQ resolves
*randomly generated* confounds — mechanical generality with no ecological
meaning — this module grounds the framework against a panel of *real* ecological
rules whose directional structure is fixed by the literature. For each rule it
checks three things:

    (V1) confound reproduced  — RACH flags as jointly admissible the very
         mechanisms the literature recognises as hard to separate;
    (V2) NOV points correctly — the next-observation value ranks the literature's
         distinguishing assay above a decoy observation that cannot separate the
         confound;
    (V3) direction recovered  — supplying the distinguishing observation at the
         literature-attributed direction makes RACH recover that mechanism.

EPISTEMIC SCOPE — read this before citing the result
----------------------------------------------------
The ground truth here is the *directional structure the ecological literature
has established* (which mechanisms are confounded, what observation separates
them, and the sign each mechanism predicts) — NOT a claim about which mechanism
is true in nature. Most of these rules are genuinely unresolved; that is exactly
why they are good degeneracy examples. The validation therefore demonstrates that
RACH correctly *operationalises ecological reasoning* — it reproduces the known
confound, recommends the observation ecologists actually use, and recovers the
attributed mechanism when that observation is supplied. It does not, and cannot,
show that ecology's attributions are correct.

PROVISIONAL ENCODINGS — domain-expert verification required
-----------------------------------------------------------
Each rule's mechanisms, signature directions and ``literature_truth`` are a
PROVISIONAL transcription. They are tagged with ``literature_note`` and MUST be
verified (and cited) by the domain expert before any publication use. The
contribution is the validation *method*; the specific directional values are
inputs to be checked.

Usage
-----
    python -m causal_model.ecological_rules_validation --figure outputs/mee/eco_rules.png
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field

_THETA_LO, _THETA_HI = 0.8, 1.2
_PATTERN_TOL = 0.05
_SIG_TOL = 0.10


@dataclass
class EcologicalRule:
    """One established ecological rule, transcribed into RACH's confound schema."""
    name: str
    pattern_statement: str            # the observed directional rule (the y_obs)
    mechanisms: list[str]             # >=2 candidate mechanisms confounded on the pattern
    coeffs: dict[str, float]          # mechanism -> coefficient on the shared pattern (>0)
    inert_controls: list[str]         # mechanisms that do NOT drive the pattern (CA~0.5 expected)
    literature_truth: str             # mechanism the literature attributes (PROVISIONAL) or "unresolved"
    distinguishing_obs: str           # the covariate/assay the literature uses to separate mechanisms
    literature_note: str              # citation / caveat — TO BE VERIFIED by the domain expert


# ---------------------------------------------------------------------------
# Panel of ecological rules (PROVISIONAL directional encodings — verify!)
# ---------------------------------------------------------------------------

ECOLOGICAL_RULES: list[EcologicalRule] = [
    EcologicalRule(
        name="Bergmann",
        pattern_statement="Endotherm body size increases with latitude / colder climate.",
        mechanisms=["heat_conservation", "fasting_endurance"],
        coeffs={"heat_conservation": 0.30, "fasting_endurance": 0.55},
        inert_controls=["resource_productivity", "dispersal"],
        literature_truth="unresolved",   # mechanism genuinely contested (not cleanly attributed)
        distinguishing_obs="size–seasonality vs size–mean-temperature partial association",
        literature_note=(
            "Bergmann 1847 (Göttinger Studien 3:595–708): pattern robust but "
            "MECHANISM UNRESOLVED — heat conservation (original) vs fasting/"
            "seasonality endurance (Lindstedt & Boyce 1985, Am. Nat. 125:873–878); "
            "validity and mechanism debated (Meiri & Dayan 2003, J. Biogeogr. "
            "30:331–351). Knowledge-based; online re-verification pending."),
    ),
    EcologicalRule(
        name="Allen",
        pattern_statement="Extremity length decreases in colder climates.",
        mechanisms=["thermoregulation", "developmental_plasticity"],
        coeffs={"thermoregulation": 0.55, "developmental_plasticity": 0.30},
        inert_controls=["allometric_scaling"],
        literature_truth="thermoregulation",    # established ULTIMATE driver
        distinguishing_obs="extremity–heat-loss experimental manipulation vs rearing-temperature plasticity",
        literature_note=(
            "Allen 1877 (Radical Review 1:108–140): thermoregulatory heat "
            "conservation is the established ULTIMATE driver; developmental "
            "plasticity (Serrat et al. 2008, PNAS 105:19348–19353) is a PROXIMATE "
            "mechanism at a different explanatory level rather than a true "
            "competitor — VERIFY framing and page ranges (online re-verification "
            "pending)."),
    ),
    EcologicalRule(
        # 3-way confound: three mechanisms drive the island size shift, so the
        # degeneracy is deeper than a 2-way rule (CA ≈ 4/7 ≈ 0.57, not 2/3).
        name="Foster_island",
        pattern_statement="Small mammals enlarge and large mammals dwarf on islands.",
        mechanisms=["predation_release", "resource_limitation", "competition_release"],
        coeffs={"predation_release": 0.40, "resource_limitation": 0.55, "competition_release": 0.30},
        inert_controls=["dispersal"],
        literature_truth="unresolved",           # genuinely contested (3 competing mechanisms)
        distinguishing_obs="body-size shift vs predator density vs island area vs competitor richness",
        literature_note=(
            "Foster 1964 (Nature 202:234–235) island rule; 3-way UNRESOLVED — "
            "predation release vs resource limitation vs competition release, no "
            "consensus driver (Lomolino 2005, J. Biogeogr. 32:1683–1699); rule "
            "generality itself debated. Knowledge-based; online re-verification "
            "pending."),
    ),
    EcologicalRule(
        # extra inert controls (K = 5) so the overall degeneracy D is higher.
        name="Gloger",
        pattern_statement="Pigmentation is darker in warm/humid climates.",
        mechanisms=["thermal_melanism", "pathogen_resistance"],
        coeffs={"thermal_melanism": 0.40, "pathogen_resistance": 0.50},
        inert_controls=["photoprotection", "crypsis", "dispersal"],
        literature_truth="unresolved",
        distinguishing_obs="pigmentation–humidity vs pigmentation–parasite-load association",
        literature_note=(
            "Gloger 1833 (Breslau: August Schulz); UNRESOLVED — thermal melanism "
            "vs pathogen/feather-degrading-bacteria resistance (Burtt & Ichida "
            "2004, Condor 106(3):681) vs photoprotection vs crypsis; multiple "
            "non-exclusive hypotheses. Knowledge-based; online re-verification "
            "pending."),
    ),
]


# ---------------------------------------------------------------------------
# Generic phenomenological confound runner (one ecological rule)
# ---------------------------------------------------------------------------

def _rule_switches(rule: EcologicalRule):
    from causal_model.switch_inference import BiologicalSwitch
    names = rule.mechanisms + rule.inert_controls
    return [BiologicalSwitch(name=n, pathway_key=n, biological_question="", description="")
            for n in names]


def _abc_accept(rule: EcologicalRule, n_attempts: int, seed: int) -> list[dict]:
    """Accept draws reproducing the rule's pattern; the driving mechanisms form a
    disjunction confound. Each draw carries per-mechanism signature columns."""
    rng = random.Random(seed)
    names = rule.mechanisms + rule.inert_controls
    accepted = []
    for _ in range(n_attempts):
        s = {n: (rng.random() < 0.5) for n in names}
        theta = rng.uniform(_THETA_LO, _THETA_HI)
        pattern = theta * sum(rule.coeffs.get(m, 0.0) * int(s[m]) for m in rule.mechanisms)
        if pattern > _PATTERN_TOL:
            row = dict(s)
            row["theta"] = theta
            for m in rule.mechanisms:
                row[f"sys_{m}sig"] = 1.0 if s[m] else 0.0
            # a decoy signature on an inert control (cannot separate the confound)
            if rule.inert_controls:
                dc = rule.inert_controls[0]
                row[f"sys_{dc}sig"] = 1.0 if s[dc] else 0.0
            accepted.append(row)
    return accepted


def _mechanism_assays(rule: EcologicalRule):
    """One assay per driving mechanism + a decoy assay on an inert control."""
    from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome

    def _assay_rows(col: str, present: bool):
        return [{
            "type": "absolute_summary", "variable": col.split("_", 1)[1],
            "population": "sys",
            "observed_value": f"{1.0 if present else 0.0:.4f}",
            "scale": f"{_SIG_TOL / 2:.4f}",
        }]

    cands = []
    for m in rule.mechanisms:
        col = f"sys_{m}sig"
        cands.append(CandidateObservation(
            name=f"assay_{m}", description=f"Measure the {m} signature.",
            target_switches=[m], rationale=f"Signature present iff {m} operates.",
            pattern_type="absolute_summary",
            outcomes=[
                CandidateOutcome(f"{m}_present", "", 0.5, _assay_rows(col, True)),
                CandidateOutcome(f"{m}_absent", "", 0.5, _assay_rows(col, False)),
            ],
        ))
    # decoy: measuring an inert control's signature cannot cut the confounding edge
    if rule.inert_controls:
        dc = rule.inert_controls[0]
        col = f"sys_{dc}sig"
        cands.append(CandidateObservation(
            name=f"decoy_{dc}", description=f"Measure the inert {dc} signature (decoy).",
            target_switches=[dc], rationale="Decoy: cannot separate the confounded mechanisms.",
            pattern_type="absolute_summary",
            outcomes=[
                CandidateOutcome(f"{dc}_present", "", 0.5, _assay_rows(col, True)),
                CandidateOutcome(f"{dc}_absent", "", 0.5, _assay_rows(col, False)),
            ],
        ))
    return cands


@dataclass
class RuleValidation:
    name: str
    pattern_statement: str
    n_accepted: int
    ca_confound: dict[str, float]      # CA of the driving mechanisms (pattern only)
    ca_controls: dict[str, float]      # CA of the inert controls
    D0: float
    R0: float
    edge_present: bool
    confound_reproduced: bool          # V1
    nov_points_correctly: bool         # V2
    literature_truth: str
    direction_recovered: bool | None   # V3 (None if literature_truth == "unresolved")
    ca_after: dict[str, float] = field(default_factory=dict)
    literature_note: str = ""

    @property
    def passes(self) -> bool:
        checks = [self.confound_reproduced, self.nov_points_correctly]
        if self.direction_recovered is not None:
            checks.append(self.direction_recovered)
        return all(checks)


def _all_off_fraction(acc: list[dict], mechanisms: list[str]) -> float:
    """Fraction of A_ε in which *every* driving mechanism is off. ~0 ⇒ the
    mechanism set forms an (n-way) disjunction confound ('at least one required')."""
    if not acc:
        return 0.0
    return sum(1 for r in acc if not any(r.get(m) for m in mechanisms)) / len(acc)


def _mech_degeneracy(acc: list[dict], rule_switches, mechanisms: list[str]) -> float:
    """Joint degeneracy restricted to the driving-mechanism switches (bits)."""
    from causal_model.causal_admissibility import causal_degeneracy
    mech_sw = [sw for sw in rule_switches if sw.name in set(mechanisms)]
    return causal_degeneracy(acc, mech_sw)


def validate_rule(rule: EcologicalRule, n_attempts: int = 4000, seed: int = 1) -> RuleValidation:
    from causal_model.causal_admissibility import rach_summary, causal_resolvability
    from causal_model.mechanism_equivalence import mechanism_equivalence_structure
    from causal_model.rach_seq import filter_by_outcome

    switches = _rule_switches(rule)
    acc = _abc_accept(rule, n_attempts, seed)

    summ = rach_summary(acc, switches)
    ca = {r.switch_name: round(r.CA_j, 4) for r in summ.causal_admissibility}
    ca_conf = {m: ca[m] for m in rule.mechanisms}
    ca_ctrl = {c: ca[c] for c in rule.inert_controls}
    D0 = round(summ.causal_degeneracy, 4)
    R0 = round(summ.causal_resolvability, 4)

    struct = mechanism_equivalence_structure(acc, switches)
    mech_set = set(rule.mechanisms)
    edge_present = any({e.a, e.b} <= mech_set for e in struct.edges)

    # (V1) confound reproduced — degeneracy-based, so it captures BOTH 2-way
    # disjunction edges and higher-order (n-way) confounds the pairwise edge layer
    # misses: the mechanism set is jointly required (all-off cell ~empty), each
    # mechanism CA is elevated above 0.5, and the inert controls stay near 0.5.
    all_off = _all_off_fraction(acc, rule.mechanisms)
    conf_ok = (
        all_off < 0.02
        and all(0.52 < ca_conf[m] < 0.85 for m in rule.mechanisms)
        and all(abs(ca_ctrl[c] - 0.5) < 0.12 for c in rule.inert_controls)
    )

    # (V2) NOV points correctly — degeneracy-based so it also works for n-way:
    # each mechanism assay reduces the *mechanism-subset* degeneracy (it resolves
    # the confound), whereas the decoy (an inert-control assay) does not.
    D_mech0 = _mech_degeneracy(acc, switches, rule.mechanisms)

    def _expected_mech_D(cand) -> float:
        tot = 0.0
        for oc in cand.outcomes:
            sub = filter_by_outcome(acc, oc.extra_pattern_rows)
            if len(sub) < 10:
                continue
            tot += (len(sub) / len(acc)) * _mech_degeneracy(sub, switches, rule.mechanisms)
        return tot

    cands = _mechanism_assays(rule)
    mech_assay_drop = [D_mech0 - _expected_mech_D(c)
                       for c in cands if c.name.startswith("assay_")]
    decoy = next((c for c in cands if c.name.startswith("decoy_")), None)
    decoy_drop = (D_mech0 - _expected_mech_D(decoy)) if decoy else 0.0
    nov_ok = bool(mech_assay_drop) and min(mech_assay_drop) > 0.05 and decoy_drop < 0.05

    # (V3) direction recovery: supply the distinguishing assays at the attributed truth
    direction_recovered: bool | None = None
    ca_after: dict[str, float] = {}
    if rule.literature_truth != "unresolved":
        truth = rule.literature_truth
        rows = acc
        for m in rule.mechanisms:
            present = (m == truth)
            col = f"sys_{m}sig"
            rows = filter_by_outcome(rows, [{
                "type": "absolute_summary", "variable": col.split("_", 1)[1],
                "population": "sys",
                "observed_value": f"{1.0 if present else 0.0:.4f}",
                "scale": f"{_SIG_TOL / 2:.4f}",
            }])
        if len(rows) >= 5:
            summ2 = rach_summary(rows, switches)
            ca_after = {r.switch_name: round(r.CA_j, 4) for r in summ2.causal_admissibility}
            direction_recovered = (
                ca_after.get(truth, 0.0) > 0.9
                and all(ca_after.get(m, 1.0) < 0.1 for m in rule.mechanisms if m != truth)
            )

    return RuleValidation(
        name=rule.name, pattern_statement=rule.pattern_statement, n_accepted=len(acc),
        ca_confound=ca_conf, ca_controls=ca_ctrl, D0=D0, R0=R0,
        edge_present=edge_present, confound_reproduced=conf_ok,
        nov_points_correctly=nov_ok, literature_truth=rule.literature_truth,
        direction_recovered=direction_recovered, ca_after=ca_after,
        literature_note=rule.literature_note,
    )


def run_validation(rules: list[EcologicalRule] | None = None,
                   n_attempts: int = 4000, seed: int = 1) -> list[RuleValidation]:
    rules = rules or ECOLOGICAL_RULES
    return [validate_rule(r, n_attempts=n_attempts, seed=seed) for r in rules]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(results: list[RuleValidation]) -> None:
    print("=" * 74)
    print("RACH validation against established ecological rules (照合)")
    print("=" * 74)
    print("EPISTEMIC SCOPE: ground truth = literature's directional structure, NOT")
    print("nature's true cause. Directional encodings are PROVISIONAL — verify & cite.")
    print("-" * 74)
    n_pass = sum(1 for r in results if r.passes)
    for r in results:
        v1 = "✓" if r.confound_reproduced else "✗"
        v2 = "✓" if r.nov_points_correctly else "✗"
        v3 = ("✓" if r.direction_recovered else "✗") if r.direction_recovered is not None else "—"
        print(f"\n{r.name}: {r.pattern_statement}")
        cas = ", ".join(f"{m}={v}" for m, v in r.ca_confound.items())
        print(f"   pattern-only CA (confounded): {cas}   D={r.D0}, R={r.R0}")
        print(f"   (V1) confound reproduced : {v1}")
        print(f"   (V2) NOV points to assay : {v2}")
        if r.direction_recovered is not None:
            after = ", ".join(f"{m}={v}" for m, v in r.ca_after.items()
                              if m in r.ca_confound)
            print(f"   (V3) direction recovered : {v3}   (truth={r.literature_truth}; after: {after})")
        else:
            print(f"   (V3) direction recovered : {v3}   (literature: unresolved — confound+NOV only)")
        print(f"   note: {r.literature_note}")
    print("-" * 74)
    print(f"PASS: {n_pass}/{len(results)} rules agree with the established ecological structure.")


def make_figure(results: list[RuleValidation], path: str) -> str | None:
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

    checks = ["(V1)\nconfound\nreproduced", "(V2)\nNOV points\nto assay",
              "(V3)\ndirection\nrecovered"]
    names = [r.name for r in results]
    M = np.full((len(results), 3), np.nan)
    for i, r in enumerate(results):
        M[i, 0] = 1.0 if r.confound_reproduced else 0.0
        M[i, 1] = 1.0 if r.nov_points_correctly else 0.0
        M[i, 2] = (np.nan if r.direction_recovered is None
                   else (1.0 if r.direction_recovered else 0.0))

    fig, ax = plt.subplots(figsize=(6.2, 0.9 + 0.7 * len(results)))
    cmap = plt.cm.RdYlGn
    ax.imshow(np.nan_to_num(M, nan=0.5), cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(len(results)):
        for j in range(3):
            if np.isnan(M[i, j]):
                txt, col = "—", "#444444"
            else:
                txt, col = ("✓", "white") if M[i, j] > 0.5 else ("✗", "white")
            ax.text(j, i, txt, ha="center", va="center", fontsize=14, color=col)
    ax.set_xticks(range(3)); ax.set_xticklabels(checks, fontsize=8)
    ax.set_yticks(range(len(results))); ax.set_yticklabels(names, fontsize=9)
    ax.set_title("RACH vs established ecological rules\n"
                 "(green = agrees with literature structure; — = rule unresolved)",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate RACH against established ecological rules.")
    p.add_argument("--n-attempts", type=int, default=4000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    results = run_validation(n_attempts=args.n_attempts, seed=args.seed)
    print_report(results)
    if args.figure:
        out = make_figure(results, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
