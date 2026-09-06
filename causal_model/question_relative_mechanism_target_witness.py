"""Internal witness for question-relative mechanism resolution.

This audit specializes the existing target-aware MROD utilities to the case where
an ecological question target ``T`` is a deterministic coarsening of the full
mechanism world ``S``.  It demonstrates that learning more about the full mechanism
state is not the same objective as resolving the mechanism distinction named by
the scientific question.

The module does not change the publication-facing MROD objective and does not
introduce a new information-theory result.  It uses the existing public mechanism
and target information-value APIs on one controlled finite admissible region.
"""
from __future__ import annotations

from dataclasses import dataclass

from causal_model.mechanism_region import CandidateObservation, CandidateOutcome, mechanism_entropy
from causal_model.observation_value import observation_information_value
from causal_model.target_observation_value import (
    target_entropy_bits,
    target_observation_information_value,
)


@dataclass(frozen=True)
class _Switch:
    name: str


@dataclass(frozen=True)
class QuestionRelativeMechanismTargetWitness:
    full_state_entropy_bits: float
    question_target_entropy_bits: float
    full_state_information_bits: dict[str, float]
    full_state_normalized_values: dict[str, float]
    question_target_information_bits: dict[str, float]
    question_target_normalized_values: dict[str, float]
    full_state_best: str
    question_target_best: str
    resolved_target_entropy_bits: float
    residual_full_state_entropy_bits_after_target_resolution: float


def _absolute_outcome(name: str, variable: str, value: float, probability: float) -> CandidateOutcome:
    return CandidateOutcome(
        name=name,
        description=f"{variable}={value}",
        prior_probability=probability,
        extra_pattern_rows=[
            {
                "type": "absolute_summary",
                "variable": variable,
                "population": "pop",
                "observed_value": str(value),
                "scale": "0.01",
            }
        ],
    )


def _candidates() -> list[CandidateObservation]:
    return [
        CandidateObservation(
            name="deep_submechanism",
            description="Read two within-class submechanism bits U1 and U2.",
            target_switches=["U1", "U2"],
            rationale="Deep measurement resolves within-question-class mechanism detail.",
            outcomes=[
                _absolute_outcome(f"u_code_{code}", "deep_read", float(code), 0.25)
                for code in range(4)
            ],
        ),
        CandidateObservation(
            name="question_class",
            description="Read the ecological mechanism class T named by the question.",
            target_switches=["T"],
            rationale="Coarser measurement directly resolves the declared ecological contrast.",
            outcomes=[
                _absolute_outcome("class_0", "target_read", 0.0, 0.5),
                _absolute_outcome("class_1", "target_read", 1.0, 0.5),
            ],
        ),
    ]


def _rows() -> list[dict]:
    rows: list[dict] = []
    for target in (0, 1):
        for u1 in (0, 1):
            for u2 in (0, 1):
                rows.append(
                    {
                        "T": bool(target),
                        "U1": bool(u1),
                        "U2": bool(u2),
                        # T = tau(S): the question target is a deterministic
                        # coarsening of the full mechanism vector S=(T,U1,U2).
                        "question_class": "pollinator" if target else "abiotic",
                        "pop_target_read": float(target),
                        "pop_deep_read": float(2 * u1 + u2),
                    }
                )
    return rows


def _resolved_target_rows() -> list[dict]:
    # Hold the ecological question class fixed while retaining four distinct
    # within-class mechanism worlds.  This is the strict converse witness:
    # H(T)=0 while H(S)>0.
    return [row for row in _rows() if not row["T"]]


def build_question_relative_mechanism_target_witness() -> QuestionRelativeMechanismTargetWitness:
    rows = _rows()
    switches = [_Switch("T"), _Switch("U1"), _Switch("U2")]
    candidates = _candidates()

    mechanism_results = {
        row.candidate: row
        for row in observation_information_value(rows, switches, candidates)
    }
    target_results = {
        row.candidate: row
        for row in target_observation_information_value(
            rows,
            candidates,
            target_columns=["question_class"],
        )
    }

    full_bits = {
        name: float(result.mutual_information_bits)
        for name, result in mechanism_results.items()
        if result.estimable and result.mutual_information_bits is not None
    }
    full_values = {
        name: float(result.information_value)
        for name, result in mechanism_results.items()
        if result.estimable and result.information_value is not None
    }
    target_bits = {
        name: float(result.mutual_information_bits)
        for name, result in target_results.items()
        if result.estimable and result.mutual_information_bits is not None
    }
    target_values = {
        name: float(result.normalized_target_value)
        for name, result in target_results.items()
        if result.estimable and result.normalized_target_value is not None
    }

    resolved_rows = _resolved_target_rows()
    return QuestionRelativeMechanismTargetWitness(
        full_state_entropy_bits=mechanism_entropy(rows, switches),
        question_target_entropy_bits=target_entropy_bits(rows, ["question_class"]),
        full_state_information_bits=full_bits,
        full_state_normalized_values=full_values,
        question_target_information_bits=target_bits,
        question_target_normalized_values=target_values,
        full_state_best=max(full_values, key=full_values.get),
        question_target_best=max(target_values, key=target_values.get),
        resolved_target_entropy_bits=target_entropy_bits(resolved_rows, ["question_class"]),
        residual_full_state_entropy_bits_after_target_resolution=mechanism_entropy(
            resolved_rows, switches
        ),
    )


__all__ = [
    "QuestionRelativeMechanismTargetWitness",
    "build_question_relative_mechanism_target_witness",
]
