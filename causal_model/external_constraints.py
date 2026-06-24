"""External constraints on RACH parameters — definitions and penalty functions.

In the Causal Replaceability Cost (CRC) framework, a constraint specifies how
much "ecological or statistical strain" is required to reproduce the observed
pattern when one mechanism is ablated. Three constraint types are supported:

  hard    Absolutely forbidden region (e.g. probability > 1, count < 0).
          Penalty = ∞ for any violation; 0 otherwise.

  normal  Parameter has a literature prior with known mean μ and SE σ.
          Penalty = ((value − μ) / σ)².  A draw that reproduces the observed
          pattern only with an extreme shift from the literature value is
          penalised proportionally to the shift magnitude.

  range   Parameter has a documented plausible range [lower, upper] but no
          prior shape.  Penalty = 0 inside the range; rises as the fractional
          excess outside the range squared.

  soft    Qualitative expectation (sign, ranking).  Used for bottleneck
          attribution only; contributes 0 to the numerical penalty.

Constraint bottleneck
---------------------
When multiple constraints are active, ``constraint_bottleneck()`` identifies
which single constraint imposes the largest individual penalty in the minimum-
penalty ablated draw — the constraint most limiting the replacement path.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Constraint:
    """A single external constraint on a parameter or switch."""
    name: str                    # parameter name (must be a key in accepted row dicts)
    type: str                    # "hard" | "normal" | "range" | "soft"
    lower: float | None = None   # lower bound (hard / range)
    upper: float | None = None   # upper bound (hard / range)
    mu: float | None = None      # prior mean (normal)
    sigma: float | None = None   # prior SE  (normal); must be > 0
    weight: float = 1.0          # scaling weight for soft constraints (informational only)
    description: str = ""        # human-readable label


def penalty(constraint: Constraint, value: float) -> float:
    """Penalty for a single parameter value under its constraint.

    Returns 0.0 when the constraint is satisfied (normal type returns the
    Mahalanobis distance squared from the prior, which is 0 only at μ).
    Returns ``float("inf")`` for a violated hard constraint.
    """
    t = constraint.type
    if t == "hard":
        if constraint.lower is not None and value < constraint.lower:
            return float("inf")
        if constraint.upper is not None and value > constraint.upper:
            return float("inf")
        return 0.0
    if t == "normal":
        if constraint.sigma is None or constraint.sigma <= 0:
            return 0.0
        mu = constraint.mu if constraint.mu is not None else 0.0
        return ((value - mu) / constraint.sigma) ** 2
    if t == "range":
        lo = constraint.lower if constraint.lower is not None else -math.inf
        hi = constraint.upper if constraint.upper is not None else math.inf
        excess = max(0.0, lo - value, value - hi)
        width = hi - lo if (hi != math.inf and lo != -math.inf) else 1.0
        return (excess / max(width, 1e-12)) ** 2
    # soft — contributes 0 to numerical penalty
    return 0.0


def total_penalty(constraints: list[Constraint], parameter_values: dict) -> float:
    """Sum of individual penalties across all constraints.

    Missing parameter keys default to ``constraint.mu`` (for normal) or 0.0
    for other types — conservative (no extra penalty for missing data).
    """
    total = 0.0
    for c in constraints:
        if c.name not in parameter_values:
            default = c.mu if c.mu is not None else 0.0
        else:
            default = parameter_values[c.name]
        p = penalty(c, default)
        if p == float("inf"):
            return float("inf")
        total += p
    return total


def individual_penalties(constraints: list[Constraint], parameter_values: dict) -> dict[str, float]:
    """Return the individual penalty for each constraint by name."""
    return {c.name: penalty(c, parameter_values.get(c.name, c.mu or 0.0))
            for c in constraints}


def constraint_bottleneck(
    constraints: list[Constraint],
    ablated_rows: list[dict],
) -> Constraint | None:
    """Identify the constraint that most limits replacement.

    Among the ablated accepted rows (s_j = 0), finds the row with the
    minimum total constraint penalty (the "easiest" replacement path).
    Within that row, returns the constraint with the highest individual
    penalty — the bottleneck that limits how easy the replacement is.

    Returns ``None`` when ``constraints`` or ``ablated_rows`` is empty.
    """
    if not constraints or not ablated_rows:
        return None
    # Find the minimum-cost ablated row
    best_row = min(ablated_rows, key=lambda r: total_penalty(constraints, r))
    # Within that row, find the highest-penalty constraint
    indiv = individual_penalties(constraints, best_row)
    worst_name = max(indiv, key=lambda n: (indiv[n] if indiv[n] != float("inf") else 1e18))
    return next((c for c in constraints if c.name == worst_name), None)
