"""Internal finite Bernoulli replication audit using the existing likelihood API.

Fresh measurements are conditionally iid given one fixed full world, including
persistent nuisance parameters. That assumption must be declared, not inferred
from marginal predictions. This is not a new optimizer or a field calibration.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from math import exp, fsum, lgamma, log
from numbers import Integral
from typing import Mapping, Sequence

from causal_model.empirical_observation_contract import (
    LikelihoodCandidate,
    _entropy,
    _matrix,
    _weights,
    condition_on_selected,
    score_likelihood_candidates,
    target_state,
)

# A computational guard for this exhaustive count audit, not a scientific limit.
MAX_REPEATS = 256


@dataclass(frozen=True)
class ObservableLawClass:
    world_indices: tuple[int, ...]
    outcome_one_probability: float
    exact_probability_ratio: str
    target_image_size: int
    probability_mass: float


@dataclass(frozen=True)
class ReplicationHorizon:
    repeats: int
    information_bits: float
    expected_remaining_entropy_bits: float
    reducible_remainder_bits: float
    complete_repair_in_declared_pool: bool
    max_remaining_target_image_size: int
    positive_outcome_count: int


@dataclass(frozen=True)
class ReplicationInformationAudit:
    candidate: str
    estimable: bool
    reason: str
    support_reference: str
    weight_reference: str
    conditional_iid_reference: str
    calibration_reference: str | None
    target_columns: tuple[str, ...]
    target_entropy_bits: float
    target_identified_in_declared_pool: bool
    irreducible_target_entropy_bits: float | None
    asymptotic_information_bits: float | None
    law_classes: tuple[ObservableLawClass, ...]
    same_law_different_target_pair: tuple[int, int] | None
    horizons: tuple[ReplicationHorizon, ...]
    feasible_domain_exhaustiveness: str = "not_certified"
    scope: str = "finite_declared_worlds_and_fixed_calibrated_bernoulli_law"


def _horizons(values: Sequence[int]) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("horizons must be a sequence of repeat counts")
    counts = tuple(values)
    if not counts or any(
        isinstance(n, bool) or not isinstance(n, Integral)
        or n < 0 or n > MAX_REPEATS for n in counts
    ):
        raise ValueError(f"horizons must be nonempty integers in [0, {MAX_REPEATS}]")
    if len(set(counts)) != len(counts):
        raise ValueError("horizons must be unique")
    return tuple(sorted(int(n) for n in counts))


def _binomial_row(binary_row: tuple[float, float], n: int) -> tuple[float, ...]:
    p0, p1 = binary_row
    if n == 0:
        return (1.0,)
    if p0 == 0.0:
        return (0.0,) * n + (1.0,)
    if p1 == 0.0:
        return (1.0,) + (0.0,) * n
    # Use both supplied positive entries: 1-p1 can round to zero even when p0
    # was explicitly positive. Never turn numerical underflow into exclusion.
    probabilities = tuple(
        exp(lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)
            + k * log(p1) + (n - k) * log(p0))
        for k in range(n + 1)
    )
    if any(p == 0.0 for p in probabilities):
        raise ValueError("binomial probability underflow; use a smaller horizon or log-domain audit")
    total = fsum(probabilities)
    normalized = tuple(p / total for p in probabilities)
    if any(p == 0.0 for p in normalized):
        raise ValueError("binomial normalization underflow; positive support must be preserved")
    return normalized


def replication_information_profile(
    accepted_rows: Sequence[Mapping], candidate: LikelihoodCandidate, *,
    target_columns: Sequence[str], weights: Sequence[float],
    support_reference: str, weight_reference: str,
    conditional_iid_reference: str,
    horizons: Sequence[int] = (0, 1, 2, 5, 10, 20),
) -> ReplicationInformationAudit:
    """Separate finite-sample uncertainty from the same-law residual floor.

    With C the per-world Bernoulli law, I(T; count_n) tends to I(T; C).
    H(T|C) is an irreducible target entropy for this fixed acquisition protocol,
    not for every possible observation. Equal-law/different-target pairs are
    structural witnesses only within the declared domain and calibrated laws.

    Outcome index 1 is counted. Counts suffice for iid binary sequences.
    Missing likelihoods return non-estimable; malformed inputs raise ValueError.
    Numerical zero information never supplies an impossibility certificate.
    """
    if not isinstance(conditional_iid_reference, str) or not conditional_iid_reference.strip():
        raise ValueError("conditional_iid_reference must declare the fixed-world replication assumption")
    if isinstance(target_columns, (str, bytes)):
        raise ValueError("target_columns must be a sequence, not a bare string")
    if isinstance(candidate.outcomes, (str, bytes)) or len(candidate.outcomes) != 2:
        raise ValueError("replication audit requires exactly two named outcomes")
    counts = _horizons(horizons)
    rows, columns, supplied_weights = tuple(accepted_rows), tuple(target_columns), tuple(weights)
    current = score_likelihood_candidates(
        rows, [candidate], target_columns=columns, weights=supplied_weights,
        support_reference=support_reference, weight_reference=weight_reference,
    )
    common = dict(
        candidate=candidate.name, support_reference=support_reference,
        weight_reference=weight_reference, conditional_iid_reference=conditional_iid_reference,
        calibration_reference=candidate.calibration_reference, target_columns=columns,
        target_entropy_bits=current.target_entropy_bits,
        target_identified_in_declared_pool=current.target_point_identified,
    )
    matrix = _matrix(candidate, len(rows))
    if matrix is None:
        return ReplicationInformationAudit(
            **common, estimable=False, reason="missing_per_world_predictive_likelihood",
            irreducible_target_entropy_bits=None, asymptotic_information_bits=None,
            law_classes=(), same_law_different_target_pair=None, horizons=(),
        )
    w = _weights(supplied_weights, len(rows))
    states = tuple(target_state(row, columns) for row in rows)
    groups: dict[Fraction, list[int]] = defaultdict(list)
    for index, (p0, p1) in enumerate(matrix):
        # Exact equality of the normalized *supplied* likelihood ratio. Close
        # estimated probabilities are not declared equal by an isclose rule.
        ratio = Fraction(p1) / (Fraction(p0) + Fraction(p1))
        groups[ratio].append(index)
    law_classes, floor_terms = [], []
    conflict = None
    for ratio, indices in groups.items():
        mass = fsum(w[i] for i in indices)
        target_values = tuple(dict.fromkeys(states[i] for i in indices))
        target_masses = [fsum(w[i] for i in indices if states[i] == t) for t in target_values]
        floor_terms.append(mass * _entropy(p / mass for p in target_masses))
        law_classes.append(ObservableLawClass(
            tuple(indices), float(ratio), str(ratio), len(target_values), mass,
        ))
        if conflict is None and len(target_values) > 1:
            first = indices[0]
            conflict = (first, next(i for i in indices if states[i] != states[first]))
    floor = fsum(floor_terms)
    ceiling = max(0.0, current.target_entropy_bits - floor)
    results = []
    for n in counts:
        count_matrix = tuple(_binomial_row(binary_row, n) for binary_row in matrix)
        count_candidate = LikelihoodCandidate(
            f"{candidate.name}__fresh_iid_count_{n}",
            tuple(f"count_{k}" for k in range(n + 1)), count_matrix,
            candidate.calibration_reference,
        )
        scored = score_likelihood_candidates(
            rows, [count_candidate], target_columns=columns, weights=supplied_weights,
            support_reference=support_reference, weight_reference=weight_reference,
        ).scores[0]
        residual_terms, remaining_sizes = [], []
        for k, outcome in enumerate(count_candidate.outcomes):
            if not any(row[k] > 0.0 for row in count_matrix):
                continue  # Impossible outcomes are not failed identification.
            posterior = condition_on_selected(
                rows, count_candidate, outcome, target_columns=columns, weights=supplied_weights,
            )
            residual_terms.append(posterior.outcome_probability * posterior.target_entropy_bits)
            remaining_sizes.append(posterior.remaining_target_image_size)
        residual = fsum(residual_terms)
        mi = scored.information_bits
        if mi is None or residual < floor - 1e-10 or mi > ceiling + 1e-10:
            raise ArithmeticError("replication information exceeded its observable-law ceiling")
        if abs((current.target_entropy_bits - residual) - mi) > 1e-10:
            raise ArithmeticError("count scoring and outcome conditioning disagree")
        results.append(ReplicationHorizon(
            n, mi, residual, max(0.0, residual - floor),
            all(size == 1 for size in remaining_sizes), max(remaining_sizes), len(remaining_sizes),
        ))
    if any(b.information_bits < a.information_bits - 1e-10 for a, b in zip(results, results[1:])):
        raise ArithmeticError("nested fresh iid observations lost expected target information")
    return ReplicationInformationAudit(
        **common, estimable=True,
        reason="conditional_on_declared_fixed_world_iid_model; calibration_not_verified_here",
        irreducible_target_entropy_bits=floor, asymptotic_information_bits=ceiling,
        law_classes=tuple(law_classes), same_law_different_target_pair=conflict,
        horizons=tuple(results),
    )
