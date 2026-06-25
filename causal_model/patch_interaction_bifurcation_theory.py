"""Analytic patch-size / interaction-feedback bifurcation theory.

This module is the deterministic theorem layer for a proposed eco-evolutionary
sequence. It intentionally starts before alleles, drift, or a full ABM.

Interaction availability ``q`` is a patch-level state summarising encounter,
display, or partner persistence. It obeys the mean-field fixed-point equation

    q = sigmoid(kappa * (A*q - theta)),

where

    A      patch size (or an effective interaction-supporting area),
    kappa  strength of positive individual-to-interaction feedback,
    theta  exogenous interaction barrier / degradation pressure.

The equation has an exact critical size ``A_c = 4/kappa``. Below it there is one
interaction equilibrium; above it there is a barrier interval with two stable
states separated by one unstable state. This produces hysteresis.

A high-investment trait mode is represented minimally by a required interaction
availability ``q_required``. If ``q_required`` lies between the two saddle-node
availability values, high-trait viability is history-dependent and collapses or
recovers discontinuously when the interaction branch disappears.

The proofs are in ``docs/patch_interaction_bifurcation_theorem.md``. Numerical
root functions are regression and diagram helpers, not the proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, exp, log, sqrt
from typing import Literal


Stability = Literal["stable", "unstable", "critical"]


@dataclass(frozen=True)
class SaddleNodes:
    """Saddle-node locations for a bistable patch.

    ``q_low`` and ``q_high`` are the interaction availabilities where the low and
    high stable branches respectively meet the unstable branch. ``theta_low`` is
    the recovery boundary under decreasing barrier; ``theta_high`` is the collapse
    boundary under increasing barrier.
    """

    patch_size: float
    feedback_strength: float
    q_low: float
    q_high: float
    theta_low: float
    theta_high: float


@dataclass(frozen=True)
class InteractionEquilibrium:
    """One fixed point of the patch interaction equation."""

    q: float
    theta: float
    patch_size: float
    feedback_strength: float
    stability: Stability


@dataclass(frozen=True)
class TraitTippingWindow:
    """Conditions for history-dependent high-trait viability."""

    patch_size: float
    feedback_strength: float
    q_required: float
    bistable: bool
    history_dependent: bool
    collapse_barrier: float | None
    recovery_barrier: float | None


@dataclass(frozen=True)
class PartitionCapacity:
    """Whether an equal partition can retain hysteresis-capable patches."""

    total_area: float
    patch_count: int
    patch_size: float
    critical_patch_size: float
    any_hysteresis_capable_patch: bool
    all_patches_hysteresis_capable: bool
    minimum_equal_patch_count_without_hysteresis: int


def sigmoid(value: float) -> float:
    """Numerically stable logistic sigmoid."""
    if value >= 0:
        inverse = exp(-value)
        return 1.0 / (1.0 + inverse)
    inverse = exp(value)
    return inverse / (1.0 + inverse)


def logit(q: float) -> float:
    """Logit on the strict interior of the interaction state space."""
    if not 0.0 < q < 1.0:
        raise ValueError("q must lie strictly between 0 and 1")
    return log(q / (1.0 - q))


def critical_patch_size(feedback_strength: float) -> float:
    """Return the exact onset size for possible interaction bistability.

    The derivative of the fixed-point map is at most ``kappa*A/4``. Therefore
    multiple fixed points require, and in this logistic family are possible iff,
    ``kappa*A > 4``.
    """
    if feedback_strength <= 0.0:
        raise ValueError("feedback_strength must be positive")
    return 4.0 / feedback_strength


def is_bistability_capable(patch_size: float, feedback_strength: float) -> bool:
    """Return whether the patch can admit a three-fixed-point barrier interval."""
    if patch_size <= 0.0:
        raise ValueError("patch_size must be positive")
    return feedback_strength * patch_size > 4.0


def barrier_from_q(q: float, patch_size: float, feedback_strength: float) -> float:
    """Rearrange the fixed point equation to obtain theta as a function of q."""
    if patch_size <= 0.0 or feedback_strength <= 0.0:
        raise ValueError("patch_size and feedback_strength must be positive")
    return patch_size * q - logit(q) / feedback_strength


def saddle_nodes(patch_size: float, feedback_strength: float) -> SaddleNodes:
    """Return exact saddle-node coordinates when ``kappa*A > 4``.

    At a saddle node, the derivative of the fixed-point map is one:

        kappa*A*q*(1-q) = 1.

    Solving that quadratic gives the two q values returned here.
    """
    if not is_bistability_capable(patch_size, feedback_strength):
        raise ValueError("saddle nodes exist only when feedback_strength*patch_size > 4")
    discriminant = sqrt(1.0 - 4.0 / (feedback_strength * patch_size))
    q_low = (1.0 - discriminant) / 2.0
    q_high = (1.0 + discriminant) / 2.0
    theta_low = barrier_from_q(q_low, patch_size, feedback_strength)
    theta_high = barrier_from_q(q_high, patch_size, feedback_strength)
    if not theta_low < theta_high:
        raise RuntimeError("invalid saddle-node ordering")
    return SaddleNodes(
        patch_size=patch_size,
        feedback_strength=feedback_strength,
        q_low=q_low,
        q_high=q_high,
        theta_low=theta_low,
        theta_high=theta_high,
    )


def fixed_point_residual(q: float, patch_size: float, feedback_strength: float, barrier: float) -> float:
    """Return q minus its interaction-map update; roots are fixed points."""
    return q - sigmoid(feedback_strength * (patch_size * q - barrier))


def fixed_point_slope(q: float, patch_size: float, feedback_strength: float) -> float:
    """Derivative of the interaction update at a fixed point."""
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must lie in [0, 1]")
    return feedback_strength * patch_size * q * (1.0 - q)


def classify_stability(q: float, patch_size: float, feedback_strength: float, *, tolerance: float = 1e-10) -> Stability:
    """Classify a fixed point by the magnitude of its one-dimensional slope."""
    if tolerance < 0.0:
        raise ValueError("tolerance must be non-negative")
    slope = fixed_point_slope(q, patch_size, feedback_strength)
    if abs(slope - 1.0) <= tolerance:
        return "critical"
    return "stable" if slope < 1.0 else "unstable"


def _bisect_root(
    patch_size: float,
    feedback_strength: float,
    barrier: float,
    left: float,
    right: float,
    *,
    tolerance: float = 1e-12,
    max_iterations: int = 200,
) -> float:
    """Bisection over a bracket known to contain one residual sign change."""
    f_left = fixed_point_residual(left, patch_size, feedback_strength, barrier)
    f_right = fixed_point_residual(right, patch_size, feedback_strength, barrier)
    if abs(f_left) <= tolerance:
        return left
    if abs(f_right) <= tolerance:
        return right
    if f_left * f_right > 0.0:
        raise ValueError("root interval does not bracket a sign change")
    for _ in range(max_iterations):
        middle = (left + right) / 2.0
        f_middle = fixed_point_residual(middle, patch_size, feedback_strength, barrier)
        if abs(f_middle) <= tolerance or (right - left) <= tolerance:
            return middle
        if f_left * f_middle <= 0.0:
            right = middle
            f_right = f_middle
        else:
            left = middle
            f_left = f_middle
    return (left + right) / 2.0


def equilibria(
    patch_size: float,
    feedback_strength: float,
    barrier: float,
    *,
    tolerance: float = 1e-10,
) -> tuple[InteractionEquilibrium, ...]:
    """Return all interior fixed points in deterministic order.

    The branch structure is derived analytically from the saddle nodes, then each
    root is numerically bracketed only for use in tests and figures.
    """
    if patch_size <= 0.0 or feedback_strength <= 0.0:
        raise ValueError("patch_size and feedback_strength must be positive")
    epsilon = 1e-12
    intervals: list[tuple[float, float]]
    if not is_bistability_capable(patch_size, feedback_strength):
        intervals = [(epsilon, 1.0 - epsilon)]
    else:
        nodes = saddle_nodes(patch_size, feedback_strength)
        if barrier < nodes.theta_low - tolerance:
            intervals = [(nodes.q_high, 1.0 - epsilon)]
        elif barrier > nodes.theta_high + tolerance:
            intervals = [(epsilon, nodes.q_low)]
        elif abs(barrier - nodes.theta_low) <= tolerance:
            intervals = [(nodes.q_low, nodes.q_low), (nodes.q_high, 1.0 - epsilon)]
        elif abs(barrier - nodes.theta_high) <= tolerance:
            intervals = [(epsilon, nodes.q_low), (nodes.q_high, nodes.q_high)]
        else:
            intervals = [
                (epsilon, nodes.q_low),
                (nodes.q_low, nodes.q_high),
                (nodes.q_high, 1.0 - epsilon),
            ]
    roots: list[float] = []
    for left, right in intervals:
        if left == right:
            root = left
        else:
            root = _bisect_root(patch_size, feedback_strength, barrier, left, right)
        if not roots or abs(root - roots[-1]) > tolerance:
            roots.append(root)
    return tuple(
        InteractionEquilibrium(
            q=root,
            theta=barrier,
            patch_size=patch_size,
            feedback_strength=feedback_strength,
            stability=classify_stability(root, patch_size, feedback_strength, tolerance=tolerance),
        )
        for root in roots
    )


def high_trait_viable(q: float, q_required: float, *, tolerance: float = 1e-12) -> bool:
    """Return whether a high-investment trait mode clears its interaction threshold."""
    if not 0.0 <= q <= 1.0 or not 0.0 <= q_required <= 1.0:
        raise ValueError("q and q_required must lie in [0, 1]")
    return q + tolerance >= q_required


def trait_tipping_window(
    patch_size: float,
    feedback_strength: float,
    q_required: float,
) -> TraitTippingWindow:
    """Return whether high-trait viability is hysteretic in the interaction window.

    If ``q_low < q_required < q_high``, then inside the barrier interval the low
    stable branch cannot sustain the high trait while the high stable branch can.
    At the upper barrier the high branch disappears and high-trait viability
    collapses; on recovery it reappears only at the lower barrier.
    """
    if not 0.0 < q_required < 1.0:
        raise ValueError("q_required must lie strictly between 0 and 1")
    if not is_bistability_capable(patch_size, feedback_strength):
        return TraitTippingWindow(
            patch_size=patch_size,
            feedback_strength=feedback_strength,
            q_required=q_required,
            bistable=False,
            history_dependent=False,
            collapse_barrier=None,
            recovery_barrier=None,
        )
    nodes = saddle_nodes(patch_size, feedback_strength)
    history_dependent = nodes.q_low < q_required < nodes.q_high
    return TraitTippingWindow(
        patch_size=patch_size,
        feedback_strength=feedback_strength,
        q_required=q_required,
        bistable=True,
        history_dependent=history_dependent,
        collapse_barrier=nodes.theta_high if history_dependent else None,
        recovery_barrier=nodes.theta_low if history_dependent else None,
    )


def partition_capacity(total_area: float, patch_count: int, feedback_strength: float) -> PartitionCapacity:
    """Evaluate an equal-area habitat partition against the hysteresis threshold.

    This formalises the non-additivity result: total area can exceed the critical
    size while every equal subpatch is below it. The result concerns capacity for
    patch-level interaction hysteresis, not guaranteed persistence in every
    environment.
    """
    if total_area <= 0.0:
        raise ValueError("total_area must be positive")
    if patch_count < 1:
        raise ValueError("patch_count must be at least one")
    threshold = critical_patch_size(feedback_strength)
    size = total_area / patch_count
    minimum_count = ceil(total_area / threshold)
    capable = size > threshold
    return PartitionCapacity(
        total_area=total_area,
        patch_count=patch_count,
        patch_size=size,
        critical_patch_size=threshold,
        any_hysteresis_capable_patch=capable,
        all_patches_hysteresis_capable=capable,
        minimum_equal_patch_count_without_hysteresis=minimum_count,
    )
