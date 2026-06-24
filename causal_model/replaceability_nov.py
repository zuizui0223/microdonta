"""Replaceability-aware NOV — expected gain in CRC upon observing a candidate.

Standard RACH NOV (from minimal_explanations.py) measures expected gain in
explanation-level resolvability R_expl.  Replaceability-NOV measures instead:

    NOV_CRC(q, j) = Σ_v  P(v | A_ε)  ·  [CRC_j(A_ε | v) − CRC_j(A_ε)]

For a candidate q with enumerated outcomes v_1 … v_m (each modelled as a
pattern filter on A_ε), this is the expected change in mechanism j's
replaceability cost — how much harder will it be to replace j after we
observe q?

Aggregate over all switches:
    NOV_CRC_total(q) = Σ_j  NOV_CRC(q, j)

A candidate that simultaneously raises CRC for the most-contested mechanism
(making it harder to replace) and lowers CRC for redundant mechanisms (making
them easier to drop) is the highest-value next observation.

Handling inf
------------
When ablating j after observing outcome v yields an empty sub-region
(CRC_j(A_ε | v) = ∞), the gain is capped at a large finite sentinel
``_INF_SENTINEL`` so that the expectation remains numerically meaningful.
The sentinel is set to log₂(|A_ε|) — the maximum resolvable information for
the given sample size.  A NOV_CRC ≈ log₂(|A_ε|) means "this observation
will almost certainly make j irreplaceable."
"""
from __future__ import annotations

import math

from causal_model.causal_replaceability import causal_replaceability_cost
from causal_model.external_constraints import Constraint
from causal_model.rach_seq import filter_by_outcome


def _finite_crc(crc: float, sentinel: float) -> float:
    if crc == float("inf"):
        return sentinel
    if crc != crc:  # nan
        return 0.0
    return crc


def replaceability_nov(
    candidate,
    switch_name: str,
    accepted_rows: list[dict],
    constraints: list[Constraint] | None = None,
    *,
    min_sub_size: int = 5,
) -> float:
    """NOV_CRC for a single switch j under a single candidate observation.

    Parameters
    ----------
    candidate:
        A ``CandidateObservation`` with ``.outcomes`` (each exposing
        ``.prior_probability`` and ``.extra_pattern_rows``).
    switch_name:
        The mechanism whose replaceability is being assessed.
    accepted_rows:
        Current admissible region A_ε.
    constraints:
        Optional external constraints for CRC penalty computation.
    min_sub_size:
        Minimum sub-region size for an outcome to contribute.

    Returns
    -------
    float
        Expected ΔCRC in bits.  Positive = observation makes j harder to
        replace (more causally load-bearing).  Negative = j becomes more
        redundant after the observation.
    """
    n = len(accepted_rows)
    if n == 0 or not candidate.outcomes:
        return float("nan")

    sentinel = math.log2(n) if n > 1 else 1.0
    crc_now = causal_replaceability_cost(switch_name, accepted_rows, constraints)
    crc_now_f = _finite_crc(crc_now, sentinel)

    evsi = 0.0
    for outcome in candidate.outcomes:
        sub = filter_by_outcome(accepted_rows, outcome.extra_pattern_rows)
        if len(sub) < min_sub_size:
            continue
        p = len(sub) / n
        crc_post = causal_replaceability_cost(switch_name, sub, constraints)
        crc_post_f = _finite_crc(crc_post, sentinel)
        evsi += p * (crc_post_f - crc_now_f)

    return round(evsi, 4)


def replaceability_nov_total(
    candidate,
    accepted_rows: list[dict],
    switches,
    constraints: list[Constraint] | None = None,
    *,
    min_sub_size: int = 5,
) -> float:
    """Aggregate NOV_CRC summed over all switches."""
    names = [sw.name for sw in switches]
    total = sum(
        replaceability_nov(candidate, name, accepted_rows, constraints,
                           min_sub_size=min_sub_size)
        for name in names
    )
    return round(total, 4)


def replaceability_nov_profile(
    candidate,
    accepted_rows: list[dict],
    switches,
    constraints: list[Constraint] | None = None,
    *,
    min_sub_size: int = 5,
) -> dict[str, float]:
    """Per-switch NOV_CRC profile for a candidate observation.

    Returns
    -------
    dict
        ``{switch_name: NOV_CRC_j}`` for every switch.
    """
    names = [sw.name for sw in switches]
    return {
        name: replaceability_nov(candidate, name, accepted_rows, constraints,
                                 min_sub_size=min_sub_size)
        for name in names
    }


def rank_candidates_by_replaceability_nov(
    candidates,
    accepted_rows: list[dict],
    switches,
    constraints: list[Constraint] | None = None,
    *,
    min_sub_size: int = 5,
) -> list[tuple[str, float]]:
    """Rank candidate observations by total NOV_CRC, highest first.

    Returns
    -------
    list of (candidate_name, NOV_CRC_total) sorted descending.
    """
    ranking = [
        (c.name, replaceability_nov_total(c, accepted_rows, switches, constraints,
                                          min_sub_size=min_sub_size))
        for c in candidates
    ]
    ranking.sort(key=lambda x: (x[1] if x[1] == x[1] else -1), reverse=True)
    return ranking
