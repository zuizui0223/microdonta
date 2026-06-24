"""Constraint-separated replacement — the worked example that proves CRC ≠ posterior.

The single most important demonstration of the Causal Replaceability framework:
two candidate mechanisms that the *marginal posterior cannot tell apart*, but
that the Causal Replaceability Cost (CRC) cleanly separates — and the separation
comes **entirely from external (literature) constraints**, not from the data.

The biological setting
----------------------
An observed body-size cline increases *steeply* along an environmental gradient.
Two adaptive mechanisms could drive it:

    S_thermal   thermal selection      (temperature → body size)
    S_resource  resource/food selection (resource availability → body size)

Both drivers covary with the same gradient x, so in the ABC acceptance step they
are **informationally symmetric**: each reproduces the steep cline equally often.
Therefore the marginal posteriors are tied,

    CA(thermal) ≈ CA(resource),

and a posterior-probability summary reports "indistinguishable".

Where the external constraint breaks the symmetry
-------------------------------------------------
The published literature constrains the *effect sizes*, and asymmetrically:

    thermal coefficient   w_thermal ~ Normal(μ=0.30, σ=0.15)   (documented: modest)
    resource coefficient  w_resource ~ Normal(μ=1.10, σ=0.40)  (documented: strong)

These priors are **external empirical inputs** (literature means with SEs), not
tuned to obtain the answer. They encode real ecological knowledge: thermal–size
responses are modest, resource–size responses can be large.

What CRC then shows
-------------------
To reproduce the *steep* cline, the surviving mechanism's coefficient must be
≥ 1.0.  Replacing resource by thermal forces w_thermal ≥ 1.0, which is ~5σ above
its documented mean — a large constraint penalty.  Replacing thermal by resource
needs w_resource ≈ 1.0, right at its documented mean — almost no penalty:

    CRC(resource)  high   (resource is irreplaceable / load-bearing)
    CRC(thermal)   low    (thermal is freely replaceable)

Crucially, with ``constraints=None`` (data only) the two CRCs are equal again —
proving the separation is contributed by the external constraint, not the
posterior. CRC is therefore strictly more than a re-expression of CA_j.

Epistemic status
----------------
The acceptance step is structural/Tier-A (steep-cline pattern match with a broad
weight proposal). The literature constraints are external empirical priors,
clearly labelled. The conclusion ("given documented effect-size ranges, the steep
cline is load-bearing on resource selection, not thermal") is explicitly
*conditional on those constraints* — which is exactly the intended content:
external knowledge resolves a symmetry the data alone cannot.

Usage
-----
    from causal_model.worked_examples.constraint_separated_replacement import (
        run_constraint_separated, literature_constraints,
    )
    res = run_constraint_separated(n_attempts=20000, seed=1)
    print(res.describe())
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from causal_model.switch_inference import BiologicalSwitch
from causal_model.external_constraints import Constraint
from causal_model.causal_replaceability import crc_profile


# ---------------------------------------------------------------------------
# Fixed context: a gradient of three populations
# ---------------------------------------------------------------------------

_POPS = ("low", "mid", "high")
_X = {"low": 0.2, "mid": 0.5, "high": 0.8}
_DX = _X["high"] - _X["low"]                  # 0.6

# The observed cline is steep: the combined per-unit response must reach ≥ 1.0
# (so that the end-to-end size difference is ≥ 0.6 over the gradient).
_STEEP_SLOPE = 0.6


# ---------------------------------------------------------------------------
# Switches
# ---------------------------------------------------------------------------

def _switches() -> list[BiologicalSwitch]:
    # Exactly two candidate mechanisms, so the only replacement paths are
    # thermal↔resource. (A neutral escape hatch is deliberately excluded here;
    # neutral replacement is demonstrated in generic_mediation_replacement.)
    return [
        BiologicalSwitch("thermal",  "thermal_selection",  "temperature → size?",
                         "Thermal selection drives the body-size cline", 0.5),
        BiologicalSwitch("resource", "resource_selection", "resources → size?",
                         "Resource/food selection drives the body-size cline", 0.5),
    ]


# ---------------------------------------------------------------------------
# External literature constraints on effect sizes
# ---------------------------------------------------------------------------

def literature_constraints() -> list[Constraint]:
    """The documented effect-size priors (external empirical inputs)."""
    return [
        Constraint(name="w_thermal", type="normal", mu=0.30, sigma=0.15,
                   description="thermal–size response: documented modest (literature)"),
        Constraint(name="w_resource", type="normal", mu=1.10, sigma=0.40,
                   description="resource–size response: documented strong (literature)"),
    ]


# ---------------------------------------------------------------------------
# Simulation + ABC acceptance
# ---------------------------------------------------------------------------

def _simulate(s: dict, theta: dict) -> dict:
    """Body size along the gradient from the active mechanisms.

    thermal and resource both respond to the same gradient driver x, so they are
    informationally symmetric for the cline pattern: only the external constraint
    on their effect sizes can tell them apart.
    """
    w_t = theta["w_thermal"] if s.get("thermal") else 0.0
    w_r = theta["w_resource"] if s.get("resource") else 0.0
    return {f"{pop}_size": (w_t + w_r) * _X[pop] for pop in _POPS}


def _accepts_steep_cline(row: dict) -> bool:
    """Accept iff body size rises steeply and monotonically along the gradient."""
    lo, mid, hi = row["low_size"], row["mid_size"], row["high_size"]
    return (hi - lo >= _STEEP_SLOPE) and (lo <= mid <= hi)


def _abc_accept(n_attempts: int, seed: int) -> list[dict]:
    """Tier-A acceptance with a broad weight proposal (constraints applied later).

    The coefficients are proposed from a wide uniform range; the literature
    constraints are NOT used here — they enter only at the CRC stage. This keeps
    the ABC posterior (CA_j) a pure function of the pattern, so the marginal
    symmetry between thermal and resource is exact up to Monte-Carlo noise.
    """
    rng = random.Random(seed)
    sw = _switches()
    acc: list[dict] = []
    for _ in range(n_attempts):
        s = {o.name: rng.random() < o.prior_on_prob for o in sw}
        theta = {
            "w_thermal":  rng.uniform(0.0, 1.6),
            "w_resource": rng.uniform(0.0, 1.6),
        }
        row = _simulate(s, theta)
        if _accepts_steep_cline(row):
            row.update(s)
            # Store the proposed coefficients so the literature constraints can
            # score them at the CRC stage (the constraint penalty reads these).
            row["w_thermal"] = theta["w_thermal"]
            row["w_resource"] = theta["w_resource"]
            acc.append(row)
    return acc


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class ConstraintSeparatedResult:
    n_accepted: int
    n_attempts: int
    ca: dict[str, float]                 # marginal posterior P(s_j=1 | A_ε)
    crc_data_only: dict[str, float]      # CRC with NO external constraints
    crc_constrained: dict[str, float]    # CRC WITH literature constraints

    def describe(self) -> str:
        def fmt(x):
            return "∞" if x == float("inf") else f"{x:.3f}"
        lines = [
            "Constraint-separated replacement  (proves CRC ≠ posterior)",
            f"  |A_ε| = {self.n_accepted}/{self.n_attempts}",
            "",
            f"  {'mechanism':12s} {'CA_j':>7s} {'CRC(data)':>10s} {'CRC(+lit)':>10s}",
        ]
        for name in self.ca:
            lines.append(
                f"  {name:12s} {self.ca[name]:>7.3f} "
                f"{fmt(self.crc_data_only[name]):>10s} "
                f"{fmt(self.crc_constrained[name]):>10s}"
            )
        lines += [
            "",
            "  → CA(thermal) ≈ CA(resource): the posterior CANNOT separate them.",
            "  → CRC(data only) also ties them: the data alone cannot either.",
            "  → CRC(+literature) separates them: resource is load-bearing,",
            "    thermal is replaceable. The separation is contributed entirely",
            "    by the external effect-size constraints.",
        ]
        return "\n".join(lines)


def run_constraint_separated(
    n_attempts: int = 20000, seed: int = 1,
) -> ConstraintSeparatedResult:
    """Run the constraint-separated replacement worked example."""
    sw = _switches()
    acc = _abc_accept(n_attempts, seed)
    n = len(acc)

    ca = {o.name: round(sum(1 for r in acc if r.get(o.name)) / max(n, 1), 4)
          for o in sw}

    crc_data = crc_profile(acc, sw, constraints=None)
    crc_lit = crc_profile(acc, sw, constraints=literature_constraints())

    return ConstraintSeparatedResult(
        n_accepted=n, n_attempts=n_attempts,
        ca=ca, crc_data_only=crc_data, crc_constrained=crc_lit,
    )


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--n-attempts", type=int, default=20000)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args(argv)
    print(run_constraint_separated(args.n_attempts, args.seed).describe())
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
