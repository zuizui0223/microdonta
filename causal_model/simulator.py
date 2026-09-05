"""Simulator contract and two-tier evidence policy for mechanism-resolution design.

Mechanism-Resolving Observation Design is simulator-agnostic. Every publication
quantity is a functional of the admissible mechanism region ``A_ε`` — a set of
accepted ``(θ, s)`` draws — and is computed without assuming how those draws were
produced. The generative map

    f : (x_obs context, θ, s)  ↦  pattern outputs

is a user-supplied input to the method, not the method itself. This module makes
that contract explicit (``SimulatorProtocol``) and pins down the evidentiary
status of the two kinds of ``f`` used in this repository, because that status
determines what the resulting numbers are allowed to claim.

Why this matters
----------------
There are two simulator classes in this codebase and they are not interchangeable:

  TIER A — VALIDATED (randomised-coefficient generic f).
      The map is structural only: each candidate mechanism / edge is switched on
      or off, and every present edge is given a random sign and magnitude that is
      then marginalised out. No effect size is hand-chosen. The accepted region
      therefore reflects the confound logic — which mechanisms produce the same
      ordinal pattern — rather than any particular assumed coefficient set.
      Instances include ``generality_sweep``, ``structure_discovery``,
      ``bergmann_worked_example`` and ``ecological_rules_validation``.
      Conclusions drawn from these runs concern behaviour of the method itself.

  TIER B — ILLUSTRATIVE (hand-coded phenomenological f).
      ``examples/campanula_izu`` / ``causal_model.phenomenological_model`` encode
      specific functional relationships with chosen coefficients
      (``guide += w·1.30·bombus·bgb·ob`` …). Their posteriors reflect the encoded
      assumptions rather than empirical effect-size estimation. These runs are
      for pipeline illustration and observation-design motivation only; any
      causal statement from them is conditional on the encoded f.

The publishable validation claims rest on Tier A. Tier B is explicitly
conditional.

The contract
------------
A simulator is any callable that, given a context and a ``(θ, s)`` draw, returns
a flat dict of named outputs (population/trait values, signatures, …) that
``P_sim`` can map into the declared pattern space. Determinism of ``f`` is what
makes stored-region filtering exact for the tested information-value calibration
cases; a stochastic ``f`` (for example an ABM) is admissible but that exactness
weakens to a Monte Carlo approximation.

This module also provides :func:`randomised_linear_f`, the generic Tier-A map
used by validated experiments: linear forward propagation through a DAG with
random signed weights. It is the reusable embodiment of the principle “make the
mechanism the random object and marginalise nuisance effect magnitudes.”
"""
from __future__ import annotations

import random
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Evidence tiers — the status a result inherits from its simulator
# ---------------------------------------------------------------------------

TIER_VALIDATED = "validated"        # randomised-coefficient generic f (Tier A)
TIER_ILLUSTRATIVE = "illustrative"  # hand-coded phenomenological f (Tier B)

#: Modules whose accepted regions come from a Tier-A (validated) simulator.
VALIDATED_SIMULATOR_MODULES = (
    "causal_model.generality_sweep",
    "causal_model.structure_discovery",
    "causal_model.bergmann_worked_example",
    "causal_model.ecological_rules_validation",
    "causal_model.campanula_structural",
    "causal_model.adaptation_plasticity",
    "causal_model.fitness_rule_discovery",
    "causal_model.converse_bergmann",
    "causal_model.neutral_adaptive",
    "causal_model.campanula_real_data",
    "causal_model.worked_examples.generic_mediation_replacement",
    "causal_model.worked_examples.constraint_separated_replacement",
    "causal_model.worked_examples.drosophila_latitudinal_cline",
)

#: Modules whose accepted regions come from a Tier-B (illustrative) simulator.
ILLUSTRATIVE_SIMULATOR_MODULES = (
    "causal_model.phenomenological_model",
    "examples.campanula_izu.campanula_phenomenological",
)


def evidence_tier(module_name: str) -> str:
    """Return the evidence tier for a simulator module.

    Unknown modules default to ``TIER_ILLUSTRATIVE`` — the conservative choice:
    a result is illustrative until its simulator is known to randomise and
    marginalise nuisance effect magnitudes.
    """
    if module_name in VALIDATED_SIMULATOR_MODULES:
        return TIER_VALIDATED
    return TIER_ILLUSTRATIVE


# ---------------------------------------------------------------------------
# The simulator contract
# ---------------------------------------------------------------------------

@runtime_checkable
class SimulatorProtocol(Protocol):
    """Generative map ``f`` used by the observation-design method.

    A simulator maps a context and a ``(θ, s)`` draw to a flat dict of named
    numeric outputs. ``s`` is the binary mechanism/edge vector; ``theta`` carries
    continuous latent parameters, including random signed edge weights for
    Tier-A maps.

    The returned dict must contain every column that the pattern map ``P_sim``
    and candidate-observation filters will read (for example
    ``"Hachijo_selfing_rate"`` or ``"v_T1"``).
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
    """Forward-propagate a unit driver through a DAG with random signed weights.

    This is the Tier-A generic ``f``: structure (which edges are ``present``) is
    the object of inference, while every present edge's effect size is drawn
    afresh and marginalised. No coefficient is hand-chosen, so the accepted
    region reflects only the declared confound structure.

    Parameters
    ----------
    rng:
        Seeded RNG used to marginalise nuisance effect magnitudes.
    present:
        ``{edge_name: bool}`` — which directed edges are active in this draw.
    nodes:
        Node names in topological order; ``nodes[0]`` is the exogenous driver.
    parents:
        ``{node: [(parent_node, edge_name), ...]}`` for every non-source node.
    weight_lo, weight_hi:
        Magnitude range for each present edge's weight.
    signed:
        If True, each weight receives a random ± sign.
    source_value:
        Value injected at the source node.

    Returns
    -------
    dict
        ``{node: net_propagated_value}`` for every node, including the source.
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
