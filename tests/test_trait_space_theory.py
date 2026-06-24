"""Regression tests for the trait-space contraction theorems.

The algebraic proofs live in ``docs/trait_space_contraction_theorem.md``.  These
checks guard the implementation across random monotone benefit/cost instances,
the exact edge-retention threshold, the no-fragmentation result under convexity,
the spatial-route construction, and the spatial-ABM correspondence.
"""
from __future__ import annotations

from random import Random

from causal_model.spatial_metapopulation_abm import sample_constrained_ecosystem
from causal_model.trait_space_theory import (
    InvasionFitnessModel,
    abm_invasion_factor,
    abm_viable_upper_edge,
    benefit_replacement_bound,
    compensation_threshold,
    edge_retention_threshold,
    is_interval,
    is_subset,
    random_model,
    spatial_route_contraction,
    upper_edge,
    verify_compensation_threshold,
    verify_incomplete_compensation_contracts,
    verify_no_fragmentation_under_convexity,
    verify_pure_loss_contracts,
)


# ---------------------------------------------------------------------------
# Algebraic-theorem regression checks
# ---------------------------------------------------------------------------

def test_T1_pure_loss_contracts():
    result = verify_pure_loss_contracts(n=4000, seed=0)
    assert result.proved, result.counterexample


def test_T2_incomplete_compensation_contracts():
    result = verify_incomplete_compensation_contracts(n=4000, seed=1)
    assert result.proved, result.counterexample


def test_T3_exact_edge_retention_threshold():
    result = verify_compensation_threshold(n=4000, seed=2)
    assert result.proved, result.counterexample


def test_T4_no_fragmentation_under_convexity():
    result = verify_no_fragmentation_under_convexity(n=4000, seed=3)
    assert result.proved, result.counterexample


# ---------------------------------------------------------------------------
# Concrete worked instance: exact threshold versus sufficient bound
# ---------------------------------------------------------------------------

def test_edge_retention_threshold_is_exact_and_benefit_bound_is_only_sufficient():
    # B(z) = 0.8z, C(z) = 0.5z, K = 0.1.  The intact upper edge is z*=1,
    # but it is strictly inside the pre-loss viable set: s_before(1)=0.4.
    grid = tuple(i / 20 for i in range(21))
    model = InvasionFitnessModel(
        grid=grid,
        benefit=tuple(0.8 * z for z in grid),
        cost=tuple(0.5 * z for z in grid),
        baseline=0.1,
    )
    edge_before = upper_edge(model, 1.0, 0.0)
    assert edge_before == 1.0
    assert upper_edge(model, 0.0, 0.0) < edge_before

    # Exact requirement for retaining z*=1: R >= C(1)-K = 0.4.
    r_keep = edge_retention_threshold(model)
    assert abs(r_keep - 0.4) < 1e-9
    assert abs(compensation_threshold(model) - r_keep) < 1e-12
    assert upper_edge(model, 0.0, r_keep) >= edge_before - 1e-9
    assert upper_edge(model, 0.0, r_keep - 0.05) < edge_before - 1e-9

    # B(1)=0.8 also retains the edge, but is not minimal in this example.
    r_replace = benefit_replacement_bound(model)
    assert abs(r_replace - 0.8) < 1e-9
    assert r_replace > r_keep
    assert upper_edge(model, 0.0, r_replace) >= edge_before - 1e-9


def test_benefit_bound_equals_exact_threshold_at_an_invasion_boundary():
    # Here z*=1 is exactly on the pre-loss boundary: B(1)-C(1)+K = 0.
    grid = tuple(i / 20 for i in range(21))
    model = InvasionFitnessModel(
        grid=grid,
        benefit=tuple(0.4 * z for z in grid),
        cost=tuple(0.5 * z for z in grid),
        baseline=0.1,
    )
    assert upper_edge(model, 1.0, 0.0) == 1.0
    assert abs(edge_retention_threshold(model) - 0.4) < 1e-9
    assert abs(benefit_replacement_bound(model) - 0.4) < 1e-9


def test_subset_helpers():
    assert is_subset((False, True, False), (True, True, False))
    assert not is_subset((True, False), (False, False))
    assert is_interval((False, True, True, False))
    assert not is_interval((True, False, True))


def test_pure_loss_is_subset_on_a_random_model():
    model = random_model(Random(7))
    before = model.viable_mask(1.0, 0.0)
    after = model.viable_mask(0.0, 0.0)
    assert is_subset(after, before)


# ---------------------------------------------------------------------------
# Proposition S1: spatial-route construction
# ---------------------------------------------------------------------------

def test_S1_spatial_route_contracts_and_can_fragment():
    contracted = 0
    fragmented = 0
    n = 100
    for seed in range(n):
        result = spatial_route_contraction(seed=seed)
        contracted += result["contracted"]
        fragmented += int(result["components_after"] > result["components_before"])
    assert contracted >= int(0.9 * n)
    assert fragmented >= int(0.5 * n)


# ---------------------------------------------------------------------------
# Correspondence with the spatial ABM
# ---------------------------------------------------------------------------

def test_abm_invasion_factor_is_increasing_in_benefit_and_decreasing_in_cost():
    common = dict(
        interaction_benefit=0.9,
        investment_reward=1.2,
        trait_cost=0.4,
        survival_tradeoff=0.02,
        base_survival=0.9,
        predation_pressure=0.1,
        predation_scale=1.0,
        repro_baseline=0.0,
        resident_trait=0.5,
    )
    z = 0.8
    g_full = abm_invasion_factor(z, interaction_scale=1.0, **common)
    g_lost = abm_invasion_factor(z, interaction_scale=0.0, **common)
    assert g_full > g_lost
    hi_cost = dict(common)
    hi_cost["trait_cost"] = 0.9
    assert abm_invasion_factor(z, interaction_scale=1.0, **hi_cost) < g_full


def test_abm_upper_edge_recedes_under_loss():
    """The leading theorem structure persists in most sampled ABM ecosystems."""
    rng = Random(0)
    recede = 0
    total = 0
    grid = [j / 40 for j in range(41)]
    for _ in range(200):
        parameters, _ = sample_constrained_ecosystem(rng)
        common = dict(
            interaction_benefit=parameters.interaction_benefit,
            investment_reward=parameters.investment_reward,
            trait_cost=parameters.trait_cost,
            survival_tradeoff=parameters.survival_tradeoff,
            base_survival=parameters.base_survival,
            predation_pressure=parameters.predation_pressure,
            predation_scale=1.0,
            density_threshold=parameters.density_threshold,
        )
        resident = max(
            grid,
            key=lambda z: abm_invasion_factor(
                z,
                interaction_scale=1.0,
                repro_baseline=0.0,
                resident_trait=z,
                **common,
            ),
        )
        edge_before = abm_viable_upper_edge(
            interaction_scale=1.0,
            repro_baseline=0.0,
            resident_trait=resident,
            **common,
        )
        edge_after = abm_viable_upper_edge(
            interaction_scale=0.0,
            repro_baseline=0.08 * parameters.interaction_benefit,
            resident_trait=resident,
            **common,
        )
        total += 1
        if edge_after <= edge_before + 1e-9:
            recede += 1
    assert recede / total >= 0.85
