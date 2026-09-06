"""Controlled witness separating structural novelty from mechanism information.

This module is intentionally small and deterministic.  It demonstrates the
one-way Boundary -> MROD interface without importing the separate ``boundary``
package or creating a runtime dependency between repositories.

The latent log-linear state is x=(x0,x1,x2).  Current evidence observes only

    x0 + x1 = 0.

The scientific mechanism switch is S = 1[x1>0], while x2 is an independent
nuisance coordinate.  Three candidate scalar observations are compared:

1. ``redundant``      row (2,2,0): inside the current row span;
2. ``nuisance_new``   row (0,0,1): adds structural rank but only measures x2;
3. ``mechanism_new``  row (0,1,0): adds structural rank and reveals S.

Thus rank gain can rule out the first candidate but cannot distinguish the
second from the third.  MROD's I(S;Q|A)/K separates them exactly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import json
from typing import Iterable, Sequence

from causal_model import CandidateObservation, CandidateOutcome, observation_information_value


CURRENT_ROWS: tuple[tuple[int, int, int], ...] = ((1, 1, 0),)
CANDIDATE_ROWS: dict[str, tuple[int, int, int]] = {
    "redundant": (2, 2, 0),
    "nuisance_new": (0, 0, 1),
    "mechanism_new": (0, 1, 0),
}


class _Switch:
    def __init__(self, name: str):
        self.name = name


@dataclass(frozen=True)
class ScreenWitnessResult:
    candidate: str
    observation_row: tuple[int, int, int]
    rank_gain: int
    mutual_information_bits: float
    information_value: float
    structurally_new: bool
    mechanism_informative: bool


@dataclass(frozen=True)
class ScreenPolicySummary:
    random_all_expected_information: float
    structural_filter_uniform_tie_expected_information: float
    mrod_max_information: float
    mrod_selected_candidate: str


def _exact_rank(rows: Iterable[Sequence[int]]) -> int:
    """Exact row rank for this tiny rational witness."""
    a = [[Fraction(v) for v in row] for row in rows]
    if not a:
        return 0
    n_cols = len(a[0])
    if any(len(row) != n_cols for row in a):
        raise ValueError("all rows must have the same length")

    rank = 0
    for col in range(n_cols):
        pivot = next((i for i in range(rank, len(a)) if a[i][col] != 0), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        pivot_value = a[rank][col]
        a[rank] = [v / pivot_value for v in a[rank]]
        for i in range(len(a)):
            if i == rank or a[i][col] == 0:
                continue
            factor = a[i][col]
            a[i] = [u - factor * v for u, v in zip(a[i], a[rank])]
        rank += 1
        if rank == len(a):
            break
    return rank


def _rank_gain(candidate_row: Sequence[int]) -> int:
    before = _exact_rank(CURRENT_ROWS)
    after = _exact_rank((*CURRENT_ROWS, tuple(candidate_row)))
    gain = after - before
    if gain not in (0, 1):
        raise AssertionError("one scalar candidate must change rank by zero or one")
    return gain


def _band(variable: str, value: float) -> list[dict[str, str]]:
    return [{
        "type": "absolute_summary",
        "variable": variable,
        "population": "pop",
        "observed_value": str(value),
        "scale": "0.05",
    }]


def _candidates() -> list[CandidateObservation]:
    return [
        CandidateObservation(
            name="redundant",
            description="Rescaled copy of the current observation direction.",
            target_switches=["S"],
            rationale="Structural zero-value witness.",
            outcomes=[
                CandidateOutcome(
                    name="zero",
                    description="The current fibre already fixes this value.",
                    prior_probability=1.0,
                    extra_pattern_rows=_band("redundant", 0.0),
                )
            ],
        ),
        CandidateObservation(
            name="nuisance_new",
            description="A structurally new observation of nuisance coordinate x2.",
            target_switches=["S"],
            rationale="False-converse witness: new rank need not inform S.",
            outcomes=[
                CandidateOutcome(
                    name="low",
                    description="x2=-1",
                    prior_probability=0.5,
                    extra_pattern_rows=_band("nuisance", -1.0),
                ),
                CandidateOutcome(
                    name="high",
                    description="x2=1",
                    prior_probability=0.5,
                    extra_pattern_rows=_band("nuisance", 1.0),
                ),
            ],
        ),
        CandidateObservation(
            name="mechanism_new",
            description="A structurally new observation of mechanism coordinate x1.",
            target_switches=["S"],
            rationale="Positive witness: the outcome identifies S.",
            outcomes=[
                CandidateOutcome(
                    name="off",
                    description="x1=-1, hence S is OFF",
                    prior_probability=0.5,
                    extra_pattern_rows=_band("mechanism", -1.0),
                ),
                CandidateOutcome(
                    name="on",
                    description="x1=1, hence S is ON",
                    prior_probability=0.5,
                    extra_pattern_rows=_band("mechanism", 1.0),
                ),
            ],
        ),
    ]


def build_witness_rows(n_per_cell: int = 25) -> list[dict]:
    """Return a balanced current fibre with S independent of nuisance x2."""
    if n_per_cell < 1:
        raise ValueError("n_per_cell must be positive")
    rows: list[dict] = []
    for switch_on in (False, True):
        x1 = 1.0 if switch_on else -1.0
        x0 = -x1  # current observation x0+x1 is identically zero
        for x2 in (-1.0, 1.0):
            for _ in range(n_per_cell):
                rows.append({
                    "S": switch_on,
                    "x0": x0,
                    "x1": x1,
                    "x2": x2,
                    "pop_redundant": 2.0 * x0 + 2.0 * x1,
                    "pop_nuisance": x2,
                    "pop_mechanism": x1,
                })
    return rows


def structural_vs_mechanism_witness(n_per_cell: int = 25) -> tuple[list[ScreenWitnessResult], ScreenPolicySummary]:
    """Compute exact rank gains and publication-level MROD information values."""
    rows = build_witness_rows(n_per_cell=n_per_cell)
    switches = [_Switch("S")]
    info = {
        result.candidate: result
        for result in observation_information_value(rows, switches, _candidates())
    }

    results: list[ScreenWitnessResult] = []
    for name, candidate_row in CANDIDATE_ROWS.items():
        value = info[name]
        if not value.estimable or not value.partition_verified:
            raise RuntimeError(f"candidate {name!r} lost its verified partition")
        mi = float(value.mutual_information_bits or 0.0)
        iv = float(value.information_value or 0.0)
        gain = _rank_gain(candidate_row)
        results.append(ScreenWitnessResult(
            candidate=name,
            observation_row=candidate_row,
            rank_gain=gain,
            mutual_information_bits=mi,
            information_value=iv,
            structurally_new=bool(gain),
            mechanism_informative=mi > 0.0,
        ))

    values = {result.candidate: result.information_value for result in results}
    structurally_new = [result for result in results if result.structurally_new]
    max_result = max(results, key=lambda result: result.information_value)
    policy = ScreenPolicySummary(
        random_all_expected_information=sum(values.values()) / len(values),
        structural_filter_uniform_tie_expected_information=(
            sum(result.information_value for result in structurally_new) / len(structurally_new)
        ),
        mrod_max_information=max_result.information_value,
        mrod_selected_candidate=max_result.candidate,
    )
    return results, policy


def summary_dict(n_per_cell: int = 25) -> dict:
    results, policy = structural_vs_mechanism_witness(n_per_cell=n_per_cell)
    return {
        "candidates": [asdict(result) for result in results],
        "policy_summary": asdict(policy),
    }


if __name__ == "__main__":
    print(json.dumps(summary_dict(), indent=2, sort_keys=True))
