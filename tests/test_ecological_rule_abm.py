from causal_model.abm_family_adapter import RobustnessPolicy
from causal_model.ecological_rule_abm import (
    EcologicalRuleParameters,
    generate_sweep_records,
    ordinal_trait_decline,
    simulate_rule_transition,
)
from causal_model.rule_transition_pipeline import analyse_rule_transitions


def draws():
    return [
        EcologicalRuleParameters(0.9, 0.6, 0.4, 0.3, 0.5, 0.0),
        EcologicalRuleParameters(0.8, 0.7, 0.5, 0.35, 0.4, 0.0),
        EcologicalRuleParameters(0.9, 0.5, 0.6, 0.25, 0.6, 0.0),
        EcologicalRuleParameters(0.7, 0.8, 0.5, 0.30, 0.5, 0.0),
    ]


def test_abstract_program_returns_relation_and_trait_space_motifs():
    before, after, motifs = simulate_rule_transition("reproductive_reconfiguration", draws()[0])
    assert ordinal_trait_decline(before, after)
    assert "interaction_loss" in motifs
    assert "reproductive_reconfiguration" in motifs
    assert "trait_space_reconfiguration" in motifs


def test_sweep_connects_to_rule_transition_pipeline():
    pollination = generate_sweep_records(
        "pollination",
        ["direct_selection", "reproductive_reconfiguration"],
        draws(),
    )
    predation = generate_sweep_records(
        "predation",
        ["direct_selection", "demographic_reconfiguration"],
        draws(),
    )
    result = analyse_rule_transitions(
        pollination + predation,
        policy=RobustnessPolicy(min_replicates=4, min_match_fraction=0.2, fragile_max_fraction=0.05),
    )
    assert "interaction_loss" in result.invariant_result.cross_system_common_motifs
    assert "selection_reconfiguration" in result.invariant_result.cross_system_common_motifs
