from causal_model.mechanism_region import CandidateObservation, CandidateOutcome
from causal_model.observation_information import candidate_mutual_information_bits
from causal_model.target_observation_value import (
    candidate_target_mutual_information_bits,
    target_entropy_bits,
    target_observation_information_value,
)


class _SW:
    def __init__(self, name: str):
        self.name = name


def _candidate():
    return CandidateObservation(
        name="measure_trait",
        description="measure high/low trait",
        target_switches=["A"],
        rationale="candidate partitions current rows by trait",
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


def test_target_value_can_be_high_when_mechanism_value_is_zero():
    rows = []
    for mechanism in (False, True):
        rows.extend(
            {"A": mechanism, "pop_trait": 0.25, "target_sign": "low"}
            for _ in range(20)
        )
        rows.extend(
            {"A": mechanism, "pop_trait": 0.75, "target_sign": "high"}
            for _ in range(20)
        )
    candidate = _candidate()
    assert candidate_mutual_information_bits(rows, [_SW("A")], candidate) == 0.0
    assert candidate_target_mutual_information_bits(
        rows, candidate, ["target_sign"]
    ) == 1.0
    result = target_observation_information_value(
        rows, [candidate], target_columns=["target_sign"]
    )[0]
    assert result.estimable
    assert result.normalized_target_value == 1.0


def test_already_identified_target_has_zero_additional_value():
    rows = [
        {"A": bool(i % 2), "pop_trait": 0.25 if i % 2 else 0.75, "target": "same"}
        for i in range(40)
    ]
    result = target_observation_information_value(
        rows, [_candidate()], target_columns=["target"]
    )[0]
    assert result.estimable
    assert result.target_already_identified
    assert result.current_target_entropy_bits == 0.0
    assert result.normalized_target_value == 0.0


def test_target_entropy_requires_declared_target_columns():
    rows = [{"target": 0}, {"target": 1}]
    try:
        target_entropy_bits(rows, [])
    except ValueError as exc:
        assert "non-empty" in str(exc)
    else:
        raise AssertionError("missing target columns should fail")


def test_missing_predictive_partition_is_nonestimable():
    rows = [{"A": bool(i % 2), "target": i % 2, "unrelated": i} for i in range(20)]
    result = target_observation_information_value(
        rows, [_candidate()], target_columns=["target"]
    )[0]
    assert not result.estimable
    assert not result.partition_verified
    assert result.normalized_target_value is None
