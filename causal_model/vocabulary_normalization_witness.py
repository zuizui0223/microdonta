"""Controlled witness for mechanism-vocabulary normalization sensitivity.

MROD reports raw joint mechanism entropy H(S|A), raw mechanism-observation
mutual information I(S;Q|A), and normalized quantities

    R = 1 - H(S|A)/K
    V = I(S;Q|A)/K,

where K is the number of declared binary mechanism coordinates.

This witness appends a deterministic redundant coordinate ``A_copy = A``.  The
scientific mechanism state is unchanged: (A,B,A_copy) contains no information
beyond (A,B).  Therefore raw entropy and raw candidate mutual information are
unchanged, while the K-normalized magnitudes change because the declared binary
coordinate count changes from 2 to 3.

The candidate ordering remains unchanged because all candidate information
values within one vocabulary are multiplied by the same positive factor 1/K.
The witness therefore distinguishes two claims:

* raw information and within-vocabulary candidate selection are invariant to a
  deterministic redundant coordinate;
* normalized R and V magnitudes are not vocabulary-invariant and must not be
  compared naively across differently encoded mechanism vocabularies.
"""
from __future__ import annotations

from dataclasses import dataclass

from causal_model import (
    CandidateObservation,
    CandidateOutcome,
    mechanism_entropy,
    mechanism_resolvability,
    observation_information_value,
)


@dataclass(frozen=True)
class _Switch:
    name: str


@dataclass(frozen=True)
class VocabularyNormalizationWitness:
    original_entropy_bits: float
    redundant_entropy_bits: float
    original_resolvability: float
    redundant_resolvability: float
    original_information_bits: dict[str, float]
    redundant_information_bits: dict[str, float]
    original_values: dict[str, float]
    redundant_values: dict[str, float]
    original_ranking: tuple[str, ...]
    redundant_ranking: tuple[str, ...]


def _outcome(name: str, variable: str, value: float) -> CandidateOutcome:
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


def candidates() -> list[CandidateObservation]:
    return [
        CandidateObservation(
            name="observe_A",
            description="Read A exactly.",
            target_switches=["A"],
            rationale="One-bit mechanism observation.",
            outcomes=[
                _outcome("A_on", "qA", 0.75),
                _outcome("A_off", "qA", 0.25),
            ],
        ),
        CandidateObservation(
            name="observe_A_and_B",
            description="Read the conjunction A and B.",
            target_switches=["A", "B"],
            rationale="Deterministic lower-entropy mechanism observation.",
            outcomes=[
                _outcome("AB_on", "qAB", 0.75),
                _outcome("AB_off", "qAB", 0.25),
            ],
        ),
    ]


def rows(repeats_per_state: int = 20) -> list[dict]:
    if repeats_per_state < 1:
        raise ValueError("repeats_per_state must be positive")
    out: list[dict] = []
    for a in (False, True):
        for b in (False, True):
            out.extend(
                {
                    "A": a,
                    "B": b,
                    "A_copy": a,
                    "p_qA": 0.75 if a else 0.25,
                    "p_qAB": 0.75 if (a and b) else 0.25,
                }
                for _ in range(repeats_per_state)
            )
    return out


def _score(sample: list[dict], switches: list[_Switch]):
    result = observation_information_value(sample, switches, candidates())
    information_bits = {
        item.candidate: float(item.mutual_information_bits or 0.0)
        for item in result
    }
    values = {
        item.candidate: float(item.information_value or 0.0)
        for item in result
    }
    ranking = tuple(
        item.candidate
        for item in sorted(
            result,
            key=lambda item: item.information_value if item.information_value is not None else -1.0,
            reverse=True,
        )
    )
    return information_bits, values, ranking


def evaluate_vocabulary_normalization(
    repeats_per_state: int = 20,
) -> VocabularyNormalizationWitness:
    sample = rows(repeats_per_state)
    original_switches = [_Switch("A"), _Switch("B")]
    redundant_switches = [_Switch("A"), _Switch("B"), _Switch("A_copy")]

    original_information_bits, original_values, original_ranking = _score(
        sample, original_switches
    )
    redundant_information_bits, redundant_values, redundant_ranking = _score(
        sample, redundant_switches
    )

    return VocabularyNormalizationWitness(
        original_entropy_bits=mechanism_entropy(sample, original_switches),
        redundant_entropy_bits=mechanism_entropy(sample, redundant_switches),
        original_resolvability=mechanism_resolvability(sample, original_switches),
        redundant_resolvability=mechanism_resolvability(sample, redundant_switches),
        original_information_bits=original_information_bits,
        redundant_information_bits=redundant_information_bits,
        original_values=original_values,
        redundant_values=redundant_values,
        original_ranking=original_ranking,
        redundant_ranking=redundant_ranking,
    )


if __name__ == "__main__":
    result = evaluate_vocabulary_normalization()
    print("entropy bits:", result.original_entropy_bits, result.redundant_entropy_bits)
    print("resolvability:", result.original_resolvability, result.redundant_resolvability)
    print("raw MI:", result.original_information_bits, result.redundant_information_bits)
    print("normalized V:", result.original_values, result.redundant_values)
    print("rankings:", result.original_ranking, result.redundant_ranking)
