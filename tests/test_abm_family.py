from causal_model.abm_family import ABMTrial, RobustnessPolicy, classify_abm_family


def motif_map(_scenario, program_id):
    return {
        "robust_program": {"interaction_loss", "selection_reconfiguration"},
        "fragile_program": {"interaction_loss", "exact_cancellation"},
    }[program_id]


def test_classifies_robust_and_fragile_programs_from_multiple_regions():
    trials = [
        ABMTrial("pollination", "robust_program", "low", True),
        ABMTrial("pollination", "robust_program", "low", True),
        ABMTrial("pollination", "robust_program", "high", True),
        ABMTrial("pollination", "robust_program", "high", False),
        ABMTrial("pollination", "fragile_program", "tuned", True),
        ABMTrial("pollination", "fragile_program", "tuned", False),
    ]

    runs, audits = classify_abm_family(
        trials,
        pattern_matches=lambda output: output,
        motifs_for_program=motif_map,
        policy=RobustnessPolicy(min_success_rate=0.6, min_regions=2),
    )

    assert {run.program_id: run.robust for run in runs} == {
        "robust_program": True,
        "fragile_program": False,
    }
    audit = {item.program_id: item for item in audits}
    assert audit["robust_program"].occupied_regions == 2
    assert audit["fragile_program"].occupied_regions == 1


def test_omits_program_with_no_matching_run():
    trials = [
        ABMTrial("s", "robust_program", "a", False),
        ABMTrial("s", "robust_program", "b", False),
    ]
    runs, audits = classify_abm_family(
        trials,
        pattern_matches=lambda output: output,
        motifs_for_program=motif_map,
    )
    assert runs == []
    assert audits[0].n_matching_trials == 0
