import pytest

from eco_genetic_criticality.patch_feedback_hysteresis_theory import (
    PatchFeedbackSystem,
    frequency_derivative,
    interior_equilibrium_stability,
    long_run_state_from_initial_frequency,
    restoration_requires_reseeding,
    restoration_threshold,
    selection_bracket,
)


def _restored_system() -> PatchFeedbackSystem:
    # eta*A^alpha = 16, cost=9, so A_c=3 and restored A=4 is bistable.
    return PatchFeedbackSystem(
        area=4.0,
        interaction_yield=1.0,
        area_exponent=2.0,
        feedback_exponent=2.0,
        trait_cost=9.0,
    )


def _degraded_system() -> PatchFeedbackSystem:
    return PatchFeedbackSystem(
        area=2.0,
        interaction_yield=1.0,
        area_exponent=2.0,
        feedback_exponent=2.0,
        trait_cost=9.0,
    )


def test_critical_patch_area_and_bistable_restoration_threshold():
    system = _restored_system()
    assert system.critical_patch_area == pytest.approx(3.0)
    assert system.high_state_stability == "stable"
    assert system.low_state_stability == "stable"
    assert restoration_threshold(system) == pytest.approx(0.75)
    assert interior_equilibrium_stability(system) == "unstable"

    assert long_run_state_from_initial_frequency(0.70, system) == "low"
    assert long_run_state_from_initial_frequency(0.75, system) == "threshold"
    assert long_run_state_from_initial_frequency(0.80, system) == "high"


def test_selection_field_points_away_from_the_interior_threshold():
    system = _restored_system()
    # Below x_c the bracket is negative; above it the bracket is positive.
    assert selection_bracket(0.70, system) < 0.0
    assert selection_bracket(0.80, system) > 0.0
    assert frequency_derivative(0.70, system) < 0.0
    assert frequency_derivative(0.80, system) > 0.0


def test_degradation_below_critical_area_loses_high_state_stability():
    system = _degraded_system()
    assert system.high_state_stability == "unstable"
    assert restoration_threshold(system) is None
    assert interior_equilibrium_stability(system) == "absent"
    assert long_run_state_from_initial_frequency(1.0, system) == "low"


def test_habitat_restoration_alone_does_not_restore_collapsed_high_trait_state():
    degraded = _degraded_system()
    restored = _restored_system()
    assert restoration_requires_reseeding(
        degraded_system=degraded,
        restored_system=restored,
        collapsed_frequency=0.0,
    )
    assert long_run_state_from_initial_frequency(0.0, restored) == "low"
    # A reintroduction above the analytically derived threshold changes the basin.
    assert long_run_state_from_initial_frequency(0.76, restored) == "high"


def test_no_hysteresis_claim_when_no_loss_or_no_recovery_regime_change_occurred():
    restored = _restored_system()
    assert not restoration_requires_reseeding(
        degraded_system=restored,
        restored_system=restored,
    )


def test_invalid_frequency_and_parameters_are_rejected():
    system = _restored_system()
    with pytest.raises(ValueError):
        frequency_derivative(-0.1, system)
    with pytest.raises(ValueError):
        PatchFeedbackSystem(
            area=0.0,
            interaction_yield=1.0,
            area_exponent=2.0,
            feedback_exponent=2.0,
            trait_cost=1.0,
        )
