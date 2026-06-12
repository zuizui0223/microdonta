"""ABC-style distance and tolerance functions for RACH pattern filtering.

Formalises the pattern-distance rejection step that is central to the RACH
(Restricted Admissible Causal Hypotheses) workflow.

Distance definition
-------------------
We treat each ordinal pattern as a binary outcome: the simulated direction either
matches the observed target (match = 0) or does not (mismatch = 1). The canonical
RACH y_obs patterns are ordinal *gradient* directions along the island-isolation
axis (e.g. "selfing increases with isolation"); legacy pairwise endpoint forms
(e.g. "Oshima > Hachijo") are handled by the same matcher but are diagnostic_only.

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
strict_all      all patterns must match           epsilon = 0.000
relaxed_0.83    at least 83% of patterns match    epsilon = 1/N
relaxed_0.67    at least 67% of patterns match    epsilon = 2/N
weighted_strict all patterns with weight > 0      epsilon = 0.000
weighted_lax    weighted distance <= 0.20         epsilon = 0.200

Rule names are pattern-count-independent (no hardcoded "6_of_6").

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
    "strict_all":      0.0,
    "relaxed_0.83":    1.0 / 6.0,   # ≈ 1/N; exact epsilon computed dynamically
    "relaxed_0.67":    2.0 / 6.0,   # ≈ 2/N; exact epsilon computed dynamically
    "weighted_strict": 0.0,
    "weighted_lax":    0.20,
}


def epsilon_for_rule(rule: str, pattern_total: int = 6) -> float:
    """Return the epsilon threshold for a named acceptance rule.

    Parameters
    ----------
    rule:
        One of ``strict_all``, ``relaxed_0.83``, ``relaxed_0.67``,
        ``weighted_strict``, ``weighted_lax``.
    pattern_total:
        Used for proportion-based rules: ``relaxed_0.83`` = 1/pattern_total,
        ``relaxed_0.67`` = 2/pattern_total.

    Returns
    -------
    float
    """
    if rule == "strict_all":
        return 0.0
    if rule == "relaxed_0.83":
        return 1.0 / max(pattern_total, 1)
    if rule == "relaxed_0.67":
        return 2.0 / max(pattern_total, 1)
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
        "weighted_strict" if rule == "strict_all" else "weighted_lax",
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
