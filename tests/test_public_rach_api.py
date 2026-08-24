"""Contract tests for the package-level RACH mainline."""
import importlib

import causal_model as rach


def test_primary_rach_symbols_are_package_level():
    expected = {
        "CandidateObservation",
        "CandidateOutcome",
        "RACHSummary",
        "compute_causal_admissibility",
        "causal_degeneracy",
        "causal_resolvability",
        "causal_replaceability_cost",
        "crc_profile",
        "mechanism_equivalence_structure",
        "next_observation_value",
        "run_rach_seq",
        "rach_summary",
    }
    assert expected <= set(rach.__all__)
    for name in expected:
        assert hasattr(rach, name)


def test_canonical_submodules_are_not_shadowed_by_root_callables():
    ca_module = importlib.import_module("causal_model.causal_admissibility")
    seq_module = importlib.import_module("causal_model.rach_seq")
    assert rach.causal_admissibility is ca_module
    assert rach.rach_seq is seq_module
    assert rach.compute_causal_admissibility is ca_module.causal_admissibility
    assert rach.run_rach_seq is seq_module.rach_seq


def test_rule_transition_installer_is_not_advertised_as_primary_api():
    assert "install_rule_transition_contracts" not in rach.__all__
