"""Joint observation-set optimizer for causal replaceability (RACH-SET).

Individual Replaceability-NOV ranking (``replaceability_nov``) scores each
candidate observation independently. When eliminations are *synergistic*
(Theorem C), every individual observation may have zero resolution value while
the right *combination* resolves the target mechanism. RACH-SET addresses this
by searching jointly within a budget.

Algorithm
---------
Budget-B brute-force: enumerate all subsets of candidates of size ≤ B, evaluate
each by the binary resolution indicator R_j, return the highest-scoring subset
(ties broken by smallest size, then lexicographic). This is exact and tractable
for |candidates| ≲ 15, B ≲ 5; for larger problems it provides an exact
benchmark to evaluate approximate/greedy approaches.

Greedy baseline
---------------
Also runs positive-marginal-gain-stopping greedy (the standard myopic heuristic:
repeatedly add the observation of largest marginal R_j gain; stop when no element
has positive gain or budget is exhausted). As proven in Theorem C, this greedy
fails in the canonical synergy regime — where all singletons have zero gain — and
its failure is quantified by the greedy/optimal ratio.

Submodularity status
--------------------
Reports whether R_j is submodular over the given candidate set (i.e., diminishing
returns hold). Synergy implies non-submodularity; this field distinguishes the
synergistic case ('violated'), the submodular case ('holds'), and the degenerate
case with fewer than two candidates ('trivial').

Outputs (RachSetResult)
-----------------------
  optimal_set          : tuple of candidate names achieving maximum R_j
  optimal_value        : R_j of the optimal set (0 or 1)
  greedy_set           : candidates chosen by positive-gain-stopping greedy
  greedy_value         : R_j of the greedy set
  greedy_optimal_ratio : greedy_value / optimal_value (nan if optimal_value = 0)
  synergy_warning      : True iff all singletons have zero gain but optimal > 0
  submodularity_status : 'violated' | 'holds' | 'trivial'
  n_evaluated          : number of candidate subsets evaluated
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import combinations

from causal_model.replaceability_theory import (
    StructuralModel,
    Observation,
    resolution_indicator,
    _add_nulls,
    submodularity_violated,
)


@dataclass
class RachSetResult:
    """Result of the RACH-SET joint observation-set search."""
    optimal_set: tuple[str, ...]
    optimal_value: int                   # 0 or 1 (R_j is binary)
    greedy_set: list[str]
    greedy_value: int
    greedy_optimal_ratio: float          # nan when optimal_value = 0
    synergy_warning: bool
    submodularity_status: str            # 'violated' | 'holds' | 'trivial'
    n_evaluated: int

    def describe(self) -> str:
        ratio = (f"{self.greedy_optimal_ratio:.3f}"
                 if not math.isnan(self.greedy_optimal_ratio)
                 else "nan")
        lines = [
            "RACH-SET joint observation-set result",
            f"  optimal set      : {list(self.optimal_set)}  (R_j = {self.optimal_value})",
            f"  greedy set       : {self.greedy_set}  (R_j = {self.greedy_value})",
            f"  greedy/optimal   : {ratio}",
            f"  synergy warning  : {self.synergy_warning}",
            f"  submodularity    : {self.submodularity_status}",
            f"  subsets evaluated: {self.n_evaluated}",
        ]
        return "\n".join(lines)


def rach_set(
    model: StructuralModel,
    baseline: Observation,
    candidate_nulls: list[str],
    j: int,
    budget: int,
) -> RachSetResult:
    """Brute-force joint observation-set optimizer within budget B.

    Searches all subsets of ``candidate_nulls`` of size ≤ ``budget`` for the
    one that maximises the resolution indicator R_j = 𝟙[CRC_j = ∞]. Also runs
    positive-marginal-gain-stopping greedy for comparison.

    Parameters
    ----------
    model:
        Structural causal model (K mechanisms, driver sets per trait).
    baseline:
        Starting observation (typically: focal trait PRESENT, no NULLs).
    candidate_nulls:
        Names of traits that can be observed NULL (the elimination candidates).
    j:
        Index of the target mechanism to resolve.
    budget:
        Maximum number of NULL observations to add (subset size ≤ budget).

    Returns
    -------
    RachSetResult
    """
    base_r = resolution_indicator(model, baseline, j)

    # --- Brute-force optimal ------------------------------------------------
    optimal_set: tuple[str, ...] = ()
    optimal_value = base_r
    n_evaluated = 0
    for r in range(1, budget + 1):
        for combo in combinations(candidate_nulls, r):
            val = resolution_indicator(model, _add_nulls(baseline, combo), j)
            n_evaluated += 1
            if val > optimal_value or (val == optimal_value and r < len(optimal_set)):
                optimal_value = val
                optimal_set = combo
            if optimal_value == 1:
                break
        if optimal_value == 1:
            break

    # --- Positive-marginal-gain-stopping greedy -----------------------------
    greedy_set: list[str] = []
    obs = baseline
    for _ in range(budget):
        cur = resolution_indicator(model, obs, j)
        best_gain, best = 0, None
        for c in candidate_nulls:
            if c in greedy_set:
                continue
            gain = resolution_indicator(model, _add_nulls(obs, [c]), j) - cur
            if gain > best_gain:
                best_gain, best = gain, c
        if best is None:
            break
        greedy_set.append(best)
        obs = _add_nulls(obs, [best])
        if resolution_indicator(model, obs, j) == 1:
            break
    greedy_value = resolution_indicator(model, obs, j)

    # --- Greedy / optimal ratio ---------------------------------------------
    if optimal_value == 0:
        greedy_optimal_ratio = float("nan")
    elif greedy_value == 0:
        greedy_optimal_ratio = 0.0
    else:
        greedy_optimal_ratio = greedy_value / optimal_value

    # --- Synergy warning: all singletons gain=0, but optimal>base -----------
    singleton_gains = [
        resolution_indicator(model, _add_nulls(baseline, [c]), j) - base_r
        for c in candidate_nulls
    ]
    all_singletons_zero = all(g == 0 for g in singleton_gains)
    synergy_warning = all_singletons_zero and optimal_value > base_r

    # --- Submodularity status -----------------------------------------------
    if len(candidate_nulls) < 2:
        sub_status = "trivial"
    elif submodularity_violated(model, baseline, candidate_nulls, j):
        sub_status = "violated"
    else:
        sub_status = "holds"

    return RachSetResult(
        optimal_set=optimal_set,
        optimal_value=optimal_value,
        greedy_set=greedy_set,
        greedy_value=greedy_value,
        greedy_optimal_ratio=greedy_optimal_ratio,
        synergy_warning=synergy_warning,
        submodularity_status=sub_status,
        n_evaluated=n_evaluated,
    )
