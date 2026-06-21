"""Generic mediation-vs-direct replacement worked example.

This Tier-A worked example demonstrates Causal Replaceability Cost (CRC) and
the Causal Substitution Matrix (CSM) using a minimal three-mechanism setting:

    S1  direct     x → Z         (environmental driver affects trait directly)
    S2  mediated   x → M → Z     (effect mediated through an intermediate M)
    S3  neutral    ε → Z         (trait drifts independently of x; no selection)

Two cases show how CRC and CSM change when additional observations are added:

    Case A  y_obs = {Z increases along x gradient}
            S1 and S2 are freely interchangeable:
              CRC(S1) ≈ CRC(S2)  (similar informational cost)
              CSM_{S1→S2} > 0    (when S1 absent, S2 compensates)

    Case B  y_obs = {Z increases along x gradient  AND
                     M increases along x gradient}
            Only S2 produces M↑ with x; observing M pins S2 as irreplaceable:
              CRC(S2) → ∞  (S2 is now indispensable)
              CRC(S1)   lower or unchanged (S1 is now redundant given S2)

Replaceability-NOV for "observe M gradient": the expected gain in CRC(S2)
upon observing M is large — measuring the mediator M distinguishes the
direct and mediated pathways.

Usage
-----
    from causal_model.worked_examples.generic_mediation_replacement import (
        run_generic_mediation, GenericMediationResult,
    )
    res_A = run_generic_mediation(n_attempts=8000, seed=1, case="A")
    res_B = run_generic_mediation(n_attempts=8000, seed=1, case="B")
    print(res_A.crc)   # {"direct": …, "mediated": …, "neutral": …}
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from causal_model.switch_inference import BiologicalSwitch
from causal_model.causal_replaceability import crc_profile, crc_profile_full
from causal_model.causal_substitution import causal_substitution_matrix, csm_dict
from causal_model.neutral_module import NeutralProcess, neutral_crc_profile


# ---------------------------------------------------------------------------
# Fixed context: three populations along a unit gradient
# ---------------------------------------------------------------------------

_POPS = ("low", "mid", "high")
_X = {"low": 0.2, "mid": 0.5, "high": 0.8}


# ---------------------------------------------------------------------------
# Causal switches
# ---------------------------------------------------------------------------

def _switches() -> list[BiologicalSwitch]:
    return [
        BiologicalSwitch("direct",   "direct_pathway",   "x → Z?",   "Direct effect of x on trait Z", 0.5),
        BiologicalSwitch("mediated", "mediated_pathway", "x → M → Z?","Effect via mediator M",         0.5),
        BiologicalSwitch("neutral",  "neutral_process",  "ε → Z?",   "Neutral drift in Z",             0.5),
    ]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _simulate(s: dict, theta: dict) -> dict:
    """Generate population-level (M, Z) values along the gradient.

    Edges active by switch:
      direct   → x contributes directly to Z via weight w_xZ
      mediated → x affects M (weight w_xM) which affects Z (weight w_MZ)
      neutral  → independent drift terms (drift_low/mid/high) added to Z
    """
    w_xZ = theta["w_xZ"] if s.get("direct") else 0.0
    w_xM = theta["w_xM"] if s.get("mediated") else 0.0
    w_MZ = theta["w_MZ"] if s.get("mediated") else 0.0
    w_dr = theta["w_drift"] if s.get("neutral") else 0.0

    out: dict = {}
    for pop in _POPS:
        x = _X[pop]
        M = w_xM * x
        Z = w_xZ * x + w_MZ * M + w_dr * theta.get(f"drift_{pop}", 0.0)
        out[f"{pop}_M"] = M
        out[f"{pop}_Z"] = Z
    return out


# ---------------------------------------------------------------------------
# ABC acceptance
# ---------------------------------------------------------------------------

_TOL = 0.05   # minimum gap required for directional acceptance

def _accept_case_a(row: dict) -> bool:
    """Case A: Z increases along the gradient (low < high)."""
    return row["low_Z"] + _TOL < row["high_Z"]

def _accept_case_b(row: dict) -> bool:
    """Case B: Z increases AND M increases along the gradient."""
    return _accept_case_a(row) and row["low_M"] + _TOL < row["high_M"]


def _abc_accept(
    n_attempts: int,
    seed: int,
    case: str = "A",
    *,
    weight_lo: float = 0.5,
    weight_hi: float = 1.5,
) -> list[dict]:
    """Run Tier-A ABC and return accepted rows.

    Each accepted row contains:
      - {pop}_M, {pop}_Z columns for CRC/CSM outcome filtering
      - switch booleans (direct, mediated, neutral)
    """
    rng = random.Random(seed)
    accept_fn = _accept_case_b if case.upper() == "B" else _accept_case_a
    sw = _switches()
    acc: list[dict] = []

    for _ in range(n_attempts):
        s = {sw_obj.name: rng.random() < sw_obj.prior_on_prob for sw_obj in sw}
        theta = {
            "w_xZ":       rng.choice((-1.0, 1.0)) * rng.uniform(weight_lo, weight_hi),
            "w_xM":       rng.choice((-1.0, 1.0)) * rng.uniform(weight_lo, weight_hi),
            "w_MZ":       rng.choice((-1.0, 1.0)) * rng.uniform(weight_lo, weight_hi),
            "w_drift":    rng.uniform(weight_lo, weight_hi),
            "drift_low":  rng.uniform(-1.0, 1.0),
            "drift_mid":  rng.uniform(-1.0, 1.0),
            "drift_high": rng.uniform(-1.0, 1.0),
        }
        row = _simulate(s, theta)
        if accept_fn(row):
            row.update(s)
            acc.append(row)

    return acc


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class GenericMediationResult:
    case: str
    n_accepted: int
    n_attempts: int
    crc: dict[str, float]                    # {switch_name: CRC_j}
    csm: dict[tuple[str, str], float]        # {(j, k): delta}
    substitutes: dict[str, list[tuple[str, float]]]  # j → [(k, delta), ...]
    p_neutral: float                         # P(neutral active | A_ε)

    def describe(self) -> str:
        lines = [
            f"Generic Mediation Replacement  (Case {self.case})",
            f"  |A_ε| = {self.n_accepted}/{self.n_attempts}",
            "  CRC profile:",
        ]
        for name, crc in self.crc.items():
            crc_str = "∞" if crc == float("inf") else f"{crc:.3f}"
            lines.append(f"    {name:12s}  CRC = {crc_str} bits")
        lines.append("  Top CSM entries:")
        for (j, k), delta in sorted(self.csm.items(), key=lambda x: -abs(x[1]) if x[1]==x[1] else 0)[:4]:
            sign = "+" if delta >= 0 else ""
            lines.append(f"    [{j}→{k}] = {sign}{delta:.3f}")
        lines.append(f"  P(neutral | A_ε) = {self.p_neutral:.3f}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_generic_mediation(
    n_attempts: int = 8000,
    seed: int = 1,
    case: str = "A",
) -> GenericMediationResult:
    """Run the generic mediation replacement example.

    Parameters
    ----------
    n_attempts:
        ABC proposal count.
    seed:
        RNG seed for reproducibility.
    case:
        ``"A"`` — y_obs = Z gradient only (S1/S2 interchangeable).
        ``"B"`` — y_obs = Z gradient + M gradient (S2 becomes irreplaceable).

    Returns
    -------
    GenericMediationResult
    """
    sw = _switches()
    acc = _abc_accept(n_attempts, seed, case)

    crc = crc_profile(acc, sw)
    csm = csm_dict(acc, sw)
    from causal_model.causal_substitution import substitutes_for
    subs = {sw_obj.name: substitutes_for(sw_obj.name, acc, sw) for sw_obj in sw}

    n = len(acc)
    p_neutral = sum(1 for r in acc if r.get("neutral")) / max(n, 1)

    return GenericMediationResult(
        case=case.upper(),
        n_accepted=n,
        n_attempts=n_attempts,
        crc=crc,
        csm=csm,
        substitutes=subs,
        p_neutral=round(p_neutral, 4),
    )
