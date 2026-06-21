from causal_model.abm_family_adapter import RobustnessPolicy, SweepRecord, program_runs_from_sweep, summarise_sweep
from causal_model.rule_transition_invariants import infer_rule_transition_invariants


def _records(scenario, program, motifs, total, successes):
    return [SweepRecord(scenario, program, frozenset(motifs), index < successes) for index in range(total)]


def test_sweep_classification():
    policy = RobustnessPolicy(min_replicates=10, min_match_fraction=0.30, fragile_max_fraction=0.10)
    data = []
    data.extend(_records("a", "robust", {"interaction_loss"}, 10, 4))
    data.extend(_records("a", "fragile", {"exact_cancellation"}, 10, 1))
    data.extend(_records("a", "rejected", {"direct_path"}, 10, 2))
    data.extend(_records("a", "small", {"mediated_path"}, 5, 5))
    summary = {item.program_id: item for item in summarise_sweep(data, policy)}
    assert summary["robust"].classification == "robust"
    assert summary["fragile"].classification == "fragile"
    assert summary["rejected"].classification == "rejected"
    assert summary["small"].classification == "insufficient"


def test_adapter_to_rule_transition_layer():
    policy = RobustnessPolicy(min_replicates=10, min_match_fraction=0.30, fragile_max_fraction=0.10)
    data = []
    data.extend(_records("pollination", "direct_pollination", {"interaction_loss", "selection_reconfiguration"}, 10, 4))
    data.extend(_records("pollination", "tuned_pollination", {"exact_cancellation"}, 10, 1))
    data.extend(_records("predation", "direct_predation", {"interaction_loss", "selection_reconfiguration"}, 10, 5))
    data.extend(_records("predation", "bad_predation", {"unrelated"}, 10, 0))
    runs = program_runs_from_sweep(data, policy)
    assert {run.program_id for run in runs} == {"direct_pollination", "tuned_pollination", "direct_predation"}
    result = infer_rule_transition_invariants(runs)
    assert result.cross_system_common_motifs == frozenset({"interaction_loss", "selection_reconfiguration"})


def test_invalid_policy_order_raises():
    try:
        RobustnessPolicy(min_match_fraction=0.1, fragile_max_fraction=0.2)
    except ValueError:
        return
    raise AssertionError("invalid threshold ordering must raise ValueError")
