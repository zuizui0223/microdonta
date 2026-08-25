"""Contract tests for the package-level RACH mainline."""
import importlib

import causal_model as rach


EXPECTED_PUBLIC_API = {
    "CandidateObservation",
    "CandidateOutcome",
    "CausalAdmissibilityResult",
    "CRCResult",
    "EVSIResult",
    "ObservationContribution",
    "RACHSummary",
    "SeqResult",
    "SeqStep",
    "compute_causal_admissibility",
    "causal_degeneracy",
    "causal_replaceability_cost",
    "causal_replaceability_cost_full",
    "causal_resolvability",
    "crc_profile",
    "crc_profile_full",
    "mechanism_equivalence_structure",
    "next_observation_evsi",
    "observation_contribution",
    "run_rach_seq",
    "rach_summary",
}


def test_release_public_api_is_exactly_the_rach_mainline():
    assert set(rach.__all__) == EXPECTED_PUBLIC_API
    for name in EXPECTED_PUBLIC_API:
        assert hasattr(rach, name)


def test_compatibility_helpers_remain_explicit_but_are_not_advertised():
    compatibility_only = {
        "heuristic_next_observation_value",
        "expected_edge_cuts",
        "filter_by_outcome",
        "CausalStructure",
        "score_causal_structure",
        "install_rule_transition_contracts",
    }
    assert not (compatibility_only & set(rach.__all__))
    for name in compatibility_only:
        assert hasattr(rach, name)


def test_validated_evsi_not_heuristic_is_primary_nov_api():
    assert "next_observation_evsi" in rach.__all__
    assert "heuristic_next_observation_value" not in rach.__all__
    assert "next_observation_value" not in rach.__all__
    assert callable(rach.next_observation_evsi)
    assert callable(rach.heuristic_next_observation_value)


def test_canonical_submodules_are_not_shadowed_by_root_callables():
    ca_module = importlib.import_module("causal_model.causal_admissibility")
    seq_module = importlib.import_module("causal_model.rach_seq")
    assert rach.causal_admissibility is ca_module
    assert rach.rach_seq is seq_module
    assert rach.compute_causal_admissibility is ca_module.causal_admissibility
    assert rach.run_rach_seq is seq_module.rach_seq
