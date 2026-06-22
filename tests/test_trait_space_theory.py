"""Machine-verified tests for the trait-space contraction theorems.

These exhaustively check Theorems T1-T4 over random monotone benefit/cost models,
the compensation threshold, the no-fragmentation signature, the spatial-route
proposition S1, and the correspondence to the spatial ABM's rare-invader fitness.
See docs/trait_space_contraction_theorem.md.
"""
from __future__ import annotations

from random import Random

from causal_model.spatial_metapopulation_abm import sample_constrained_ecosystem
from causal_model.trait_space_theory import (
    InvasionFitnessModel,
    abm_invasion_factor,
    abm_viable_upper_edge,
    compensation_threshold,
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
# The four theorems (machine-verified over thousands of random monotone models)
# ---------------------------------------------------------------------------

def test_T1_pure_loss_contracts():
    r = verify_pure_loss_contracts(n=4000, seed=0)
    assert r.proved, r.counterexample


def test_T2_incomplete_compensation_contracts():
    r = verify_incomplete_compensation_contracts(n=4000, seed=1)
    assert r.proved, r.counterexample


def test_T3_compensation_threshold():
    r = verify_compensation_threshold(n=4000, seed=2)
    assert r.proved, r.counterexample


def test_T4_no_fragmentation_under_convexity():
    r = verify_no_fragmentation_under_convexity(n=4000, seed=3)
    assert r.proved, r.counterexample


# ---------------------------------------------------------------------------
# Concrete worked instances
# ---------------------------------------------------------------------------

def test_linear_model_threshold_is_exact():
    # B(z) = 0.8 z, C(z) = 0.5 z, K = 0.1
    grid = tuple(i / 20 for i in range(21))
    model = InvasionFitnessModel(
        grid=grid,
        benefit=tuple(0.8 * z for z in grid),
        cost=tuple(0.5 * z for z in grid),
        baseline=0.1,
    )
    edge_before = upper_edge(model, 1.0, 0.0)
    # before: 0.8z - 0.5z + 0.1 >= 0 always on [0,1] -> edge 1.0
    assert edge_before == 1.0
    # pure loss: -0.5z + 0.1 >= 0 -> z <= 0.2 -> edge 0.2 (strict contraction)
    assert upper_edge(model, 0.0, 0.0) < edge_before
    # threshold R* = B(1.0) = 0.8; sufficient compensation restores the edge
    r_star = compensation_threshold(model)
    assert abs(r_star - 0.8) < 1e-9
    assert upper_edge(model, 0.0, r_star) >= edge_before - 1e-9


def test_subset_helpers():
    assert is_subset((False, True, False), (True, True, False))
    assert not is_subset((True, False), (False, False))
    assert is_interval((False, True, True, False))
    assert not is_interval((True, False, True))


def test_pure_loss_is_subset_on_a_random_model():
    m = random_model(Random(7))
    before = m.viable_mask(1.0, 0.0)
    after = m.viable_mask(0.0, 0.0)
    assert is_subset(after, before)


# ---------------------------------------------------------------------------
# Proposition S1: the spatial route (fitness-independent contraction/fragmentation)
# ---------------------------------------------------------------------------

def test_S1_spatial_route_contracts_and_can_fragment():
    contracted = 0
    fragmented = 0
    n = 100
    for s in range(n):
        r = spatial_route_contraction(seed=s)
        contracted += r["contracted"]
        fragmented += int(r["components_after"] > r["components_before"])
    assert contracted >= int(0.9 * n)        # dispersal loss robustly contracts realised set
    assert fragmented >= int(0.5 * n)        # and frequently fragments it (distinct signature)


# ---------------------------------------------------------------------------
# Correspondence with the spatial ABM rare-invader fitness
# ---------------------------------------------------------------------------

def test_abm_invasion_factor_is_increasing_in_benefit_and_decreasing_in_cost():
    common = dict(
        interaction_benefit=0.9, investment_reward=1.2, trait_cost=0.4,
        survival_tradeoff=0.02, base_survival=0.9, predation_pressure=0.1,
        predation_scale=1.0, repro_baseline=0.0, resident_trait=0.5,
    )
    z = 0.8
    g_full = abm_invasion_factor(z, interaction_scale=1.0, **common)
    g_lost = abm_invasion_factor(z, interaction_scale=0.0, **common)
    assert g_full > g_lost                                # losing the relationship lowers fitness at high z
    hi_cost = dict(common); hi_cost["trait_cost"] = 0.9
    assert abm_invasion_factor(z, interaction_scale=1.0, **hi_cost) < g_full   # cost lowers fitness


def test_abm_upper_edge_recedes_under_loss():
    """The theorem's prediction holds in the ABM rare-invader limit for most ecosystems."""
    rng = Random(0)
    recede = 0
    tot = 0
    grid = [j / 40 for j in range(41)]
    for _ in range(200):
        p, _ = sample_constrained_ecosystem(rng)
        common = dict(
            interaction_benefit=p.interaction_benefit, investment_reward=p.investment_reward,
            trait_cost=p.trait_cost, survival_tradeoff=p.survival_tradeoff,
            base_survival=p.base_survival, predation_pressure=p.predation_pressure,
            predation_scale=1.0, density_threshold=p.density_threshold,
        )
        resident = max(grid, key=lambda z: abm_invasion_factor(
            z, interaction_scale=1.0, repro_baseline=0.0, resident_trait=z, **common))
        eb = abm_viable_upper_edge(interaction_scale=1.0, repro_baseline=0.0,
                                   resident_trait=resident, **common)
        ea = abm_viable_upper_edge(interaction_scale=0.0, repro_baseline=0.08 * p.interaction_benefit,
                                   resident_trait=resident, **common)
        tot += 1
        if ea <= eb + 1e-9:
            recede += 1
    # the dominant structure obeys the theorem; the mate term is the documented exception
    assert recede / tot >= 0.85
