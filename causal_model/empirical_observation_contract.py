"""Optional noisy-likelihood target design; not a replacement for core MROD.

The caller declares a finite admissible ensemble, strictly positive weights,
target encoding, and per-world predictive likelihoods. References are provenance
metadata, not independently verified empirical calibration certificates. Missing
predictions remain non-estimable. Small entropy never licenses point identification.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import json
from math import fsum, isfinite, log2
from numbers import Number, Rational
from typing import Mapping, Sequence


def target_state(row: Mapping, columns: Sequence[str]) -> tuple:
    """Reject absent/null/nonfinite target values instead of creating a null class."""
    if isinstance(columns, (str, bytes)):
        raise ValueError("target_columns must be a sequence, not a bare string")
    names=tuple(columns)
    if not names or any(not isinstance(c,str) or not c.strip() for c in names):
        raise ValueError("target_columns must contain non-empty column names")
    if len(set(names)) != len(names):
        raise ValueError("target_columns must be unique")
    def check(value):
        if value is None:
            raise ValueError("target values must not be missing or null")
        if isinstance(value,Number) and not isinstance(value,Rational):
            try:
                finite=isfinite(value)
            except (TypeError,ValueError,OverflowError) as exc:
                raise ValueError("numeric target values must be finite real numbers") from exc
            if not finite:
                raise ValueError("numeric target values must be finite")
        if isinstance(value,(tuple,frozenset)):
            for component in value:
                check(component)
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("target values must be hashable") from exc
        try:
            reflexive = bool(value == value)
        except (TypeError, ValueError) as exc:
            raise ValueError("target contains a missing/invalid label") from exc
        if not reflexive:
            raise ValueError("target contains a missing/invalid label")
    values=[]
    for column in names:
        if column not in row:
            raise ValueError(f"missing target column: {column}")
        value=row[column]
        check(value)
        values.append(value)
    return tuple(values)


def _weights(weights: Sequence[float], n: int) -> tuple[float,...]:
    values=tuple(float(v) for v in weights)
    if len(values)!=n or n==0 or any(not isfinite(v) or v<=0 for v in values):
        raise ValueError("one finite strictly positive weight is required per admissible row")
    scale=max(values)
    scaled=tuple(v/scale for v in values)
    total=fsum(scaled)
    normalized=tuple(v/total for v in scaled)
    if any(v==0 for v in normalized):
        raise ValueError("weights underflow; do not silently drop admissible worlds")
    return normalized


def _entropy(masses) -> float:
    return -fsum(p*log2(p) for p in masses if p>0)


@dataclass(frozen=True)
class LikelihoodCandidate:
    name: str
    outcomes: tuple[str,...]
    probabilities: tuple[tuple[float,...],...] | None
    calibration_reference: str | None = None


@dataclass(frozen=True)
class LikelihoodScore:
    name: str
    estimable: bool
    information_bits: float | None
    normalized_target_value: float | None
    reason: str
    calibration_reference: str | None


@dataclass(frozen=True)
class DesignReceipt:
    support_reference: str
    weight_reference: str
    target_columns: tuple[str,...]
    target_image_size: int
    target_entropy_bits: float
    target_point_identified: bool
    scores: tuple[LikelihoodScore,...]
    best_estimable_names: tuple[str,...]
    complete_vocabulary: bool
    ranking_scope: str


@dataclass(frozen=True)
class PosteriorReceipt:
    selected_candidate: str
    realised_outcome: str
    outcome_probability: float
    posterior_weights: tuple[float,...]
    remaining_target_image_size: int
    target_point_identified: bool
    target_entropy_bits: float


def _matrix(candidate: LikelihoodCandidate, n: int):
    if not isinstance(candidate.name,str) or not candidate.name.strip():
        raise ValueError("candidate needs a non-empty name")
    names=tuple(candidate.outcomes)
    if (not names or len(set(names))!=len(names)
            or any(not isinstance(q,str) or not q.strip() for q in names)):
        raise ValueError("outcome names must be non-empty and unique")
    if candidate.probabilities is None:
        return None
    matrix=tuple(tuple(float(x) for x in row) for row in candidate.probabilities)
    if len(matrix)!=n or any(len(row)!=len(names) for row in matrix):
        raise ValueError("likelihood matrix must cover every world and outcome")
    for row in matrix:
        if any(not isfinite(x) or x<0 or x>1 for x in row) or abs(fsum(row)-1)>1e-12:
            raise ValueError("each likelihood row must be a finite probability distribution")
    return tuple(tuple(x/fsum(row) for x in row) for row in matrix)


def _joint(states, weights, matrix):
    contributions=defaultdict(list)
    for state,weight,row in zip(states,weights,matrix):
        for q,likelihood in enumerate(row):
            mass=weight*likelihood
            if weight>0 and likelihood>0 and mass==0:
                raise ValueError("joint probability underflow; rescale before inference")
            contributions[state,q].append(mass)
    return {key:fsum(values) for key,values in contributions.items()}


def score_likelihood_candidates(
    accepted_rows: Sequence[Mapping], candidates: Sequence[LikelihoodCandidate], *,
    target_columns: Sequence[str], weights: Sequence[float],
    support_reference: str, weight_reference: str,
) -> DesignReceipt:
    """Compute one-step I(T;Q) for declared noisy predictive models.

    All weights and outcome probabilities are supplied, not learned here. A
    candidate with no matrix is non-estimable, not zero-information. A best
    singleton is not a globally best sequence: no independence or joint model
    across different candidates is inferred from these marginal matrices.
    """
    if (not isinstance(support_reference,str) or not support_reference.strip()
            or not isinstance(weight_reference,str) or not weight_reference.strip()):
        raise ValueError("support and weight provenance must be declared")
    columns=tuple(target_columns)
    states=tuple(target_state(row,columns) for row in accepted_rows)
    w=_weights(weights,len(states))
    vocabulary=tuple(candidates)
    if len({c.name for c in vocabulary})!=len(vocabulary):
        raise ValueError("candidate names must be unique")
    target_mass={t:fsum(p for s,p in zip(states,w) if s==t) for t in set(states)}
    entropy=_entropy(target_mass.values())
    scores=[]
    for candidate in vocabulary:
        matrix=_matrix(candidate,len(states))
        if matrix is None:
            scores.append(LikelihoodScore(candidate.name,False,None,None,
                                          "missing_per_world_predictive_likelihood",candidate.calibration_reference))
            continue
        joint=_joint(states,w,matrix)
        expected=0.0
        for q in range(len(candidate.outcomes)):
            masses=[joint[t,q] for t in target_mass]
            probability=fsum(masses)
            if probability>0:
                expected+=probability*_entropy(m/probability for m in masses)
        mi=entropy-expected
        if mi < -1e-10 or mi > entropy+1e-10:
            raise ArithmeticError("information calculation left its probability bounds")
        mi=max(0.0,min(entropy,mi))
        normalized=0.0 if len(target_mass)==1 else (mi/entropy if entropy>0 else None)
        scores.append(LikelihoodScore(candidate.name,True,mi,normalized,
                                      "conditional_on_declared_likelihood; calibration_not_verified_here",
                                      candidate.calibration_reference))
    estimable=[s for s in scores if s.estimable]
    best=max((s.information_bits for s in estimable),default=None)
    best_names=tuple(s.name for s in estimable if best is not None
                     and abs(s.information_bits-best)<=1e-12)
    complete=bool(vocabulary) and len(estimable)==len(vocabulary)
    scope="full_declared_singleton_vocabulary" if complete else "provisional_estimable_subset"
    return DesignReceipt(support_reference,weight_reference,columns,len(target_mass),entropy,
                         len(target_mass)==1,tuple(scores),best_names,complete,scope)


def condition_on_selected(
    accepted_rows: Sequence[Mapping], selected: LikelihoodCandidate, realised_outcome: str, *,
    target_columns: Sequence[str], weights: Sequence[float],
) -> PosteriorReceipt:
    """Condition only the selected observation; preserve every positive-likelihood target."""
    states=tuple(target_state(row,target_columns) for row in accepted_rows)
    w=_weights(weights,len(states))
    matrix=_matrix(selected,len(states))
    if matrix is None:
        raise ValueError("selected candidate has no predictive likelihood")
    if realised_outcome not in selected.outcomes:
        raise ValueError("unknown realised outcome")
    q=selected.outcomes.index(realised_outcome)
    _joint(states,w,matrix)  # includes underflow audit
    unnormalized=tuple(weight*row[q] for weight,row in zip(w,matrix))
    probability=fsum(unnormalized)
    if probability<=0:
        raise ValueError("realised outcome incompatible with every admissible world")
    posterior=tuple(p/probability for p in unnormalized)
    remaining={state for state,row in zip(states,matrix) if row[q]>0}
    masses=[fsum(p for s,p in zip(states,posterior) if s==t) for t in remaining]
    return PosteriorReceipt(selected.name,realised_outcome,probability,posterior,
                            len(remaining),len(remaining)==1,_entropy(masses))


def synthetic_example() -> dict:
    rows=[{"target":0},{"target":1}]
    candidate=LikelihoodCandidate("noisy_target",("low","high"),((0.9,0.1),(0.1,0.9)),
                                  "synthetic symmetric error=0.1")
    receipt=score_likelihood_candidates(rows,[candidate],target_columns=["target"],weights=[1,1],
                                        support_reference="synthetic two worlds",weight_reference="uniform by design")
    posterior=condition_on_selected(rows,candidate,"high",target_columns=["target"],weights=[1,1])
    return {"data_kind":"synthetic_noisy_likelihood_witness", "design":asdict(receipt),
            "posterior":asdict(posterior)}


if __name__ == "__main__":
    print(json.dumps(synthetic_example(),indent=2,allow_nan=False))
