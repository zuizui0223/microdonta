"""ABC-style distance and tolerance functions for RACH pattern filtering.

Formalises the pattern-distance rejection step that is central to the RACH
(Restricted Admissible Causal Hypotheses) workflow.

Distance definition
-------------------
We treat each ordinal pattern comparison (e.g. "Oshima > Hachijo") as a
binary outcome: the simulated relation either matches the observed target
(match = 0) or does not (mismatch = 1).

Unweighted distance::

    pattern_distance = 1 - matches / total

Weighted distance::

    weighted_distance = sum(w_i * mismatch_i) / sum(w_i)

Acceptance rule
---------------
A run is admitted if::

    distance <= epsilon

where ``epsilon`` is derived from the acceptance rule.

Acceptance rules
----------------
strict_6_of_6   all 6 patterns must match        epsilon = 0.000
relaxed_5_of_6  at least 5 of 6 must match       epsilon = 1/6 ≈ 0.167
relaxed_4_of_6  at least 4 of 6 must match       epsilon = 2/6 ≈ 0.333
weighted_strict all patterns with weight > 0      epsilon = 0.000
weighted_lax    weighted distance <= 0.20         epsilon = 0.200

Research framing
----------------
The accepted-run criterion should be reported explicitly in any manuscript.
Pattern-distance filtering is a form of rejection ABC where the summary
statistic is the set of ordinal pattern relations and the distance measure
is the (optionally weighted) mismatch fraction.
"""

from __future__ import annotations

from typing import Mapping


# ---------------------------------------------------------------------------
# Core distance functions
# ---------------------------------------------------------------------------

def pattern_distance(pattern_matches: int, pattern_total: int) -> float:
    """Return ABC-style distance as fraction of unmatched patterns.

    Parameters
    ----------
    pattern_matches:
        Number of patterns where simulation matches observation.
    pattern_total:
        Total number of patterns being compared.

    Returns
    -------
    float
        0.0 (all match) to 1.0 (none match).
    """

    if pattern_total == 0:
        return 1.0
    return 1.0 - pattern_matches / pattern_total


def weighted_pattern_distance(
    pattern_match_results: Mapping[str, bool],
    weights: Mapping[str, float],
) -> float:
    """Return weighted ABC distance.

    Parameters
    ----------
    pattern_match_results:
        Mapping from pattern name to True (match) / False (mismatch).
    weights:
        Per-pattern weights. Patterns absent from this mapping receive
        weight 1.0.

    Returns
    -------
    float
        Weighted mismatch fraction in [0, 1].
    """

    total_weight = sum(float(weights.get(k, 1.0)) for k in pattern_match_results)
    if total_weight == 0:
        return 1.0
    weighted_mismatches = sum(
        float(weights.get(k, 1.0)) * (0.0 if v else 1.0)
        for k, v in pattern_match_results.items()
    )
    return weighted_mismatches / total_weight


# ---------------------------------------------------------------------------
# Epsilon (tolerance) for named acceptance rules
# ---------------------------------------------------------------------------

_NAMED_RULES: dict[str, float] = {
    "strict_6_of_6":   0.0,
    "relaxed_5_of_6":  1.0 / 6.0,
    "relaxed_4_of_6":  2.0 / 6.0,
    "weighted_strict": 0.0,
    "weighted_lax":    0.20,
}


def epsilon_for_rule(rule: str, pattern_total: int = 6) -> float:
    """Return the epsilon threshold for a named acceptance rule.

    Parameters
    ----------
    rule:
        One of ``strict_6_of_6``, ``relaxed_5_of_6``, ``relaxed_4_of_6``,
        ``weighted_strict``, ``weighted_lax``.
    pattern_total:
        Used for rules that depend on the number of patterns (e.g.
        ``relaxed_5_of_6`` = 1/pattern_total).

    Returns
    -------
    float
    """

    if rule in ("relaxed_5_of_6", "strict_6_of_6") and pattern_total != 6:
        # Generalise to any pattern count
        if rule == "strict_6_of_6":
            return 0.0
        return 1.0 / pattern_total
    return _NAMED_RULES.get(rule, 0.0)


def available_rules() -> list[str]:
    """Return the list of named acceptance rules."""
    return list(_NAMED_RULES.keys())


# ---------------------------------------------------------------------------
# Acceptance predicate
# ---------------------------------------------------------------------------

def accepted_by_epsilon(distance: float, epsilon: float) -> bool:
    """Return True if distance <= epsilon (run is admissible)."""
    return distance <= epsilon + 1e-9  # float tolerance


# ---------------------------------------------------------------------------
# Compute all distance metrics for one run
# ---------------------------------------------------------------------------

def compute_run_distances(
    observed_rels: Mapping[str, str],
    simulated_rels: Mapping[str, str],
    weights: Mapping[str, float],
    rule: str,
) -> dict[str, float | bool | str]:
    """Compute all ABC distance metrics for one simulation run.

    Parameters
    ----------
    observed_rels:
        Pattern name → observed relation string, e.g. ``"Oshima > Hachijo"``.
    simulated_rels:
        Pattern name → simulated relation string.
    weights:
        Pattern name → weight.
    rule:
        Acceptance rule name.

    Returns
    -------
    dict with keys:
        pattern_matches, pattern_total, pattern_distance,
        weighted_distance, epsilon, accepted_by_epsilon,
        weighted_accepted
    """

    total = len(observed_rels)
    match_results: dict[str, bool] = {
        k: (simulated_rels.get(k, "") == v)
        for k, v in observed_rels.items()
    }
    matches = sum(1 for v in match_results.values() if v)
    dist = pattern_distance(matches, total)
    w_dist = weighted_pattern_distance(match_results, weights)
    eps = epsilon_for_rule(rule, total)
    w_eps = epsilon_for_rule(
        "weighted_strict" if rule == "strict_6_of_6" else "weighted_lax",
        total,
    )

    return {
        "pattern_matches": matches,
        "pattern_total": total,
        "abc_distance": round(dist, 4),
        "weighted_abc_distance": round(w_dist, 4),
        "epsilon": round(eps, 4),
        "accepted_by_epsilon": accepted_by_epsilon(dist, eps),
        "weighted_accepted": accepted_by_epsilon(w_dist, w_eps),
        "acceptance_rule": rule,
    }
