from math import isclose

import pytest

from causal_model.patch_interaction_bifurcation_theory import (
    barrier_from_q,
    critical_patch_size,
    equilibria,
    fixed_point_residual,
    fixed_point_slope,
    is_bistability_capable,
    partition_capacity,
    saddle_nodes,
    trait_tipping_window,
)


def test_exact_critical_patch_size_and_strict_bistability_boundary():
    kappa = 2.0
    assert critical_patch_size(kappa) == 2.0
    assert not is_bistability_capable(2.0, kappa)
    assert not is_bistability_capable(1.999999, kappa)
    assert is_bistability_capable(2.000001, kappa)


def test_saddle_nodes_solve_unit_slope_and_fixed_point_equations():
    patch_size = 3.0
    kappa = 2.0
    nodes = saddle_nodes(patch_size, kappa)

    assert 0.0 < nodes.q_low < 0.5 < nodes.q_high < 1.0
    assert nodes.theta_low < nodes.theta_high
    assert isclose(fixed_point_slope(nodes.q_low, patch_size, kappa), 1.0, abs_tol=1e-12)
    assert isclose(fixed_point_slope(nodes.q_high, patch_size, kappa), 1.0, abs_tol=1e-12)
    assert isclose(
        barrier_from_q(nodes.q_low, patch_size, kappa), nodes.theta_low, abs_tol=1e-12
    )
    assert isclose(
        barrier_from_q(nodes.q_high, patch_size, kappa), nodes.theta_high, abs_tol=1e-12
    )


def test_bistable_barrier_window_has_two_stable_equilibria_and_one_unstable_equilibrium():
    patch_size = 3.0
    kappa = 2.0
    nodes = saddle_nodes(patch_size, kappa)
    barrier = (nodes.theta_low + nodes.theta_high) / 2.0
    roots = equilibria(patch_size, kappa, barrier)

    assert len(roots) == 3
    assert tuple(root.stability for root in roots) == ("stable", "unstable", "stable")
    assert roots[0].q < nodes.q_low < roots[1].q < nodes.q_high < roots[2].q
    assert all(
        abs(fixed_point_residual(root.q, patch_size, kappa, barrier)) < 1e-8
        for root in roots
    )


def test_below_or_above_hysteresis_window_has_one_stable_equilibrium():
    patch_size = 3.0
    kappa = 2.0
    nodes = saddle_nodes(patch_size, kappa)

    high_only = equilibria(patch_size, kappa, nodes.theta_low - 0.1)
    low_only = equilibria(patch_size, kappa, nodes.theta_high + 0.1)

    assert len(high_only) == 1
    assert high_only[0].stability == "stable"
    assert high_only[0].q > nodes.q_high
    assert len(low_only) == 1
    assert low_only[0].stability == "stable"
    assert low_only[0].q < nodes.q_low


def test_high_trait_mode_has_discontinuous_collapse_and_recovery_window():
    patch_size = 3.0
    kappa = 2.0
    nodes = saddle_nodes(patch_size, kappa)
    q_required = 0.5
    window = trait_tipping_window(patch_size, kappa, q_required)

    assert window.bistable
    assert window.history_dependent
    assert window.collapse_barrier == pytest.approx(nodes.theta_high)
    assert window.recovery_barrier == pytest.approx(nodes.theta_low)
    assert window.recovery_barrier < window.collapse_barrier

    # At the same barrier inside the window, history selects a low or high state.
    roots = equilibria(patch_size, kappa, (nodes.theta_low + nodes.theta_high) / 2.0)
    assert roots[0].q < q_required < roots[-1].q


def test_trait_tipping_requires_threshold_between_saddle_node_availabilities():
    patch_size = 3.0
    kappa = 2.0
    nodes = saddle_nodes(patch_size, kappa)

    assert not trait_tipping_window(patch_size, kappa, nodes.q_low).history_dependent
    assert not trait_tipping_window(patch_size, kappa, nodes.q_high).history_dependent
    assert not trait_tipping_window(2.0, kappa, 0.5).bistable


def test_partition_capacity_is_nonadditive_in_total_area():
    # kappa=2 gives A_c=2. A total area of 6 can support a hysteresis-capable
    # single patch but an equal partition into three patches sits exactly at A_c.
    one_patch = partition_capacity(total_area=6.0, patch_count=1, feedback_strength=2.0)
    three_patches = partition_capacity(total_area=6.0, patch_count=3, feedback_strength=2.0)

    assert one_patch.any_hysteresis_capable_patch
    assert not three_patches.any_hysteresis_capable_patch
    assert three_patches.minimum_equal_patch_count_without_hysteresis == 3


def test_partition_count_formula_removes_hysteresis_capacity_for_any_total_area():
    kappa = 1.25
    total_area = 17.3
    capacity = partition_capacity(total_area, 1, kappa)
    n = capacity.minimum_equal_patch_count_without_hysteresis
    reduced = partition_capacity(total_area, n, kappa)

    assert reduced.patch_size <= reduced.critical_patch_size
    assert not reduced.any_hysteresis_capable_patch


def test_invalid_model_parameters_are_rejected():
    with pytest.raises(ValueError):
        critical_patch_size(0.0)
    with pytest.raises(ValueError):
        saddle_nodes(2.0, 2.0)
    with pytest.raises(ValueError):
        trait_tipping_window(3.0, 2.0, 0.0)
    with pytest.raises(ValueError):
        partition_capacity(1.0, 0, 1.0)
