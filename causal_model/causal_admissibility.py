"""RACH: Causal Admissibility and Degeneracy Framework.

This module implements the five core RACH quantities:

    CA_j   Causal admissibility    P(s_j = 1 | A_ε)
    D      Causal degeneracy       H(S | A_ε)
    R      Causal resolvability    1 - H(S | A_ε) / H(S)
    OC_k   Observation contribution  R(O) - R(O \\ {k})
    NOV(q) Next-observation value  E[ R(O ∪ q) - R(O) ]

RACH is NOT a model-comparison or ABC framework.
Its primary inferential objects are causal admissibility and causal degeneracy.
ABC / simulation / POM are computational components used to approximate A_ε,
but they are not the framework itself.

Formal RACH object
------------------
RACH = (X, Y, Θ, S, G, f, P_sim, P_obs, d, ε, A_ε, CA, D, R, OC, NOV)

    X       fixed ecological context space (island distance, Bombus frequency, ...)
    Y       independent observation space  (guide, selfing, herkogamy, Fis, ...)
    Θ       latent ecological parameter space
    S       causal switch space {0,1}^K
    G       biological constraint grammar  (G(θ) = 1 iff θ is feasible)
    f       generative ecological dynamics (axioms: W-F drift, selection, inheritance)
    P_sim   simulated output → pattern-space map
    P_obs   empirical observation → pattern-space map
    d       distance between P_sim and P_obs outputs
    ε       admissibility tolerance
    A_ε     admissible causal region (see below)
    CA      causal admissibility function
    D       causal degeneracy measure
    R       causal resolvability measure
    OC      observation contribution function
    NOV     next-observation value function

Admissible causal region
------------------------
    A_ε(y_obs, x_obs) = { (θ, s) ∈ Θ × S :
                           G(θ) = 1,
                           d(P_sim(f(x_obs; θ, s)), P_obs(y_obs)) ≤ ε }

Public API
----------
    causal_admissibility(accepted_rows, switches)
        → list[CausalAdmissibilityResult]  one per switch

    causal_degeneracy(accepted_rows, switches)
        → float  H(S | A_ε) in bits

    causal_resolvability(accepted_rows, switches)
        → float  R ∈ [0, 1]

    observation_contribution(accepted_rows, switches, threshold)
        → list[ObservationContribution]  one per (pattern, switch)

    next_observation_value(accepted_rows, switches, candidates)
        → list[NextObservationValueResult]  one per candidate

    rach_summary(accepted_rows, switches)
        → RACHSummary  all five quantities in one object

Relationship to identifiability.py
-----------------------------------
identifiability.py contains the low-level entropy computations (I_j, H(S|A_ε)).
This module reframes those computations in RACH terminology and adds
causal_resolvability, observation_contribution (as resolvability LOO, not
identifiability LOO), and next_observation_value.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Sequence


# ---------------------------------------------------------------------------
# Math helpers (self-contained; also used by identifiability.py)
# ---------------------------------------------------------------------------

def _binary_entropy(p: float) -> float:
    """Binary entropy H(p) in bits. Returns 0.0 for p in {0, 1}."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def _joint_entropy(vectors: list[tuple]) -> float:
    """Empirical joint entropy of binary vectors, in bits."""
    if not vectors:
        return 0.0
    n = len(vectors)
    counts = Counter(vectors)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _max_entropy(n_switches: int) -> float:
    """Maximum possible joint entropy for K binary switches = K bits."""
    return float(n_switches)


# ---------------------------------------------------------------------------
# Core RACH data structures
# ---------------------------------------------------------------------------

@dataclass
class CausalAdmissibilityResult:
    """Causal admissibility for one biological switch.

    CA_j = P(s_j = 1 | (θ, s) ∈ A_ε)

    Interpretation
    --------------
    CA_j is the posterior probability that mechanism j is active, given the
    observed data and biological constraints. Unlike a frequentist p-value,
    CA_j expresses the proportion of parameter-mechanism space that is
    simultaneously biologically feasible and observation-compatible.

    Attributes
    ----------
    switch_name:
        Identifier of the biological switch.
    biological_question:
        The ecological hypothesis being tested.
    CA_j:
        P(s_j=1 | A_ε) — causal admissibility ∈ [0, 1].
    prior_on_prob:
        Prior P(s_j=1) — default 0.5 (uninformative).
    Bayes_factor:
        (CA_j / (1-CA_j)) / (prior / (1-prior)) — evidence ratio.
    n_ON:
        Count of accepted samples with switch j ON.
    n_accepted:
        Total accepted samples |A_ε|.
    interpretation:
        Plain-language summary of support level.
    """

    switch_name: str
    biological_question: str
    CA_j: float
    prior_on_prob: float
    Bayes_factor: float | None
    n_ON: int
    n_accepted: int

    @property
    def interpretation(self) -> str:
        bf = self.Bayes_factor
        if bf is None or (isinstance(bf, float) and bf != bf):  # None or NaN
            return "indeterminate"
        if bf > 3.0:
            return "admissible (BF>3)"
        if bf > 1.0:
            return "weakly admissible"
        if bf > 0.33:
            return "weakly inadmissible"
        return "inadmissible (BF<1/3)"


@dataclass
class RACHSummary:
    """All five core RACH quantities for one inference run.

    Attributes
    ----------
    causal_admissibility:
        CA_j per switch.
    causal_degeneracy:
        D = H(S | A_ε) in bits. Lower = more resolved.
    max_degeneracy:
        H(S) = K bits (uninformative prior). Upper bound for D.
    causal_resolvability:
        R = 1 - D/K ∈ [0, 1].
        0 = completely unresolved (data provide no causal information).
        1 = completely resolved (unique mechanism combination identified).
    n_accepted:
        |A_ε| — size of the admissible causal region sample.
    n_switches:
        K — dimensionality of the causal switch space.
    """

    causal_admissibility: list[CausalAdmissibilityResult]
    causal_degeneracy: float
    max_degeneracy: float
    causal_resolvability: float
    n_accepted: int
    n_switches: int

    def summary_dict(self) -> dict:
        return {
            "n_accepted":          self.n_accepted,
            "n_switches":          self.n_switches,
            "causal_degeneracy_D": round(self.causal_degeneracy, 4),
            "max_degeneracy_K":    round(self.max_degeneracy, 4),
            "causal_resolvability_R": round(self.causal_resolvability, 4),
        }


@dataclass
class ObservationContribution:
    """Contribution of one pattern to causal resolvability.

    OC_k = R_RACH(O) - R_RACH(O \\ {k})

    Positive OC_k → pattern k increases resolvability.
    Negative OC_k → removing k would improve resolvability (k confounds inference).
    OC_k ≈ 0    → pattern k does not affect causal resolution.
    """

    pattern: str
    switch: str
    OC_k: float           # resolvability contribution (positive = helpful)
    R_full: float         # R with all patterns
    R_loo: float          # R without this pattern (LOO)
    n_loo: int
    n_full: int


@dataclass
class CandidateObservation:
    """A proposed additional empirical observation.

    Used as input to next_observation_value().

    Attributes
    ----------
    name:
        Short identifier for the candidate observation.
    description:
        What is measured and how.
    target_switches:
        Which switches this observation is theoretically informative about.
    rationale:
        Why this observation is expected to improve causal resolution.
    pattern_type:
        RACH pattern role if collected: 'pairwise_relation', 'gradient_slope', etc.
    """

    name: str
    description: str
    target_switches: list[str]
    rationale: str
    pattern_type: str = "pairwise_relation"


@dataclass
class NextObservationValueResult:
    """Estimated value of one candidate observation for causal resolution.

    NOV(q) ≈ E[ R(O ∪ q) - R(O) ]

    The expected resolvability gain is approximated as follows:
    For each candidate q, we estimate the expected change in causal resolvability
    if q were added to y_obs, by weighting the current identifiability gaps
    of the target switches by the estimated discriminating power of q.

    Note: This is an approximation. The true NOV requires integrating over
    possible outcomes of observation q; the approximation uses the current
    accepted sample to estimate average discriminating power.
    """

    candidate: str
    description: str
    target_switches: list[str]
    expected_resolvability_gain: float   # approximate ΔR ∈ [0, 1]
    current_R: float                     # R before adding q
    rationale: str
    priority: str   # "high" / "medium" / "low"


# ---------------------------------------------------------------------------
# Default candidate observations for Campanula / Izu worked example
# ---------------------------------------------------------------------------

CAMPANULA_CANDIDATE_OBSERVATIONS: list[CandidateObservation] = [
    CandidateObservation(
        name="guide_removal_experiment",
        description=(
            "Experimental removal / masking of nectar guides on Oshima plants, "
            "measuring change in Bombus visitation rate. Direct test of S1."
        ),
        target_switches=["guide_attracts_bombus"],
        rationale=(
            "S1 (guide → Bombus) is currently weakly identified because we lack "
            "a direct manipulation. Experimental removal provides near-definitive "
            "evidence for or against the guide-attraction pathway."
        ),
        pattern_type="experimental_manipulation",
    ),
    CandidateObservation(
        name="bagging_seed_set",
        description=(
            "Bagged (autonomous selfing) vs open-pollinated seed set across "
            "≥3 islands. Quantifies reproductive assurance value."
        ),
        target_switches=["selfing_syndrome_active", "small_pollinator_substitution"],
        rationale=(
            "S2 (selfing syndrome) requires that selfing provides a fitness benefit "
            "(RA). Bagging experiments directly measure RA strength across the "
            "isolation gradient, separating S2 from S5 (small pollinators compensate)."
        ),
        pattern_type="pairwise_relation",
    ),
    CandidateObservation(
        name="pollinator_visitation_rate",
        description=(
            "Visitation rate and pollen load per visit for Bombus vs halictids "
            "on each island. Distinguishes S1 (guide-attraction) from S5 (substitution)."
        ),
        target_switches=["guide_attracts_bombus", "small_pollinator_substitution"],
        rationale=(
            "S1 and S5 make opposing predictions about outcrossing service: "
            "S1 = Bombus drives outcrossing; S5 = halictids replace Bombus. "
            "Visitation data can distinguish which guild provides most pollen transfer."
        ),
        pattern_type="gradient_slope",
    ),
    CandidateObservation(
        name="He_neutral_diversity_gradient",
        description=(
            "Expected heterozygosity He measured by microsatellites across ≥4 islands "
            "along the isolation gradient."
        ),
        target_switches=["island_isolation_common_cause"],
        rationale=(
            "S3 (common cause) predicts that isolation drives multiple traits "
            "simultaneously via reduced Ne and migration. He measured genetically "
            "provides an independent test of the Ne-isolation relationship that "
            "is not circular with the existing Fis proxy."
        ),
        pattern_type="gradient_slope",
    ),
    CandidateObservation(
        name="Fis_gradient_intermediate_islands",
        description=(
            "Fis (inbreeding coefficient) measured on Kozushima and other intermediate "
            "islands to fill the current 2-endpoint dataset."
        ),
        target_switches=["selfing_syndrome_active", "island_isolation_common_cause"],
        rationale=(
            "Current y_obs has only Oshima vs Hachijo (2 endpoints). Adding "
            "intermediate-island Fis values tests whether the gradient is monotone "
            "(S2/S3) or stepped (alternative mechanisms), substantially improving "
            "causal resolution."
        ),
        pattern_type="gradient_slope",
    ),
    CandidateObservation(
        name="herkogamy_gradient_intermediate",
        description=(
            "Herkogamy measured on ≥2 intermediate islands (Kozushima, Niijima). "
            "Tests the monotone herkogamy-isolation relationship."
        ),
        target_switches=["selfing_syndrome_active"],
        rationale=(
            "S2 (selfing syndrome) predicts correlated decline of herkogamy with "
            "guide expression. Intermediate island data distinguishes co-evolved "
            "syndrome (monotone S2) from incidental herkogamy change (non-monotone)."
        ),
        pattern_type="gradient_slope",
    ),
    CandidateObservation(
        name="natural_seed_set_gradient",
        description=(
            "Natural (open-pollinated) seed set measured per island. "
            "Tests whether pollination limitation increases with isolation."
        ),
        target_switches=["small_pollinator_substitution", "selfing_syndrome_active"],
        rationale=(
            "If S5 (halictid substitution) is active, natural seed set should "
            "remain high even on Hachijo. If S2 drives evolution, seed set should "
            "increase with selfing rate. Combined with bagging data, this separates "
            "the two mechanisms."
        ),
        pattern_type="pairwise_relation",
    ),
    CandidateObservation(
        name="guide_area_spectrophotometry",
        description=(
            "Precise UV-reflectance measurement of guide expression across populations. "
            "Replaces provisional visual scoring with spectrophotometric data."
        ),
        target_switches=["guide_attracts_bombus", "selfing_syndrome_active"],
        rationale=(
            "Current guide data has high measurement uncertainty (visual proxy). "
            "Spectrophotometry reduces noise in y_obs, improving ABC discrimination "
            "for both S1 (guide attracts Bombus) and S2 (guide loss part of syndrome)."
        ),
        pattern_type="pairwise_relation",
    ),
]


# ---------------------------------------------------------------------------
# Core RACH quantity functions
# ---------------------------------------------------------------------------

def causal_admissibility(
    accepted_rows: list[dict],
    switches,   # Sequence[BiologicalSwitch]
) -> list[CausalAdmissibilityResult]:
    """Compute causal admissibility CA_j for each switch.

    CA_j = P(s_j = 1 | (θ, s) ∈ A_ε)

    Parameters
    ----------
    accepted_rows:
        Accepted sample rows from A_ε (output of run_switch_posterior_inference).
        Each row must contain boolean columns named by switch.name.
    switches:
        Sequence of BiologicalSwitch definitions.

    Returns
    -------
    list[CausalAdmissibilityResult]
        One entry per switch, sorted by switch order.
    """
    n = len(accepted_rows)
    results: list[CausalAdmissibilityResult] = []

    for sw in switches:
        n_on = sum(1 for r in accepted_rows if r.get(sw.name))
        ca = n_on / n if n > 0 else sw.prior_on_prob

        # Bayes factor
        prior = sw.prior_on_prob
        if 0.0 < ca < 1.0 and 0.0 < prior < 1.0:
            posterior_odds = ca / (1.0 - ca)
            prior_odds = prior / (1.0 - prior)
            bf: float | None = posterior_odds / prior_odds
        else:
            bf = None

        results.append(CausalAdmissibilityResult(
            switch_name=sw.name,
            biological_question=sw.biological_question,
            CA_j=round(ca, 4),
            prior_on_prob=prior,
            Bayes_factor=round(bf, 3) if bf is not None else None,
            n_ON=n_on,
            n_accepted=n,
        ))

    return results


def causal_degeneracy(
    accepted_rows: list[dict],
    switches,   # Sequence[BiologicalSwitch]
) -> float:
    """Compute causal degeneracy D = H(S | A_ε) in bits.

    D measures the remaining uncertainty about causal mechanism combinations
    after filtering by observations and constraints.

    D = 0: single mechanism combination — unique causal explanation.
    D = K: maximum uncertainty — observations do not constrain mechanisms.

    Parameters
    ----------
    accepted_rows:
        Accepted sample rows from A_ε.
    switches:
        Sequence of BiologicalSwitch definitions.

    Returns
    -------
    float
        H(S | A_ε) in bits.
    """
    if not accepted_rows:
        return float(len(list(switches)))  # maximum degeneracy if no accepted rows

    switch_names = [sw.name for sw in switches]
    vectors = [
        tuple(bool(r.get(name)) for name in switch_names)
        for r in accepted_rows
    ]
    return round(_joint_entropy(vectors), 4)


def causal_resolvability(
    accepted_rows: list[dict],
    switches,   # Sequence[BiologicalSwitch]
) -> float:
    """Compute causal resolvability R = 1 - H(S | A_ε) / H(S).

    R ∈ [0, 1] measures the fraction of causal uncertainty resolved by
    the current observation set and biological constraints.

    R = 0: no resolution — observations provide zero causal information.
    R = 1: complete resolution — unique mechanism combination identified.

    Parameters
    ----------
    accepted_rows:
        Accepted sample rows from A_ε.
    switches:
        Sequence of BiologicalSwitch definitions.

    Returns
    -------
    float
        R ∈ [0, 1].
    """
    K = len(list(switches))
    if K == 0:
        return 1.0
    D = causal_degeneracy(accepted_rows, switches)
    H_prior = _max_entropy(K)
    R = max(0.0, 1.0 - D / H_prior)
    return round(R, 4)


def observation_contribution(
    evaluated_rows: list[dict],
    switches,        # Sequence[BiologicalSwitch]
    threshold: float = 0.8,
) -> list[ObservationContribution]:
    """Compute OC_k = R(O) - R(O \\ {k}) for each pattern (leave-one-out).

    Positive OC_k: pattern k improves causal resolvability.
    Negative OC_k: removing k would INCREASE resolvability (pattern confounds).
    OC_k ≈ 0: pattern k is redundant / irrelevant.

    Parameters
    ----------
    evaluated_rows:
        ALL evaluated rows (accepted + rejected), each with ``per_pattern_matched``.
        Must NOT be filtered to accepted_rows only.  When pattern k is removed
        some previously-rejected rows may cross the threshold and must be counted.
        Passing only accepted_rows produces a downward-biased OC_k estimate.
    switches:
        Sequence of BiologicalSwitch definitions.
    threshold:
        ABC acceptance threshold (weighted_match_rate) used for LOO re-evaluation.
        Should match the threshold used in the original inference run.

    Returns
    -------
    list[ObservationContribution]
        One per (pattern, switch) pair.
    """
    # Rows that have per_pattern_matched data (simulation succeeded)
    rows_with_data = [
        r for r in evaluated_rows
        if isinstance(r.get("per_pattern_matched"), dict)
    ]
    if not rows_with_data:
        return []

    # Full-set accepted rows and resolvability (baseline)
    full_accepted = [r for r in rows_with_data if r.get("weighted_match_rate", 0.0) >= threshold]
    if not full_accepted:
        return []
    R_full = causal_resolvability(full_accepted, switches)

    all_pattern_names: set[str] = set()
    for r in rows_with_data:
        all_pattern_names.update(r["per_pattern_matched"].keys())

    results: list[ObservationContribution] = []
    for pattern_k in sorted(all_pattern_names):
        # Re-evaluate ALL rows (not just accepted_rows) without pattern k.
        # This is the correct LOO: some rejected rows may become accepted once
        # pattern k is removed from the distance computation.
        loo_accepted: list[dict] = []
        for r in rows_with_data:
            ppm = r["per_pattern_matched"]
            entry = ppm.get(pattern_k)
            if entry is None:
                # Pattern k not in this row's eval; use original acceptance
                if r.get("weighted_match_rate", 0.0) >= threshold:
                    loo_accepted.append(r)
                continue
            matched_k, weight_k = entry
            total_w = sum(w for _, w in ppm.values())
            matched_w = sum(w for m, w in ppm.values() if m)
            new_total = total_w - weight_k
            new_matched = matched_w - (weight_k if matched_k else 0.0)
            loo_wmr = (new_matched / new_total) if new_total > 0 else 1.0
            if loo_wmr >= threshold:
                loo_accepted.append(r)

        R_loo = causal_resolvability(loo_accepted, switches) if loo_accepted else 0.0

        for sw in switches:
            results.append(ObservationContribution(
                pattern=pattern_k,
                switch=sw.name,
                OC_k=round(R_full - R_loo, 4),
                R_full=R_full,
                R_loo=R_loo,
                n_loo=len(loo_accepted),
                n_full=len(full_accepted),
            ))

    return results


def next_observation_value(
    accepted_rows: list[dict],
    switches,        # Sequence[BiologicalSwitch]
    candidates: list[CandidateObservation] | None = None,
) -> list[NextObservationValueResult]:
    """Approximate NOV(q) for each candidate observation.

    NOV(q) ≈ E[ R(O ∪ q) - R(O) ]

    This function approximates the expected gain in causal resolvability if
    candidate q were added to the observation set.  The approximation is:

    1. Compute current R = causal_resolvability(accepted_rows, switches).
    2. For each candidate q, identify the target switches it informs.
    3. For each target switch j, compute the current CA_j and the
       remaining ambiguity: max(CA_j, 1-CA_j) - 0.5 (deviation from 0.5).
    4. Expected resolvability gain ≈ mean ambiguity reduction over target switches,
       weighted by theoretical discriminating power.

    This is a heuristic approximation, not the exact E[R(O∪q) - R(O)].
    The exact NOV requires integrating over possible outcomes of q, which
    requires a forward model for q's distribution — not available without
    additional empirical data.

    Parameters
    ----------
    accepted_rows:
        Accepted sample rows from A_ε.
    switches:
        Sequence of BiologicalSwitch definitions.
    candidates:
        List of CandidateObservation. Defaults to CAMPANULA_CANDIDATE_OBSERVATIONS.

    Returns
    -------
    list[NextObservationValueResult]
        One entry per candidate, sorted by expected resolvability gain (descending).
    """
    if candidates is None:
        candidates = CAMPANULA_CANDIDATE_OBSERVATIONS

    R_current = causal_resolvability(accepted_rows, switches)
    ca_results = causal_admissibility(accepted_rows, switches)
    ca_by_name = {r.switch_name: r for r in ca_results}
    K = len(list(switches))

    results: list[NextObservationValueResult] = []
    for cand in candidates:
        # Estimate expected resolvability gain from this candidate
        target_sw_names = cand.target_switches
        if not target_sw_names:
            gain = 0.0
        else:
            gains: list[float] = []
            for sw_name in target_sw_names:
                ca_r = ca_by_name.get(sw_name)
                if ca_r is None:
                    continue
                # Current ambiguity for this switch: distance from 0.5
                # (0 = fully resolved; 0.5 = maximally ambiguous)
                ambiguity = abs(ca_r.CA_j - 0.5)  # 0 = most ambiguous; 0.5 = resolved
                # Expected gain ∝ remaining ambiguity / K
                # (discriminating observation about a highly ambiguous switch
                #  provides more gain than one about an already-resolved switch)
                remaining_ambiguity = 0.5 - ambiguity   # 0 = resolved; 0.5 = max ambiguous
                gain_per_switch = remaining_ambiguity / K
                gains.append(gain_per_switch)
            gain = sum(gains) if gains else 0.0

        # Heuristic priority
        if gain > 0.15 / K:
            priority = "high"
        elif gain > 0.05 / K:
            priority = "medium"
        else:
            priority = "low"

        results.append(NextObservationValueResult(
            candidate=cand.name,
            description=cand.description,
            target_switches=cand.target_switches,
            expected_resolvability_gain=round(gain, 4),
            current_R=R_current,
            rationale=cand.rationale,
            priority=priority,
        ))

    # Sort by expected gain descending
    results.sort(key=lambda x: x.expected_resolvability_gain, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Unified summary object
# ---------------------------------------------------------------------------

def rach_summary(
    accepted_rows: list[dict],
    switches,   # Sequence[BiologicalSwitch]
    threshold: float = 1.0,
    candidates: list[CandidateObservation] | None = None,
) -> RACHSummary:
    """Compute all five core RACH quantities in one call.

    Parameters
    ----------
    accepted_rows:
        Accepted sample rows from A_ε.
    switches:
        Sequence of BiologicalSwitch definitions.
    threshold:
        ABC acceptance threshold for LOO re-evaluation (observation_contribution).
    candidates:
        Candidate observations for NOV. Defaults to CAMPANULA_CANDIDATE_OBSERVATIONS.

    Returns
    -------
    RACHSummary
        Contains CA_j, D, R, and convenience methods.
    """
    K = len(list(switches))
    D = causal_degeneracy(accepted_rows, switches)
    R = causal_resolvability(accepted_rows, switches)
    CA = causal_admissibility(accepted_rows, switches)

    return RACHSummary(
        causal_admissibility=CA,
        causal_degeneracy=D,
        max_degeneracy=float(K),
        causal_resolvability=R,
        n_accepted=len(accepted_rows),
        n_switches=K,
    )


# ---------------------------------------------------------------------------
# Backward compatibility: re-export identifiability-module equivalents
# ---------------------------------------------------------------------------

def compute_causal_admissibility_table(
    accepted_rows: list[dict],
    switches,
) -> list[dict]:
    """Return CA_j table as list[dict] for display in dataframes.

    Convenience wrapper for Streamlit / CSV export.
    """
    ca_results = causal_admissibility(accepted_rows, switches)
    return [
        {
            "switch":               r.switch_name,
            "biological_question":  r.biological_question[:90],
            "CA_j":                 r.CA_j,
            "prior_on_prob":        r.prior_on_prob,
            "Bayes_factor":         r.Bayes_factor,
            "n_ON":                 r.n_ON,
            "n_accepted":           r.n_accepted,
            "interpretation":       r.interpretation,
        }
        for r in ca_results
    ]
