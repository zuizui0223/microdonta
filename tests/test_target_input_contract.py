"""Unmeasured or malformed targets must never become resolved target states."""
from copy import deepcopy
import math

import pytest

from causal_model.mechanism_region import CandidateObservation, CandidateOutcome
from causal_model.target_observation_value import (
    candidate_target_mutual_information_bits,
    target_entropy_bits,
    target_observation_information_value,
)


def _candidate(outcomes=True):
    return CandidateObservation(
        name="q", description="binary q", target_switches=[], rationale="input audit",
        outcomes=[CandidateOutcome(
            name=str(i), description=str(i), prior_probability=0.5,
            extra_pattern_rows=[{
                "type": "absolute_summary", "population": "pop", "variable": "q",
                "observed_value": str(i), "scale": "0.01",
            }],
        ) for i in (0, 1)] if outcomes else [],
    )


@pytest.mark.parametrize("rows", [
    [{"pop_q": 0}, {"pop_q": 1}],
    [{"pop_q": 0, "T": 0}, {"pop_q": 1}],
    [{"pop_q": 0, "T": None}, {"pop_q": 1, "T": None}],
    [{"pop_q": 0, "T": float("nan")}, {"pop_q": 1, "T": 1}],
    [{"pop_q": 0, "T": float("inf")}, {"pop_q": 1, "T": 1}],
    [{"pop_q": 0, "T": float("-inf")}, {"pop_q": 1, "T": 1}],
    [{"pop_q": 0, "T": (None,)}, {"pop_q": 1, "T": (1,)}],
    [{"pop_q": 0, "T": (float("nan"),)}, {"pop_q": 1, "T": (1,)}],
])
def test_missing_or_nonfinite_targets_fail_before_information_is_reported(rows):
    with pytest.raises(ValueError, match="target column"):
        target_entropy_bits(rows, ["T"])
    for candidate in (_candidate(), _candidate(outcomes=False)):
        with pytest.raises(ValueError, match="target column"):
            candidate_target_mutual_information_bits(rows, candidate, ["T"])
        with pytest.raises(ValueError, match="target column"):
            target_observation_information_value(rows, [candidate], target_columns=["T"])
    with pytest.raises(ValueError, match="target column"):
        target_observation_information_value(rows, [], target_columns=["T"])


@pytest.mark.parametrize("columns", [[], "T", ["T", "T"], [""], [" "], [3]])
def test_target_declaration_is_validated_consistently(columns):
    rows = [{"T": 0, "pop_q": 0}, {"T": 1, "pop_q": 1}]
    with pytest.raises(ValueError, match="target"):
        target_entropy_bits(rows, columns)
    with pytest.raises(ValueError, match="target"):
        candidate_target_mutual_information_bits(rows, _candidate(), columns)
    with pytest.raises(ValueError, match="target"):
        target_observation_information_value(rows, [_candidate()], target_columns=columns)


@pytest.mark.parametrize("labels", [(False, True), (0, 1), ("low", "high"), ((0, "a"), (1, "b")), (10**1000, 10**1000 + 1)])
def test_valid_discrete_targets_keep_exact_information_and_do_not_mutate_rows(labels):
    rows = [{"T": labels[i], "pop_q": i} for i in (0, 1)]
    before = deepcopy(rows)
    assert target_entropy_bits(rows, ["T"]) == pytest.approx(1.0)
    result = target_observation_information_value(rows, [_candidate()], target_columns=["T"])[0]
    assert result.estimable
    assert result.mutual_information_bits == pytest.approx(1.0)
    assert result.normalized_target_value == pytest.approx(1.0)
    assert rows == before


def test_genuinely_constant_target_remains_resolved():
    rows = [{"T": "fixed", "pop_q": i} for i in (0, 1)]
    result = target_observation_information_value(rows, [_candidate()], target_columns=["T"])[0]
    assert result.target_already_identified
    assert result.mutual_information_bits == 0.0
    assert result.normalized_target_value == 0.0


def test_missing_targets_cannot_stop_sequential_design_as_identified():
    from causal_model.target_sequential_design import target_sequential_observation_design
    with pytest.raises(ValueError, match="missing target column"):
        target_sequential_observation_design(
            [{"pop_q": 0}, {"pop_q": 1}], [_candidate()],
            target_columns=["T"], realised_outcomes={"q": "0"}, budget=1,
        )


def test_empty_and_unhashable_targets_keep_explicit_errors():
    with pytest.raises(ValueError, match="non-empty"):
        target_entropy_bits([], ["T"])
    with pytest.raises(ValueError, match="hashable"):
        target_entropy_bits([{"T": []}], ["T"])
    assert candidate_target_mutual_information_bits([], _candidate(), ["T"]) is None
