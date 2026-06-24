from types import SimpleNamespace

import pytest

from causal_model.abm_family_adapter import RobustnessPolicy, SweepRecord
from causal_model.rule_transition_diagnostics import (
    EndpointSensitivitySettings,
    build_benchmark_report,
    endpoint_sensitivity_grid,
    run_spatial_endpoint_sensitivity,
    summarise_match_uncertainty,
    wilson_interval,
)


def _record(region, seed, matched, *, scenario="pollination_loss", program="p"):
    return SweepRecord(
        scenario=scenario,
        program_id=program,
        motifs=frozenset({"relation_change", "positive_trait_cost"}),
        pattern_matched=matched,
        metadata={
            "trait_space_primary": "contraction" if matched else "conserved",
            "P_sim": {"omega_inv_state": "contracted" if matched else "conserved"},
        },
        region_id=region,
        seed=seed,
    )


def test_wilson_interval_is_bounded_and_contains_estimate():
    interval = wilson_interval(3, 4)
    assert interval.estimate == pytest.approx(0.75)
    assert 0.0 <= interval.lower <= interval.estimate <= interval.upper <= 1.0


def test_uncertainty_is_reported_by_region_and_seed():
    records = (
        _record("north", 1, True),
        _record("north", 2, False),
        _record("south", 1, True),
        _record("south", 2, True),
    )
    summary = summarise_match_uncertainty(records)[0]
    assert summary.n_replicates == 4
    assert summary.n_matches == 3
    assert {group.group_id for group in summary.by_region} == {"north", "south"}
    assert {group.group_id for group in summary.by_seed} == {"1", "2"}


def test_endpoint_sensitivity_grid_spans_all_requested_axes():
    grid = endpoint_sensitivity_grid(
        grid_points=(7, 11),
        invasion_steps=(4,),
        invasion_replicates=(1, 3),
        invasion_thresholds=(0.0,),
        stationarity_windows=(8, 12),
    )
    assert len(grid) == 8
    assert {setting.grid_points for setting in grid} == {7, 11}
    assert {setting.invasion_replicates for setting in grid} == {1, 3}
    with pytest.raises(ValueError):
        EndpointSensitivitySettings(grid_points=1)


def test_sensitivity_runner_records_settings_and_region_seed(monkeypatch):
    import causal_model.rule_transition_diagnostics as diagnostics

    calls = []

    def fake_evaluate(params, patches, intervention, settings, **kwargs):
        calls.append((settings, kwargs["seed"]))
        return True, {
            "trait_space_primary": "contraction",
            "P_sim": {"omega_inv_state": "contracted"},
            "sensitivity_settings": {
                "grid_points": settings.grid_points,
                "invasion_steps": settings.invasion_steps,
            },
        }

    monkeypatch.setattr(diagnostics, "evaluate_spatial_endpoint", fake_evaluate)
    intervention = SimpleNamespace(name="pollination_loss")
    params = SimpleNamespace(interaction_benefit=1.0, trait_cost=0.2, predation_pressure=0.1)
    settings = (EndpointSensitivitySettings(grid_points=7, invasion_steps=4, stationarity_window=8),)
    cells = run_spatial_endpoint_sensitivity(
        intervention,
        program_id="program",
        program_motifs=frozenset({"relation_change"}),
        ecosystem_sampler=lambda _rng: (params, {}),
        settings=settings,
        observed_pattern={"omega_inv_state": "contracted"},
        n_regions=2,
        seeds=(0, 1),
    )
    assert len(calls) == 4
    assert len(cells) == 1
    assert len(cells[0].records) == 4
    assert {record.region_id for record in cells[0].records} == {"eco_0", "eco_1"}
    assert {record.seed for record in cells[0].records} == {0, 1}


def test_benchmark_report_separates_required_sections():
    records = tuple(_record(region, seed, True, scenario=scenario) for scenario in ("a", "b") for region in ("r1", "r2") for seed in (0, 1))
    report = build_benchmark_report(
        records,
        policy=RobustnessPolicy(min_replicates=4, min_match_fraction=0.5, fragile_max_fraction=0.1),
        unresolved_limitations=("finite grid resolution",),
    )
    assert set(report) == {
        "assumptions",
        "observed_outcomes",
        "conditional_necessity",
        "counterexamples",
        "uncertainty",
        "unresolved_limitations",
    }
    assert report["unresolved_limitations"] == ["finite grid resolution"]
    assert report["uncertainty"]
    assert report["observed_outcomes"]
