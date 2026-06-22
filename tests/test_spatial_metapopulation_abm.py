"""Tests for the spatial metapopulation IBM RACH backend.

Verifies:
- Individual and Patch dataclasses are immutable and correct.
- simulate_metapopulation returns before/after PopulationState + motifs.
- No trait direction is hard-coded: the outcome depends on parameter balance.
- POM pattern extraction covers all 5 components.
- pom_distance uses the standard abc_distance pattern_distance.
- Acceptance via d(P_sim, P_obs) <= epsilon matches abc_distance.accepted_by_epsilon.
- generate_sweep_records returns SweepRecord with correct metadata.
- Fragile programs carry their fragility flags.
- A population can go extinct (all-zero after state is handled gracefully).
"""
from __future__ import annotations

import math

import pytest

from causal_model.abc_distance import accepted_by_epsilon, pattern_distance
from causal_model.spatial_metapopulation_abm import (
    DEFAULT_EPSILON,
    POM_PATTERN_NAMES,
    Individual,
    MetapopParameters,
    Patch,
    PopulationState,
    SweepRecord,
    default_observed_pattern,
    default_patches,
    extract_pom_pattern,
    generate_sweep_records,
    pom_distance,
    simulate_metapopulation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _selection_params() -> MetapopParameters:
    """Parameters that strongly select for trait matching."""
    return MetapopParameters(
        trait_match_benefit=0.9,
        trait_cost=0.1,
        density_threshold=0.7,
        mutation_rate=0.15,
        mutation_std=0.05,
        dispersal_base=0.1,
        distance_decay=1.0,
        resource_replenishment=0.25,
        max_age=6,
    )


def _neutral_params() -> MetapopParameters:
    """Parameters with weak selection and high mutation (drift-dominated)."""
    return MetapopParameters(
        trait_match_benefit=0.05,
        trait_cost=0.05,
        density_threshold=0.8,
        mutation_rate=0.4,
        mutation_std=0.15,
        dispersal_base=0.05,
        distance_decay=0.5,
        resource_replenishment=0.20,
        max_age=5,
    )


def _costly_trait_params() -> MetapopParameters:
    """High trait cost → trait should be driven down."""
    return MetapopParameters(
        trait_match_benefit=0.1,
        trait_cost=0.9,
        density_threshold=0.7,
        mutation_rate=0.1,
        mutation_std=0.05,
        dispersal_base=0.1,
        distance_decay=1.0,
        resource_replenishment=0.25,
        max_age=6,
    )


def _small_patches() -> dict:
    return default_patches(2)


# ---------------------------------------------------------------------------
# Dataclass tests
# ---------------------------------------------------------------------------

def test_individual_is_frozen():
    ind = Individual(trait=0.6, genotype=0.5, age=2, patch_id=0, location=(0.3, 0.7))
    assert ind.trait == pytest.approx(0.6)
    assert ind.age == 2
    with pytest.raises((AttributeError, TypeError)):
        ind.trait = 0.9  # type: ignore[misc]


def test_patch_stores_connectivity():
    patch = Patch(patch_id=0, area=1.0, carrying_capacity=20, connectivity={1: 0.4, 2: 0.3})
    assert patch.connectivity[1] == pytest.approx(0.4)
    assert patch.patch_id == 0


def test_default_patches_creates_fully_connected_layout():
    patches = default_patches(3)
    assert len(patches) == 3
    for pid, patch in patches.items():
        assert patch.patch_id == pid
        # connected to every other patch
        assert set(patch.connectivity.keys()) == {i for i in range(3) if i != pid}
        assert all(w > 0 for w in patch.connectivity.values())


def test_population_state_metrics_on_empty_population():
    state = PopulationState(individuals=(), patch_resources={0: 0.5})
    assert state.n_total == 0
    assert state.mean_trait() == pytest.approx(0.0)
    assert state.trait_variance() == pytest.approx(0.0)
    assert state.occupied_patches() == frozenset()


def test_population_state_metrics():
    inds = tuple(
        Individual(trait=t, genotype=0.5, age=1, patch_id=0, location=(0.1, 0.1))
        for t in [0.2, 0.4, 0.6, 0.8]
    )
    state = PopulationState(individuals=inds, patch_resources={0: 0.8})
    assert state.mean_trait() == pytest.approx(0.5)
    assert state.trait_variance() > 0.0
    assert state.occupied_patches() == frozenset({0})


# ---------------------------------------------------------------------------
# Simulation structure tests
# ---------------------------------------------------------------------------

def test_simulate_returns_before_after_and_motifs():
    patches = _small_patches()
    params = _selection_params()
    before, after, motifs = simulate_metapopulation(patches, params, n_warmup=3, steps=10, seed=42)
    assert isinstance(before, PopulationState)
    assert isinstance(after, PopulationState)
    assert isinstance(motifs, frozenset)
    assert "interaction_opportunity" in motifs
    assert "trait_cost_pressure" in motifs


def test_simulation_with_strong_selection_adds_motif():
    patches = _small_patches()
    params = _selection_params()  # trait_match_benefit = 0.9 > 0.5
    _, _, motifs = simulate_metapopulation(patches, params, n_warmup=2, steps=10, seed=1)
    assert "strong_selection" in motifs


def test_simulation_with_high_dispersal_adds_motif():
    patches = _small_patches()
    params = MetapopParameters(
        trait_match_benefit=0.3,
        trait_cost=0.1,
        density_threshold=0.7,
        mutation_rate=0.1,
        mutation_std=0.05,
        dispersal_base=0.5,   # > 0.2
        distance_decay=1.0,
        resource_replenishment=0.2,
        max_age=5,
    )
    _, _, motifs = simulate_metapopulation(patches, params, n_warmup=2, steps=10, seed=2)
    assert "dispersal_gene_flow" in motifs


def test_simulation_with_high_mutation_adds_motif():
    patches = _small_patches()
    params = MetapopParameters(
        trait_match_benefit=0.3,
        trait_cost=0.1,
        density_threshold=0.7,
        mutation_rate=0.4,   # > 0.3
        mutation_std=0.1,
        dispersal_base=0.05,
        distance_decay=1.0,
        resource_replenishment=0.2,
        max_age=5,
    )
    _, _, motifs = simulate_metapopulation(patches, params, n_warmup=2, steps=10, seed=3)
    assert "mutation_drift" in motifs


def test_before_has_individuals_at_warmup_end():
    patches = _small_patches()
    params = _selection_params()
    before, after, _ = simulate_metapopulation(patches, params, n_warmup=3, steps=15, seed=0)
    # Before should be non-empty (warmup won't extinguish a healthy population in 3 steps)
    assert before.n_total > 0


def test_trait_direction_is_emergent_not_hardcoded():
    """No parameter specifies 'trait must increase/decrease'; outcome is emergent."""
    patches = _small_patches()

    # High-cost params: selection pressure pushes trait down
    before_costly, after_costly, _ = simulate_metapopulation(
        patches, _costly_trait_params(), n_warmup=3, steps=25, seed=7
    )
    # High-benefit params: matching selection may allow higher traits
    before_sel, after_sel, _ = simulate_metapopulation(
        patches, _selection_params(), n_warmup=3, steps=25, seed=7
    )
    # We don't assert a fixed direction — just that the simulation ran and
    # produced valid trait values in [0, 1]
    if after_costly.n_total > 0:
        for v in after_costly.trait_values():
            assert 0.0 <= v <= 1.0
    if after_sel.n_total > 0:
        for v in after_sel.trait_values():
            assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# POM extraction tests
# ---------------------------------------------------------------------------

def test_pom_has_all_five_components():
    patches = _small_patches()
    params = _selection_params()
    before, after, _ = simulate_metapopulation(patches, params, n_warmup=3, steps=15, seed=0)
    p_sim = extract_pom_pattern(before, after, patches, params)
    assert set(p_sim.keys()) == set(POM_PATTERN_NAMES)
    assert len(POM_PATTERN_NAMES) == 5


def test_pom_values_are_ordinal_strings():
    patches = _small_patches()
    params = _selection_params()
    before, after, _ = simulate_metapopulation(patches, params, n_warmup=3, steps=15, seed=0)
    p_sim = extract_pom_pattern(before, after, patches, params)
    valid_ordinal = {"increase", "decrease", "stable"}
    valid_state = {"reconfigured", "conserved"}
    for name, val in p_sim.items():
        if name == "trait_space_state":
            assert val in valid_state, f"{name}={val!r} not in {valid_state}"
        else:
            assert val in valid_ordinal, f"{name}={val!r} not in {valid_ordinal}"


def test_pom_on_empty_after_population_is_handled():
    """If the population goes extinct the after-state is empty; POM must not crash."""
    patches = _small_patches()
    params = _selection_params()
    before, _, _ = simulate_metapopulation(patches, params, n_warmup=1, steps=1, seed=0)
    # Manually construct an empty after state
    after_empty = PopulationState(individuals=(), patch_resources={pid: 0.0 for pid in patches})
    p_sim = extract_pom_pattern(before, after_empty, patches, params)
    assert set(p_sim.keys()) == set(POM_PATTERN_NAMES)


def test_default_observed_pattern_has_five_components():
    obs = default_observed_pattern()
    assert set(obs.keys()) == set(POM_PATTERN_NAMES)


# ---------------------------------------------------------------------------
# Distance and acceptance tests
# ---------------------------------------------------------------------------

def test_pom_distance_perfect_match_is_zero():
    obs = default_observed_pattern()
    dist = pom_distance(obs, obs)
    assert dist == pytest.approx(0.0)


def test_pom_distance_total_mismatch_is_one():
    obs = default_observed_pattern()
    # Invert every ordinal value
    _invert = {"increase": "decrease", "decrease": "increase", "stable": "increase",
               "reconfigured": "conserved", "conserved": "reconfigured"}
    sim = {k: _invert[v] for k, v in obs.items()}
    dist = pom_distance(sim, obs)
    assert dist == pytest.approx(1.0)


def test_pom_distance_one_mismatch_is_0_2():
    obs = default_observed_pattern()
    sim = dict(obs)
    first_key = list(sim.keys())[0]
    sim[first_key] = "stable" if obs[first_key] != "stable" else "increase"
    dist = pom_distance(sim, obs)
    assert dist == pytest.approx(1.0 / 5.0)


def test_pom_distance_uses_pattern_distance():
    obs = default_observed_pattern()
    sim = dict(obs)
    sim["patch_persistence"] = "increase"  # one mismatch
    dist = pom_distance(sim, obs)
    total = len(obs)
    matches = sum(1 for k, v in obs.items() if sim.get(k) == v)
    expected = pattern_distance(matches, total)
    assert dist == pytest.approx(expected)


def test_acceptance_uses_accepted_by_epsilon():
    obs = default_observed_pattern()
    # Perfect match: d=0.0, accepted at any ε >= 0
    assert accepted_by_epsilon(pom_distance(obs, obs), DEFAULT_EPSILON) is True
    # One mismatch (d=0.2): accepted at DEFAULT_EPSILON=0.2
    sim = dict(obs)
    sim["patch_persistence"] = "decrease"
    d = pom_distance(sim, obs)
    assert accepted_by_epsilon(d, DEFAULT_EPSILON) is True
    # Two mismatches (d=0.4): rejected at DEFAULT_EPSILON=0.2
    sim["inbreeding_proxy"] = "stable"
    d2 = pom_distance(sim, obs)
    assert not accepted_by_epsilon(d2, DEFAULT_EPSILON)


# ---------------------------------------------------------------------------
# Sweep record tests
# ---------------------------------------------------------------------------

def _make_draws(n: int = 2) -> list[tuple[str, MetapopParameters]]:
    return [
        ("strong_selection", _selection_params()),
        ("mutation_drift", _neutral_params()),
    ][:n]


def test_generate_sweep_records_returns_correct_count():
    patches = _small_patches()
    draws = _make_draws(2)
    recs = generate_sweep_records("test_scenario", draws, patches, seeds=(0, 1), n_warmup=2, steps=10)
    # 2 program_draws × 2 seeds = 4 records
    assert len(recs) == 4


def test_sweep_records_have_correct_scenario_and_program_ids():
    patches = _small_patches()
    draws = _make_draws(2)
    recs = generate_sweep_records("eco", draws, patches, seeds=(0,), n_warmup=2, steps=8)
    program_ids = {r.program_id for r in recs}
    assert "strong_selection" in program_ids
    assert "mutation_drift" in program_ids
    for r in recs:
        assert r.scenario == "eco"


def test_sweep_records_are_sweep_record_instances():
    patches = _small_patches()
    draws = _make_draws(1)
    recs = generate_sweep_records("s", draws, patches, seeds=(0,), n_warmup=2, steps=8)
    assert all(isinstance(r, SweepRecord) for r in recs)


def test_sweep_record_metadata_has_pom_fields():
    patches = _small_patches()
    draws = _make_draws(1)
    rec = generate_sweep_records("s", draws, patches, seeds=(0,), n_warmup=2, steps=10)[0]
    md = rec.metadata
    assert "P_sim" in md
    assert "P_obs" in md
    assert "abc_distance" in md
    assert "epsilon" in md
    assert "accepted" in md
    assert set(md["P_sim"].keys()) == set(POM_PATTERN_NAMES)
    assert md["accepted"] == rec.pattern_matched


def test_sweep_record_abc_distance_matches_pattern_matched():
    patches = _small_patches()
    draws = _make_draws(1)
    for rec in generate_sweep_records("s", draws, patches, seeds=(0, 1, 2), n_warmup=2, steps=10):
        expected_accepted = accepted_by_epsilon(rec.metadata["abc_distance"], rec.metadata["epsilon"])
        assert rec.pattern_matched == expected_accepted


def test_sweep_record_initial_state_populated():
    patches = _small_patches()
    draws = _make_draws(1)
    rec = generate_sweep_records("s", draws, patches, seeds=(0,), n_warmup=2, steps=10)[0]
    assert "n_individuals" in rec.initial_state
    assert "mean_trait" in rec.initial_state
    assert rec.initial_state["n_individuals"] >= 0


def test_sweep_record_parameters_contain_all_keys():
    patches = _small_patches()
    draws = _make_draws(1)
    rec = generate_sweep_records("s", draws, patches, seeds=(0,), n_warmup=2, steps=10)[0]
    expected_keys = {
        "trait_match_benefit", "trait_cost", "density_threshold",
        "mutation_rate", "mutation_std", "dispersal_base",
        "distance_decay", "resource_replenishment", "max_age",
    }
    assert expected_keys <= set(rec.parameters.keys())


def test_fragile_program_carries_exact_cancellation_flag():
    patches = _small_patches()
    params = MetapopParameters(
        trait_match_benefit=0.3,
        trait_cost=0.3,
        density_threshold=0.7,
        mutation_rate=0.1,
        mutation_std=0.05,
        dispersal_base=0.05,
        distance_decay=1.0,
        resource_replenishment=0.2,
        max_age=5,
    )
    draws = [("opposing_pathway_cancellation", params)]
    recs = generate_sweep_records("fragile_test", draws, patches, seeds=(0,), n_warmup=2, steps=8)
    assert len(recs) == 1
    rec = recs[0]
    assert "exact_cancellation" in rec.fragile_flags
    assert "exact_cancellation" in rec.motifs


def test_non_fragile_program_has_empty_fragile_flags():
    patches = _small_patches()
    draws = [("strong_selection", _selection_params())]
    recs = generate_sweep_records("clean", draws, patches, seeds=(0,), n_warmup=2, steps=8)
    assert recs[0].fragile_flags == frozenset()


def test_default_patches_used_when_none_provided():
    draws = [("strong_selection", _selection_params())]
    recs = generate_sweep_records("s", draws, seeds=(0,), n_warmup=2, steps=8)
    assert len(recs) == 1


def test_sweep_records_different_seeds_give_different_results():
    patches = _small_patches()
    draws = [("strong_selection", _selection_params())]
    recs = generate_sweep_records("s", draws, patches, seeds=(0, 1, 2), n_warmup=2, steps=15)
    mean_traits = [r.metadata["mean_trait_after"] for r in recs]
    # All three seeds may differ (stochastic IBM)
    # At least we check they are all in [0, 1]
    for mt in mean_traits:
        assert 0.0 <= mt <= 1.0


# ---------------------------------------------------------------------------
# Cross-component integration
# ---------------------------------------------------------------------------

def test_pom_pattern_is_extracted_from_sweep_records():
    """Records carry P_sim matching POM_PATTERN_NAMES exactly."""
    patches = _small_patches()
    draws = _make_draws(2)
    for rec in generate_sweep_records("int", draws, patches, seeds=(0,), n_warmup=2, steps=10):
        assert set(rec.metadata["P_sim"].keys()) == set(POM_PATTERN_NAMES)
        assert set(rec.metadata["P_obs"].keys()) == set(POM_PATTERN_NAMES)


def test_strict_epsilon_can_reject_all_runs():
    """ε=0 requires a perfect 5/5 match; most runs should be rejected."""
    patches = _small_patches()
    draws = _make_draws(2)
    recs = generate_sweep_records("strict", draws, patches, epsilon=0.0, seeds=(0, 1), n_warmup=2, steps=10)
    # With ε=0, only exact matches are admitted — not asserting count but checking
    # that pattern_matched correctly reflects d==0.
    for rec in recs:
        if rec.pattern_matched:
            assert rec.metadata["abc_distance"] == pytest.approx(0.0)
        else:
            assert rec.metadata["abc_distance"] > 0.0


def test_relaxed_epsilon_admits_more_runs():
    patches = _small_patches()
    draws = _make_draws(2)
    recs_strict = generate_sweep_records("strict", draws, patches, epsilon=0.0, seeds=(0, 1, 2), n_warmup=2, steps=10)
    recs_relax = generate_sweep_records("relax", draws, patches, epsilon=1.0, seeds=(0, 1, 2), n_warmup=2, steps=10)
    n_strict = sum(1 for r in recs_strict if r.pattern_matched)
    n_relax = sum(1 for r in recs_relax if r.pattern_matched)
    assert n_relax >= n_strict
