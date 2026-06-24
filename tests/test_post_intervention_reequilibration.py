from types import SimpleNamespace

from causal_model.spatial_metapopulation_abm import Individual, PopulationState, ViableTraitSet


def _resident(n, trait=0.4):
    return PopulationState(
        tuple(Individual(trait, trait, 0, 0, (0.0, 0.0), 0) for _ in range(n)),
        {0: 0.5},
    )


def _omega(mask):
    return ViableTraitSet((0.0, 1.0), tuple(mask), (0.2, 0.2))


def test_defense_after_omega_uses_reequilibrated_resident(monkeypatch):
    import causal_model.defense_metapopulation_abm as defense

    before, after, seen = _resident(3), _resident(7), []
    monkeypatch.setattr(defense, "equilibrate_defense", lambda *args, **kwargs: (before, {}, SimpleNamespace(status="stationary")))

    def fake_reequilibrate(resident, *_args, **_kwargs):
        assert resident is before
        return after, {}, SimpleNamespace(status="stationary")

    monkeypatch.setattr(defense, "reequilibrate_defense", fake_reequilibrate)

    def fake_omega(resident, *_args, **_kwargs):
        seen.append(resident.n_total)
        return _omega((True, True) if resident is before else (True, False))

    monkeypatch.setattr(defense, "estimate_defense_omega_inv", fake_omega)
    monkeypatch.setattr(defense, "extract_defense_pom", lambda *_args, **_kwargs: defense.defense_observed_pattern())
    result = defense.run_defense_intervention(object(), {}, defense.make_defense_intervention(), epsilon=1.0)
    assert seen == [3, 7]
    assert result.diagnostics["omega_after_resident"] == "post_intervention_reequilibrated"


def test_colonization_after_omega_uses_reequilibrated_resident(monkeypatch):
    import causal_model.colonization_metapopulation_abm as colonization

    before, after, seen = _resident(4), _resident(9), []
    monkeypatch.setattr(colonization, "equilibrate_colonization", lambda *args, **kwargs: (before, {}, SimpleNamespace(status="stationary")))

    def fake_reequilibrate(resident, *_args, **_kwargs):
        assert resident is before
        return after, {}, SimpleNamespace(status="stationary")

    monkeypatch.setattr(colonization, "reequilibrate_colonization", fake_reequilibrate)

    def fake_omega(resident, *_args, **_kwargs):
        seen.append(resident.n_total)
        return _omega((True, True) if resident is before else (True, False))

    monkeypatch.setattr(colonization, "estimate_colonization_omega_inv", fake_omega)
    monkeypatch.setattr(colonization, "extract_colonization_pom", lambda *_args, **_kwargs: colonization.colonization_observed_pattern())
    result = colonization.run_colonization_intervention(object(), {}, colonization.make_colonization_intervention(), epsilon=1.0)
    assert seen == [4, 9]
    assert result.diagnostics["omega_after_resident"] == "post_intervention_reequilibrated"


def test_nonstationary_after_resident_is_not_accepted(monkeypatch):
    import causal_model.defense_metapopulation_abm as defense

    before = _resident(3)
    monkeypatch.setattr(defense, "equilibrate_defense", lambda *args, **kwargs: (before, {}, SimpleNamespace(status="stationary")))
    monkeypatch.setattr(defense, "reequilibrate_defense", lambda *_args, **_kwargs: (_resident(3), {}, SimpleNamespace(status="not_converged")))
    calls = []
    monkeypatch.setattr(defense, "estimate_defense_omega_inv", lambda *_args, **_kwargs: calls.append(True) or _omega((True, True)))
    result = defense.run_defense_intervention(object(), {}, defense.make_defense_intervention(), epsilon=1.0)
    assert len(calls) == 1
    assert not result.accepted
    assert result.diagnostics["omega_after_resident"] == "not_stationary"


def test_colonization_without_after_resident_is_not_counted_as_endpoint_support(monkeypatch):
    import causal_model.colonization_metapopulation_abm as colonization

    before = _resident(3)
    monkeypatch.setattr(colonization, "equilibrate_colonization", lambda *args, **kwargs: (before, {}, SimpleNamespace(status="stationary")))
    monkeypatch.setattr(colonization, "reequilibrate_colonization", lambda *_args, **_kwargs: (_resident(0), {}, SimpleNamespace(status="extinct")))
    calls = []
    monkeypatch.setattr(colonization, "estimate_colonization_omega_inv", lambda *_args, **_kwargs: calls.append(True) or _omega((True, True)))
    result = colonization.run_colonization_intervention(object(), {}, colonization.make_colonization_intervention(), epsilon=1.0)
    assert len(calls) == 1
    assert not result.accepted
    assert result.diagnostics["omega_after_resident"] == "not_stationary"
