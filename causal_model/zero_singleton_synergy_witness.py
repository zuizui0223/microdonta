"""Minimal witness: zero singleton information can hide joint mechanism information.

The construction is the XOR table.  The declared mechanism S and two future
observations Q1, Q2 satisfy

    I(S;Q1) = I(S;Q2) = 0
    I(S;Q1,Q2) = 1 bit.

After either zero-valued observation is realised, the other observation carries
one full bit about S.  The witness therefore constrains only the interpretation
of a positive-only greedy stopping rule: all singleton values equal to zero is a
one-step information limit, not in general a proof that the full candidate
vocabulary contains no resolving information in combinations.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math

from causal_model import CandidateObservation, CandidateOutcome, observation_information_value


@dataclass(frozen=True)
class _Switch:
    name: str


@dataclass(frozen=True)
class ZeroSingletonSynergyWitness:
    singleton_information_bits: dict[str, float]
    singleton_values: dict[str, float]
    joint_information_bits: float
    expected_conditional_second_information_bits: float
    greedy_positive_only_stops: bool
    n_rows: int


def _band_outcome(name: str, variable: str, value: float) -> CandidateOutcome:
    return CandidateOutcome(
        name=name,
        description=f"{variable} around {value}",
        prior_probability=0.5,
        extra_pattern_rows=[
            {
                "type": "absolute_summary",
                "variable": variable,
                "population": "p",
                "observed_value": str(value),
                "scale": "0.05",
            }
        ],
    )


def candidate_observations() -> list[CandidateObservation]:
    return [
        CandidateObservation(
            name="observe_Q1",
            description="Observe the first XOR component.",
            target_switches=["S"],
            rationale="Zero singleton MI but can unlock conditional information in Q2.",
            outcomes=[
                _band_outcome("Q1_1", "q1", 0.75),
                _band_outcome("Q1_0", "q1", 0.25),
            ],
        ),
        CandidateObservation(
            name="observe_Q2",
            description="Observe the second XOR component.",
            target_switches=["S"],
            rationale="Zero singleton MI but jointly resolves S with Q1.",
            outcomes=[
                _band_outcome("Q2_1", "q2", 0.75),
                _band_outcome("Q2_0", "q2", 0.25),
            ],
        ),
    ]


def xor_rows(repeats_per_cell: int = 20) -> list[dict]:
    if repeats_per_cell < 1:
        raise ValueError("repeats_per_cell must be positive")
    rows: list[dict] = []
    for q1 in (False, True):
        for q2 in (False, True):
            s = bool(q1) ^ bool(q2)
            rows.extend(
                {
                    "S": s,
                    "p_q1": 0.75 if q1 else 0.25,
                    "p_q2": 0.75 if q2 else 0.25,
                }
                for _ in range(repeats_per_cell)
            )
    return rows


def _mutual_information_bits(rows: list[dict], outcome_names: tuple[str, ...]) -> float:
    """Empirical I(S; outcome tuple) for deterministic row columns."""
    if not rows:
        raise ValueError("rows must be nonempty")
    joint: Counter[tuple[bool, tuple[bool, ...]]] = Counter()
    s_counts: Counter[bool] = Counter()
    q_counts: Counter[tuple[bool, ...]] = Counter()
    for row in rows:
        s = bool(row["S"])
        q = tuple(float(row[name]) > 0.5 for name in outcome_names)
        joint[(s, q)] += 1
        s_counts[s] += 1
        q_counts[q] += 1
    n = len(rows)
    value = 0.0
    for (s, q), count in joint.items():
        p_joint = count / n
        p_s = s_counts[s] / n
        p_q = q_counts[q] / n
        value += p_joint * math.log2(p_joint / (p_s * p_q))
    return 0.0 if abs(value) < 1e-12 else value


def _expected_q2_information_after_q1(rows: list[dict]) -> float:
    """E[I(S;Q2 | Q1=q1)] computed with the publication candidate scorer."""
    q2_candidate = candidate_observations()[1]
    switch = [_Switch("S")]
    total = 0.0
    n = len(rows)
    for q1_state in (False, True):
        subset = [row for row in rows if (float(row["p_q1"]) > 0.5) == q1_state]
        result = observation_information_value(subset, switch, [q2_candidate])[0]
        if not result.estimable or result.mutual_information_bits is None:
            raise RuntimeError("Q2 should be estimable after conditioning on Q1")
        total += (len(subset) / n) * float(result.mutual_information_bits)
    return total


def evaluate_zero_singleton_synergy(repeats_per_cell: int = 20) -> ZeroSingletonSynergyWitness:
    rows = xor_rows(repeats_per_cell)
    candidates = candidate_observations()
    results = observation_information_value(rows, [_Switch("S")], candidates)
    bits = {
        result.candidate: float(result.mutual_information_bits or 0.0)
        for result in results
    }
    values = {
        result.candidate: float(result.information_value or 0.0)
        for result in results
    }
    joint_bits = _mutual_information_bits(rows, ("p_q1", "p_q2"))
    conditional_bits = _expected_q2_information_after_q1(rows)
    return ZeroSingletonSynergyWitness(
        singleton_information_bits=bits,
        singleton_values=values,
        joint_information_bits=joint_bits,
        expected_conditional_second_information_bits=conditional_bits,
        greedy_positive_only_stops=all(value <= 1e-12 for value in values.values()),
        n_rows=len(rows),
    )


if __name__ == "__main__":
    result = evaluate_zero_singleton_synergy()
    print("singleton MI:", result.singleton_information_bits)
    print("joint MI:", result.joint_information_bits)
    print("E conditional second-step MI:", result.expected_conditional_second_information_bits)
    print("positive-only greedy stops:", result.greedy_positive_only_stops)
