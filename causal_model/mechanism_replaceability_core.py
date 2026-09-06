"""Mechanism replaceability inside a declared admissible region.

Historical implementations called the main quantity ``Causal Replaceability
Cost (CRC)`` and described switch-OFF filtering as a counterfactual ablation.
The publication-facing interpretation is narrower: the calculation asks how
much of the already accepted region remains when a declared mechanism switch is
restricted to OFF.

For switch ``j``, the informational component is

    -log2 P(s_j = 0 | A_epsilon).

An optional constraint component records the least external-constraint penalty
among accepted rows with ``s_j=0``.  The calculation is therefore a
set-membership / replaceability diagnostic conditional on the declared model,
prior, constraints, discrepancy and tolerance.  It does **not** by itself
identify a potential outcome, do-intervention effect or other causal
counterfactual distribution.

Two additive components
-----------------------

Informational cost
    ``-log2 P(s_j = 0 | A_epsilon)``
    How rare are accepted rows in which mechanism ``j`` is already OFF?

Constraint penalty
    ``min_{r in A_epsilon ∩ {s_j=0}} L_constraint(r)``
    The minimum declared external-constraint strain among those rows.

In Tier-A randomised-coefficient runs the constraint penalty is zero by
construction when every accepted row already satisfies the hard constraints,
so the quantity reduces to the informational cost.

Interpretation
--------------

- 0 bits: the mechanism is freely droppable inside the accepted region;
- finite positive value: accepted OFF rows exist but occupy a smaller share;
- infinity: no accepted row has the mechanism OFF under the declared region.

None of these states proves a causal intervention effect.  They describe
replaceability within ``A_epsilon``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from causal_model.counterfactual_ablation import ablate_switch
from causal_model.external_constraints import Constraint, total_penalty


@dataclass
class CRCResult:
    """Historical result container for one mechanism-replaceability calculation."""
    switch_name: str
    CRC: float
    info_cost: float
    constraint_penalty: float
    n_ablated: int
    n_total: int
    fraction_ablated: float

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
    """Historical API name for mechanism-replaceability cost inside ``A_epsilon``.

    The value is informational cost plus an optional external-constraint
    penalty.  The function name is preserved for frozen provenance and internal
    compatibility; publication-facing code should use the descriptive
    ``mechanism_replaceability_*`` aliases.
    """
    res = causal_replaceability_cost_full(switch_name, accepted_rows, constraints)
    return res.CRC


def causal_replaceability_cost_full(
    switch_name: str,
    accepted_rows: list[dict],
    constraints: list[Constraint] | None = None,
) -> CRCResult:
    """Return the full replaceability calculation and diagnostics."""
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
    """Historical backend profile over all declared switches."""
    names = [sw.name for sw in switches]
    return {name: causal_replaceability_cost(name, accepted_rows, constraints)
            for name in names}


def crc_profile_full(
    accepted_rows: list[dict],
    switches,
    constraints: list[Constraint] | None = None,
) -> list[CRCResult]:
    """Historical backend full profile over all declared switches."""
    names = [sw.name for sw in switches]
    return [causal_replaceability_cost_full(name, accepted_rows, constraints)
            for name in names]
