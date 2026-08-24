"""Validated next-observation EVSI from the current RACH admissible region.

The publication-level NOV is a preposterior expected gain in causal
resolvability, not the older target-switch heuristic score.  For a candidate
observation whose listed outcomes form a verified mutually exclusive and
exhaustive partition of the current ``A_epsilon``:

    EVSI(q) = sum_v Pr(v | A_epsilon)
                    [R(A_epsilon | q=v) - R(A_epsilon)].

The predictive probabilities and conditional regions are computed from exactly
the same row-level observation maps used by RACH-SEQ.  If those maps do not
partition the current admissible region, this module refuses to call the score a
validated EVSI; declared outcome priors remain available to legacy/simulation
workflows but are not substituted silently into the publication-level quantity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from causal_model.causal_admissibility import CandidateObservation, causal_resolvability
from causal_model.rach_seq import filter_by_outcome, predictive_outcome_distribution


@dataclass(frozen=True)
class EVSIResult:
    """One candidate's admissible-region EVSI and provenance."""

    candidate: str
    current_R: float
    expected_R: float | None
    evsi: float | None
    estimable: bool
    probability_source: str
    partition_verified: bool
    outcome_probabilities: dict[str, float] = field(default_factory=dict)
    outcome_sizes: dict[str, int] = field(default_factory=dict)
    reason: str = ""


def _nonestimable(
    candidate: CandidateObservation,
    current_R: float,
    *,
    source: str,
    partition_verified: bool,
    probabilities: dict[str, float] | None = None,
    sizes: dict[str, int] | None = None,
    reason: str,
) -> EVSIResult:
    return EVSIResult(
        candidate=candidate.name,
        current_R=current_R,
        expected_R=None,
        evsi=None,
        estimable=False,
        probability_source=source,
        partition_verified=partition_verified,
        outcome_probabilities=dict(probabilities or {}),
        outcome_sizes=dict(sizes or {}),
        reason=reason,
    )


def next_observation_evsi(
    accepted_rows: list[dict],
    switches,
    candidates: list[CandidateObservation],
    *,
    min_sub_size: int = 1,
) -> list[EVSIResult]:
    """Compute publication-level NOV/EVSI for explicit candidate outcomes.

    Only candidates whose outcome maps partition the *current* admissible region
    are estimable by this cheap filtering identity.  This is the same condition
    under which RACH-SEQ uses ``Pr(v | current A_epsilon)`` rather than a declared
    fallback prior.

    ``min_sub_size`` is a numerical reliability guard, not a scientific success
    threshold.  If any positive-probability outcome has fewer rows than the guard,
    the candidate is reported as non-estimable instead of dropping that outcome
    and biasing the expectation.
    """
    if min_sub_size < 1:
        raise ValueError("min_sub_size must be at least 1")

    current_R = causal_resolvability(accepted_rows, switches)
    results: list[EVSIResult] = []

    for candidate in candidates:
        if not candidate.outcomes:
            results.append(_nonestimable(
                candidate,
                current_R,
                source="no_outcomes",
                partition_verified=False,
                reason="candidate has no explicit outcome map",
            ))
            continue

        distribution = predictive_outcome_distribution(candidate, accepted_rows)
        probabilities = dict(distribution.probabilities)
        if not distribution.partition_verified:
            results.append(_nonestimable(
                candidate,
                current_R,
                source=distribution.source,
                partition_verified=False,
                probabilities=probabilities,
                reason=(
                    "outcome maps do not form a verified partition of current A_epsilon; "
                    "validated admissible-region EVSI is unavailable"
                ),
            ))
            continue

        expected_R = 0.0
        sizes: dict[str, int] = {}
        failed_reason = ""
        for outcome in candidate.outcomes:
            probability = probabilities.get(outcome.name, 0.0)
            sub = filter_by_outcome(accepted_rows, outcome.extra_pattern_rows)
            sizes[outcome.name] = len(sub)
            if probability <= 0.0:
                continue
            if len(sub) < min_sub_size:
                failed_reason = (
                    f"positive-probability outcome {outcome.name!r} has "
                    f"{len(sub)} rows < min_sub_size={min_sub_size}"
                )
                break
            R_outcome = causal_resolvability(sub, switches)
            if not math.isfinite(R_outcome):
                failed_reason = f"non-finite resolvability for outcome {outcome.name!r}"
                break
            expected_R += probability * R_outcome

        if failed_reason:
            results.append(_nonestimable(
                candidate,
                current_R,
                source=distribution.source,
                partition_verified=True,
                probabilities=probabilities,
                sizes=sizes,
                reason=failed_reason,
            ))
            continue

        evsi = expected_R - current_R
        # Tiny negative values can arise only from floating-point/rounded R values.
        if abs(evsi) < 1e-12:
            evsi = 0.0
        results.append(EVSIResult(
            candidate=candidate.name,
            current_R=current_R,
            expected_R=round(expected_R, 4),
            evsi=round(evsi, 4),
            estimable=True,
            probability_source=distribution.source,
            partition_verified=True,
            outcome_probabilities=probabilities,
            outcome_sizes=sizes,
            reason="",
        ))

    # Estimable observations first, ordered by EVSI. Non-estimable candidates are
    # retained for transparency instead of disappearing from the report.
    results.sort(
        key=lambda result: (
            result.estimable,
            result.evsi if result.evsi is not None else float("-inf"),
        ),
        reverse=True,
    )
    return results


__all__ = ["EVSIResult", "next_observation_evsi"]
