"""RACH theory metrics: mechanism identifiability, causal degeneracy, pattern contribution.

Mathematical background
-----------------------
RACH defines the *admissible causal region* A_ε as the subset of the
parameter-mechanism space that satisfies biological constraints C and reproduces
observed gradient pattern targets within tolerance ε:

    A_ε = { (θ, s) ∈ Θ × {0,1}^K :
             θ satisfies constraint grammar C,
             d(simulate(θ, s), y_obs) ≤ ε }

From the ABC sample {(θ_i, s_i)} ⊂ A_ε, RACH computes three quantities:

Mechanism identifiability  I_j  (bits, per switch)
    How much does observing the accepted sample reduce our uncertainty about
    switch j?
        I_j = H(s_j prior) − H(s_j | A_ε)
            = 1 − H(p̂_j)               [prior is Bernoulli(0.5) → H(prior)=1]
    where H(p) = −p log₂p − (1−p) log₂(1−p) is binary entropy.
    I_j = 1 → switch j is fully identified (posterior is 0 or 1).
    I_j = 0 → switch j is unidentified (posterior equals prior).

Causal degeneracy  D = H(S | A_ε)  (bits)
    Joint entropy of the switch vector over the accepted sample.
    D = 0 → single mechanism combination explains all accepted samples.
    D = K → all 2^K combinations are equally represented (maximum degeneracy).
    The *degeneracy reduction* R = K − D measures how much A_ε constrains the
    mechanism space relative to the uninformative K-bit prior.

Pattern contribution  C_k(j)  (bits, per pattern × per switch)
    How much does pattern k contribute to the identifiability of switch j?
    Estimated by leave-one-out (LOO) from the stored per-pattern match data:
        C_k(j) = I_j(all patterns) − I_j(patterns excluding k)
    where I_j(subset) is recomputed on the sub-sample of accepted rows that
    would still pass the acceptance criterion if pattern k were removed.

Public API
----------
compute_rach_theory_metrics(accepted_rows, switches)
    → RACHTheoryMetrics  (identifiability + degeneracy)

pattern_contribution_table(accepted_rows, switches, threshold)
    → list[dict]  one row per (pattern, switch) with C_k(j) in bits

identifiability_summary(accepted_rows, switches)
    → list[dict]  one row per switch
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Sequence


# ---------------------------------------------------------------------------
# Small math helpers
# ---------------------------------------------------------------------------

def _binary_entropy(p: float) -> float:
    """Binary entropy H(p) in bits.  Returns 0 for p=0 or p=1."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def _switch_identifiability(p_posterior: float, p_prior: float = 0.5) -> float:
    """I_j = H(prior) - H(posterior) in bits."""
    return _binary_entropy(p_prior) - _binary_entropy(p_posterior)


def _joint_entropy(switch_vectors: list[tuple]) -> float:
    """Empirical joint entropy of a list of binary vectors, in bits."""
    if not switch_vectors:
        return 0.0
    counts = Counter(switch_vectors)
    n = len(switch_vectors)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SwitchIdentifiability:
    """Identifiability of one biological switch."""

    switch_name: str
    p_prior: float
    p_posterior: float
    H_prior: float       # binary entropy of prior (bits)
    H_posterior: float   # binary entropy of posterior (bits)
    I_j: float           # identifiability = H_prior - H_posterior (bits)
    n_ON: int
    n_accepted: int

    @property
    def interpretation(self) -> str:
        if self.n_accepted == 0:
            return "no accepted samples"
        if self.I_j >= 0.75:
            return "highly identifiable"
        if self.I_j >= 0.40:
            return "moderately identifiable"
        if self.I_j >= 0.10:
            return "weakly identifiable"
        return "not identifiable"


@dataclass
class RACHTheoryMetrics:
    """RACH theory metrics for one inference run.

    Attributes
    ----------
    identifiability:
        Per-switch identifiability I_j.
    causal_degeneracy:
        H(S | A_ε) in bits — joint entropy of switch vectors in accepted sample.
    max_degeneracy:
        K bits (uninformative prior over K switches).
    degeneracy_reduction:
        K − H(S | A_ε) — bits of mechanism information gained by A_ε.
    total_identifiability:
        Sum of I_j over all switches (total bits identified).
    n_accepted:
        Number of accepted samples in A_ε.
    n_switches:
        K (number of switches).
    """

    identifiability: list[SwitchIdentifiability]
    causal_degeneracy: float
    max_degeneracy: float
    degeneracy_reduction: float
    total_identifiability: float
    n_accepted: int
    n_switches: int

    def summary_dict(self) -> dict:
        return {
            "n_accepted":             self.n_accepted,
            "n_switches":             self.n_switches,
            "causal_degeneracy_bits": round(self.causal_degeneracy, 4),
            "max_degeneracy_bits":    round(self.max_degeneracy, 4),
            "degeneracy_reduction":   round(self.degeneracy_reduction, 4),
            "total_identifiability":  round(self.total_identifiability, 4),
        }


# ---------------------------------------------------------------------------
# Main computation functions
# ---------------------------------------------------------------------------

def compute_rach_theory_metrics(
    accepted_rows: list[dict],
    switches,   # Sequence[BiologicalSwitch]
) -> RACHTheoryMetrics:
    """Compute identifiability and causal degeneracy from accepted ABC sample.

    Parameters
    ----------
    accepted_rows:
        Accepted sample rows from ``run_switch_posterior_inference()``.
        Each row must contain boolean columns named by switch.name.
    switches:
        Sequence of BiologicalSwitch definitions (e.g. CAMPANULA_SWITCHES).

    Returns
    -------
    RACHTheoryMetrics
    """
    n = len(accepted_rows)
    K = len(switches)

    # Per-switch identifiability
    identifiability: list[SwitchIdentifiability] = []
    for sw in switches:
        n_on = sum(1 for r in accepted_rows if r.get(sw.name))
        p_post = n_on / n if n > 0 else sw.prior_on_prob
        h_prior = _binary_entropy(sw.prior_on_prob)
        h_post  = _binary_entropy(p_post)
        I_j = max(0.0, h_prior - h_post)
        identifiability.append(SwitchIdentifiability(
            switch_name=sw.name,
            p_prior=sw.prior_on_prob,
            p_posterior=round(p_post, 4),
            H_prior=round(h_prior, 4),
            H_posterior=round(h_post, 4),
            I_j=round(I_j, 4),
            n_ON=n_on,
            n_accepted=n,
        ))

    # Causal degeneracy: joint entropy of switch vectors in accepted sample
    switch_names = [sw.name for sw in switches]
    if n > 0:
        vectors = [
            tuple(bool(r.get(name)) for name in switch_names)
            for r in accepted_rows
        ]
        degeneracy = _joint_entropy(vectors)
    else:
        degeneracy = float(K)   # maximum uncertainty if no accepted samples

    max_deg = float(K)  # K bits = uninformative prior over K switches
    reduction = max(0.0, max_deg - degeneracy)
    total_I = sum(s.I_j for s in identifiability)

    return RACHTheoryMetrics(
        identifiability=identifiability,
        causal_degeneracy=round(degeneracy, 4),
        max_degeneracy=round(max_deg, 4),
        degeneracy_reduction=round(reduction, 4),
        total_identifiability=round(total_I, 4),
        n_accepted=n,
        n_switches=K,
    )


def identifiability_summary(
    accepted_rows: list[dict],
    switches,   # Sequence[BiologicalSwitch]
) -> list[dict]:
    """Return one dict per switch with identifiability metrics.

    Convenience wrapper around compute_rach_theory_metrics() for display.
    """
    metrics = compute_rach_theory_metrics(accepted_rows, switches)
    return [
        {
            "switch":          s.switch_name,
            "P_prior_ON":      s.p_prior,
            "P_posterior_ON":  s.p_posterior,
            "H_posterior":     s.H_posterior,
            "I_j (bits)":      s.I_j,
            "n_ON":            s.n_ON,
            "n_accepted":      s.n_accepted,
            "interpretation":  s.interpretation,
        }
        for s in metrics.identifiability
    ]


def pattern_contribution_table(
    accepted_rows: list[dict],
    switches,        # Sequence[BiologicalSwitch]
    threshold: float = 1.0,
) -> list[dict]:
    """Estimate pattern contribution C_k(j) via leave-one-out.

    For each pattern k, the function estimates what the identifiability
    I_j would be if pattern k were excluded from the acceptance criterion.
    It does this by constructing the hypothetical accepted subset:
    rows that would still pass even if pattern k did not contribute to
    the weighted_match_rate.

    C_k(j) = I_j(all) − I_j(LOO-k)

    Positive C_k(j) → pattern k increases identifiability of switch j.
    Negative C_k(j) → removing pattern k would INCREASE identifiability
                      (pattern k is confounding).

    Requires ``per_pattern_matched`` field in accepted_rows (dict of
    {pattern_name: (matched, weight)}).  Rows without this field are skipped.

    Parameters
    ----------
    accepted_rows:
        Accepted sample rows from switch_inference (must include
        ``per_pattern_matched`` and ``weighted_match_rate``).
    switches:
        Sequence of BiologicalSwitch definitions.
    threshold:
        ABC acceptance threshold (weighted_match_rate >= threshold).
        Used to determine which rows would remain accepted after LOO.

    Returns
    -------
    list of dict
        One row per (pattern, switch): keys are
        ``pattern``, ``switch``, ``C_k_j``, ``I_j_all``, ``I_j_loo``.
    """
    # Filter rows that have per_pattern_matched data
    rows_with_data = [r for r in accepted_rows if isinstance(r.get("per_pattern_matched"), dict)]
    if not rows_with_data:
        return []

    # Full-set identifiability (on the rows-with-data subset)
    metrics_all = compute_rach_theory_metrics(rows_with_data, switches)
    I_all = {s.switch_name: s.I_j for s in metrics_all.identifiability}

    # Collect all pattern names
    all_patterns: set[str] = set()
    for r in rows_with_data:
        all_patterns.update(r["per_pattern_matched"].keys())

    results: list[dict] = []
    for pattern_k in sorted(all_patterns):
        # For each accepted row, compute what the weighted_match_rate would be
        # if pattern k were dropped (its matched/weight contribution removed).
        loo_accepted: list[dict] = []
        for r in rows_with_data:
            ppm = r["per_pattern_matched"]
            entry = ppm.get(pattern_k)
            if entry is None:
                # pattern k not evaluated for this row — keep it
                loo_accepted.append(r)
                continue
            matched_k, weight_k = entry
            # Recompute weighted_match_rate without pattern k
            cur_wmr = r.get("weighted_match_rate", 0.0)
            total_w = sum(w for _, w in ppm.values())
            matched_w = sum(w for m, w in ppm.values() if m)
            new_total = total_w - weight_k
            new_matched = matched_w - (weight_k if matched_k else 0.0)
            if new_total <= 0:
                loo_wmr = 1.0  # no patterns remaining → trivially pass
            else:
                loo_wmr = new_matched / new_total
            if loo_wmr >= threshold:
                loo_accepted.append(r)

        if not loo_accepted:
            metrics_loo = None
            I_loo = {sw.name: 0.0 for sw in switches}
        else:
            metrics_loo = compute_rach_theory_metrics(loo_accepted, switches)
            I_loo = {s.switch_name: s.I_j for s in metrics_loo.identifiability}

        for sw in switches:
            i_full = I_all.get(sw.name, 0.0)
            i_loo  = I_loo.get(sw.name, 0.0)
            results.append({
                "pattern":   pattern_k,
                "switch":    sw.name,
                "I_j_all":   round(i_full, 4),
                "I_j_loo":   round(i_loo, 4),
                "C_k_j":     round(i_full - i_loo, 4),   # positive = k helps identify j
                "n_loo":     len(loo_accepted),
                "n_all":     len(rows_with_data),
            })

    return results


def constraint_posterior_shift(
    accepted_rows: list[dict],
    unconstrained_rows: list[dict],
    switches,   # Sequence[BiologicalSwitch]
) -> list[dict]:
    """Quantify how much the constraint grammar shifts the posterior.

    Compares the switch posterior from the constrained accepted sample (A_ε)
    to the posterior from an unconstrained accepted sample (no C1-C4 rejection).

    Parameters
    ----------
    accepted_rows:
        Accepted rows from the constrained inference (C1-C4 applied).
    unconstrained_rows:
        Accepted rows from the unconstrained inference (no ecological constraints).
    switches:
        Switch definitions.

    Returns
    -------
    list of dict
        One row per switch with ``delta_P_ON`` = constrained − unconstrained.
    """
    n_c = len(accepted_rows)
    n_u = len(unconstrained_rows)

    results = []
    for sw in switches:
        p_c = (sum(1 for r in accepted_rows      if r.get(sw.name)) / n_c
               if n_c > 0 else float("nan"))
        p_u = (sum(1 for r in unconstrained_rows if r.get(sw.name)) / n_u
               if n_u > 0 else float("nan"))
        delta = (p_c - p_u) if (p_c == p_c and p_u == p_u) else float("nan")
        results.append({
            "switch":           sw.name,
            "P_constrained":    round(p_c, 4) if p_c == p_c else None,
            "P_unconstrained":  round(p_u, 4) if p_u == p_u else None,
            "delta_P_ON":       round(delta, 4) if delta == delta else None,
        })
    return results
