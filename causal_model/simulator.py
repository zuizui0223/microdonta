"""The RACH simulator contract and the two-tier evidence policy.

RACH is **simulator-agnostic**. Every core quantity (CA, D, R, OC, NOV) is a
functional of the admissible region ``A_ε`` — a set of accepted ``(θ, s)`` draws
— and is computed without any knowledge of *how* those draws were produced. The
generative map

    f : (x_obs context, θ, s)  ↦  pattern outputs

is a *user-supplied input* to RACH, not part of the framework. This module makes
that contract explicit (``SimulatorProtocol``) and pins down the evidentiary
status of the two kinds of ``f`` used in this repository, because that status
determines what the numbers are allowed to claim.

Why this matters (the decision)
-------------------------------
There are two simulators in this codebase and they are NOT interchangeable:

  TIER A — VALIDATED (randomised-coefficient generic f).
      The map is *structural only*: each candidate mechanism / edge is switched
      on or off, and every present edge is given a RANDOM sign and magnitude that
      is then marginalised out. No effect size is hand-chosen. The accepted
      region therefore reflects the *logic of the confound* (which mechanisms
      produce the same ordinal pattern), not any particular assumed economics.
      Instances: ``generality_sweep``, ``structure_discovery``,
      ``bergmann_worked_example``, ``ecological_rules_validation``. Conclusions
      drawn from these are conclusions about RACH's behaviour and are safe to
      report as validation of the *method*.

  TIER B — ILLUSTRATIVE (hand-coded phenomenological f).
      ``examples/campanula_izu`` / ``causal_model.phenomenological_model`` encode
      specific functional relationships with chosen coefficients
      (``guide += w·1.30·bombus·bgb·ob`` …). The posteriors then reflect the
      researcher's encoded assumptions, NOT data. These runs are for pipeline
      illustration and observation-design motivation only; any causal statement
      from them is *conditional on the encoded f* and must say so. The
      phenomenological module documents this in its own header.

The publishable claims rest on Tier A. Tier B is explicitly conditional.

The contract
------------
A RACH simulator is any callable that, given a context and a ``(θ, s)`` draw,
returns a flat dict of named outputs (population/trait values, signatures, …)
that ``P_sim`` can turn into the ordinal pattern space. Determinism of ``f`` is
what makes the NOV filter-update *exact* (see ``nov_calibration``); a stochastic
``f`` (e.g. an ABM) is admissible but the NOV exactness weakens to the Monte
Carlo limit.

This module also provides :func:`randomised_linear_f`, the generic Tier-A map
that the validated experiments instantiate: a linear forward-propagation through
a DAG with random signed weights. It is the reusable embodiment of the
"make the mechanism the random object, marginalise the economics" principle.
"""
from __future__ import annotations

import random
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Evidence tiers — the status a result inherits from its simulator
# ---------------------------------------------------------------------------

TIER_VALIDATED = "validated"      # randomised-coefficient generic f (Tier A)
TIER_ILLUSTRATIVE = "illustrative"  # hand-coded phenomenological f (Tier B)

#: Modules whose accepted regions come from a Tier-A (validated) simulator.
VALIDATED_SIMULATOR_MODULES = (
    "causal_model.generality_sweep",
    "causal_model.structure_discovery",
    "causal_model.bergmann_worked_example",
    "causal_model.ecological_rules_validation",
)

#: Modules whose accepted regions come from a Tier-B (illustrative) simulator.
ILLUSTRATIVE_SIMULATOR_MODULES = (
    "causal_model.phenomenological_model",
    "examples.campanula_izu.campanula_phenomenological",
)


def evidence_tier(module_name: str) -> str:
    """Return the evidence tier (``TIER_VALIDATED`` / ``TIER_ILLUSTRATIVE``) for a
    simulator module, so callers can label what a result is allowed to claim.

    Unknown modules default to ``TIER_ILLUSTRATIVE`` — the conservative choice:
    a result is illustrative until its simulator is known to randomise (and
    thereby marginalise) all effect sizes.
    """
    if module_name in VALIDATED_SIMULATOR_MODULES:
        return TIER_VALIDATED
    return TIER_ILLUSTRATIVE


# ---------------------------------------------------------------------------
# The simulator contract
# ---------------------------------------------------------------------------

@runtime_checkable
class SimulatorProtocol(Protocol):
    """The RACH generative map ``f``.

    A simulator maps a context and a ``(θ, s)`` draw to a flat dict of named
    numeric outputs. ``s`` is the binary mechanism/edge vector; ``theta`` carries
    any continuous latent parameters (including, for Tier-A maps, the random
    signed edge weights that marginalise the economics).

    The returned dict must contain every column that the pattern map ``P_sim``
    and the candidate-observation filters will read (e.g. ``"Hachijo_selfing_rate"``
    or ``"v_T1"``).
    """

    def __call__(self, context: dict, theta: dict, s: dict) -> dict:
        ...


# ---------------------------------------------------------------------------
# Tier-A generic map: randomised-coefficient linear forward propagation
# ---------------------------------------------------------------------------

def randomised_linear_f(
    rng: random.Random,
    present: dict[str, bool],
    nodes: tuple[str, ...],
    parents: dict[str, list[tuple[str, str]]],
    *,
    weight_lo: float = 0.5,
    weight_hi: float = 1.5,
    signed: bool = True,
    source_value: float = 1.0,
) -> dict[str, float]:
    """Forward-propagate a unit driver through a DAG with RANDOM signed weights.

    This is the Tier-A (validated) generic ``f``: the structure (which edges are
    ``present``) is the object of inference, while every present edge's effect
    size is drawn fresh and marginalised. No coefficient is hand-chosen, so the
    accepted region reflects only the confound logic.

    Parameters
    ----------
    rng:
        Seeded RNG (the marginalisation of economics happens through it).
    present:
        ``{edge_name: bool}`` — which directed edges are active in this draw.
    nodes:
        Node names in topological order; ``nodes[0]`` is the exogenous driver.
    parents:
        ``{node: [(parent_node, edge_name), ...]}`` for every non-source node.
    weight_lo, weight_hi:
        Magnitude range for each present edge's weight.
    signed:
        If True, each weight gets a random ± sign (the usual setting: the
        direction of each mechanism's effect is itself unknown).
    source_value:
        Value injected at the source node (a unit cline increase by default).

    Returns
    -------
    dict
        ``{node: net_propagated_value}`` for every node (the source included).
    """
    weight = {
        e: (rng.choice((-1.0, 1.0)) if signed else 1.0) * rng.uniform(weight_lo, weight_hi)
        for e in present
    }
    v: dict[str, float] = {nodes[0]: float(source_value)}
    for node in nodes[1:]:
        s = 0.0
        for parent, edge in parents.get(node, []):
            if present.get(edge):
                s += weight[edge] * v.get(parent, 0.0)
        v[node] = s
    return v
