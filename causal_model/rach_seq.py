"""RACH-SEQ: Sequential mechanism-equivalence reduction.

RACH-SEQ closes the loop left open by single-shot RACH. Starting from the
current admissible causal region ``A_epsilon``, it ranks candidate observations
by expected confounding-edge cuts, takes the best observation, conditions the
admissible region on the realised outcome, recomputes the mechanism-equivalence
structure, and repeats until either no confounding edge remains or the observation
budget is exhausted.

A key contract is that outcome probabilities are sequential. Whenever a
candidate's outcome filters form a mutually exclusive and exhaustive partition
of the *current* admissible region, RACH-SEQ estimates ``Pr(v | A_epsilon)``
directly from that region at the current step. Declared ``prior_probability``
values are used only as an explicit fallback when the available outcome maps do
not define such a partition (for example, because simulator columns are missing,
outcome bands overlap, or the listed outcomes are incomplete).

Under a deterministic simulator, filtering the stored admissible region is exact
for observation maps represented by these patterns. Under stochastic simulators,
this remains an approximation and requires the NOV calibration diagnostics.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from causal_model.mechanism_equivalence import (
    ConfoundingEdge,
    EquivalenceStructure,
    mechanism_equivalence_structure,
)
from causal_model.causal_admissibility import (
    CandidateObservation,
    causal_resolvability,
)


_PAIRWISE_TOL = 0.02
_GRADIENT_POPS = ("mainland", "Oshima", "Kozushima", "Hachijo")


# ---------------------------------------------------------------------------
# Row-level observation mapping
# ---------------------------------------------------------------------------

def _row_matches_pattern(row: dict, pattern: dict) -> bool:
    """Return whether one simulated row is consistent with one pattern.

    Unknown pattern types and missing columns return ``True`` conservatively:
    absent evidence must not silently exclude an admissible row. That conservative
    behaviour is also why predictive reweighting below is used only when the
    listed outcomes demonstrably partition the current admissible region.
    """
    ptype = pattern.get("type", "")
    var = pattern.get("variable", "")

    if ptype == "pairwise_relation":
        left = pattern.get("left_population", "")
        right = pattern.get("right_population", "")
        relation = pattern.get("relation", "")
        lv = row.get(f"{left}_{var}")
        rv = row.get(f"{right}_{var}")
        if lv is None or rv is None:
            return True
        lf, rf = float(lv), float(rv)
        if "<" in relation and "~" not in relation:
            return lf < rf - _PAIRWISE_TOL
        if ">" in relation and "~" not in relation:
            return lf > rf + _PAIRWISE_TOL
        if "~=" in relation or "≈" in relation:
            return abs(lf - rf) <= _PAIRWISE_TOL * 3
        return True

    if ptype in ("gradient_slope", "numeric_gradient"):
        direction = pattern.get("expected_direction", "")
        pops = [p for p in _GRADIENT_POPS if row.get(f"{p}_{var}") is not None]
        if len(pops) < 2:
            return True
        first = float(row[f"{pops[0]}_{var}"])
        last = float(row[f"{pops[-1]}_{var}"])
        if direction == "negative":
            return first >= last - _PAIRWISE_TOL
        if direction == "positive":
            return first <= last + _PAIRWISE_TOL
        return True

    if ptype == "rank_order":
        direction = pattern.get("expected_direction", "")
        pops = [p for p in _GRADIENT_POPS if row.get(f"{p}_{var}") is not None]
        if len(pops) < 2:
            return True
        vals = [float(row[f"{p}_{var}"]) for p in pops]
        if direction == "increasing":
            return all(vals[i] <= vals[i + 1] + _PAIRWISE_TOL for i in range(len(vals) - 1))
        if direction == "decreasing":
            return all(vals[i] >= vals[i + 1] - _PAIRWISE_TOL for i in range(len(vals) - 1))
        return True

    if ptype == "absolute_summary":
        pop = pattern.get("population", "")
        try:
            obs_val = float(pattern.get("observed_value", "nan"))
            scale = float(pattern.get("scale") or pattern.get("se") or 0.1)
        except (ValueError, TypeError):
            return True
        sim_val = row.get(f"{pop}_{var}")
        if sim_val is None:
            return True
        return abs(float(sim_val) - obs_val) <= scale * 2

    return True


def filter_by_outcome(
    accepted_rows: list[dict],
    extra_pattern_rows: list[dict],
) -> list[dict]:
    """Condition ``A_epsilon`` on all patterns describing one observed outcome."""
    result = accepted_rows
    for pattern in extra_pattern_rows:
        result = [row for row in result if _row_matches_pattern(row, pattern)]
    return result


# ---------------------------------------------------------------------------
# Sequential predictive outcome probabilities
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PredictiveOutcomeDistribution:
    """Outcome probabilities used at one RACH-SEQ step.

    ``source`` is ``current_admissible_region`` only when the outcome filters are
    mutually exclusive and exhaustive over the current rows. Otherwise it is
    ``declared_prior`` and the declared probabilities are normalised before use.
    """

    probabilities: dict[str, float]
    source: str
    partition_verified: bool


def predictive_outcome_distribution(
    candidate: CandidateObservation,
    accepted_rows: list[dict],
) -> PredictiveOutcomeDistribution:
    """Return ``Pr(v | current A_epsilon)`` when it is identifiable from rows.

    Outcome filters must form a true partition: each current row must match
    exactly one listed outcome. This guard prevents missing simulator columns,
    overlapping tolerance bands, or incomplete outcome vocabularies from being
    mistaken for an empirical predictive distribution.

    If the partition cannot be verified, declared ``prior_probability`` values
    are used as a transparent fallback and normalised to one.
    """
    outcomes = list(candidate.outcomes or [])
    if not outcomes:
        return PredictiveOutcomeDistribution({}, "no_outcomes", False)

    if accepted_rows:
        counts = {outcome.name: 0 for outcome in outcomes}
        memberships = [0] * len(accepted_rows)
        for outcome in outcomes:
            for idx, row in enumerate(accepted_rows):
                if all(
                    _row_matches_pattern(row, pattern)
                    for pattern in outcome.extra_pattern_rows
                ):
                    counts[outcome.name] += 1
                    memberships[idx] += 1
        if all(count == 1 for count in memberships):
            n = len(accepted_rows)
            return PredictiveOutcomeDistribution(
                probabilities={name: count / n for name, count in counts.items()},
                source="current_admissible_region",
                partition_verified=True,
            )

    declared = [float(outcome.prior_probability) for outcome in outcomes]
    if any(probability < 0 for probability in declared):
        raise ValueError(
            f"candidate {candidate.name!r} has a negative outcome prior probability"
        )
    total = sum(declared)
    if total <= 0:
        raise ValueError(
            f"candidate {candidate.name!r} must declare positive fallback outcome probability"
        )
    return PredictiveOutcomeDistribution(
        probabilities={
            outcome.name: probability / total
            for outcome, probability in zip(outcomes, declared)
        },
        source="declared_prior",
        partition_verified=False,
    )


# ---------------------------------------------------------------------------
# Candidate value
# ---------------------------------------------------------------------------

def expected_edge_cuts(
    candidate: CandidateObservation,
    accepted_rows: list[dict],
    switches,
    current_structure: EquivalenceStructure,
    *,
    min_sub_size: int = 5,
) -> float:
    """Expected number of confounding edges cut by one candidate observation.

    For explicit outcomes,

    ``E[cuts] = sum_v Pr(v | current A_epsilon) * max(0, |E|-|E_v|)``.

    The predictive distribution is recomputed from the current admissible region
    whenever the outcome maps define a verified partition. Declared priors are
    used only as the documented fallback. Candidates without outcome maps retain
    the older discounted target-overlap heuristic.
    """
    n_edges = len(current_structure.edges)
    if n_edges == 0:
        return 0.0

    if not candidate.outcomes:
        targets = set(candidate.target_switches)
        heuristic = sum(
            1
            for edge in current_structure.edges
            if edge.a in targets or edge.b in targets
        )
        return heuristic * 0.4

    distribution = predictive_outcome_distribution(candidate, accepted_rows)
    total = 0.0
    for outcome in candidate.outcomes:
        probability = distribution.probabilities.get(outcome.name, 0.0)
        if probability <= 0:
            continue
        sub = filter_by_outcome(accepted_rows, outcome.extra_pattern_rows)
        if len(sub) < min_sub_size:
            continue
        sub_structure = mechanism_equivalence_structure(sub, switches)
        cuts = max(0, n_edges - len(sub_structure.edges))
        total += probability * cuts
    return total


# ---------------------------------------------------------------------------
# Result objects
# ---------------------------------------------------------------------------

@dataclass
class SeqStep:
    """One iteration of RACH-SEQ."""

    step: int
    observation_taken: str | None
    outcome_observed: str | None
    n_accepted: int
    equivalence_structure: EquivalenceStructure
    edges_cut_this_step: int
    R: float
    candidate_ranking: list[tuple[str, float]]
    candidate_probability_sources: dict[str, str] = field(default_factory=dict)


@dataclass
class SeqResult:
    """Outcome of a full RACH-SEQ run."""

    initial_structure: EquivalenceStructure
    steps: list[SeqStep]
    final_structure: EquivalenceStructure
    converged: bool
    budget_exhausted: bool
    observations_taken: list[str]
    edges_resolved: list[ConfoundingEdge]
    edges_unresolved: list[ConfoundingEdge]

    def describe(self) -> str:
        lines = [
            f"RACH-SEQ ({len(self.steps)} step(s))",
            f"  converged={self.converged}  budget_exhausted={self.budget_exhausted}",
            f"  edges resolved={len(self.edges_resolved)}  unresolved={len(self.edges_unresolved)}",
        ]
        for step in self.steps:
            if step.step == 0:
                lines.append(
                    f"  [init]  {step.n_accepted} accepted rows  "
                    f"{len(step.equivalence_structure.edges)} confounding edge(s)  R={step.R:.3f}"
                )
            else:
                source = step.candidate_probability_sources.get(
                    step.observation_taken or "", "unknown"
                )
                lines.append(
                    f"  [step {step.step}]  took '{step.observation_taken}' "
                    f"-> outcome '{step.outcome_observed}'  "
                    f"cut {step.edges_cut_this_step} edge(s)  "
                    f"{len(step.equivalence_structure.edges)} remaining  "
                    f"R={step.R:.3f}  n={step.n_accepted}  p-source={source}"
                )
        if self.edges_unresolved:
            lines.append("  unresolved:")
            for edge in self.edges_unresolved:
                lines.append(f"    {edge.describe()}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Outcome materialisation
# ---------------------------------------------------------------------------

def _materialize_and_filter(
    candidate: CandidateObservation,
    accepted_rows: list[dict],
    rng: random.Random,
    *,
    outcome_override: str | None = None,
    min_sub_size: int = 5,
) -> tuple[str | None, list[dict]]:
    """Materialise one outcome and condition the current admissible region."""
    if not candidate.outcomes:
        return None, list(accepted_rows)

    if outcome_override is not None:
        matches = [o for o in candidate.outcomes if o.name == outcome_override]
        if not matches:
            raise ValueError(
                f"Outcome {outcome_override!r} not found in candidate {candidate.name!r}"
            )
        chosen = matches[0]
    else:
        distribution = predictive_outcome_distribution(candidate, accepted_rows)
        draw = rng.random()
        cumulative = 0.0
        chosen = candidate.outcomes[-1]
        for outcome in candidate.outcomes:
            cumulative += distribution.probabilities.get(outcome.name, 0.0)
            if draw <= cumulative:
                chosen = outcome
                break

    filtered = filter_by_outcome(accepted_rows, chosen.extra_pattern_rows)
    if len(filtered) < min_sub_size:
        return chosen.name, []
    return chosen.name, filtered


# ---------------------------------------------------------------------------
# Main algorithm
# ---------------------------------------------------------------------------

def rach_seq(
    accepted_rows: list[dict],
    switches,
    candidates: list[CandidateObservation],
    *,
    budget: int = 5,
    min_sub_size: int = 5,
    seed: int | None = None,
    outcome_overrides: dict[str, str] | None = None,
) -> SeqResult:
    """Sequentially reduce mechanism equivalence under an observation budget.

    At every step candidate values and, when sampling is needed, realised-outcome
    probabilities are computed against the *current* ``A_epsilon``. Explicit
    ``outcome_overrides`` represent externally observed results (or hidden truth
    in a controlled benchmark) and therefore bypass outcome sampling without
    affecting pre-observation candidate ranking.
    """
    rng = random.Random(seed)
    current_rows = list(accepted_rows)
    used: set[str] = set()
    observations_taken: list[str] = []
    steps: list[SeqStep] = []

    current_structure = mechanism_equivalence_structure(current_rows, switches)
    current_R = causal_resolvability(current_rows, switches)
    steps.append(SeqStep(
        step=0,
        observation_taken=None,
        outcome_observed=None,
        n_accepted=len(current_rows),
        equivalence_structure=current_structure,
        edges_cut_this_step=0,
        R=current_R,
        candidate_ranking=[],
        candidate_probability_sources={},
    ))

    budget_exhausted = False

    for step_num in range(1, budget + 1):
        if not current_structure.edges:
            break

        available = [candidate for candidate in candidates if candidate.name not in used]
        if not available:
            break

        ranking: list[tuple[str, float]] = []
        probability_sources: dict[str, str] = {}
        for candidate in available:
            if candidate.outcomes:
                probability_sources[candidate.name] = predictive_outcome_distribution(
                    candidate, current_rows
                ).source
            else:
                probability_sources[candidate.name] = "heuristic_no_outcomes"
            ranking.append((
                candidate.name,
                expected_edge_cuts(
                    candidate,
                    current_rows,
                    switches,
                    current_structure,
                    min_sub_size=min_sub_size,
                ),
            ))
        ranking.sort(key=lambda item: -item[1])

        best_name, best_value = ranking[0]
        if best_value <= 0:
            break

        best_candidate = next(c for c in available if c.name == best_name)
        override = (outcome_overrides or {}).get(best_name)
        outcome_name, filtered = _materialize_and_filter(
            best_candidate,
            current_rows,
            rng,
            outcome_override=override,
            min_sub_size=min_sub_size,
        )

        used.add(best_candidate.name)
        if not filtered:
            continue

        edges_before = len(current_structure.edges)
        current_rows = filtered
        current_structure = mechanism_equivalence_structure(current_rows, switches)
        current_R = causal_resolvability(current_rows, switches)
        observations_taken.append(best_candidate.name)

        steps.append(SeqStep(
            step=step_num,
            observation_taken=best_candidate.name,
            outcome_observed=outcome_name,
            n_accepted=len(current_rows),
            equivalence_structure=current_structure,
            edges_cut_this_step=max(0, edges_before - len(current_structure.edges)),
            R=current_R,
            candidate_ranking=ranking,
            candidate_probability_sources=probability_sources,
        ))

        if step_num == budget and current_structure.edges:
            budget_exhausted = True

    initial_structure = steps[0].equivalence_structure
    final_ids = {(edge.a, edge.b) for edge in current_structure.edges}
    edges_resolved = [
        edge
        for edge in initial_structure.edges
        if (edge.a, edge.b) not in final_ids
    ]

    return SeqResult(
        initial_structure=initial_structure,
        steps=steps,
        final_structure=current_structure,
        converged=not bool(current_structure.edges),
        budget_exhausted=budget_exhausted,
        observations_taken=observations_taken,
        edges_resolved=edges_resolved,
        edges_unresolved=list(current_structure.edges),
    )
