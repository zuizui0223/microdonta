"""Finite-scenario sensitivity and minimax-regret target observation design.

Scenario weights and likelihoods are separate coherent declared models. They
are not averaged, nor assigned an invented meta-prior. Guarantees cover only
the enumerated scenarios, not their convex hull, an unknown continuous family,
or a globally optimal observation sequence. The publication core is unchanged.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from math import isfinite
from typing import Mapping, Sequence

from .empirical_observation_contract import LikelihoodCandidate, score_likelihood_candidates


@dataclass(frozen=True)
class CalibrationScenario:
    name: str
    weights: tuple[float, ...]
    candidates: tuple[LikelihoodCandidate, ...]
    calibration_reference: str


@dataclass(frozen=True)
class RobustCandidateScore:
    name: str
    information_by_scenario: dict[str, float | None]
    lower_information_bits: float | None
    upper_information_bits: float | None
    worst_regret_bits: float | None
    complete_across_scenarios: bool


@dataclass(frozen=True)
class RobustDesignReceipt:
    scenario_names: tuple[str, ...]
    scores: tuple[RobustCandidateScore, ...]
    pairwise_minimum_advantage_bits: dict[str, dict[str, float]]
    uniformly_best_names: tuple[str, ...]
    unique_uniform_winner: str | None
    minimax_regret_names: tuple[str, ...]
    minimum_worst_regret_bits: float | None
    complete_vocabulary: bool
    ranking_scope: str
    unresolved_candidate_names: tuple[str, ...]
    comparison_tolerance_bits: float
    scope: str = "enumerated_scenarios_equal_acquisition_cost_one_step_target_information"
    utility_units: str = "raw_target_information_bits"


def robust_likelihood_design(
    accepted_rows: Sequence[Mapping], scenarios: Sequence[CalibrationScenario], *,
    target_columns: Sequence[str], support_reference: str,
    comparison_tolerance_bits: float = 1e-12,
) -> RobustDesignReceipt:
    """Return uniform winners and an explicitly alternative minimax-regret choice.

    Dominance uses paired scenario differences min_s[I_s(Q)-I_s(R)], not
    min_s I_s(Q)-max_s I_s(R). The latter compares different worlds and can miss
    real dominance. Missing predictions cannot certify a full-vocabulary winner.
    Minimax regret is an explicit robust decision rule, not ordinary MI maximization.
    """
    tol = float(comparison_tolerance_bits)
    if not isfinite(tol) or tol < 0:
        raise ValueError("comparison tolerance must be finite and nonnegative")
    if isinstance(target_columns, (str, bytes)):
        raise ValueError("target_columns must be a sequence, not a bare string")
    rows, columns, models = tuple(accepted_rows), tuple(target_columns), tuple(scenarios)
    if not models:
        raise ValueError("declare at least one calibration scenario")
    if any(not isinstance(s.name, str) or not s.name.strip() for s in models):
        raise ValueError("scenario names must be non-empty strings")
    if len({s.name for s in models}) != len(models):
        raise ValueError("scenario names must be unique")
    names = tuple(c.name for c in models[0].candidates)
    if len(names) != len(set(names)):
        raise ValueError("candidate names must be unique")
    outcome_sets = {c.name: set(c.outcomes) for c in models[0].candidates}
    values = {name: {} for name in names}
    for scenario in models:
        if {c.name for c in scenario.candidates} != set(names):
            raise ValueError("every scenario must declare the same candidate vocabulary")
        if any(set(c.outcomes) != outcome_sets[c.name] for c in scenario.candidates):
            raise ValueError("each candidate must retain the same outcome vocabulary across scenarios")
        if not isinstance(scenario.calibration_reference, str) or not scenario.calibration_reference.strip():
            raise ValueError("each scenario needs a calibration/weight provenance reference")
        receipt = score_likelihood_candidates(
            rows, scenario.candidates, target_columns=columns, weights=scenario.weights,
            support_reference=support_reference, weight_reference=scenario.calibration_reference,
        )
        for score in receipt.scores:
            values[score.name][scenario.name] = score.information_bits
    model_names = tuple(s.name for s in models)
    known = tuple(name for name in names if all(values[name][s] is not None for s in model_names))
    unknown = tuple(name for name in names if name not in known)
    complete = bool(names) and not unknown
    differences = {
        q: {r: min(values[q][s]-values[r][s] for s in model_names)
            for r in known if r != q} for q in known
    }
    uniform = tuple(q for q in known if all(v >= -tol for v in differences[q].values()))
    strict = tuple(q for q in known if all(v > tol for v in differences[q].values()))
    worst_regret = {
        q: max(max(values[r][s] for r in known)-values[q][s] for s in model_names)
        for q in known
    }
    min_regret = min(worst_regret.values()) if known else None
    min_names = tuple(q for q in known if worst_regret[q] <= min_regret+tol) if known else ()
    scores = tuple(RobustCandidateScore(
        q, values[q], min(values[q].values()) if q in known else None,
        max(values[q].values()) if q in known else None,
        worst_regret.get(q), q in known,
    ) for q in names)
    # Partial-set pairwise results remain inspectable, but never emit an
    # authoritative winner or minimax regret against the incomplete vocabulary.
    return RobustDesignReceipt(
        model_names, scores, differences, uniform if complete else (),
        strict[0] if complete and len(strict) == 1 else None,
        min_names if complete else (), min_regret if complete else None,
        complete, "full_declared_finite_scenario_vocabulary" if complete else "provisional_common_estimable_subset",
        unknown, tol,
    )


def synthetic_example() -> dict:
    candidates = (
        LikelihoodCandidate("specialist_A", ("low", "high"), ((1, 0), (0.5, 0.5))),
        LikelihoodCandidate("specialist_B", ("low", "high"), ((0.5, 0.5), (0, 1))),
        LikelihoodCandidate("balanced", ("low", "high"), ((0.85, 0.15), (0.15, 0.85))),
    )
    scenarios = tuple(CalibrationScenario(name, weights, candidates, "synthetic prior sensitivity")
                      for name, weights in (("target_one_rare", (9, 1)), ("target_one_common", (1, 9))))
    receipt = robust_likelihood_design(
        [{"target": 0}, {"target": 1}], scenarios,
        target_columns=["target"], support_reference="synthetic identical two-world support",
    )
    return {"data_kind": "synthetic_finite_scenario", "receipt": asdict(receipt)}


if __name__ == "__main__":
    print(json.dumps(synthetic_example(), indent=2, allow_nan=False))
