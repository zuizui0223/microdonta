from types import SimpleNamespace

from causal_model.endpoint_sensitivity_backends import run_defense_endpoint_sensitivity
from causal_model.rule_transition_diagnostics import EndpointSensitivitySettings


def test_defense_sensitivity_records_every_region_seed_and_setting(monkeypatch):
    import causal_model.endpoint_sensitivity_backends as endpoints

    calls = []

    def fake_evaluate(params, patches, intervention, settings, **kwargs):
        calls.append((settings.grid_points, kwargs["seed"]))
        return True, {
            "trait_space_primary": "shift",
            "P_sim": {"omega_inv_state": "shifted"},
            "omega_measure_before": 0.8,
            "sensitivity_settings": {"grid_points": settings.grid_points},
        }

    monkeypatch.setattr(endpoints, "evaluate_defense_endpoint", fake_evaluate)
    params = SimpleNamespace(predator_pressure=0.3, defense_cost=0.2, dispersal_base=0.1)
    intervention = SimpleNamespace(name="predator_loss_defense")
    settings = (
        EndpointSensitivitySettings(grid_points=7, stationarity_window=8),
        EndpointSensitivitySettings(grid_points=9, stationarity_window=8),
    )
    cells = run_defense_endpoint_sensitivity(
        intervention,
        program_id="survival_reward",
        program_motifs=frozenset({"relation_change"}),
        ecosystem_sampler=lambda _rng: (params, {}),
        settings=settings,
        n_regions=2,
        seeds=(0, 1),
    )

    assert len(cells) == 2
    assert len(calls) == 8
    for cell in cells:
        assert len(cell.records) == 4
        assert {record.region_id for record in cell.records} == {"eco_0", "eco_1"}
        assert {record.seed for record in cell.records} == {0, 1}
        assert cell.uncertainty[0].n_matches == 4
