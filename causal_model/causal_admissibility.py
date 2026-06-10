"""RACH: Causal Admissibility and Degeneracy Framework.

This module implements the five core RACH quantities:

    CA_j    Causal admissibility    P(s_j = 1 | A_ε)
    D_RACH  Causal degeneracy       H(S | A_ε)
    R_RACH  Causal resolvability    1 - H(S | A_ε) / log2|S| = 1 - H(S|A_ε)/K
    OC_k    Observation contribution  R_RACH(O) - R_RACH(O \\ {k})
    NOV(q)  Next-observation value  E[ R_RACH(O ∪ q) - R_RACH(O) ]

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

    observation_contribution(evaluated_rows, switches, threshold)
        → list[ObservationContribution]  one per pattern (OC_k is pattern-level)

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
    """Contribution of one observation pattern to causal resolvability.

    OC_k = R_RACH(O) - R_RACH(O \\ {k})

    LEVEL — OC_k is **pattern-level, not switch-specific.**
        R_RACH is the *joint* resolvability of the whole switch vector
        s ∈ {0,1}^K; it is derived from the joint entropy H(S | A_ε), a single
        scalar over all K switches (see ``causal_resolvability``).  OC_k
        therefore measures how observation pattern k changes the resolvability
        of the *entire* mechanism combination, not of any individual switch.
        There is exactly **one OC_k per pattern**; it does not decompose into a
        per-switch quantity.  ``n_switches`` records K — the size of the joint
        switch vector OC_k was computed over — for provenance.

    Positive OC_k → pattern k increases joint resolvability.
    Negative OC_k → removing k would improve resolvability (k confounds inference).
    OC_k ≈ 0    → pattern k does not affect causal resolution.
    """

    pattern: str
    OC_k: float           # resolvability contribution (positive = helpful)
    R_full: float         # R with all patterns
    R_loo: float          # R without this pattern (LOO)
    n_loo: int
    n_full: int
    level: str = "pattern"   # OC_k is pattern-level (joint over all switches)
    n_switches: int = 0      # K = number of switches the joint R was computed over


@dataclass
class CandidateOutcome:
    """One possible empirical result of collecting candidate observation q.

    Used in next_observation_value_simulation() to integrate over outcomes.

    Attributes
    ----------
    name:
        Short identifier, e.g. "monotone_gradient" or "no_effect".
    description:
        What this outcome means biologically.
    prior_probability:
        Prior probability of this outcome.  Must sum to 1.0 across all
        outcomes for a given CandidateObservation.
    extra_pattern_rows:
        New pattern rows (CSV-style dicts) to add to y_obs if this outcome
        is observed.  Each row must be evaluable by evaluate_patterns() —
        i.e. role must be in ABC_TARGET_ROLES and type must be one of
        pairwise_relation / gradient_slope / rank_order / trait_correlation.
    """

    name: str
    description: str
    prior_probability: float
    extra_pattern_rows: list[dict]


@dataclass
class CandidateObservation:
    """A proposed additional empirical observation.

    Used as input to next_observation_value() and
    next_observation_value_simulation().

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
    outcomes:
        Possible empirical outcomes with prior probabilities and the
        corresponding new pattern rows.  Used by
        next_observation_value_simulation().  Empty list = heuristic only.
    """

    name: str
    description: str
    target_switches: list[str]
    rationale: str
    pattern_type: str = "pairwise_relation"
    outcomes: list[CandidateOutcome] = None   # type: ignore[assignment]

    def __post_init__(self):
        if self.outcomes is None:
            self.outcomes = []


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
    # Which of this candidate's target switches are prior/ε sensitive (from the
    # ensemble robustness check).  NOV exists to resolve sensitive switches, so a
    # candidate that targets one is the actionable next observation.
    sensitive_targets: list[str] = field(default_factory=list)
    targets_sensitive_switch: bool = False


# ---------------------------------------------------------------------------
# Default candidate observations for Campanula / Izu worked example
# ---------------------------------------------------------------------------

def _pw(name, variable, left, right, relation, weight=1.0, source="candidate_nov"):
    """Build a pairwise_relation pattern row (helper for outcomes)."""
    return {
        "pattern": name, "type": "pairwise_relation",
        "variable": variable,
        "left_population": left, "right_population": right,
        "populations": "", "predictor": "", "expected_direction": "",
        "relation": relation, "weight": str(weight),
        "source": source, "notes": "NOV candidate outcome",
        "role": "observed_target", "epistemic_status": "candidate",
        "weight_rationale": "NOV simulation outcome",
    }


def _slope(name, variable, direction, weight=1.0, source="candidate_nov"):
    """Build a gradient_slope pattern row (helper for outcomes)."""
    return {
        "pattern": name, "type": "gradient_slope",
        "variable": variable,
        "left_population": "", "right_population": "",
        "populations": "", "predictor": "distance_from_mainland",
        "expected_direction": direction,
        "relation": "", "weight": str(weight),
        "source": source, "notes": "NOV candidate outcome",
        "role": "observed_target", "epistemic_status": "candidate",
        "weight_rationale": "NOV simulation outcome",
    }


def _rank(name, variable, direction, weight=1.0, source="candidate_nov"):
    """Build a rank_order pattern row (helper for outcomes)."""
    return {
        "pattern": name, "type": "rank_order",
        "variable": variable,
        "left_population": "", "right_population": "",
        "populations": "", "predictor": "",
        "expected_direction": direction,
        "relation": "", "weight": str(weight),
        "source": source, "notes": "NOV candidate outcome",
        "role": "observed_target", "epistemic_status": "candidate",
        "weight_rationale": "NOV simulation outcome",
    }


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
        outcomes=[
            CandidateOutcome(
                name="guide_effect_confirmed",
                description="Bombus visitation drops significantly after guide removal (S1 confirmed).",
                prior_probability=0.55,
                extra_pattern_rows=[
                    # guide positively correlates with outcrossing opportunity
                    {
                        "pattern": "guide_outcross_corr_obs",
                        "type": "trait_correlation",
                        "variable": "outcrossing_opportunity",
                        "left_population": "", "right_population": "",
                        "populations": "",
                        "predictor": "nectar_guide",
                        "expected_direction": "positive",
                        "relation": "", "weight": "1.2",
                        "source": "candidate_nov", "notes": "guide removal confirmed S1",
                        "role": "observed_target", "epistemic_status": "candidate",
                        "weight_rationale": "experimental manipulation; high weight",
                    },
                ],
            ),
            CandidateOutcome(
                name="guide_effect_absent",
                description="Bombus visitation unchanged after guide removal (S1 refuted).",
                prior_probability=0.45,
                extra_pattern_rows=[
                    {
                        "pattern": "guide_outcross_corr_obs",
                        "type": "trait_correlation",
                        "variable": "outcrossing_opportunity",
                        "left_population": "", "right_population": "",
                        "populations": "",
                        "predictor": "nectar_guide",
                        "expected_direction": "negative",
                        "relation": "", "weight": "1.2",
                        "source": "candidate_nov", "notes": "guide removal refuted S1",
                        "role": "observed_target", "epistemic_status": "candidate",
                        "weight_rationale": "experimental manipulation; high weight",
                    },
                ],
            ),
        ],
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
        outcomes=[
            CandidateOutcome(
                name="high_ra_on_hachijo",
                description=(
                    "Bagged/open seed-set ratio higher on Hachijo: pollination limitation "
                    "confirmed → higher selfing rate on Hachijo."
                ),
                prior_probability=0.6,
                extra_pattern_rows=[
                    # selfing_benefit is a θ parameter (not in ABMPopulationProxy).
                    # selfing_rate is the population-level simulation output that captures
                    # the same reproductive-assurance signal.
                    _pw("bagging_pairwise_RA", "selfing_rate",
                        "Oshima", "Hachijo", "Oshima < Hachijo", weight=1.0),
                ],
            ),
            CandidateOutcome(
                name="equal_ra_both_islands",
                description=(
                    "Bagged/open ratio similar on both islands: halictids compensate (S4 favoured) "
                    "→ Hachijo selfing rate not elevated above Oshima."
                ),
                prior_probability=0.4,
                extra_pattern_rows=[
                    _pw("bagging_pairwise_RA", "selfing_rate",
                        "Oshima", "Hachijo", "Oshima > Hachijo", weight=1.0),
                ],
            ),
        ],
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
        outcomes=[
            CandidateOutcome(
                name="outcrossing_declines_with_isolation",
                description="Total outcrossing opportunity decreases with isolation (supports S1 or S3).",
                prior_probability=0.55,
                extra_pattern_rows=[
                    _slope("outcrossing_gradient_obs", "outcrossing_opportunity",
                           "negative", weight=1.0),
                ],
            ),
            CandidateOutcome(
                name="outcrossing_flat_gradient",
                description="Outcrossing opportunity flat across islands (halictids compensate — S4).",
                prior_probability=0.45,
                extra_pattern_rows=[
                    _pw("outcrossing_pairwise_obs", "outcrossing_opportunity",
                        "Oshima", "Hachijo", "Oshima < Hachijo", weight=0.8),
                ],
            ),
        ],
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
        outcomes=[
            CandidateOutcome(
                name="diversity_declines_monotone",
                description="He declines monotonically with isolation (S3 confirmed).",
                prior_probability=0.65,
                extra_pattern_rows=[
                    _slope("He_gradient_obs", "neutral_diversity", "negative", weight=1.0),
                    _rank("He_rank_obs", "neutral_diversity", "decreasing", weight=0.8),
                ],
            ),
            CandidateOutcome(
                name="diversity_no_gradient",
                description="He does not decline with isolation (S3 weakened).",
                prior_probability=0.35,
                extra_pattern_rows=[
                    _slope("He_gradient_obs", "neutral_diversity", "positive", weight=1.0),
                ],
            ),
        ],
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
        outcomes=[
            CandidateOutcome(
                name="monotone_Fis_gradient",
                description="Kozushima Fis is between Oshima and Hachijo — monotone gradient confirmed.",
                prior_probability=0.6,
                extra_pattern_rows=[
                    # Oshima < Kozushima < Hachijo in Fis
                    _pw("Fis_Oshima_Kozushima", "Fis",
                        "Oshima", "Kozushima", "Oshima < Kozushima", weight=0.9),
                    _pw("Fis_Kozushima_Hachijo", "Fis",
                        "Kozushima", "Hachijo", "Kozushima < Hachijo", weight=0.9),
                    _rank("Fis_rank_obs", "Fis", "increasing", weight=0.8),
                ],
            ),
            CandidateOutcome(
                name="stepped_Fis_gradient",
                description="Kozushima Fis similar to Oshima — step change only at Hachijo.",
                prior_probability=0.4,
                extra_pattern_rows=[
                    # Oshima ≈ Kozushima < Hachijo: only Kozushima < Hachijo holds
                    _pw("Fis_Kozushima_Hachijo", "Fis",
                        "Kozushima", "Hachijo", "Kozushima < Hachijo", weight=0.9),
                    _pw("Fis_Oshima_Kozushima", "Fis",
                        "Oshima", "Kozushima", "Oshima > Kozushima", weight=0.5),
                ],
            ),
        ],
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
        outcomes=[
            CandidateOutcome(
                name="monotone_herkogamy_decline",
                description="Herkogamy declines monotonically: Oshima > Kozushima > Hachijo.",
                prior_probability=0.55,
                extra_pattern_rows=[
                    _pw("herkogamy_Oshima_Kozushima", "herkogamy",
                        "Oshima", "Kozushima", "Oshima > Kozushima", weight=0.8),
                    _rank("herkogamy_rank_obs", "herkogamy", "decreasing", weight=0.8),
                ],
            ),
            CandidateOutcome(
                name="herkogamy_step_at_hachijo",
                description="Herkogamy similar on Oshima and Kozushima; abrupt drop at Hachijo.",
                prior_probability=0.45,
                extra_pattern_rows=[
                    _pw("herkogamy_Oshima_Kozushima", "herkogamy",
                        "Oshima", "Kozushima", "Oshima < Kozushima", weight=0.5),
                    _pw("herkogamy_Kozushima_Hachijo", "herkogamy",
                        "Kozushima", "Hachijo", "Kozushima > Hachijo", weight=0.8),
                ],
            ),
        ],
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
        outcomes=[
            CandidateOutcome(
                name="seed_set_lower_on_hachijo",
                description="Natural seed set lower on Hachijo — pollination limitation present.",
                prior_probability=0.5,
                extra_pattern_rows=[
                    _pw("seed_set_pairwise_obs", "outcrossing_opportunity",
                        "Oshima", "Hachijo", "Oshima > Hachijo", weight=0.9),
                ],
            ),
            CandidateOutcome(
                name="seed_set_equal",
                description="Seed set similar across islands — halictids compensate (S4).",
                prior_probability=0.5,
                extra_pattern_rows=[
                    _pw("seed_set_pairwise_obs", "outcrossing_opportunity",
                        "Oshima", "Hachijo", "Oshima < Hachijo", weight=0.9),
                ],
            ),
        ],
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
        outcomes=[
            CandidateOutcome(
                name="guide_gradient_confirmed_precise",
                description="Precise UV measurements confirm nectar guide gradient with high confidence.",
                prior_probability=0.7,
                extra_pattern_rows=[
                    # Same pairwise direction but with higher weight (measurement quality upgrade)
                    _pw("nectar_guide_precise_pairwise", "nectar_guide",
                        "Oshima", "Hachijo", "Oshima > Hachijo", weight=1.5),
                    _rank("nectar_guide_rank_precise", "nectar_guide",
                          "decreasing", weight=1.0),
                ],
            ),
            CandidateOutcome(
                name="guide_difference_smaller_than_expected",
                description="UV measurement shows weaker guide gradient than visual scoring suggested.",
                prior_probability=0.3,
                extra_pattern_rows=[
                    _pw("nectar_guide_precise_pairwise", "nectar_guide",
                        "Oshima", "Hachijo", "Oshima > Hachijo", weight=0.5),
                ],
            ),
        ],
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
    """Compute causal resolvability R_RACH = 1 - H(S | A_ε) / K.

    K = log₂|S| = number of switches (maximum possible joint entropy in bits).
    This equals H(S_prior) when all switch priors are Bernoulli(0.5), which
    is the standard Campanula setting.  Using K (a fixed constant) rather than
    H(S_prior) ensures R_RACH is bounded in [0, 1] regardless of prior choice.

    R = 0: no resolution — observations do not constrain mechanism combinations.
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
        One entry **per pattern** (OC_k is pattern-level — it is the change in
        the joint resolvability R_RACH and does not decompose per switch).
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
    K = len(list(switches))

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

        # OC_k is pattern-level: a single value per pattern, computed from the
        # joint resolvability over all switches.  It is NOT replicated per switch.
        results.append(ObservationContribution(
            pattern=pattern_k,
            OC_k=round(R_full - R_loo, 4),
            R_full=R_full,
            R_loo=R_loo,
            n_loo=len(loo_accepted),
            n_full=len(full_accepted),
            level="pattern",
            n_switches=K,
        ))

    return results


def next_observation_value(
    accepted_rows: list[dict],
    switches,        # Sequence[BiologicalSwitch]
    candidates: list[CandidateObservation] | None = None,
    sensitive_switches: list[str] | None = None,
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
    sensitive_switches:
        Names of switches the ensemble robustness check flagged as prior/ε
        sensitive (see ``causal_model.ensemble.sensitive_switches``).  NOV exists
        to resolve these switches, so candidates that target a sensitive switch
        are marked (``targets_sensitive_switch``) and sorted ahead of equal-gain
        candidates that only target already-robust switches.  ``None`` or empty
        leaves the original behaviour (gain-only ranking) unchanged.

    Returns
    -------
    list[NextObservationValueResult]
        One entry per candidate.  Sorted by (targets a sensitive switch, then
        expected resolvability gain), both descending.
    """
    if candidates is None:
        candidates = CAMPANULA_CANDIDATE_OBSERVATIONS

    sensitive_set = set(sensitive_switches or [])

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

        # Sensitive-switch linkage: which target switches are prior/ε sensitive?
        sens_targets = [s for s in target_sw_names if s in sensitive_set]
        targets_sensitive = bool(sens_targets)

        # Heuristic priority
        if gain > 0.15 / K:
            priority = "high"
        elif gain > 0.05 / K:
            priority = "medium"
        else:
            priority = "low"
        # A candidate that resolves a sensitive switch is actionable even when its
        # raw gain is modest: promote it at least to "medium".
        if targets_sensitive and priority == "low":
            priority = "medium"

        rationale = cand.rationale
        if targets_sensitive:
            rationale = (
                f"[targets prior/ε-sensitive switch(es): {', '.join(sens_targets)}] "
                + rationale
            )

        results.append(NextObservationValueResult(
            candidate=cand.name,
            description=cand.description,
            target_switches=cand.target_switches,
            expected_resolvability_gain=round(gain, 4),
            current_R=R_current,
            rationale=rationale,
            priority=priority,
            sensitive_targets=sens_targets,
            targets_sensitive_switch=targets_sensitive,
        ))

    # Sort sensitive-switch targets first, then by expected gain (both descending).
    results.sort(key=lambda x: (x.targets_sensitive_switch, x.expected_resolvability_gain),
                 reverse=True)
    return results


def next_observation_value_simulation(
    observed_rels: list[dict],
    pattern_weights: dict,
    switches,        # Sequence[BiologicalSwitch]
    candidates: list[CandidateObservation] | None = None,
    n_attempts: int = 200,
    preset_name: str = "literature_grounded",
    acceptance_rule: str = "weighted_lax",
    seed: int | None = None,
    threshold: float = 0.8,
    progress_callback=None,
    current_accepted_rows: list[dict] | None = None,
    nov_backend: str = "proxy",
) -> list[NextObservationValueResult]:
    """Simulation-based NOV(q) by integrating over candidate outcomes.

    NOV(q) = Σ_v  p(v) · R(O ∪ {q=v})  −  R(O)

    For each candidate observation q and each of its possible empirical
    outcomes v (defined in CandidateObservation.outcomes), this function:

    1. Augments observed_rels with the outcome's extra_pattern_rows.
    2. Re-runs ABC inference with n_attempts draws.
    3. Computes R from the resulting accepted sample.
    4. Weights by prior_probability of the outcome.

    Unlike the heuristic next_observation_value(), this provides an
    empirically grounded expected R gain rather than an approximation
    based only on current CA_j.  Candidates without defined outcomes fall
    back to the heuristic estimate.

    Parameters
    ----------
    observed_rels:
        Current y_obs pattern rows (list[dict] from observed_patterns.csv).
    pattern_weights:
        Pattern weight dict keyed by pattern name.
    switches:
        Sequence of BiologicalSwitch definitions.
    candidates:
        Candidate observations with outcomes.  Defaults to
        CAMPANULA_CANDIDATE_OBSERVATIONS.
    n_attempts:
        ABC draws per outcome run.  200 proxy draws ≈ 2-5 s per candidate;
        use 500+ for stable R estimates.  With nov_backend="abm" each draw
        runs 6 ABM replicates so prefer 100 or lower.
    preset_name:
        Parameter preset for ABC sampling.
    acceptance_rule:
        ABC acceptance rule (e.g. "weighted_lax").
    seed:
        Random seed for reproducibility.  Each outcome uses seed+i to
        ensure diversity across runs while remaining reproducible.
    threshold:
        Weighted match rate threshold for acceptance.
    progress_callback:
        Optional callable(candidate_name: str, outcome_name: str,
        total_done: int, total: int) — called after each ABC run.
    nov_backend:
        Backend used for per-outcome ABC runs.  "proxy" (default) is ~50x
        faster than "abm" and sufficient for NOV priority ranking.  Use
        "abm" only when you need high-fidelity R estimates per outcome.

    Returns
    -------
    list[NextObservationValueResult]
        One entry per candidate, sorted by NOV (descending).
        expected_resolvability_gain = NOV(q) = E[R_new] - R_current.
    """
    from causal_model.switch_inference import (   # lazy import
        run_switch_posterior_inference_abm as _run_abm,
        run_switch_posterior_inference as _run_proxy,
    )

    _run_outcome = _run_proxy if nov_backend == "proxy" else _run_abm

    if candidates is None:
        candidates = CAMPANULA_CANDIDATE_OBSERVATIONS

    # --- Step 1: baseline R from current accepted sample (no re-run needed) ---
    # If current_accepted_rows is provided, use it directly to avoid a redundant
    # ABC run and to ensure the baseline R matches the caller's posterior.
    if current_accepted_rows is not None:
        R_current = causal_resolvability(current_accepted_rows, switches)
        _baseline_rows = current_accepted_rows
    else:
        _bl = _run_abm(
            preset_name=preset_name,
            n_attempts=n_attempts,
            acceptance_rule=acceptance_rule,
            seed=seed,
            observed_rels=observed_rels,
            pattern_weights=pattern_weights,
            threshold=threshold,
        )
        R_current = causal_resolvability(_bl.accepted_rows, switches)
        _baseline_rows = _bl.accepted_rows

    # --- Step 2: for each candidate, integrate over outcomes ---
    total_runs = sum(len(c.outcomes) for c in candidates if c.outcomes)
    done = 0
    results: list[NextObservationValueResult] = []

    # Relative priority thresholds: fraction of maximum possible gain (1 - R_current)
    _max_possible_gain = max(1.0 - R_current, 0.01)
    _high_thresh   = 0.20 * _max_possible_gain   # top 20% of headroom
    _medium_thresh = 0.05 * _max_possible_gain   # top 5% of headroom

    for cand in candidates:
        if not cand.outcomes:
            # No outcomes defined — fall back to heuristic
            heuristic = next_observation_value(_baseline_rows, switches, [cand])
            if heuristic:
                results.append(heuristic[0])
            continue

        R_expected = 0.0
        outcome_details: list[dict] = []

        for i, outcome in enumerate(cand.outcomes):
            _run_seed = (seed + done + 1) if seed is not None else None
            sp = _run_outcome(
                preset_name=preset_name,
                n_attempts=n_attempts,
                acceptance_rule=acceptance_rule,
                seed=_run_seed,
                observed_rels=observed_rels,
                pattern_weights=pattern_weights,
                threshold=threshold,
                extra_pattern_rows=outcome.extra_pattern_rows,
            )
            R_outcome = causal_resolvability(sp.accepted_rows, switches)
            R_expected += outcome.prior_probability * R_outcome
            outcome_details.append({
                "outcome": outcome.name,
                "p": outcome.prior_probability,
                "R": round(R_outcome, 4),
                "n_accepted": len(sp.accepted_rows),
            })
            done += 1
            if progress_callback is not None:
                progress_callback(cand.name, outcome.name, done, total_runs)

        NOV_q = R_expected - R_current

        if NOV_q > _high_thresh:
            priority = "high"
        elif NOV_q > _medium_thresh:
            priority = "medium"
        else:
            priority = "low"

        rationale_ext = (
            cand.rationale + "  [Simulation NOV: " +
            "; ".join(f"{d['outcome']} p={d['p']:.2f} R={d['R']:.3f}" for d in outcome_details) +
            f"; NOV={NOV_q:.4f}]"
        )
        results.append(NextObservationValueResult(
            candidate=cand.name,
            description=cand.description,
            target_switches=cand.target_switches,
            expected_resolvability_gain=round(NOV_q, 4),
            current_R=R_current,
            rationale=rationale_ext,
            priority=priority,
        ))

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
