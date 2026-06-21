from causal_model.abm_family import RobustnessPolicy, SweepRecord, program_runs_from_sweep


def record(cell, seed, match=True):
    return SweepRecord(
        scenario="pollination",
        program_id="mediated",
        parameter_cell=cell,
        seed=seed,
        motifs=frozenset({"interaction_loss", "reproductive_reconfiguration"}),
        matches_pattern=match,
    )


def test_marks_repeated_multi_cell_pattern_as_robust():
    runs = program_runs_from_sweep([
        record("a", 1), record("a", 2), record("b", 1), record("b", 2),
    ])
    assert len(runs) == 1
    assert runs[0].robust
    assert runs[0].metadata["n_parameter_cells"] == 2


def test_keeps_single_tuned_success_as_fragile():
    runs = program_runs_from_sweep([
        record("a", 1), record("a", 2, False), record("b", 1, False),
    ])
    assert len(runs) == 1
    assert not runs[0].robust


def test_omits_programs_that_never_match_pattern():
    runs = program_runs_from_sweep([record("a", 1, False)])
    assert runs == []


def test_policy_validation():
    try:
        RobustnessPolicy(min_success_fraction=0.0)
    except ValueError:
        return
    raise AssertionError("invalid robustness policy should fail")
