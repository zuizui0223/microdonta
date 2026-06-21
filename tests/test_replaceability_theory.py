"""Machine verification of the Causal Replaceability theorems.

These tests are the proof-corroboration: Theorem A (the Elimination Principle)
and its Lemma are checked EXHAUSTIVELY (exact enumeration of A(O)) over thousands
of randomly generated structural models. A single counterexample anywhere would
fail the suite. Theorem B's monotonicity and strict-refinement claims are checked
directly.
"""
import math
import random

import pytest

from causal_model.replaceability_theory import (
    StructuralModel,
    Observation,
    admissible_configs,
    structural_crc,
    forced_off,
    forced_on,
    is_last_driver_standing,
    private_witnesses,
    null_off,
    verify_lemma_elimination,
    verify_theorem_A,
    verify_present_focal_cannot_pin,
    random_instance,
    corroborate,
    info_term_from_ca,
    info_term_is_monotone,
)


# ---------------------------------------------------------------------------
# Theorem A + Lemma: exhaustive machine verification over random models
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("seed", [0, 1, 2, 3, 7, 42, 99])
def test_theorem_A_and_lemma_hold_over_random_models(seed):
    rng = random.Random(seed)
    nonempty = 0
    for _ in range(3000):
        model, obs = random_instance(rng)
        if not admissible_configs(model, obs):
            continue
        nonempty += 1
        assert verify_theorem_A(model, obs).holds
        assert verify_lemma_elimination(model, obs).holds
    assert nonempty > 100, "expected many non-empty regions to actually test"


def test_corroborate_runs_clean():
    summary = corroborate(n_trials=4000, seed=5)
    assert summary["theorem_A"] == "verified"
    assert summary["lemma_elimination"] == "verified"
    assert summary["nonempty_regions"] > 100


# ---------------------------------------------------------------------------
# The Corollary: shared (focal) present traits alone pin nothing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("seed", [0, 1, 2, 3, 11])
def test_shared_present_traits_alone_never_pin_a_mechanism(seed):
    rng = random.Random(seed)
    tested = 0
    for _ in range(4000):
        model, obs = random_instance(rng)
        # restrict to the corollary's regime: only present, only shared traits
        present_shared = tuple(t for t in obs.present
                               if len(model.driver_sets[t]) >= 2)
        obs2 = Observation(present=present_shared, null=())
        if not present_shared or not admissible_configs(model, obs2):
            continue
        tested += 1
        chk = verify_present_focal_cannot_pin(model, obs2)
        assert chk.holds, chk.detail
    assert tested > 50


# ---------------------------------------------------------------------------
# A concrete, hand-built instance illustrating the principle
# (mirrors the Drosophila confound: body-size shared; private witnesses)
# ---------------------------------------------------------------------------

def _drosophila_like_model():
    # mechanisms: 0 = thermal, 1 = demographic, 2 = inversion
    return StructuralModel(
        K=3,
        driver_sets={
            "body_size":     frozenset({0, 1, 2}),  # shared focal trait
            "neutral_marker": frozenset({1}),        # private witness of demography
            "inversion_freq": frozenset({2}),        # private witness of inversion
        },
    )


def test_focal_trait_alone_pins_nothing():
    model = _drosophila_like_model()
    obs = Observation(present=("body_size",))
    configs = admissible_configs(model, obs)
    # no mechanism is irreplaceable on the focal cline alone
    assert all(structural_crc(j, configs) != float("inf") for j in range(3))


def test_necessity_requires_eliminating_alternatives_via_nulls():
    model = _drosophila_like_model()
    # observe focal cline present, AND both competitors' private signatures NULL
    obs = Observation(present=("body_size",), null=("neutral_marker", "inversion_freq"))
    configs = admissible_configs(model, obs)
    # demography (1) and inversion (2) are eliminated; thermal (0) is now the
    # last driver standing for body_size → irreplaceable
    assert forced_off(configs, 1) and forced_off(configs, 2)
    assert structural_crc(0, configs) == float("inf")
    assert is_last_driver_standing(model, obs, 0)


def test_present_private_witness_pins_its_mechanism():
    model = _drosophila_like_model()
    obs = Observation(present=("neutral_marker",))   # private to demography (1)
    configs = admissible_configs(model, obs)
    assert structural_crc(1, configs) == float("inf")


def test_private_witnesses_are_identified():
    model = _drosophila_like_model()
    assert private_witnesses(model, 1) == ["neutral_marker"]
    assert private_witnesses(model, 2) == ["inversion_freq"]
    assert private_witnesses(model, 0) == []   # thermal has NO private witness


def test_mechanism_without_private_witness_can_still_be_pinned_by_elimination():
    """Thermal (0) has no private witness, yet becomes necessary once its
    competitors are eliminated — necessity need not come from a private witness
    of j itself, but always from making j the last driver standing."""
    model = _drosophila_like_model()
    obs = Observation(present=("body_size",), null=("neutral_marker", "inversion_freq"))
    assert not private_witnesses(model, 0)
    configs = admissible_configs(model, obs)
    assert structural_crc(0, configs) == float("inf")


# ---------------------------------------------------------------------------
# Theorem B: decomposition / strict refinement
# ---------------------------------------------------------------------------

def test_info_term_is_strictly_increasing_in_ca():
    assert info_term_is_monotone([i / 100 for i in range(100)])
    # and explicit values
    assert info_term_from_ca(0.5) == pytest.approx(1.0)   # −log2(0.5)
    assert info_term_from_ca(0.75) == pytest.approx(2.0)
    assert info_term_from_ca(0.0) == 0.0
    assert info_term_from_ca(1.0) == float("inf")


def test_without_constraints_crc_is_ordinally_equal_to_posterior():
    """Theorem B(i): with Λ≡0, CRC ranking = CA ranking."""
    from causal_model.causal_replaceability import causal_replaceability_cost
    # two mechanisms with different marginals, no constraints
    rows = (
        [{"a": True,  "b": True}]  * 60 +   # CA(a)=0.8, CA(b)=0.5
        [{"a": True,  "b": False}] * 20 +
        [{"a": False, "b": False}] * 20
    )
    crc_a = causal_replaceability_cost("a", rows)
    crc_b = causal_replaceability_cost("b", rows)
    ca_a = sum(1 for r in rows if r["a"]) / len(rows)
    ca_b = sum(1 for r in rows if r["b"]) / len(rows)
    # higher CA ⟺ higher CRC (same order)
    assert (ca_a > ca_b) == (crc_a > crc_b)


def test_constraints_can_reorder_equal_posterior_mechanisms():
    """Theorem B(ii): equal CA_j, but Λ separates ⇒ CRC strictly refines."""
    from causal_model.causal_replaceability import causal_replaceability_cost
    from causal_model.external_constraints import Constraint
    # a and b have identical marginal CA (both on in exactly half the rows),
    # but the ablated (off) rows carry different parameter values
    rows = (
        [{"a": True,  "b": False, "pa": 0.0, "pb": 5.0}] * 50 +
        [{"a": False, "b": True,  "pa": 5.0, "pb": 0.0}] * 50
    )
    ca_a = sum(1 for r in rows if r["a"]) / len(rows)
    ca_b = sum(1 for r in rows if r["b"]) / len(rows)
    assert ca_a == ca_b == 0.5      # posterior ties them exactly
    cons = [Constraint(name="pa", type="normal", mu=0.0, sigma=1.0),
            Constraint(name="pb", type="normal", mu=0.0, sigma=1.0)]
    crc_a = causal_replaceability_cost("a", rows, cons)
    crc_b = causal_replaceability_cost("b", rows, cons)
    # ablating a keeps a-off rows (pa=5 → penalty 25); ablating b keeps b-off
    # rows (pb=5 → penalty 25): by symmetry equal here, so build asymmetry:
    assert crc_a == crc_b   # symmetric construction ⇒ still tied
    # now break symmetry: only pa is constrained
    crc_a2 = causal_replaceability_cost("a", rows, [cons[0]])
    crc_b2 = causal_replaceability_cost("b", rows, [cons[0]])
    assert crc_a2 != crc_b2, "a single asymmetric constraint must split equal-CA mechanisms"
