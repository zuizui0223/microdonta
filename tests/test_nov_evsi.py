"""Tests for publication-level NOV as admissible-region EVSI."""

from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome
from causal_model.nov_evsi import (
    candidate_mutual_information_bits,
    next_observation_evsi,
)


class _SW:
    def __init__(self, name: str):
        self.name = name


def _candidate(prior_high: float = 0.9, prior_low: float = 0.1):
    return CandidateObservation(
        name="measure_trait",
        description="measure a resolving trait",
        target_switches=["A"],
        rationale="high/low outcome identifies A",
        outcomes=[
            CandidateOutcome(
                name="high",
                description="high",
                prior_probability=prior_high,
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
                prior_probability=prior_low,
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


def test_evsi_uses_current_region_predictive_distribution_not_stale_prior():
    rows = [
        {"A": True, "pop_trait": 0.75},
        {"A": False, "pop_trait": 0.25},
    ] * 20
    switches = [_SW("A")]
    candidate = _candidate()
    result = next_observation_evsi(rows, switches, [candidate])[0]
    assert result.estimable
    assert result.partition_verified
    assert result.probability_source == "current_admissible_region"
    assert result.outcome_probabilities == {"high": 0.5, "low": 0.5}
    # Before observing q, A is maximally unresolved (R=0); either outcome pins A
    # completely (R=1). Thus I(A;Q)=1 bit and NOV=I/K=1.
    assert result.current_R == 0.0
    assert result.expected_R == 1.0
    assert result.mutual_information_bits == 1.0
    assert candidate_mutual_information_bits(rows, switches, candidate) == 1.0
    assert result.evsi == 1.0
    assert abs(result.information_identity_error or 0.0) < 1e-12


def test_evsi_is_zero_for_mechanism_independent_observation():
    # Q (high/low trait) is exactly balanced within both A states.
    rows = []
    for a in (False, True):
        for trait in (0.25, 0.75):
            rows.extend({"A": a, "pop_trait": trait} for _ in range(20))
    switches = [_SW("A")]
    candidate = _candidate(0.5, 0.5)
    result = next_observation_evsi(rows, switches, [candidate])[0]
    assert result.estimable
    assert result.mutual_information_bits == 0.0
    assert result.evsi == 0.0
    assert result.current_R == result.expected_R == 0.0


def test_evsi_refuses_to_replace_missing_predictive_map_with_declared_prior():
    rows = [{"A": bool(i % 2), "unrelated": i} for i in range(20)]
    candidate = _candidate()
    result = next_observation_evsi(rows, [_SW("A")], [candidate])[0]
    assert not result.estimable
    assert not result.partition_verified
    assert result.probability_source == "declared_prior"
    assert result.evsi is None
    assert result.mutual_information_bits is None
    assert candidate_mutual_information_bits(rows, [_SW("A")], candidate) is None
    assert "verified partition" in result.reason


def test_evsi_reports_candidate_without_outcomes_as_nonestimable():
    candidate = CandidateObservation(
        name="no_outcomes",
        description="no explicit outcome map",
        target_switches=["A"],
        rationale="legacy heuristic only",
        outcomes=[],
    )
    rows = [{"A": True}, {"A": False}] * 10
    result = next_observation_evsi(rows, [_SW("A")], [candidate])[0]
    assert not result.estimable
    assert result.probability_source == "no_outcomes"
    assert result.evsi is None
