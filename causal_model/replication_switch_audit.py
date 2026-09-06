"""Internal current-state comparison of repeating a protocol versus switching.

Uses existing noisy-target scoring and Bernoulli observable-law classes. No
realised future outcome is an input to ranking. Conditional likelihoods, support,
weights and replication assumptions are declared by the caller, not learned or
empirically verified here. This is not a cost-optimal or non-myopic policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import fsum, isfinite
from typing import Mapping, Sequence

from causal_model.empirical_observation_contract import (
    LikelihoodCandidate,
    _matrix,
    _weights,
    score_likelihood_candidates,
)
from causal_model.replication_information_audit import replication_information_profile


@dataclass(frozen=True)
class SwitchAlternative:
    candidate: str
    estimable: bool
    reason: str
    calibration_reference: str | None
    information_bits: float | None
    advantage_over_one_repeat_bits: float | None
    advantage_over_all_repeat_ceiling_bits: float | None
    within_repeat_law_information_bits: float | None
    exceeds_repeat_ceiling_with_margin: bool | None


@dataclass(frozen=True)
class ReplicationSwitchAudit:
    target_columns: tuple[str, ...]
    target_entropy_bits: float
    target_image_size: int
    target_identified_in_declared_pool: bool
    repeat_candidate: str
    repeat_estimable: bool
    repeat_calibration_reference: str | None
    one_repeat_information_bits: float | None
    all_repeat_information_ceiling_bits: float | None
    repeat_residual_floor_bits: float | None
    same_law_different_target_pair: tuple[int, int] | None
    alternatives: tuple[SwitchAlternative, ...]
    best_positive_singletons: tuple[str, ...]
    ceiling_dominant_alternatives: tuple[str, ...]
    complete_singleton_coverage: bool
    ranking_scope: str
    next_step_status: str
    support_reference: str
    weight_reference: str
    conditional_iid_reference: str
    future_likelihood_reference: str
    information_tolerance_bits: float
    feasible_domain_exhaustiveness: str = "not_certified"
    scope: str = "expected_target_information_given_current_declared_state_not_cost_utility"


def audit_replication_switch(
    accepted_rows: Sequence[Mapping], repeat_candidate: LikelihoodCandidate,
    alternatives: Sequence[LikelihoodCandidate], *, target_columns: Sequence[str],
    weights: Sequence[float], support_reference: str, weight_reference: str,
    conditional_iid_reference: str, future_likelihood_reference: str,
    information_tolerance_bits: float = 1e-10,
) -> ReplicationSwitchAudit:
    """Compare each alternative to one repeat AND the whole repeat-only ceiling.

    For current evidence D and repeat-law class C, any finite transcript Z made
    solely of fresh repeats of this fixed protocol has I(T;Z|D)<=I(T;C|D).
    An alternative with I(T;Q|D)>I(T;C|D) therefore beats every such repeat-only
    transcript in EXPECTED additional information, irrespective of repeat count.
    The returned margin flag is a floating-point comparison, not an identification
    certificate. Failure to exceed the ceiling does not imply repeating is best.

    Per-world future likelihoods must be valid conditional on current D. Reusing
    a past draw, unmodelled persistent nuisance, interventions, changed sampling
    units or order effects can invalidate that declaration. References are only
    provenance. No joint model across different candidates is manufactured here.
    """
    if (isinstance(information_tolerance_bits, bool)
            or not isfinite(information_tolerance_bits)
            or information_tolerance_bits < 0):
        raise ValueError("information_tolerance_bits must be finite and non-negative")
    if not isinstance(future_likelihood_reference, str) or not future_likelihood_reference.strip():
        raise ValueError("future_likelihood_reference must justify predictions given current data")
    if isinstance(target_columns, (str, bytes)):
        raise ValueError("target_columns must be a sequence, not a bare string")
    rows, columns, supplied_weights = tuple(accepted_rows), tuple(target_columns), tuple(weights)
    alternative_list = tuple(alternatives)
    candidates = (repeat_candidate,) + alternative_list
    for candidate in candidates:
        if not isinstance(candidate.name, str) or not candidate.name.strip():
            raise ValueError("candidate names must be non-empty strings")
        if isinstance(candidate.outcomes, (str, bytes)):
            raise ValueError("outcomes must be a sequence, not a bare string")
    current = score_likelihood_candidates(
        rows, candidates, target_columns=columns, weights=supplied_weights,
        support_reference=support_reference, weight_reference=weight_reference,
    )
    profile = replication_information_profile(
        rows, repeat_candidate, target_columns=columns, weights=supplied_weights,
        support_reference=support_reference, weight_reference=weight_reference,
        conditional_iid_reference=conditional_iid_reference, horizons=(1,),
    )
    scored = {score.name: score for score in current.scores}
    repeat_bits = scored[repeat_candidate.name].information_bits
    ceiling = profile.asymptotic_information_bits
    normalized_weights = _weights(supplied_weights, len(rows))
    comparisons = []
    for candidate in alternative_list:
        score = scored[candidate.name]
        bits = score.information_bits
        one_gap = None if bits is None or repeat_bits is None else bits - repeat_bits
        ceiling_gap = None if bits is None or ceiling is None else bits - ceiling
        within_law = None
        matrix = _matrix(candidate, len(rows))
        if profile.estimable and matrix is not None:
            contributions = []
            for law in profile.law_classes:
                indices = law.world_indices
                restricted = LikelihoodCandidate(
                    candidate.name, candidate.outcomes, tuple(matrix[i] for i in indices),
                    candidate.calibration_reference,
                )
                conditional = score_likelihood_candidates(
                    tuple(rows[i] for i in indices), [restricted], target_columns=columns,
                    weights=tuple(normalized_weights[i] for i in indices),
                    support_reference=support_reference, weight_reference=weight_reference,
                ).scores[0].information_bits
                if conditional is None:
                    raise ArithmeticError("known likelihood lost its within-law information")
                contributions.append(law.probability_mass * conditional)
            within_law = fsum(contributions)
            # Chain rule: I(T;Q)-I(T;C) <= I(T;Q|C).
            if ceiling_gap is not None and ceiling_gap > within_law + 1e-9:
                raise ArithmeticError("switch gain violated the conditional-information bound")
        comparisons.append(SwitchAlternative(
            candidate.name, score.estimable, score.reason, candidate.calibration_reference,
            bits, one_gap, ceiling_gap, within_law,
            None if ceiling_gap is None else ceiling_gap > information_tolerance_bits,
        ))
    positive = [s for s in current.scores if s.information_bits is not None
                and s.information_bits > information_tolerance_bits]
    best = max((s.information_bits for s in positive), default=None)
    best_names = tuple(sorted(s.name for s in positive
                             if abs(s.information_bits - best) <= information_tolerance_bits))
    if current.target_point_identified:
        status = "target_identified_in_declared_pool"
    elif best_names:
        status = "positive_singleton_available"
    elif not current.complete_vocabulary:
        status = "prediction_limited_no_positive_scored_singleton"
    else:
        status = "one_step_zero_at_tolerance_joint_not_audited"
    return ReplicationSwitchAudit(
        columns, current.target_entropy_bits, current.target_image_size,
        current.target_point_identified, repeat_candidate.name, profile.estimable,
        repeat_candidate.calibration_reference, repeat_bits, ceiling,
        profile.irreducible_target_entropy_bits, profile.same_law_different_target_pair,
        tuple(comparisons), best_names,
        tuple(c.candidate for c in comparisons if c.exceeds_repeat_ceiling_with_margin),
        current.complete_vocabulary, current.ranking_scope, status, support_reference,
        weight_reference, conditional_iid_reference, future_likelihood_reference,
        information_tolerance_bits,
    )
