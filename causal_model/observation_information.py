"""Observation information value from the current admissible mechanism region.

For a candidate observation ``Q`` whose listed outcomes form a verified mutually
exclusive and exhaustive partition of the current ``A_epsilon``:

    V(Q)
      = E_Q[R(S | Q)] - R(S)
      = [H(S) - H(S | Q)] / K
      = I(S; Q) / K.

The validated publication quantity is therefore normalized mechanism-observation
mutual information. It is non-negative and is zero exactly when the candidate
observation is conditionally independent of the remaining mechanism vector under
the current admissible region.

Predictive probabilities and conditional regions are computed from exactly the
same row-level observation maps used by sequential observation design. If those
maps do not partition the current admissible region, this module reports the
candidate as non-estimable for the validated information-value quantity; declared
outcome priors remain available only to explicitly labelled fallback workflows.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import math

from causal_model.mechanism_region import CandidateObservation, causal_resolvability
from causal_model.sequential_observation import filter_by_outcome, predictive_outcome_distribution


@dataclass(frozen=True)
class ObservationInformationResult:
    """One candidate's admissible-region information value and provenance."""

    candidate: str
    current_R: float
    expected_R: float | None
    evsi: float | None
    estimable: bool
    probability_source: str
    partition_verified: bool
    outcome_probabilities: dict[str, float] = field(default_factory=dict)
    outcome_sizes: dict[str, int] = field(default_factory=dict)
    mutual_information_bits: float | None = None
    information_identity_error: float | None = None
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
) -> ObservationInformationResult:
    return ObservationInformationResult(
        candidate=candidate.name,
        current_R=current_R,
        expected_R=None,
        evsi=None,
        estimable=False,
        probability_source=source,
        partition_verified=partition_verified,
        outcome_probabilities=dict(probabilities or {}),
        outcome_sizes=dict(sizes or {}),
        mutual_information_bits=None,
        information_identity_error=None,
        reason=reason,
    )


def candidate_mutual_information_bits(
    accepted_rows: list[dict],
    switches,
    candidate: CandidateObservation,
) -> float | None:
    """Return empirical ``I(S;Q | A_epsilon)`` in bits for a verified candidate.

    The calculation is independent of the resolvability implementation: it builds
    the empirical joint table of mechanism state ``S`` and candidate outcome ``Q``
    directly from the verified outcome partition. ``None`` means that the stored
    admissible region does not identify the predictive outcome distribution.
    """
    rows = list(accepted_rows)
    switch_list = list(switches)
    if not rows or not candidate.outcomes:
        return None

    distribution = predictive_outcome_distribution(candidate, rows)
    if not distribution.partition_verified:
        return None

    joint: Counter[tuple[tuple[bool, ...], str]] = Counter()
    state_counts: Counter[tuple[bool, ...]] = Counter()
    outcome_counts: Counter[str] = Counter()

    for outcome in candidate.outcomes:
        sub = filter_by_outcome(rows, outcome.extra_pattern_rows)
        for row in sub:
            state = tuple(bool(row.get(sw.name)) for sw in switch_list)
            joint[(state, outcome.name)] += 1
            state_counts[state] += 1
            outcome_counts[outcome.name] += 1

    n = len(rows)
    if sum(joint.values()) != n:
        raise RuntimeError(
            "verified predictive partition did not reproduce every admissible row exactly once"
        )

    mi = 0.0
    for (state, outcome_name), count in joint.items():
        p_joint = count / n
        p_state = state_counts[state] / n
        p_outcome = outcome_counts[outcome_name] / n
        mi += p_joint * math.log2(p_joint / (p_state * p_outcome))

    # Roundoff can produce a tiny negative value around zero only.
    if mi < 0.0 and abs(mi) < 1e-12:
        mi = 0.0
    return mi


def compute_observation_information_values(
    accepted_rows: list[dict],
    switches,
    candidates: list[CandidateObservation],
    *,
    min_sub_size: int = 1,
) -> list[ObservationInformationResult]:
    """Compute validated observation information values for explicit outcomes.

    Only candidates whose outcome maps partition the *current* admissible region
    are estimable by the filtering identity. This is the same condition under
    which sequential observation design can use ``Pr(v | current A_epsilon)``
    rather than a declared fallback prior.

    For every estimable candidate, the implementation checks
    ``V(Q) = I(S;Q)/K`` against the direct expected-resolvability calculation.
    Their only allowed discrepancy is the existing four-decimal rounding of the
    resolvability display quantity.

    ``min_sub_size`` is a numerical reliability guard, not a scientific success
    threshold. If any positive-probability outcome has fewer rows than the guard,
    the candidate is reported as non-estimable instead of dropping that outcome
    and biasing the expectation.
    """
    if min_sub_size < 1:
        raise ValueError("min_sub_size must be at least 1")

    switch_list = list(switches)
    current_R = causal_resolvability(accepted_rows, switch_list)
    results: list[ObservationInformationResult] = []

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
                    "validated admissible-region information value is unavailable"
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
            R_outcome = causal_resolvability(sub, switch_list)
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

        mi_bits = candidate_mutual_information_bits(
            accepted_rows, switch_list, candidate
        )
        if mi_bits is None:
            raise RuntimeError("verified predictive partition lost its information measure")
        K = len(switch_list)
        information_value = (mi_bits / K) if K > 0 else 0.0
        resolvability_gain = expected_R - current_R
        identity_error = resolvability_gain - information_value
        # causal_resolvability currently rounds each R value to four decimals;
        # two rounded terms can differ from the exact MI identity by ~1e-4.
        if abs(identity_error) > 2.5e-4:
            raise RuntimeError(
                f"information identity failed for {candidate.name!r}: "
                f"expected-R gain={resolvability_gain:.8f}, I(S;Q)/K={information_value:.8f}"
            )

        # Use the information-theoretic value as the canonical score. It is exact
        # for the empirical partition and cannot become spuriously negative
        # because of display rounding in the resolvability statistic.
        value = max(0.0, information_value)
        results.append(ObservationInformationResult(
            candidate=candidate.name,
            current_R=current_R,
            expected_R=round(expected_R, 4),
            evsi=round(value, 4),
            estimable=True,
            probability_source=distribution.source,
            partition_verified=True,
            outcome_probabilities=probabilities,
            outcome_sizes=sizes,
            mutual_information_bits=round(mi_bits, 6),
            information_identity_error=round(identity_error, 8),
            reason="",
        ))

    # Estimable observations first, ordered by validated information value.
    # Non-estimable candidates are retained for transparency.
    results.sort(
        key=lambda result: (
            result.estimable,
            result.evsi if result.evsi is not None else float("-inf"),
        ),
        reverse=True,
    )
    return results


# Historical backend aliases remain available for frozen/support code only.
EVSIResult = ObservationInformationResult
next_observation_evsi = compute_observation_information_values


__all__ = [
    "ObservationInformationResult",
    "candidate_mutual_information_bits",
    "compute_observation_information_values",
    "EVSIResult",
    "next_observation_evsi",
]
