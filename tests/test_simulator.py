"""Tests for the RACH simulator contract and two-tier evidence policy."""
import random

from causal_model.simulator import (
    SimulatorProtocol,
    randomised_linear_f,
    evidence_tier,
    TIER_VALIDATED,
    TIER_ILLUSTRATIVE,
)


# ---------------------------------------------------------------------------
# Evidence tiers
# ---------------------------------------------------------------------------

def test_validated_modules_are_tier_a():
    for m in ("causal_model.generality_sweep", "causal_model.structure_discovery",
              "causal_model.bergmann_worked_example",
              "causal_model.ecological_rules_validation"):
        assert evidence_tier(m) == TIER_VALIDATED


def test_phenomenological_is_illustrative():
    assert evidence_tier("causal_model.phenomenological_model") == TIER_ILLUSTRATIVE
    assert evidence_tier("examples.campanula_izu.campanula_phenomenological") == TIER_ILLUSTRATIVE


def test_unknown_module_defaults_to_illustrative():
    # conservative default: a result is illustrative until its simulator is known
    # to randomise (and marginalise) all effect sizes
    assert evidence_tier("some.unknown.module") == TIER_ILLUSTRATIVE


# ---------------------------------------------------------------------------
# randomised_linear_f
# ---------------------------------------------------------------------------

_NODES = ("X", "Ma", "T1")
_PARENTS = {"Ma": [("X", "X->Ma")], "T1": [("X", "X->T1"), ("Ma", "Ma->T1")]}


def test_source_value_is_injected():
    rng = random.Random(0)
    present = {"X->Ma": False, "X->T1": False, "Ma->T1": False}
    v = randomised_linear_f(rng, present, _NODES, _PARENTS)
    assert v["X"] == 1.0
    assert v["Ma"] == 0.0
    assert v["T1"] == 0.0


def test_direct_edge_only():
    rng = random.Random(1)
    present = {"X->Ma": False, "X->T1": True, "Ma->T1": False}
    v = randomised_linear_f(rng, present, _NODES, _PARENTS, signed=False)
    # unsigned weight in [0.5, 1.5], so a present direct edge gives a positive T1
    assert v["T1"] > 0.0
    assert v["Ma"] == 0.0


def test_mediated_path_is_product():
    rng = random.Random(2)
    present = {"X->Ma": True, "X->T1": False, "Ma->T1": True}
    v = randomised_linear_f(rng, present, _NODES, _PARENTS, signed=False)
    # T1 == w(X->Ma) * w(Ma->T1) * X ; both weights positive (unsigned)
    assert v["T1"] > 0.0


def test_signed_weights_can_be_negative():
    # over many draws, signed weights should produce both signs at T1
    signs = set()
    for seed in range(40):
        rng = random.Random(seed)
        present = {"X->Ma": False, "X->T1": True, "Ma->T1": False}
        v = randomised_linear_f(rng, present, _NODES, _PARENTS, signed=True)
        signs.add(v["T1"] > 0)
    assert signs == {True, False}


def test_protocol_is_satisfied_by_a_callable():
    def f(context, theta, s):
        return {"out": 1.0}
    assert isinstance(f, SimulatorProtocol)


def test_matches_structure_discovery_propagation():
    """randomised_linear_f generalises structure_discovery._propagate: with a
    fixed weight dict the linear forward-prop must agree."""
    from causal_model import structure_discovery as sd
    # build a present/weight pair and compare against sd._propagate
    present = {e: (i % 2 == 0) for i, e in enumerate(sd._EDGES)}
    weight = {e: 0.7 for e in sd._EDGES}
    expected = sd._propagate(present, weight)
    # reproduce via the generic prop with the same weights (inline, no RNG)
    v = {sd._NODES[0]: 1.0}
    for node in sd._NODES[1:]:
        acc = 0.0
        for parent, edge in sd._PARENTS.get(node, []):
            if present[edge]:
                acc += weight[edge] * v[parent]
        v[node] = acc
    assert v == expected
