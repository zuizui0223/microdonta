"""Three-system rule-transition demo: pollination, predation, dispersal loss.

Verifies the end-to-end RACH rule-transition flow on three independent
ecological scenarios: robust/fragile classification from an ABM sweep (with
fragility reasons), and extraction of the rule transitions necessary across all
robust program families.
"""
import pytest

from causal_model.abm_family_adapter import (
    RobustnessPolicy,
    program_runs_from_sweep,
    summarise_sweep,
)
from causal_model.ecological_rule_abm import (
    POM_PATTERN_NAMES,
    RULE_TRANSITION_CHAIN,
    EcologicalRuleParameters,
    default_observed_pattern,
    extract_pom_pattern,
    generate_sweep_records,
    pom_distance,
    rule_transition_chain,
    simulate_rule_transition,
)
from causal_model.rule_transition_pipeline import analyse_rule_transitions

_DRAWS = [
    EcologicalRuleParameters(0.9, 0.6, 0.4, 0.30, 0.5, 0.0),
    EcologicalRuleParameters(0.8, 0.7, 0.5, 0.35, 0.4, 0.0),
    EcologicalRuleParameters(0.9, 0.5, 0.6, 0.25, 0.6, 0.0),
    EcologicalRuleParameters(0.7, 0.8, 0.5, 0.30, 0.5, 0.0),
]
_POLICY = RobustnessPolicy(min_replicates=4, min_match_fraction=0.2, fragile_max_fraction=0.05)


def _all_records():
    return (
        generate_sweep_records(
            "pollination",
            ["direct_selection", "reproductive_reconfiguration", "knife_edge_cancellation"],
            _DRAWS,
        )
        + generate_sweep_records("predation", ["direct_selection", "demographic_reconfiguration"], _DRAWS)
        + generate_sweep_records("dispersal_loss", ["direct_selection", "demographic_reconfiguration"], _DRAWS)
    )


def test_chain_is_relation_constraint_traitspace():
    assert RULE_TRANSITION_CHAIN == (
        "relation_change",
        "constraint_reconfiguration",
        "trait_space_reconfiguration",
    )
    chain = rule_transition_chain("reproductive_reconfiguration")
    assert chain.relation_change == "relation_change"
    assert chain.constraint_reconfiguration == "reproductive_reconfiguration"
    assert chain.trait_space_reconfiguration == "trait_space_reconfiguration"


def test_pom_pattern_is_multi_component():
    before, after, _ = simulate_rule_transition("direct_selection", _DRAWS[0])
    p_sim = extract_pom_pattern(before, after)
    assert set(p_sim) == set(POM_PATTERN_NAMES)
    assert len(POM_PATTERN_NAMES) == 5


def test_acceptance_is_distance_thresholded_not_a_bare_decline():
    """A run enters A_epsilon only when d(P_sim, P_obs) <= epsilon over all five
    POM components — not merely because the trait declined."""
    obs = default_observed_pattern()
    # reproductive reconfiguration declines the trait yet its P_sim differs from
    # P_obs on the alternative-route component, so its distance is positive.
    before, after, _ = simulate_rule_transition("reproductive_reconfiguration", _DRAWS[0])
    assert after.trait_investment < before.trait_investment  # the trait did decline
    assert pom_distance(extract_pom_pattern(before, after), obs) > 0.0

    # under a strict epsilon that one-component mismatch is rejected; the program
    # whose P_sim equals P_obs exactly is still admitted.
    recs = generate_sweep_records(
        "strict", ["direct_selection", "reproductive_reconfiguration"], _DRAWS, epsilon=0.0,
    )
    accepted = {}
    for r in recs:
        accepted.setdefault(r.program_id, []).append(r.pattern_matched)
    assert all(accepted["direct_selection"])
    assert not any(accepted["reproductive_reconfiguration"])


def test_records_store_pom_summary_statistic():
    recs = generate_sweep_records("pollination", ["reproductive_reconfiguration"], _DRAWS)
    rec = recs[0]
    assert set(rec.metadata["P_sim"]) == set(POM_PATTERN_NAMES)
    assert rec.metadata["P_obs"] == default_observed_pattern()
    assert rec.metadata["abc_distance"] >= 0.0
    assert rec.metadata["accepted"] == rec.pattern_matched


def test_fragile_cancellation_program_is_not_robust():
    summaries = {(s.scenario, s.program_id): s for s in summarise_sweep(_all_records(), _POLICY)}
    knife = summaries[("pollination", "knife_edge_cancellation")]
    # it reproduces the pattern, yet is fragile because the match is cancellation-dependent
    assert knife.match_fraction == 1.0
    assert knife.classification == "fragile"
    assert "exact_cancellation" in knife.fragility_reasons
    # the genuine programs are robust
    assert summaries[("pollination", "direct_selection")].classification == "robust"
    assert summaries[("predation", "demographic_reconfiguration")].classification == "robust"


def test_fragility_reasons_are_preserved_in_program_runs():
    runs = {(r.scenario, r.program_id): r for r in program_runs_from_sweep(_all_records(), _POLICY)}
    knife = runs[("pollination", "knife_edge_cancellation")]
    assert knife.robust is False
    assert "exact_cancellation" in knife.metadata["fragility_reasons"]


def test_three_systems_share_the_rule_transition_chain():
    analysis = analyse_rule_transitions(_all_records(), _POLICY)
    result = analysis.invariant_result
    # the full relation -> constraint -> trait-space chain is necessary in every system
    assert set(RULE_TRANSITION_CHAIN) <= result.cross_system_common_motifs
    assert {"interaction_loss", "selection_reconfiguration"} <= result.cross_system_common_motifs
    assert not result.no_cross_system_common_rule
    # all three scenarios are present
    assert set(result.by_scenario) == {"pollination", "predation", "dispersal_loss"}
    # the fragile program is excluded from pollination's robust set
    assert "knife_edge_cancellation" in result.by_scenario["pollination"].fragile_program_ids
    assert "knife_edge_cancellation" not in result.by_scenario["pollination"].robust_program_ids


def test_no_common_rule_is_reported_when_systems_disagree():
    # a control: two scenarios whose robust programs share no motif -> no_common_rule
    from causal_model.rule_transition_invariants import ProgramRun, infer_rule_transition_invariants

    result = infer_rule_transition_invariants([
        ProgramRun("x", "a", frozenset({"interaction_loss"}), robust=True),
        ProgramRun("y", "b", frozenset({"demographic_reconfiguration"}), robust=True),
    ])
    assert result.no_cross_system_common_rule
