"""Information value of candidate observations under an admissible mechanism region.

For a candidate observation Q whose outcomes form a verified partition of the
current admissible region A_epsilon, the publication quantity is

    V(Q) = I(S; Q | A_epsilon) / K,

where S is the residual mechanism vector and K is the number of binary mechanism
coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass
from .observation_information import (
    candidate_mutual_information_bits,
    compute_observation_information_values,
)


@dataclass(frozen=True)
class InformationValueResult:
    candidate: str
    current_resolvability: float
    expected_resolvability: float | None
    information_value: float | None
    estimable: bool
    probability_source: str
    partition_verified: bool
    outcome_probabilities: dict[str, float]
    outcome_sizes: dict[str, int]
    mutual_information_bits: float | None
    information_identity_error: float | None
    reason: str


def observation_information_value(accepted_rows, switches, candidates, *, min_sub_size: int = 1):
    """Return publication-facing information-value records for candidates."""
    backend_rows = compute_observation_information_values(
        accepted_rows,
        switches,
        candidates,
        min_sub_size=min_sub_size,
    )
    return [
        InformationValueResult(
            candidate=row.candidate,
            current_resolvability=row.current_R,
            expected_resolvability=row.expected_R,
            information_value=row.evsi,
            estimable=row.estimable,
            probability_source=row.probability_source,
            partition_verified=row.partition_verified,
            outcome_probabilities=dict(row.outcome_probabilities),
            outcome_sizes=dict(row.outcome_sizes),
            mutual_information_bits=row.mutual_information_bits,
            information_identity_error=row.information_identity_error,
            reason=row.reason,
        )
        for row in backend_rows
    ]


__all__ = [
    "InformationValueResult",
    "candidate_mutual_information_bits",
    "observation_information_value",
]
