"""Executable witnesses for the Boundary -> MROD zero-value interface."""
from __future__ import annotations

from causal_model import (
    CandidateObservation,
    CandidateOutcome,
    candidate_mutual_information_bits,
    observation_information_value,
)


class _SW:
    def __init__(self, name: str):
        self.name = name


def test_candidate_determined_on_current_region_has_zero_mechanism_information():
    """A candidate constant on the current admissible region cannot resolve S."""
    rows = [{"A": False}, {"A": True}] * 20
    candidate = CandidateObservation(
        name="already_determined",
        description="A quantity already fixed by the current observation map.",
        target_switches=["A"],
        rationale="Structural redundancy witness.",
        outcomes=[
            CandidateOutcome(
                name="same_for_every_row",
                description="Current evidence already determines this outcome.",
                prior_probability=1.0,
                extra_pattern_rows=[],
            )
        ],
    )

    switches = [_SW("A")]
    assert candidate_mutual_information_bits(rows, switches, candidate) == 0.0
    result = observation_information_value(rows, switches, [candidate])[0]
    assert result.estimable
    assert result.partition_verified
    assert result.information_value == 0.0


def test_new_outcome_variation_need_not_be_mechanism_information():
    """The converse is false: varying Q can be independent of mechanism S."""
    rows = []
    for a in (False, True):
        for value in (0.25, 0.75):
            rows.extend({"A": a, "pop_trait": value} for _ in range(20))

    candidate = CandidateObservation(
        name="mechanism_independent_new_direction",
        description="A varying quantity that separates nuisance variation only.",
        target_switches=["A"],
        rationale="Witness that structural novelty is not sufficient for MROD value.",
        outcomes=[
            CandidateOutcome(
                name="high",
                description="High trait outcome.",
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
                description="Low trait outcome.",
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

    switches = [_SW("A")]
    assert candidate_mutual_information_bits(rows, switches, candidate) == 0.0
    result = observation_information_value(rows, switches, [candidate])[0]
    assert result.estimable
    assert result.partition_verified
    assert result.information_value == 0.0
