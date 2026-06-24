from causal_model.robust_abm_search import SweepRun, classify_sweep_runs


def make_run(scenario, program, motifs, context, value, valid=True):
    return SweepRun(
        scenario=scenario,
        program_id=program,
        motifs=frozenset(motifs),
        context_id=context,
        output={"match": value},
        valid=valid,
    )


def target(output):
    return output["match"]


def test_classifies_robust_program_across_contexts():
    runs = [
        make_run("pollination", "mediated", {"interaction_loss", "reproductive_reconfiguration"}, "low", True),
        make_run("pollination", "mediated", {"interaction_loss", "reproductive_reconfiguration"}, "high", True),
        make_run("pollination", "mediated", {"interaction_loss", "reproductive_reconfiguration"}, "high", False),
    ]
    programs, summaries = classify_sweep_runs(runs, target, min_success_rate=0.5, min_distinct_contexts=2)
    assert len(programs) == 1
    assert programs[0].robust
    assert summaries[0].success_rate == 2 / 3


def test_marks_single_context_success_as_fragile():
    runs = [
        make_run("pollination", "direct", {"interaction_loss", "selection_reconfiguration"}, "tuned", True),
        make_run("pollination", "direct", {"interaction_loss", "selection_reconfiguration"}, "tuned", False),
        make_run("pollination", "direct", {"interaction_loss", "selection_reconfiguration"}, "tuned", True),
    ]
    programs, summaries = classify_sweep_runs(runs, target, min_success_rate=0.5, min_distinct_contexts=2)
    assert len(programs) == 1
    assert not programs[0].robust
    assert not summaries[0].robust


def test_excludes_non_explanatory_programs():
    runs = [
        make_run("predation", "null", {"demographic_reconfiguration"}, "a", False),
        make_run("predation", "null", {"demographic_reconfiguration"}, "b", False),
    ]
    programs, summaries = classify_sweep_runs(runs, target)
    assert programs == []
    assert summaries[0].n_matching == 0


def test_ignores_invalid_runs_in_rate():
    runs = [
        make_run("a", "p", {"m"}, "one", True),
        make_run("a", "p", {"m"}, "two", True, valid=False),
    ]
    programs, summaries = classify_sweep_runs(runs, target, min_success_rate=1.0, min_distinct_contexts=1)
    assert programs[0].robust
    assert summaries[0].n_valid == 1
