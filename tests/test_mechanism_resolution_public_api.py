"""Publication-facing tests for Mechanism-Resolving Observation Design."""

import mechanism_resolution_design as method
from mechanism_resolution_design import CandidateObservation, CandidateOutcome


EXPECTED = {
    "CandidateInformationValueResult",
    "CandidateObservation",
    "CandidateOutcome",
    "InformationValueResult",
    "MechanismAdmissibilityResult",
    "MechanismResolutionSummary",
    "ObservationContribution",
    "PredictiveOutcomeDistribution",
    "ReplaceabilityResult",
    "SequentialDesignResult",
    "SequentialDesignStep",
    "candidate_mutual_information_bits",
    "compute_admissible_mechanisms",
    "expected_edge_cuts",
    "filter_by_outcome",
    "heuristic_observation_value",
    "mechanism_entropy",
    "mechanism_equivalence_structure",
    "mechanism_replaceability_cost",
    "mechanism_replaceability_cost_full",
    "mechanism_replaceability_profile",
    "mechanism_replaceability_profile_full",
    "mechanism_resolvability",
    "mechanism_resolution_summary",
    "observation_contribution",
    "observation_information_value",
    "predictive_outcome_distribution",
    "sequential_candidate_value",
    "sequential_observation_design",
    "validated_information_value",
}


class _SW:
    def __init__(self, name: str):
        self.name = name


def _candidate():
    return CandidateObservation(
        name="measure_trait",
        description="resolving trait",
        target_switches=["A"],
        rationale="high and low outcomes separate mechanism states",
        outcomes=[
            CandidateOutcome(
                name="high",
                description="high",
                prior_probability=0.5,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "trait",
                    "population": "pop",
                    "observed_value": "0.75",
                    "scale": "0.05",
                }],
            ),
            CandidateOutcome(
                name="low",
                description="low",
                prior_probability=0.5,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "trait",
                    "population": "pop",
                    "observed_value": "0.25",
                    "scale": "0.05",
                }],
            ),
        ],
    )


def test_public_api_is_descriptive_surface():
    assert set(method.__all__) == EXPECTED
    assert all(hasattr(method, name) for name in EXPECTED)
    assert method.__version__ == "0.1.0"
    assert not {"run_rach_seq", "next_observation_evsi", "rach_summary"} & set(method.__all__)


def test_observation_information_value_matches_one_bit_resolver():
    rows = ([{"A": True, "pop_trait": 0.75}, {"A": False, "pop_trait": 0.25}]) * 20
    result = method.observation_information_value(rows, [_SW("A")], [_candidate()])[0]
    assert result.estimable
    assert result.partition_verified
    assert result.probability_source == "current_admissible_region"
    assert result.mutual_information_bits == 1.0
    assert result.information_value == 1.0
    assert result.current_resolvability == 0.0
    assert result.expected_resolvability == 1.0


def test_mechanism_independent_observation_has_zero_information_value():
    rows = []
    for a in (False, True):
        for trait in (0.25, 0.75):
            rows.extend({"A": a, "pop_trait": trait} for _ in range(20))
    result = method.observation_information_value(rows, [_SW("A")], [_candidate()])[0]
    assert result.estimable
    assert result.mutual_information_bits == 0.0
    assert result.information_value == 0.0
