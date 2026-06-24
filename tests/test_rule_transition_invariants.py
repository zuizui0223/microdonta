from causal_model.rule_transition_invariants import ProgramRun, explain_result, infer_rule_transition_invariants


def run(scenario, program_id, motifs, robust=True):
    return ProgramRun(scenario, program_id, frozenset(motifs), robust)


def test_cross_system_motifs_and_fragile_programs():
    result = infer_rule_transition_invariants([
        run("pollination", "direct", {"interaction_loss", "selection_reconfiguration"}),
        run("pollination", "mediated", {"interaction_loss", "reproductive_reconfiguration", "selection_reconfiguration"}),
        run("pollination", "tuned", {"interaction_loss", "exact_cancellation"}, robust=False),
        run("predation", "direct", {"interaction_loss", "selection_reconfiguration"}),
        run("predation", "demographic", {"interaction_loss", "demographic_reconfiguration", "selection_reconfiguration"}),
    ])
    assert result.cross_system_common_motifs == frozenset({"interaction_loss", "selection_reconfiguration"})
    assert result.by_scenario["pollination"].fragile_program_ids == ("tuned",)
    assert not result.no_cross_system_common_rule


def test_disjunctive_clause_is_a_rule():
    result = infer_rule_transition_invariants([
        run("scenario", "a", {"direct_path"}),
        run("scenario", "b", {"mediated_path"}),
    ])
    summary = result.by_scenario["scenario"]
    assert summary.necessary_motifs == frozenset()
    assert summary.disjunctive_necessary_clauses == (frozenset({"direct_path", "mediated_path"}),)
    assert not summary.no_common_rule


def test_explicit_no_common_rule():
    result = infer_rule_transition_invariants([
        run("a", "one", {"interaction_loss"}),
        run("b", "two", {"demographic_reconfiguration"}),
    ])
    assert result.no_cross_system_common_rule
    assert explain_result(result)["cross_system_common_motifs"] == []
