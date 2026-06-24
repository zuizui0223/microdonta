from causal_model.abm_family_adapter import RobustnessPolicy, SweepRecord
from causal_model.rule_transition_invariants import ProgramRun, infer_rule_transition_invariants
from causal_model.rule_transition_pipeline import analyse_rule_transitions


def records(scenario, program, assumptions, primary, n=6, matched=4):
    return [
        SweepRecord(
            scenario=scenario,
            program_id=program,
            motifs=frozenset(assumptions),
            pattern_matched=i < matched,
            metadata={"trait_space_primary": primary},
            region_id=f"region_{i % 3}",
            seed=i,
        )
        for i in range(n)
    ]


def test_outcomes_are_derived_from_simulation_metadata_not_fixed_motifs():
    policy = RobustnessPolicy(min_replicates=6, min_match_fraction=0.5, fragile_max_fraction=0.1)
    # The false legacy label says contraction, but simulated records say shift.
    data = records("defense", "survival", {"relation_change", "trait_space_contraction"}, "shift")
    analysis = analyse_rule_transitions(data, policy)
    result = analysis.invariant_result
    assert "trait_space_contraction" not in result.cross_system_common_motifs
    assert "trait_space_shift" in result.cross_system_common_outcome_motifs
    assert "trait_space_reconfiguration" in result.cross_system_common_outcome_motifs
    assert result.cross_system_common_assumption_motifs == frozenset({"relation_change"})


def test_geometry_is_not_cross_system_invariant_when_simulated_backends_differ():
    policy = RobustnessPolicy(min_replicates=6, min_match_fraction=0.5, fragile_max_fraction=0.1)
    data = []
    data += records("pollination", "fecundity", {"relation_change", "finite_resources", "trait_space_contraction"}, "contraction")
    data += records("defense", "survival", {"relation_change", "finite_resources", "trait_space_shift"}, "shift")
    result = analyse_rule_transitions(data, policy).invariant_result
    assert "trait_space_reconfiguration" in result.cross_system_common_outcome_motifs
    assert "trait_space_contraction" not in result.cross_system_common_outcome_motifs
    assert "trait_space_shift" not in result.cross_system_common_outcome_motifs


def test_no_common_rule_is_possible_after_outcome_and_assumption_separation():
    policy = RobustnessPolicy(min_replicates=6, min_match_fraction=0.5, fragile_max_fraction=0.1)
    data = []
    data += records("a", "one", {"finite_resources", "trait_space_contraction"}, "contraction")
    data += records("b", "two", {"ample_dispersal", "trait_space_expansion"}, "expansion")
    result = analyse_rule_transitions(data, policy).invariant_result
    assert result.no_cross_system_common_rule


def test_invariant_boundary_ignores_legacy_outcome_labels_without_simulated_provenance():
    result = infer_rule_transition_invariants([
        ProgramRun("scenario", "program", frozenset({"relation_change", "trait_space_contraction"}), True),
    ])
    assert result.cross_system_common_assumption_motifs == frozenset({"relation_change"})
    assert result.cross_system_common_outcome_motifs == frozenset()
    assert "trait_space_contraction" not in result.cross_system_common_motifs
