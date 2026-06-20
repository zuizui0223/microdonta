"""RACH-SEQ: Sequential mechanism equivalence class reduction.

RACH-SEQ closes the open loop that plain RACH leaves: after computing the
mechanism equivalence structure (which confounding edges remain, which
mechanisms the data cannot tell apart), RACH-SEQ decides *which observation
to take next* to cut the most edges, takes it (by filtering the existing
admissible region — no re-inference), and iterates until the confounding
graph is empty (all mechanisms separated) or the budget is exhausted.

Algorithm
---------
    A_ε_0 ← initial admissible region
    structure_0 ← mechanism_equivalence_structure(A_ε_0, switches)

    for step in 1 .. budget:
        if structure has no confounding edges: STOP  (converged)
        for each candidate q not yet taken:
            edge_cuts(q) ← Σ_v  p(v)  ·  max(0, |current_edges| − |edges(A_ε | q=v)|)
        q* ← argmax edge_cuts
        if max edge_cuts == 0: STOP  (no candidate can help)
        v* ← sample outcome of q* (by prior_probability, or deterministic override)
        A_ε ← {r ∈ A_ε : outputs(r) consistent with q*=v*}   (cheap filter, no re-runs)
        structure ← mechanism_equivalence_structure(A_ε, switches)

    return SeqResult

The NOV reinterpretation
------------------------
Within RACH-SEQ, the value of observation q is *expected confounding-edge
cuts* rather than expected resolvability gain.  This is the mechanism-space
analogue: instead of a scalar gain in R, we count how many coupled-mechanism
pairs the observation would separate.  Edges are the inferential currency.

The filtering step is exact under the deterministic proxy simulator and
approximate under the stochastic ABM (as proved in nov_calibration.py).

Simulator-agnostic
------------------
This module consumes accepted_rows (anything with population-trait columns
``{pop}_{var}`` and boolean switch columns) and CandidateObservation objects.
It has no Campanula dependency.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Sequence

from causal_model.mechanism_equivalence import (
    ConfoundingEdge,
    EquivalenceStructure,
    mechanism_equivalence_structure,
)
from causal_model.causal_admissibility import (
    CandidateObservation,
    causal_resolvability,
)


# Minimum absolute difference to call a directional pairwise comparison.
_PAIRWISE_TOL = 0.02

# Isolation-gradient population order (mainland = most connected).
_GRADIENT_POPS = ("mainland", "Oshima", "Kozushima", "Hachijo")


# ---------------------------------------------------------------------------
# Row-level pattern matching (applies outcomes to the accepted region)
# ---------------------------------------------------------------------------

def _row_matches_pattern(row: dict, pattern: dict) -> bool:
    """True if the simulated row's population-trait outputs satisfy the pattern.

    Unknown pattern types and missing columns return True (conservative:
    do not exclude a row when evidence is absent).
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
        # Parse directional relation strings: "X < Y", "X > Y", "X ~= Y", etc.
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
        col = f"{pop}_{var}"
        sim_val = row.get(col)
        if sim_val is None:
            return True
        return abs(float(sim_val) - obs_val) <= scale * 2

    return True  # unknown type — include row


def filter_by_outcome(
    accepted_rows: list[dict],
    extra_pattern_rows: list[dict],
) -> list[dict]:
    """Filter accepted_rows to those consistent with all given pattern rows.

    This is the "cheap" A_ε update step of RACH-SEQ: no re-inference, just
    intersection of the existing admissible region with the new constraint.
    Exact under the deterministic proxy simulator (see nov_calibration.py).
    """
    result = accepted_rows
    for prow in extra_pattern_rows:
        result = [r for r in result if _row_matches_pattern(r, prow)]
    return result


# ---------------------------------------------------------------------------
# Edge-cut value of a candidate observation
# ---------------------------------------------------------------------------

def expected_edge_cuts(
    candidate: CandidateObservation,
    accepted_rows: list[dict],
    switches,
    current_structure: EquivalenceStructure,
    *,
    min_sub_size: int = 5,
) -> float:
    """Expected number of confounding edges cut by taking this observation.

    For candidates with defined outcomes:
        E[cuts] = Σ_v  p(v)  ·  max(0, |current_edges| − |edges(sub_v)|)

    For candidates without outcomes, a heuristic based on target-switch
    overlap with existing edges is returned (discounted to indicate uncertainty).

    Parameters
    ----------
    candidate:
        Candidate observation to evaluate.
    accepted_rows:
        Current admissible region A_ε.
    switches:
        Causal switches.
    current_structure:
        Pre-computed equivalence structure of the current A_ε.
    min_sub_size:
        Minimum sub-region size to trust.  Outcomes that filter A_ε to fewer
        than this many rows contribute 0 to the expectation.
    """
    n_edges = len(current_structure.edges)
    if n_edges == 0:
        return 0.0

    if not candidate.outcomes:
        # Heuristic: count edges where at least one endpoint is a target switch.
        target_set = set(candidate.target_switches)
        heuristic = sum(
            1 for e in current_structure.edges
            if e.a in target_set or e.b in target_set
        )
        return heuristic * 0.4   # discount for no explicit outcome model

    total = 0.0
    for outcome in candidate.outcomes:
        sub = filter_by_outcome(accepted_rows, outcome.extra_pattern_rows)
        if len(sub) < min_sub_size:
            continue
        sub_struct = mechanism_equivalence_structure(sub, switches)
        cuts = max(0, n_edges - len(sub_struct.edges))
        total += outcome.prior_probability * cuts
    return total


# ---------------------------------------------------------------------------
# Result data structures
# ---------------------------------------------------------------------------

@dataclass
class SeqStep:
    """One iteration of RACH-SEQ."""
    step: int
    observation_taken: str | None         # None at step 0 (initial)
    outcome_observed: str | None          # None at step 0
    n_accepted: int                       # |A_ε| after filtering
    equivalence_structure: EquivalenceStructure
    edges_cut_this_step: int              # edges removed in this step
    R: float                              # causal resolvability
    candidate_ranking: list[tuple[str, float]]  # (name, expected_edge_cuts)


@dataclass
class SeqResult:
    """Outcome of the full RACH-SEQ run."""
    initial_structure: EquivalenceStructure
    steps: list[SeqStep]
    final_structure: EquivalenceStructure
    converged: bool                       # no confounding edges remain
    budget_exhausted: bool                # budget ran out before convergence
    observations_taken: list[str]         # ordered sequence of candidates used
    edges_resolved: list[ConfoundingEdge] # edges cut during the run
    edges_unresolved: list[ConfoundingEdge]  # edges still remaining

    def describe(self) -> str:
        lines = [
            f"RACH-SEQ ({len(self.steps)} step(s))",
            f"  converged={self.converged}  budget_exhausted={self.budget_exhausted}",
            f"  edges resolved={len(self.edges_resolved)}  "
            f"unresolved={len(self.edges_unresolved)}",
        ]
        for step in self.steps:
            if step.step == 0:
                n_e = len(step.equivalence_structure.edges)
                lines.append(
                    f"  [init]  {step.n_accepted} accepted rows  "
                    f"{n_e} confounding edge(s)  R={step.R:.3f}"
                )
            else:
                lines.append(
                    f"  [step {step.step}]  took '{step.observation_taken}' "
                    f"→ outcome '{step.outcome_observed}'  "
                    f"cut {step.edges_cut_this_step} edge(s)  "
                    f"{len(step.equivalence_structure.edges)} remaining  "
                    f"R={step.R:.3f}  n={step.n_accepted}"
                )
        if self.edges_unresolved:
            lines.append("  unresolved:")
            for e in self.edges_unresolved:
                lines.append(f"    {e.describe()}")
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
    """Sample one outcome of a candidate and return the filtered sub-region.

    Returns
    -------
    (outcome_name, filtered_rows)
        outcome_name is None if the candidate has no outcomes.
        filtered_rows is empty if the sub-region is too small.
    """
    if not candidate.outcomes:
        return None, list(accepted_rows)   # no patterns to filter on

    if outcome_override is not None:
        pool = [o for o in candidate.outcomes if o.name == outcome_override]
        if not pool:
            raise ValueError(
                f"Outcome '{outcome_override}' not found in candidate '{candidate.name}'"
            )
        chosen = pool[0]
    else:
        # Sample by prior probability
        r = rng.random()
        cumulative = 0.0
        chosen = candidate.outcomes[-1]
        for outcome in candidate.outcomes:
            cumulative += outcome.prior_probability
            if r <= cumulative:
                chosen = outcome
                break

    filtered = filter_by_outcome(accepted_rows, chosen.extra_pattern_rows)
    if len(filtered) < min_sub_size:
        return chosen.name, []   # sub-region too small — signal failure
    return chosen.name, filtered


# ---------------------------------------------------------------------------
# Main RACH-SEQ function
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
    """Sequential mechanism equivalence class reduction algorithm.

    Iteratively selects the observation that maximally cuts confounding edges
    in the mechanism equivalence structure, updates the admissible region by
    filtering (no re-inference), and repeats.

    Parameters
    ----------
    accepted_rows:
        Initial admissible region A_ε.  Each row must expose population-trait
        columns ``{population}_{variable}`` (e.g. ``Hachijo_selfing_rate``) for
        the outcome filtering to work, plus boolean switch columns.
    switches:
        Causal switch objects (anything with a ``.name`` attribute).
    candidates:
        Candidate observations.  Those with defined ``outcomes`` get a full
        expected-edge-cut score; those without use a heuristic fallback.
    budget:
        Maximum number of observation steps.
    min_sub_size:
        Minimum post-filter sub-region size.  Outcomes filtering A_ε below
        this count are skipped (their contribution treated as 0).
    seed:
        RNG seed for outcome sampling.
    outcome_overrides:
        ``{candidate_name: outcome_name}`` — pin a specific outcome for a
        candidate instead of sampling.  Useful for deterministic tests or
        real-data updates where the researcher supplies the actual observation.

    Returns
    -------
    SeqResult
    """
    rng = random.Random(seed)
    current_rows = list(accepted_rows)
    used: set[str] = set()
    observations_taken: list[str] = []
    steps: list[SeqStep] = []

    # Step 0: initial structure
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
    ))

    budget_exhausted = False

    for step_num in range(1, budget + 1):
        if not current_structure.edges:
            break   # converged — no confounding edges remain

        available = [c for c in candidates if c.name not in used]
        if not available:
            break

        # Rank candidates by expected edge cuts
        ranking: list[tuple[str, float]] = []
        for cand in available:
            ec = expected_edge_cuts(
                cand, current_rows, switches, current_structure,
                min_sub_size=min_sub_size,
            )
            ranking.append((cand.name, ec))
        ranking.sort(key=lambda x: -x[1])

        best_name, best_value = ranking[0]
        if best_value <= 0:
            break   # no candidate can cut any edge

        best_cand = next(c for c in available if c.name == best_name)
        override = (outcome_overrides or {}).get(best_name)
        outcome_name, filtered = _materialize_and_filter(
            best_cand, current_rows, rng,
            outcome_override=override,
            min_sub_size=min_sub_size,
        )

        used.add(best_cand.name)
        if not filtered:
            # Outcome filtered too aggressively — skip without consuming a step
            continue

        edges_before = len(current_structure.edges)
        current_rows = filtered
        current_structure = mechanism_equivalence_structure(current_rows, switches)
        current_R = causal_resolvability(current_rows, switches)
        observations_taken.append(best_cand.name)

        steps.append(SeqStep(
            step=step_num,
            observation_taken=best_cand.name,
            outcome_observed=outcome_name,
            n_accepted=len(current_rows),
            equivalence_structure=current_structure,
            edges_cut_this_step=max(0, edges_before - len(current_structure.edges)),
            R=current_R,
            candidate_ranking=ranking,
        ))

        if step_num == budget and current_structure.edges:
            budget_exhausted = True

    # Classify edges resolved vs unresolved
    initial_structure = steps[0].equivalence_structure
    final_ids = {(e.a, e.b) for e in current_structure.edges}
    edges_resolved = [
        e for e in initial_structure.edges if (e.a, e.b) not in final_ids
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
