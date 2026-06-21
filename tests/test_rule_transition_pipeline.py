from causal_model.abm_family_adapter import RobustnessPolicy, SweepRecord
from causal_model.rule_transition_pipeline import analyse_rule_transitions


def records(scenario, program, motifs, n, matched):
    return [SweepRecord(scenario, program, frozenset(motifs), i < matched) for i in range(n)]


def test_pipeline_preserves_sweep_summary_and_extracts_invariant():
    policy = RobustnessPolicy(min_replicates=10, min_match_fraction=0.30, fragile_max_fraction=0.10)
    data = []
    data += records("pollination", "p", {"interaction_loss", "selection_reconfiguration"}, 10, 4)
    data += records("predation", "d", {"interaction_loss", "selection_reconfiguration"}, 10, 5)
    data += records("pollination", "rejected", {"unrelated"}, 10, 0)

    analysis = analyse_rule_transitions(data, policy)
    classifications = {x.program_id: x.classification for x in analysis.sweep_summary}
    assert classifications["rejected"] == "rejected"
    assert analysis.invariant_result.cross_system_common_motifs == frozenset(
        {"interaction_loss", "selection_reconfiguration"}
    )
