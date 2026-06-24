from random import Random

from causal_model.channel_identifiability_theory import (
    VitalRateState,
    construct_channel_loss_symmetry,
    identify_from_channel_resolved_rates,
    net_performance_equal,
    support_geometry,
)


def _baseline() -> VitalRateState:
    return VitalRateState(
        grid=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
        fecundity=(1.1, 1.4, 1.9, 2.2, 2.6, 3.0),
        establishment=(1.8, 1.5, 1.2, 0.95, 0.75, 0.55),
    )


def test_multiplicative_channel_losses_have_equal_net_performance():
    baseline = _baseline()
    attenuation = (1.0, 0.95, 0.84, 0.72, 0.63, 0.51)
    result = construct_channel_loss_symmetry(
        baseline,
        attenuation,
        thresholds=(0.5, 1.0, 1.5, 2.0, 2.5),
    )

    assert result.net_performance_equal
    assert result.all_threshold_supports_equal
    assert net_performance_equal(result.fecundity_loss, result.establishment_loss)

    # The mechanisms are still physically distinct: different channel states changed.
    assert result.fecundity_loss.fecundity != result.establishment_loss.fecundity
    assert result.fecundity_loss.establishment != result.establishment_loss.establishment


def test_equal_net_performance_implies_equal_trait_support_geometry_at_every_threshold():
    baseline = _baseline()
    result = construct_channel_loss_symmetry(
        baseline,
        attenuation=(0.91, 0.77, 0.69, 0.58, 0.43, 0.37),
        thresholds=(0.25, 0.5, 1.0, 1.4, 1.8, 2.2),
    )

    for threshold in (0.25, 0.5, 1.0, 1.4, 1.8, 2.2):
        assert (
            result.fecundity_loss.viable_mask(threshold)
            == result.establishment_loss.viable_mask(threshold)
        )
        assert (
            support_geometry(result.fecundity_loss, threshold)
            == support_geometry(result.establishment_loss, threshold)
        )


def test_nonidentifiability_holds_for_random_positive_rate_functions_and_nonconstant_attenuation():
    rng = Random(20260624)
    for _ in range(200):
        grid = tuple(i / 12 for i in range(13))
        baseline = VitalRateState(
            grid=grid,
            fecundity=tuple(rng.uniform(0.1, 4.0) for _ in grid),
            establishment=tuple(rng.uniform(0.1, 4.0) for _ in grid),
        )
        attenuation = tuple(rng.uniform(0.15, 1.0) for _ in grid)
        result = construct_channel_loss_symmetry(
            baseline,
            attenuation,
            thresholds=(0.2, 0.5, 1.0, 2.0, 4.0, 8.0),
        )
        assert result.net_performance_equal
        assert result.all_threshold_supports_equal


def test_channel_resolved_rates_identify_an_exclusive_fecundity_change():
    baseline = _baseline()
    after = construct_channel_loss_symmetry(
        baseline,
        attenuation=(1.0, 0.9, 0.8, 0.7, 0.6, 0.5),
    ).fecundity_loss
    result = identify_from_channel_resolved_rates(baseline, after)

    assert result.conclusion == "fecundity_only"
    assert any(ratio != 1.0 for ratio in result.fecundity_ratio)
    assert all(ratio == 1.0 for ratio in result.establishment_ratio)


def test_channel_resolved_rates_identify_an_exclusive_establishment_change():
    baseline = _baseline()
    after = construct_channel_loss_symmetry(
        baseline,
        attenuation=(1.0, 0.9, 0.8, 0.7, 0.6, 0.5),
    ).establishment_loss
    result = identify_from_channel_resolved_rates(baseline, after)

    assert result.conclusion == "establishment_only"
    assert all(ratio == 1.0 for ratio in result.fecundity_ratio)
    assert any(ratio != 1.0 for ratio in result.establishment_ratio)


def test_channel_resolved_rule_retains_mixed_and_unchanged_cases():
    baseline = _baseline()
    mixed = VitalRateState(
        grid=baseline.grid,
        fecundity=tuple(0.8 * value for value in baseline.fecundity),
        establishment=tuple(0.9 * value for value in baseline.establishment),
    )
    assert identify_from_channel_resolved_rates(baseline, mixed).conclusion == "mixed_or_unidentified"
    assert identify_from_channel_resolved_rates(baseline, baseline).conclusion == "unchanged"
