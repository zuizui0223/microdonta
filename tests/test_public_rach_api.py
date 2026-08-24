"""Contract tests for the package-level RACH mainline."""
import causal_model as rach


def test_primary_rach_symbols_are_package_level():
    expected = {
        "CandidateObservation",
        "CandidateOutcome",
        "RACHSummary",
        "causal_admissibility",
        "causal_degeneracy",
        "causal_resolvability",
        "causal_replaceability_cost",
        "crc_profile",
        "mechanism_equivalence_structure",
        "next_observation_value",
        "rach_seq",
        "rach_summary",
    }
    assert expected <= set(rach.__all__)
    for name in expected:
        assert hasattr(rach, name)


def test_rule_transition_installer_is_not_advertised_as_primary_api():
    assert "install_rule_transition_contracts" not in rach.__all__
