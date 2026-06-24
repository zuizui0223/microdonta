"""Public contract tests for non-circular rule-transition experiments."""
from causal_model.rule_transition_protocol import (
    OUTCOME_MOTIFS,
    changed_mechanism_channels,
)
from causal_model.spatial_metapopulation_abm import (
    compensated_program_motifs,
    constraint_program_motifs,
    make_interventions,
)
from causal_model.defense_metapopulation_abm import (
    defense_program_motifs,
    make_defense_intervention,
)
from causal_model.colonization_metapopulation_abm import (
    colonization_program_motifs,
    make_colonization_intervention,
)


def test_spatial_interventions_are_isolated_with_or_without_compensation():
    expected = {
        "pollination_loss": frozenset({"interaction_scale"}),
        "predation_loss": frozenset({"predation_scale"}),
        "dispersal_loss": frozenset({"dispersal_scale"}),
    }
    for compensation in (0.0, 0.08):
        interventions = make_interventions(compensation=compensation)
        for name, intervention in interventions.items():
            assert changed_mechanism_channels(intervention.before, intervention.after) == expected[name]
            assert intervention.after.repro_baseline == compensation


def test_all_program_factories_return_assumptions_only():
    spatial = make_interventions(compensation=0.08)["pollination_loss"]
    factories = (
        constraint_program_motifs(spatial),
        compensated_program_motifs(spatial),
        defense_program_motifs(make_defense_intervention(compensation=0.08)),
        colonization_program_motifs(make_colonization_intervention(compensation=0.06)),
    )
    for motifs in factories:
        assert not (motifs & OUTCOME_MOTIFS)


def test_compensation_does_not_change_spatial_mechanism_identity():
    uncompensated = make_interventions(compensation=0.0)
    compensated = make_interventions(compensation=0.55)
    for name in uncompensated:
        assert changed_mechanism_channels(
            uncompensated[name].before, uncompensated[name].after
        ) == changed_mechanism_channels(
            compensated[name].before, compensated[name].after
        )
