"""Patch-size-dependent basin hysteresis from individual interaction feedback.

A patch of area A contains a frequency x in [0,1] of an interaction-supporting,
high-investment trait.  The deterministic eco-evolutionary reduction is

    dx/dt = x (1-x) [ eta * A**alpha * x**feedback_exponent - cost ].

The term ``eta*A**alpha`` is the maximal interaction support supplied by a patch
of area A; ``x**feedback_exponent`` represents the fact that the interaction is
maintained by the local frequency of the supporting trait (display aggregation,
mate availability, pollinator learning, cooperative defence, and similar
individual-interaction mechanisms).

The exact results are:

F1 -- critical patch area.
    The high-trait equilibrium x=1 is stable exactly when
    A > A_c = (cost/eta)**(1/alpha).

F2 -- bistability and restoration threshold.
    Above A_c, x=0 and x=1 are both stable and there is one unstable interior
    threshold

        x_c(A) = [cost/(eta*A**alpha)]**(1/feedback_exponent).

    A perturbation below x_c converges to the low-trait state; a perturbation
    above it converges to the high-trait state.

F3 -- basin hysteresis under habitat restoration.
    If degradation drives A below A_c, the high state loses stability and the
    system can collapse to x=0. Restoring A above A_c does not by itself restore
    the high state because x=0 remains stable; restoration requires reseeding or
    some perturbation with x>x_c(A). This is basin/path hysteresis, not a claim
    of a two-fold saddle-node hysteresis diagram.

Proofs are in ``docs/eco_genetic_criticality/patch_feedback_hysteresis_theorem.md``. Code here provides
closed-form implementations and regression tests only.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Literal


EquilibriumStability = Literal["stable", "unstable", "neutral", "absent"]


@dataclass(frozen=True)
class PatchFeedbackSystem:
    """Parameters for the frequency-dependent local interaction model."""

    area: float
    interaction_yield: float
    area_exponent: float
    feedback_exponent: float
    trait_cost: float

    def __post_init__(self) -> None:
        for name in (
            "area",
            "interaction_yield",
            "area_exponent",
            "feedback_exponent",
            "trait_cost",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")

    @property
    def maximal_interaction_support(self) -> float:
        return self.interaction_yield * self.area ** self.area_exponent

    @property
    def critical_patch_area(self) -> float:
        return (self.trait_cost / self.interaction_yield) ** (1.0 / self.area_exponent)

    @property
    def high_state_stability(self) -> EquilibriumStability:
        support = self.maximal_interaction_support
        if isclose(support, self.trait_cost, rel_tol=0.0, abs_tol=1e-12):
            return "neutral"
        return "stable" if support > self.trait_cost else "unstable"

    @property
    def low_state_stability(self) -> EquilibriumStability:
        """The low state is stable because interaction support vanishes at x=0."""
        return "stable"


def selection_bracket(x: float, system: PatchFeedbackSystem) -> float:
    """Return ``eta*A**alpha*x**h - cost`` in the frequency equation."""
    if not 0.0 <= x <= 1.0:
        raise ValueError("x must lie in [0, 1]")
    return (
        system.maximal_interaction_support * x ** system.feedback_exponent
        - system.trait_cost
    )


def frequency_derivative(x: float, system: PatchFeedbackSystem) -> float:
    """Return the deterministic trait-frequency derivative ``dx/dt``."""
    if not 0.0 <= x <= 1.0:
        raise ValueError("x must lie in [0, 1]")
    return x * (1.0 - x) * selection_bracket(x, system)


def restoration_threshold(system: PatchFeedbackSystem) -> float | None:
    """Return the unique unstable interior threshold above the critical area.

    ``None`` means there is no interior separator because the patch cannot support
    the high state (or is exactly on the neutral boundary). At ``A>A_c`` this is
    the threshold x_c separating the attraction basins of x=0 and x=1.
    """
    if system.high_state_stability != "stable":
        return None
    return (
        system.trait_cost / system.maximal_interaction_support
    ) ** (1.0 / system.feedback_exponent)


def interior_equilibrium_stability(system: PatchFeedbackSystem) -> EquilibriumStability:
    """Classify the interior equilibrium in the positive-bistable regime."""
    return "unstable" if restoration_threshold(system) is not None else "absent"


def long_run_state_from_initial_frequency(
    initial_frequency: float,
    system: PatchFeedbackSystem,
    *,
    tolerance: float = 1e-12,
) -> Literal["low", "high", "threshold", "indeterminate"]:
    """Return the deterministic basin outcome of the one-dimensional model.

    At the exact interior threshold, the state is an unstable equilibrium. At the
    high-state neutral boundary, no asymptotic direction is asserted.
    """
    if not 0.0 <= initial_frequency <= 1.0:
        raise ValueError("initial_frequency must lie in [0, 1]")
    high_stability = system.high_state_stability
    if high_stability == "unstable":
        return "low"
    if high_stability == "neutral":
        return "indeterminate"
    threshold = restoration_threshold(system)
    assert threshold is not None
    if isclose(initial_frequency, threshold, rel_tol=tolerance, abs_tol=tolerance):
        return "threshold"
    return "high" if initial_frequency > threshold else "low"


def restoration_requires_reseeding(
    *,
    degraded_system: PatchFeedbackSystem,
    restored_system: PatchFeedbackSystem,
    collapsed_frequency: float = 0.0,
) -> bool:
    """Return whether habitat restoration alone leaves the system in the low basin.

    The intended use is a degradation state with A<A_c followed by a restored
    state with A>A_c. The function refuses to call this hysteresis when those
    prerequisite stability changes are absent.
    """
    if not 0.0 <= collapsed_frequency <= 1.0:
        raise ValueError("collapsed_frequency must lie in [0, 1]")
    if degraded_system.high_state_stability != "unstable":
        return False
    if restored_system.high_state_stability != "stable":
        return False
    return long_run_state_from_initial_frequency(collapsed_frequency, restored_system) == "low"
