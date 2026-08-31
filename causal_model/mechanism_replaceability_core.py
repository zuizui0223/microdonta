"""Causal Replaceability Cost (CRC) — the primary output of RACH.

CRC_j quantifies how much "adjustment" is required to reproduce the observed
pattern when mechanism j is counterfactually removed.  Formally:

    CRC_j = inf_{θ, s_{-j}} [ L_constraint(θ, s_{-j}) ]
            s.t.  s_j = 0,  d(P_sim, P_obs) ≤ ε

Two additive components:

  Informational cost
      -log₂ P(s_j = 0 | A_ε)
      How rare is the ablated world in the accepted region?
      CRC = 0 when mechanism j is never active (CA_j = 0; freely droppable).
      CRC → ∞ when j is always active (CA_j → 1; no accepted draws have j off).

  Constraint penalty  (optional; zero in Tier-A runs without explicit priors)
      min_{r ∈ A_ε ∩ {s_j=0}} L_constraint(r)
      The minimum ecological/statistical strain required to replace j.
      Computed from ``external_constraints.total_penalty`` applied to each
      ablated row, then minimised.

In Tier-A (randomised-coefficient) runs the constraint penalty is 0 by
construction: every accepted row draws weights uniformly from [weight_lo,
weight_hi], so the hard constraint L = 0 is always satisfied. CRC reduces
to the pure informational cost.

Interpretation
--------------
CRC = 0 bits      mechanism j is freely replaceable (always absent in A_ε)
CRC = 1 bit       ablating j halves the admissible region (CA_j ≈ 0.5)
CRC = 1.6 bits    typical disjunction-confound member (CA_j ≈ 0.67)
CRC = ∞           mechanism j is indispensable — no accepted draw has j off

A full CRC profile ``{j: CRC_j}`` over all switches shows, at a glance,
which mechanisms are informationally load-bearing and which are freely
substitutable.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from causal_model.counterfactual_ablation import ablate_switch
from causal_model.external_constraints import Constraint, total_penalty


@dataclass
class CRCResult:
    """Causal replaceability cost for a single mechanism."""
    switch_name: str
    CRC: float                         # total cost (informational + constraint)
    info_cost: float                   # -log₂ P(s_j=0 | A_ε)
    constraint_penalty: float          # min constraint penalty in ablated region
    n_ablated: int                     # |A_ε ∩ {s_j=0}|
    n_total: int                       # |A_ε|
    fraction_ablated: float            # n_ablated / n_total

    def describe(self) -> str:
        frac = f"{self.fraction_ablated:.3f}"
        crc_str = "∞" if self.CRC == float("inf") else f"{self.CRC:.3f}"
        return (
            f"{self.switch_name:25s}  CRC={crc_str}  "
            f"info={self.info_cost:.3f}  "
            f"pen={self.constraint_penalty:.3f}  "
            f"P(off|A_ε)={frac}  ({self.n_ablated}/{self.n_total})"
        )


def causal_replaceability_cost(
    switch_name: str,
    accepted_rows: list[dict],
    constraints: list[Constraint] | None = None,
) -> float:
    """CRC_j: informational + constraint cost of ablating mechanism j.

    Parameters
    ----------
    switch_name:
        The mechanism to ablate (must appear as a key in accepted row dicts).
    accepted_rows:
        Current admissible region A_ε.
    constraints:
        Optional list of :class:`~external_constraints.Constraint` objects
        for computing the constraint-penalty component.  Pass ``None`` (the
        default) for Tier-A runs where no external parameter priors exist.

    Returns
    -------
    float
        CRC_j in bits.  ``float("inf")`` when the ablated region is empty.
        ``float("nan")`` when ``accepted_rows`` is empty.
        ``0.0`` when mechanism j is always absent (CA_j = 0).
    """
    res = causal_replaceability_cost_full(switch_name, accepted_rows, constraints)
    return res.CRC


def causal_replaceability_cost_full(
    switch_name: str,
    accepted_rows: list[dict],
    constraints: list[Constraint] | None = None,
) -> CRCResult:
    """Full CRC computation returning a :class:`CRCResult` with diagnostics."""
    n_total = len(accepted_rows)
    if n_total == 0:
        return CRCResult(
            switch_name=switch_name,
            CRC=float("nan"), info_cost=float("nan"),
            constraint_penalty=float("nan"),
            n_ablated=0, n_total=0, fraction_ablated=float("nan"),
        )

    ablated = ablate_switch(accepted_rows, switch_name)
    n_ablated = len(ablated)

    if n_ablated == 0:
        return CRCResult(
            switch_name=switch_name,
            CRC=float("inf"), info_cost=float("inf"),
            constraint_penalty=0.0,
            n_ablated=0, n_total=n_total, fraction_ablated=0.0,
        )

    p_off = n_ablated / n_total
    # -log₂(1) = 0 when all rows have s_j=0 (mechanism always absent)
    info_cost = -math.log2(p_off) if p_off < 1.0 else 0.0

    if constraints:
        penalties = [total_penalty(constraints, r) for r in ablated]
        finite_penalties = [p for p in penalties if p != float("inf")]
        if not finite_penalties:
            con_pen = float("inf")
        else:
            con_pen = min(finite_penalties)
    else:
        con_pen = 0.0

    crc = float("inf") if con_pen == float("inf") else info_cost + con_pen

    return CRCResult(
        switch_name=switch_name,
        CRC=round(crc, 4), info_cost=round(info_cost, 4),
        constraint_penalty=round(con_pen, 4),
        n_ablated=n_ablated, n_total=n_total,
        fraction_ablated=round(p_off, 4),
    )


def crc_profile(
    accepted_rows: list[dict],
    switches,
    constraints: list[Constraint] | None = None,
) -> dict[str, float]:
    """CRC for every switch in *switches*.

    Returns
    -------
    dict
        ``{switch_name: CRC_j}``
    """
    names = [sw.name for sw in switches]
    return {name: causal_replaceability_cost(name, accepted_rows, constraints)
            for name in names}


def crc_profile_full(
    accepted_rows: list[dict],
    switches,
    constraints: list[Constraint] | None = None,
) -> list[CRCResult]:
    """Full CRC computation for every switch, returning :class:`CRCResult` objects."""
    names = [sw.name for sw in switches]
    return [causal_replaceability_cost_full(name, accepted_rows, constraints)
            for name in names]
