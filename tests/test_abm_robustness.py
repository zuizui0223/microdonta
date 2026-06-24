from causal_model.abm_robustness import (
    RobustnessPolicy,
    SweepRecord,
    program_runs_from_sweep,
    summarise_sweep_records,
)


def record(cell, replicate, match, flags=frozenset(), program="p", scenario="s"):
    return SweepRecord(
        scenario=scenario,
        program_id=program,
        parameter_cell=cell,
        replicate_id=replicate,
        motifs=frozenset({"interaction_loss", "selection_reconfiguration"}),
        matches_pattern=match,
        fragile_flags=flags,
    )


def test_recurrence_across_cells_is_robust():
    records = [
        record("a", "1", True), record("a", "2", True),
        record("b", "1", True), record("b", "2", False),
        record("c", "1", True), record("c", "2", True),
    ]
    summary = summarise_sweep_records(records)[0]
    assert summary.robust
    assert summary.n_successful_cells == 3
    assert summary.successful_cell_fraction == 1.0


def test_exact_cancellation_is_fragile_even_when_pattern_recurs():
    records = [
        record("a", "1", True, frozenset({"exact_cancellation"})),
        record("b", "1", True),
        record("c", "1", True),
    ]
    summary = summarise_sweep_records(records)[0]
    assert not summary.robust
    assert "exact_cancellation" in summary.fragility_flags


def test_insufficient_parameter_cells_is_not_robust():
    records = [record("a", "1", True), record("b", "1", True)]
    policy = RobustnessPolicy(min_parameter_cells=3)
    assert not summarise_sweep_records(records, policy)[0].robust


def test_program_runs_preserve_sweep_metadata():
    records = [
        record("a", "1", True),
        record("b", "1", True),
        record("c", "1", True),
    ]
    run = program_runs_from_sweep(records)[0]
    assert run.robust
    assert run.metadata["n_cells"] == 3
    assert run.metadata["n_successful_cells"] == 3
