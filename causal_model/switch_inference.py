"""PathwaySwitch posterior inference — the core of original RACH.

Instead of pre-defining M1-M5 causal structures and asking which fits best,
this module treats the biological pathway switches as latent binary variables
and infers their posterior distribution from observed patterns.

Algorithm
---------
1. Sample binary switch states  s ~ Bernoulli(prior_on_prob)
2. Sample latent parameters     θ ~ constrained trade-off prior
3. Simulate proxy               y = f(θ, s)
4. ABC acceptance               accept if pattern_distance(y, observed) <= ε
5. Posterior                    P(switch ON | accepted) = accepted_ON / n_accepted

Why this is an original contribution
--------------------------------------
The standard approach fixes causal structures (M1, M2, … Mk) and ranks them.
This module does not pre-define structures. Instead, the inference output IS
the posterior probability that each biological mechanism is active. The
posterior jointly reflects which switches are simultaneously supported by the
pattern evidence — something structure-ranking cannot capture.

Relation to M1-M5
-----------------
Each M structure corresponds to a particular switch combination:

    M0  direct_pollinator_to_guide=0  selfing_mediation=0  island_common_cause=0  (null: drift+env only)
    M1  direct_pollinator_to_guide=1  selfing_mediation=0  island_common_cause=0
    M2  direct_pollinator_to_guide=0  selfing_mediation=1  island_common_cause=0
    M3  direct_pollinator_to_guide=1  selfing_mediation=1  island_common_cause=0
    M4  direct_pollinator_to_guide=~  selfing_mediation=~  island_common_cause=1

    NOTE: drift_null (S4) removed.  Genetic drift is always present in finite
    populations — it is a continuous background process parameterised by
    drift_strength (θ) and Ne (derived from island_distance in env).
    The null model M0 = all selection switches OFF; drift + environmental
    gradient operate freely via θ and Ne.

The switch posterior subsumes and extends structure ranking.
"""

from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass
from typing import Sequence

from causal_model.parameter_constraints import (
    predefined_tradeoff_presets,
    sample_all_sets_with_rejection_log,
)
from causal_model.parameter_sampling import (
    param_set_to_model_parameters,
    env_slopes_from_param_set,
)
from causal_model.switches import PathwaySwitches

# ABM output column → relation variable name
# ABM final-generation dicts use verbose keys; proxy uses short keys.
_ABM_KEY_MAP: dict[str, str] = {
    "nectar_guide":  "mean_nectar_guide",
    "selfing_rate":  "selfing_rate",
    "herkogamy":     "mean_herkogamy",
    "flower_size":   "mean_flower_size",
    "Fis":           "Fis_proxy",
}

# DEPRECATED: hardcodes Campanula Izu population names in framework layer.
# The active ABM inference path (run_switch_posterior_inference_abm) uses
# generic isolation-gradient populations (iso_0.000...iso_1.000) and does
# not call this function. Kept for backward compatibility only.
# primary_pollinator_frequency is environmental; inject directly from env.
_ABM_PRIMARY_POLL: dict[str, float] = {"Oshima": 0.35, "Hachijo": 0.00}

# Minimum trait difference to call a directional relation (same as proxy tolerance)
_ABM_RELATION_TOLERANCE: float = 0.05


# ---------------------------------------------------------------------------
# Biological switch definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BiologicalSwitch:
    """A binary latent variable representing one biological pathway.

    Attributes
    ----------
    name:
        Short identifier used as dict key and column name.
    pathway_key:
        The corresponding field name in :class:`PathwaySwitches`.
    biological_question:
        The ecological / evolutionary hypothesis being tested.
    description:
        Mechanism description in plain language.
    prior_on_prob:
        Prior probability that this switch is ON (default 0.5 = uninformative).
    """

    name: str
    pathway_key: str
    biological_question: str
    description: str
    prior_on_prob: float = 0.5


CAMPANULA_SWITCHES: tuple[BiologicalSwitch, ...] = (
    BiologicalSwitch(
        name="guide_attracts_bombus",
        pathway_key="direct_pollinator_to_guide",
        biological_question="Does nectar-guide expression causally increase Bombus visitation?",
        description=(
            "Nectar-guide expression (UV-absorbing spots) guides Bombus to the "
            "flower reward. When this pathway is ON, guide expression directly "
            "increases outcrossing via Bombus-mediated pollen transfer."
        ),
    ),
    BiologicalSwitch(
        name="selfing_syndrome_active",
        pathway_key="selfing_mediation",
        biological_question=(
            "Does reduced pollinator service trigger convergent selfing-syndrome evolution "
            "(reduced herkogamy, flower size, and guide expression)?"
        ),
        description=(
            "On isolated islands with simplified pollinator faunas, the reproductive "
            "assurance benefit of selfing may drive correlated evolution of the "
            "selfing syndrome: smaller flowers, reduced herkogamy, reduced guide "
            "expression. When ON, these traits co-evolve via a selfing feedback."
        ),
    ),
    BiologicalSwitch(
        name="island_isolation_common_cause",
        pathway_key="island_common_cause",
        biological_question=(
            "Does island isolation act as a common environmental cause driving multiple "
            "traits simultaneously, without a direct guide-pollinator link?"
        ),
        description=(
            "Island isolation may directly impoverish the pollinator fauna, reduce "
            "migration, and lower effective population size — all as downstream effects "
            "of a single upstream cause (isolation), rather than through selection on "
            "any single trait."
        ),
    ),
    # drift_drives_guide_loss (S4) REMOVED.
    # Ecological rationale: genetic drift is always operating in finite populations.
    # It is parameterised continuously via drift_strength (θ) and Ne (env),
    # not as a binary ON/OFF switch.  The null hypothesis (drift+env alone,
    # no selection) is represented by M0_null_selection (all switches OFF).
    BiologicalSwitch(
        name="small_pollinator_substitution",
        pathway_key="small_pollinator_pathway",
        biological_question=(
            "Can small halictid pollinators substitute for Bombus, maintaining "
            "sufficient outcrossing to oppose selfing-syndrome evolution?"
        ),
        description=(
            "Halictid bees are abundant on all Izu islands. If their outcrossing "
            "efficiency is high enough, they may prevent reproductive-assurance "
            "selfing from spreading even when Bombus is absent."
        ),
    ),
)


# ---------------------------------------------------------------------------
# Switch state sampling and conversion
# ---------------------------------------------------------------------------

def sample_switch_state(
    rng: random.Random,
    switches: Sequence[BiologicalSwitch] = CAMPANULA_SWITCHES,
) -> dict[str, bool]:
    """Sample a binary state for each switch from its prior.

    Parameters
    ----------
    rng:
        Caller-owned RNG for reproducibility.
    switches:
        Switch definitions.  Defaults to CAMPANULA_SWITCHES.

    Returns
    -------
    dict  {switch_name: True/False}
    """

    return {sw.name: rng.random() < sw.prior_on_prob for sw in switches}


def pathway_switches_from_state(
    state: dict[str, bool],
    switches: Sequence[BiologicalSwitch] = CAMPANULA_SWITCHES,
) -> PathwaySwitches:
    """Convert a binary switch state dict to a :class:`PathwaySwitches` object.

    ON  → 1.0 weight for the corresponding pathway.
    OFF → 0.0 weight.

    Parameters
    ----------
    state:
        Binary switch state from :func:`sample_switch_state`.
    switches:
        Switch definitions matching ``state`` keys.

    Returns
    -------
    PathwaySwitches
    """

    name_to_key = {sw.name: sw.pathway_key for sw in switches}
    key_to_value: dict[str, float] = {}
    for sw_name, is_on in state.items():
        key = name_to_key.get(sw_name)
        if key:
            key_to_value[key] = 1.0 if is_on else 0.0

    return PathwaySwitches(
        direct_pollinator_to_guide=key_to_value.get("direct_pollinator_to_guide", 0.0),
        selfing_mediation=key_to_value.get("selfing_mediation", 0.0),
        island_common_cause=key_to_value.get("island_common_cause", 0.0),
        small_pollinator_pathway=key_to_value.get("small_pollinator_pathway", 0.0),
    )


def switch_state_to_nearest_structure(state: dict[str, bool]) -> str:
    """Return the M1-M5 label nearest to a binary switch state.

    Useful for annotating accepted runs with their closest named structure.
    """

    dp = state.get("guide_attracts_bombus", False)
    sm = state.get("selfing_syndrome_active", False)
    ic = state.get("island_isolation_common_cause", False)

    if ic:
        return "M4_common_island_cause"
    if dp and sm:
        return "M3_direct_plus_mediated"
    if dp:
        return "M1_direct_pollinator_to_guide"
    if sm:
        return "M2_selfing_mediated"
    return "M0_null_selection"  # all-OFF = null (drift + env gradient only)


# ---------------------------------------------------------------------------
# Posterior summary
# ---------------------------------------------------------------------------

@dataclass
class SwitchPosteriorResult:
    """Summary of switch posterior inference.

    Attributes
    ----------
    accepted_rows:
        Full records for accepted samples, including switch states and distances.
    evaluated_rows:
        ALL evaluated rows (accepted + rejected), each with per_pattern_matched.
        Required for unbiased observation_contribution() (OC_k) computation:
        when pattern k is removed from y_obs some previously-rejected rows
        can cross the acceptance threshold and must be counted in the LOO set.
        If not stored by the backend, this equals accepted_rows (biased estimate).
    rejected_count:
        Total rejected samples (parameter constraint failures + ABC rejections).
    n_attempts:
        Total draws from the joint prior.
    posterior_table:
        One row per switch: P(ON|accepted), P(ON|prior), Bayes factor, etc.
    """

    accepted_rows: list[dict]
    evaluated_rows: list[dict]
    rejected_count: int
    n_attempts: int
    posterior_table: list[dict]

    @property
    def acceptance_rate(self) -> float:
        if self.n_attempts == 0:
            return 0.0
        return len(self.accepted_rows) / self.n_attempts


def compute_switch_posterior_table(
    accepted_rows: list[dict],
    switches: Sequence[BiologicalSwitch] = CAMPANULA_SWITCHES,
    weight_key: str | None = None,
) -> list[dict]:
    """Compute P(switch ON | accepted) for each switch.

    Also computes the Bayes factor relative to the prior:
        BF = P(ON|accepted) / P(OFF|accepted) / (prior_on / prior_off)
    BF > 1 → evidence that switch is ON supports pattern matching.
    BF < 1 → switch ON is evidence against matching (inhibitory).

    Parameters
    ----------
    accepted_rows:
        Accepted sample rows from inference.
    switches:
        Switch definitions.

    Returns
    -------
    list of dict
    """

    n = len(accepted_rows)
    if n == 0:
        return [
            {
                "switch": sw.name,
                "biological_question": sw.biological_question[:80],
                "P_prior_ON": sw.prior_on_prob,
                "P_posterior_ON": float("nan"),
                "Bayes_factor": float("nan"),
                "n_ON": 0,
                "n_accepted": 0,
                "interpretation": "no accepted samples",
            }
            for sw in switches
        ]

    weights = [
        max(0.0, float(r.get(weight_key, 1.0))) if weight_key else 1.0
        for r in accepted_rows
    ]
    total_weight = sum(weights) or float(n)

    rows = []
    for sw in switches:
        n_on = sum(1 for r in accepted_rows if r.get(sw.name))
        w_on = sum(w for r, w in zip(accepted_rows, weights) if r.get(sw.name))
        p_post = w_on / total_weight
        p_prior = sw.prior_on_prob

        # Bayes factor for ON vs OFF
        if p_post in (0.0, 1.0) or p_prior in (0.0, 1.0):
            bf = float("nan")
        else:
            posterior_odds = p_post / (1.0 - p_post)
            prior_odds = p_prior / (1.0 - p_prior)
            bf = posterior_odds / prior_odds

        # NaN check: float('nan') != float('nan') in Python, so `bf == bf`
        # is True iff bf is a valid (non-NaN) float.  The condition below
        # evaluates True for non-NaN floats (proceed to interpretation)
        # and False for NaN (fall through to "indeterminate").
        if not isinstance(bf, float) or (bf == bf):
            if bf > 3.0:
                interp = "supported (BF>3)"
            elif bf > 1.0:
                interp = "weakly supported"
            elif bf >= 0.33:
                interp = "neutral / weak evidence"
            elif bf > 0.0:
                interp = "weakly opposed"
            else:
                interp = "opposed (BF=0)"
        else:
            interp = "indeterminate"

        rows.append({
            "switch": sw.name,
            "biological_question": sw.biological_question[:80],
            "P_prior_ON": round(p_prior, 3),
            "P_posterior_ON": round(p_post, 4),
            "Bayes_factor": round(bf, 3) if bf == bf else None,
            "n_ON": n_on,
            "n_accepted": n,
            "posterior_weighted": bool(weight_key),
            "accepted_weight": round(total_weight, 4),
            "interpretation": interp,
        })
    return rows


# ---------------------------------------------------------------------------
# Pairwise co-activation table
# ---------------------------------------------------------------------------

def compute_coactivation_table(
    accepted_rows: list[dict],
    switches: Sequence[BiologicalSwitch] = CAMPANULA_SWITCHES,
) -> list[dict]:
    """Compute P(switch A ON AND switch B ON | accepted) for all pairs.

    High co-activation means the two pathways tend to be simultaneously active
    in parameter-space regions that reproduce observed patterns.

    Returns
    -------
    list of dict with columns: switch_A, switch_B, P_both_ON, P_A_ON, P_B_ON,
        conditional_B_given_A
    """

    n = len(accepted_rows)
    if n == 0:
        return []
    names = [sw.name for sw in switches]
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            p_a = sum(1 for r in accepted_rows if r.get(a)) / n
            p_b = sum(1 for r in accepted_rows if r.get(b)) / n
            p_both = sum(1 for r in accepted_rows if r.get(a) and r.get(b)) / n
            cond = p_both / p_a if p_a > 0 else float("nan")
            rows.append({
                "switch_A": a,
                "switch_B": b,
                "P_A_ON": round(p_a, 4),
                "P_B_ON": round(p_b, 4),
                "P_both_ON": round(p_both, 4),
                "P_B_given_A": round(cond, 4) if cond == cond else None,
            })
    return rows


# ---------------------------------------------------------------------------
# Main inference function
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Gradient POM acceptance thresholds  (single source of truth)
# ---------------------------------------------------------------------------
# POM = 6 gradient-direction patterns (4 gradient_slope + 2 rank_order).
# Bombus_distance removed — it was tautological (always matches because
# primary_pollinator_frequency is injected from the environment, not simulated).
#
# Rule name semantics (pattern-count-independent):
#   strict_all       → 1.000  (all patterns must match)
#   relaxed_0.83     → 5/6    (≥83% of patterns by weight)
#   relaxed_0.67     → 4/6    (≥67% of patterns by weight)
#   weighted_strict  → 1.000
#   weighted_lax     → 0.800
GRADIENT_THRESH_MAP: dict[str, float] = {
    "strict_all":      1.000,
    "relaxed_0.83":    5 / 6,
    "relaxed_0.67":    4 / 6,
    "weighted_strict": 1.000,
    "weighted_lax":    0.800,
}

# Number of response_target patterns (used for epsilon display in UI).
# Computed dynamically from observed_patterns.csv so the count stays in sync.
def _count_response_target_patterns() -> int:
    try:
        import csv as _csv
        from pathlib import Path as _Path
        _csv_path = (
            _Path(__file__).resolve().parent.parent
            / "examples" / "campanula_izu" / "data" / "observed_patterns.csv"
        )
        with open(_csv_path, newline="", encoding="utf-8") as f:
            return sum(
                1 for row in _csv.DictReader(f)
                if row.get("role", "observed_target") in ("observed_target", "response_target")
            )
    except Exception:
        return 6  # fallback to original count


GRADIENT_N_PATTERNS: int = _count_response_target_patterns()

CORE_REQUIRED_PATTERNS: tuple[str, ...] = ("selfing_distance", "flower_size_distance")


def _acceptance_threshold(acceptance_rule: str) -> float:
    """Map an ABC acceptance rule name to a minimum weighted_match_rate threshold."""
    return GRADIENT_THRESH_MAP.get(acceptance_rule, 1.000)


def select_adaptive_epsilon(
    distances: list[float],
    percentile: float = 5.0,
    min_accept: int = 20,
) -> dict:
    """Select an adaptive epsilon from evaluated distances.

    The percentile threshold is widened only enough to include ``min_accept``
    evaluated rows.  This is optional and should be interpreted as a stability
    device, not stronger empirical support.
    """
    vals = sorted(float(d) for d in distances if d is not None)
    if not vals:
        return {"epsilon": float("inf"), "n_accepted": 0, "warning": "no distances"}
    pct = max(0.0, min(100.0, float(percentile)))
    idx = int(round((pct / 100.0) * (len(vals) - 1)))
    idx = max(0, min(len(vals) - 1, idx))
    min_idx = max(0, min(len(vals) - 1, int(min_accept) - 1))
    chosen_idx = max(idx, min_idx)
    eps = vals[chosen_idx]
    n_acc = sum(1 for d in vals if d <= eps)
    warning = ""
    if chosen_idx > idx:
        warning = f"epsilon widened to satisfy min_accept={min_accept}"
    return {"epsilon": eps, "n_accepted": n_acc, "warning": warning}


def structure_prior_weight(row: dict, switches: Sequence[BiologicalSwitch], lam: float = 0.0) -> float:
    """Optional parsimony prior P(s) proportional to exp(-lambda * |s|)."""
    if lam <= 0:
        return 1.0
    n_on = sum(1 for sw in switches if bool(row.get(sw.name)))
    return math.exp(-float(lam) * n_on)


def _weighted_match_distance(matches) -> float:
    total_weight = sum(float(m.weight) for m in matches)
    if total_weight == 0:
        return 1.0
    mismatch = sum(float(m.weight) * (0.0 if m.matched else 1.0) for m in matches)
    return mismatch / total_weight


def _weighted_component_distance(matches) -> float:
    total_weight = sum(float(m.weight) for m in matches)
    if total_weight == 0:
        return 0.0
    total = 0.0
    for m in matches:
        component = m.distance if m.distance is not None else (0.0 if m.matched else 1.0)
        total += float(m.weight) * max(0.0, min(1.0, float(component)))
    return total / total_weight


def strict_core_soft_acceptance(
    eval_result,
    distance_mode: str,
    epsilon: float,
) -> dict:
    """Evaluate strict_all as core_required pass plus optional soft distance."""
    core = [m for m in eval_result.matches if m.pattern in CORE_REQUIRED_PATTERNS]
    core_names = {m.pattern for m in core}
    core_required_passed = (
        set(CORE_REQUIRED_PATTERNS) <= core_names
        and all(m.matched for m in core)
    )
    soft = [m for m in eval_result.matches if m.pattern not in CORE_REQUIRED_PATTERNS]
    if not soft:
        soft_distance = 0.0
    elif distance_mode == "match_rate":
        soft_distance = _weighted_match_distance(soft)
    else:
        soft_distance = _weighted_component_distance(soft)
    return {
        "core_required_passed": core_required_passed,
        "soft_distance": soft_distance,
        "accepted": core_required_passed and soft_distance <= epsilon,
    }


def run_switch_posterior_inference(
    preset_name: str,
    n_attempts: int,
    acceptance_rule: str,
    seed: int,
    switches: Sequence[BiologicalSwitch] = CAMPANULA_SWITCHES,
    progress_callback=None,  # callable(done, total, status_text) or None
    extra_pattern_rows: list[dict] | None = None,  # additional y_obs rows for NOV sim
    threshold: float | None = None,  # override acceptance threshold (default from acceptance_rule)
    distance_mode: str = "match_rate",
    epsilon_mode: str = "fixed",
    adaptive_percentile: float = 5.0,
    min_accept: int = 20,
    structure_prior_lambda: float = 0.0,
) -> SwitchPosteriorResult:
    """Run switch posterior inference via ABC rejection — 4-population gradient POM.

    WARNING — PROXY BACKEND: NOT A VALID RACH f(θ,s)
    -------------------------------------------------
    This function uses the deterministic phenomenological model
    (``causal_model.phenomenological_model.predict_traits_phenomenological``) as f(θ,s).
    The phenomenological model directly encodes theoretical relationships; switch posteriors
    from this function may reflect researcher assumptions rather than data.

    Use :func:`run_switch_posterior_inference_abm` for valid RACH inference
    using the stochastic individual-based ABM as the canonical f(θ,s).

    This function is retained for backward compatibility and fast diagnostic
    screening only.

    Evaluates 6 gradient-direction patterns (gradient_slope + rank_order,
    Bombus_distance excluded as tautological) across all simulated populations.
    Acceptance criterion: weighted_match_rate >= threshold (mapped from acceptance_rule).

    Parameters
    ----------
    preset_name:
        Name of the trade-off preset for ecological parameter sampling.
    n_attempts:
        Total joint draws from the (switch, parameter) prior.
    acceptance_rule:
        ABC acceptance rule name; mapped to a weighted_match_rate threshold.
    seed:
        RNG seed for reproducibility.
    switches:
        Switch definitions.  Defaults to CAMPANULA_SWITCHES.
    """

    from examples.campanula_izu.observed_data import (
        response_target_patterns,
    )
    from examples.campanula_izu.pattern_evaluator import (
        evaluate_patterns,
        multi_component_distance,
    )
    from examples.campanula_izu.campanula_phenomenological import (
        default_campanula_gradient_environments,
        simulate_campanula_gradient,
    )
    from attraction_trait_model.environment import Environment as _Env
    import math as _math

    rng = random.Random(seed)
    preset = predefined_tradeoff_presets()[preset_name]
    if threshold is None:
        threshold = _acceptance_threshold(acceptance_rule)

    # y_obs = observed_target patterns only (flower_size_distance: Inoue & Amano
    # 1986; selfing_distance: Inoue 1990a). nectar_guide (planned own-field),
    # Fis (pending independent genetics), and herkogamy (latent dichogamy,
    # protandrous species) are excluded, as are
    # hypothesis_prediction gradients — preventing circular inference.
    all_patterns = list(response_target_patterns())
    if extra_pattern_rows:
        all_patterns = all_patterns + list(extra_pattern_rows)

    constraint_passed, constraint_rejected = sample_all_sets_with_rejection_log(
        preset, n_attempts, seed=seed
    )

    import time as _time
    accepted_rows: list[dict] = []
    evaluated_rows: list[dict] = []   # ALL evaluated draws (accepted + rejected)
    total_steps = len(constraint_passed)
    t_start = _time.monotonic()

    for _step, param_set in enumerate(constraint_passed):
        model_params = param_set_to_model_parameters(param_set)
        env_slopes = env_slopes_from_param_set(param_set)   # θ: Ne/migration/pollinator slopes
        state = sample_switch_state(rng, switches)
        pw = pathway_switches_from_state(state, switches)

        # Rebuild named environments (mainland/Oshima/Kozushima/Hachijo) with sampled
        # θ slopes so Ne and migration_rate reflect each draw's θ.
        # Named populations are required: pairwise patterns look for "Oshima"/"Hachijo".
        _ne_slope = float(env_slopes.get("ne_isolation_slope", 0.765))
        _mig_rate = float(env_slopes.get("migration_decay_rate", 3.19))
        _base_envs = default_campanula_gradient_environments()
        _named_envs = {}
        for _pn, _be in _base_envs.items():
            _iso = _be.island_distance
            _mig = _be.migration_rate if _iso == 0.0 else 0.15 * _math.exp(-_mig_rate * _iso)
            _named_envs[_pn] = _Env(
                name=_pn,
                primary_pollinator_frequency=_be.primary_pollinator_frequency,
                background_pollinator_frequency=_be.background_pollinator_frequency,
                community_pollinator_abundance=_be.community_pollinator_abundance,
                migration_rate=_mig,
                island_distance=_iso,
                ne_isolation_slope=_ne_slope,
            )
        synth_pop_env = {
            _pn: {
                "isolation": _e.island_distance,
                "distance_from_mainland": round(_e.island_distance * 290.0, 1),
                "primary_pollinator_frequency": _e.primary_pollinator_frequency,
            }
            for _pn, _e in _named_envs.items()
        }

        try:
            outputs_dict = simulate_campanula_gradient(
                pw, params=model_params, environments=_named_envs
            )
            outputs_list = list(outputs_dict.values())
            eval_result = evaluate_patterns(outputs_list, all_patterns, synth_pop_env)
        except Exception:
            if progress_callback:
                _el = _time.monotonic() - t_start
                progress_callback(_step + 1, total_steps,
                    f"draw {_step+1}/{total_steps} · accepted: {len(accepted_rows)} · elapsed {_el:.0f}s")
            continue

        dist = multi_component_distance(eval_result, mode=distance_mode)
        fixed_epsilon = max(0.0, 1.0 - float(threshold))
        strict_parts = strict_core_soft_acceptance(eval_result, distance_mode, fixed_epsilon)
        accepted = (
            strict_parts["accepted"]
            if acceptance_rule == "strict_all"
            else (
                eval_result.weighted_match_rate >= threshold
                if distance_mode == "match_rate"
                else dist <= fixed_epsilon
            )
        )

        # Build relation strings for the 4 populations for diagnostics
        pop_trait_cols: dict = {}
        for pop, out in outputs_dict.items():
            for var in ("nectar_guide", "selfing_rate", "herkogamy", "flower_size", "Fis", "primary_pollinator_frequency"):
                pop_trait_cols[f"{pop}_{var}"] = round(getattr(out, var, float("nan")), 4)

        row = {
            "sample_id": str(uuid.uuid4()),
            "preset_name": preset_name,
            "backend": "proxy_causal",
            "nearest_structure": switch_state_to_nearest_structure(state),
            **state,
            **{p: param_set.get(p) for p in (
                "guide_cost", "outcrossing_benefit", "selfing_benefit",
                "inbreeding_depression", "background_pollinator_efficiency",
                "drift_strength", "direct_pollinator_guide_benefit",
                "cost_of_waiting_for_pollinators",
            )},
            "pattern_matches":          eval_result.n_matched,
            "pattern_total":            eval_result.n_total,
            "weighted_match_rate":      round(eval_result.weighted_match_rate, 4),
            "gradient_distance":        round(dist, 4),
            "distance_mode":            distance_mode,
            "epsilon_mode":             epsilon_mode,
            "epsilon":                  round(fixed_epsilon, 4),
            "acceptance_distance":       round(strict_parts["soft_distance"] if acceptance_rule == "strict_all" else dist, 4),
            "core_required_passed":      strict_parts["core_required_passed"],
            "soft_distance":             round(strict_parts["soft_distance"], 4),
            "accepted_by_epsilon":      accepted,
            "acceptance_rule":          acceptance_rule,
            "guide_tradeoff_class":     param_set.get("guide_tradeoff_class", ""),
            "selfing_tradeoff_class":   param_set.get("selfing_tradeoff_class", ""),
            # Per-pattern match data — used by identifiability.pattern_contribution()
            "per_pattern_matched": {m.pattern: (m.matched, m.weight)
                                    for m in eval_result.matches},
            "per_pattern_distance": {m.pattern: (m.distance if m.distance is not None else (0.0 if m.matched else 1.0), m.weight)
                                     for m in eval_result.matches},
            **pop_trait_cols,
        }

        # Store ALL evaluated rows (not only accepted).
        # evaluated_rows is required for unbiased OC_k via LOO:
        # removing pattern k can make previously-rejected rows cross the threshold.
        evaluated_rows.append(row)
        if epsilon_mode == "fixed" and accepted:
            accepted_rows.append(row)

        if progress_callback:
            _el = _time.monotonic() - t_start
            _done = _step + 1
            _eta = (_el / _done) * (total_steps - _done) if _done > 0 else 0
            progress_callback(
                _done, total_steps,
                f"draw {_done}/{total_steps} · "
                f"accepted: {len(accepted_rows)} · "
                f"elapsed {_el:.0f}s · ETA {_eta:.0f}s"
            )

    if epsilon_mode == "adaptive_percentile":
        selected = select_adaptive_epsilon(
            [r.get("acceptance_distance", r["gradient_distance"]) for r in evaluated_rows],
            percentile=adaptive_percentile,
            min_accept=min_accept,
        )
        eps = selected["epsilon"]
        for row in evaluated_rows:
            row["epsilon"] = round(eps, 4) if math.isfinite(eps) else eps
            row["accepted_by_epsilon"] = (
                bool(row.get("core_required_passed")) and row.get("soft_distance", row["gradient_distance"]) <= eps
                if acceptance_rule == "strict_all"
                else row["gradient_distance"] <= eps
            )
            row["adaptive_epsilon_warning"] = selected.get("warning", "")
        accepted_rows = [r for r in evaluated_rows if r["accepted_by_epsilon"]]

    for row in accepted_rows:
        row["structure_prior_weight"] = structure_prior_weight(row, switches, structure_prior_lambda)
        row["structure_prior_lambda"] = structure_prior_lambda

    rejected_count = len(constraint_rejected) + len(constraint_passed) - len(accepted_rows)
    posterior_table = compute_switch_posterior_table(
        accepted_rows, switches, weight_key="structure_prior_weight" if structure_prior_lambda > 0 else None
    )

    return SwitchPosteriorResult(
        accepted_rows=accepted_rows,
        evaluated_rows=evaluated_rows,
        rejected_count=rejected_count,
        n_attempts=n_attempts,
        posterior_table=posterior_table,
    )


# ---------------------------------------------------------------------------
# ABM helpers
# ---------------------------------------------------------------------------

def abm_outputs_to_relations(
    mean_oshima: dict[str, float],
    mean_hachijo: dict[str, float],
    tolerance: float = _ABM_RELATION_TOLERANCE,
) -> dict[str, str]:
    """Convert averaged ABM final-generation outputs to ordinal relation strings.

    DEPRECATED: hardcodes Campanula Izu population names (Oshima, Hachijo) in
    the framework layer. The active ABM inference path
    (run_switch_posterior_inference_abm) uses generic isolation-gradient
    populations (iso_0.000...iso_1.000) and does not call this function.
    Kept for backward compatibility only.

    Parameters
    ----------
    mean_oshima / mean_hachijo:
        Replicate-averaged final-generation summary dicts from simulate_population().
    tolerance:
        Minimum absolute difference to call a directional relation (default 0.05).

    Returns
    -------
    dict  {variable_name: relation_string}
        Keys match those expected by compute_run_distances() for pairwise patterns.
    """
    relations: dict[str, str] = {}
    for var, abm_key in _ABM_KEY_MAP.items():
        v_o = float(mean_oshima.get(abm_key, 0.5))
        v_h = float(mean_hachijo.get(abm_key, 0.5))
        diff = v_o - v_h
        if abs(diff) <= tolerance:
            relations[var] = "Oshima ~= Hachijo"
        elif diff > 0:
            relations[var] = "Oshima > Hachijo"
        else:
            relations[var] = "Oshima < Hachijo"
    # primary_pollinator_frequency is fixed by the environment — always matches
    b_o = _ABM_PRIMARY_POLL["Oshima"]
    b_h = _ABM_PRIMARY_POLL["Hachijo"]
    relations["primary_pollinator_frequency"] = (
        "Oshima > Hachijo" if b_o - b_h > tolerance
        else "Oshima < Hachijo" if b_h - b_o > tolerance
        else "Oshima ~= Hachijo"
    )
    return relations


def _average_replicate_finals(finals: list[dict]) -> dict[str, float]:
    """Average numeric values across replicate final-generation rows."""
    if not finals:
        return {}
    keys = [k for k in finals[0] if isinstance(finals[0][k], (int, float))]
    return {k: sum(float(r.get(k, 0)) for r in finals) / len(finals) for k in keys}


# ---------------------------------------------------------------------------
# ABM-backed switch posterior inference
# ---------------------------------------------------------------------------

def run_switch_posterior_inference_abm(
    preset_name: str,
    n_attempts: int,
    acceptance_rule: str,
    seed: int,
    generations: int = 40,
    population_size: int = 150,
    replicates: int = 3,
    switches: Sequence[BiologicalSwitch] = CAMPANULA_SWITCHES,
    progress_callback=None,  # callable(done, total, status_text) or None
    extra_pattern_rows: list[dict] | None = None,  # additional y_obs rows for NOV sim
    threshold: float | None = None,  # override acceptance threshold
    distance_mode: str = "match_rate",
    epsilon_mode: str = "fixed",
    adaptive_percentile: float = 5.0,
    min_accept: int = 20,
    structure_prior_lambda: float = 0.0,
) -> SwitchPosteriorResult:
    """Run switch posterior inference using the stochastic ABM backend.

    Algorithm (same ABC-rejection scheme as the proxy version):

    1. Sample binary switch state  s ~ Bernoulli(prior_on_prob)
    2. Sample latent parameters    θ ~ constrained trade-off prior
    3. Simulate ABM for Oshima and Hachijo independently (``replicates`` times each)
    4. Average replicates → mean final-generation trait values
    5. Convert to ordinal relations with tolerance=_ABM_RELATION_TOLERANCE
    6. ABC acceptance: accept if relation matches observed targets
    7. Posterior: P(switch ON | accepted)

    Why ABM gives sharper BFs than proxy
    -------------------------------------
    The proxy model is deterministic — a switch combination either always
    produces or never produces the correct relations.  This means many
    combinations are "always on the boundary", inflating acceptance rates.
    The stochastic ABM introduces population-level noise: a switch combination
    that is *marginally* effective will sometimes produce divergence above the
    tolerance threshold and sometimes not, depending on drift and stochastic
    pollinator visits.  This creates a continuous acceptance probability
    P(accept | switches, θ), sharpening the Bayes factors.

    Parameters
    ----------
    preset_name:
        Name of the trade-off preset for ecological parameter sampling.
    n_attempts:
        Total joint draws. ABM is ~20-100x slower than proxy; 100-300 is typical.
    acceptance_rule:
        ABC acceptance rule; passed to compute_run_distances.
    seed:
        RNG seed for reproducibility.
    generations:
        Number of evolutionary generations per ABM run. 30-50 is typical.
    population_size:
        Number of individual plants per ABM run. 100-200 is typical.
    replicates:
        ABM replicates per population per draw. Averaging over replicates
        reduces stochastic noise in the relation estimate. 3-5 recommended.
    switches:
        Switch definitions. Defaults to CAMPANULA_SWITCHES.

    Returns
    -------
    SwitchPosteriorResult
        Same structure as proxy version; compatible with all downstream UI.
    """

    from attraction_trait_model.simulation import simulate_population
    from attraction_trait_model.environment import Environment as _Env
    from examples.campanula_izu.observed_data import (
        response_target_patterns,
    )
    from examples.campanula_izu.pattern_evaluator import (
        ABMPopulationProxy,
        evaluate_patterns,
        multi_component_distance,
    )
    from examples.campanula_izu.campanula_phenomenological import (
        default_campanula_gradient_environments,
    )
    import math as _math

    rng = random.Random(seed)
    preset = predefined_tradeoff_presets()[preset_name]
    if threshold is None:
        threshold = _acceptance_threshold(acceptance_rule)

    # y_obs = observed_target patterns only (flower_size_distance: Inoue & Amano
    # 1986; selfing_distance: Inoue 1990a). nectar_guide (planned own-field),
    # Fis (pending independent genetics), and herkogamy (latent dichogamy,
    # protandrous species) are excluded, as are
    # hypothesis_prediction gradients — preventing circular inference.
    all_patterns = list(response_target_patterns())
    if extra_pattern_rows:
        all_patterns = all_patterns + list(extra_pattern_rows)

    constraint_passed, constraint_rejected = sample_all_sets_with_rejection_log(
        preset, n_attempts, seed=seed
    )

    import time as _time
    accepted_rows: list[dict] = []
    evaluated_rows: list[dict] = []   # ALL evaluated draws (accepted + rejected)
    total_steps = len(constraint_passed)
    t_start = _time.monotonic()

    for draw_idx, param_set in enumerate(constraint_passed):
        model_params = param_set_to_model_parameters(param_set)
        env_slopes = env_slopes_from_param_set(param_set)   # θ: Ne/migration/pollinator slopes

        # Rebuild named environments (mainland/Oshima/Kozushima/Hachijo) per draw.
        # Named populations required: pairwise patterns look for "Oshima"/"Hachijo".
        # Ne slope and migration_rate are updated from sampled θ; canonical pollinator
        # frequencies are kept from the literature-derived population defaults.
        _ne_slope = float(env_slopes.get("ne_isolation_slope", 0.765))
        _mig_rate = float(env_slopes.get("migration_decay_rate", 3.19))
        _base_envs = default_campanula_gradient_environments()
        _abm_envs: dict[str, _Env] = {}
        for _pn, _be in _base_envs.items():
            _iso = _be.island_distance
            _mig = _be.migration_rate if _iso == 0.0 else 0.15 * _math.exp(-_mig_rate * _iso)
            _abm_envs[_pn] = _Env(
                name=_pn,
                primary_pollinator_frequency=_be.primary_pollinator_frequency,
                background_pollinator_frequency=_be.background_pollinator_frequency,
                community_pollinator_abundance=_be.community_pollinator_abundance,
                migration_rate=_mig,
                island_distance=_iso,
                ne_isolation_slope=_ne_slope,
            )
        _abm_synth_pop_env = {
            name: {
                "isolation": env.island_distance,
                "distance_from_mainland": round(env.island_distance * 290.0, 1),
                "primary_pollinator_frequency": env.primary_pollinator_frequency,
            }
            for name, env in _abm_envs.items()
        }
        environments = _abm_envs

        state = sample_switch_state(rng, switches)
        pw = pathway_switches_from_state(state, switches)

        # Run ABM for all 4 gradient populations, averaging over replicates
        pop_finals: dict[str, dict[str, float]] = {}
        abm_failed = False
        for pop_idx, (pop_name, env) in enumerate(environments.items()):
            rep_finals: list[dict] = []
            for rep in range(replicates):
                run_seed = seed + draw_idx * 100_000 + pop_idx * 10_000 + rep * 1_000
                try:
                    rows = simulate_population(
                        env=env,
                        params=model_params,
                        switches=pw,
                        generations=generations,
                        population_size=population_size,
                        seed=run_seed,
                    )
                    if rows:
                        rep_finals.append(rows[-1])
                except Exception:
                    abm_failed = True
                    break
            if abm_failed or not rep_finals:
                abm_failed = True
                break
            avg = _average_replicate_finals(rep_finals)
            avg["primary_pollinator_frequency"] = env.primary_pollinator_frequency  # inject from environment
            pop_finals[pop_name] = avg

        if abm_failed or len(pop_finals) < 2:
            continue

        # Build ABMPopulationProxy objects for gradient pattern evaluation
        outputs_list = [
            ABMPopulationProxy(pop, final_dict, _abm_synth_pop_env.get(pop))
            for pop, final_dict in pop_finals.items()
        ]
        try:
            eval_result = evaluate_patterns(outputs_list, all_patterns, _abm_synth_pop_env)
        except Exception:
            continue

        dist = multi_component_distance(eval_result, mode=distance_mode)
        fixed_epsilon = max(0.0, 1.0 - float(threshold))
        strict_parts = strict_core_soft_acceptance(eval_result, distance_mode, fixed_epsilon)
        accepted = (
            strict_parts["accepted"]
            if acceptance_rule == "strict_all"
            else (
                eval_result.weighted_match_rate >= threshold
                if distance_mode == "match_rate"
                else dist <= fixed_epsilon
            )
        )

        pop_trait_cols: dict = {}
        for pop, fd in pop_finals.items():
            pop_trait_cols[f"{pop}_nectar_guide"]  = round(float(fd.get("mean_nectar_guide", float("nan"))), 4)
            pop_trait_cols[f"{pop}_selfing_rate"]  = round(float(fd.get("selfing_rate",      float("nan"))), 4)
            pop_trait_cols[f"{pop}_herkogamy"]     = round(float(fd.get("mean_herkogamy",    float("nan"))), 4)
            pop_trait_cols[f"{pop}_flower_size"]   = round(float(fd.get("mean_flower_size",  float("nan"))), 4)
            pop_trait_cols[f"{pop}_Fis"]           = round(float(fd.get("Fis_proxy",         float("nan"))), 4)
            pop_trait_cols[f"{pop}_primary_pollinator_frequency"] = round(float(fd.get("primary_pollinator_frequency", float("nan"))), 4)

        row = {
            "sample_id": str(uuid.uuid4()),
            "preset_name": preset_name,
            "backend": "stochastic_abm",
            "generations": generations,
            "population_size": population_size,
            "replicates": replicates,
            "nearest_structure": switch_state_to_nearest_structure(state),
            **state,
            **{p: param_set.get(p) for p in (
                "guide_cost", "outcrossing_benefit", "selfing_benefit",
                "inbreeding_depression", "background_pollinator_efficiency",
                "drift_strength", "direct_pollinator_guide_benefit",
                "cost_of_waiting_for_pollinators",
            )},
            "pattern_matches":        eval_result.n_matched,
            "pattern_total":          eval_result.n_total,
            "weighted_match_rate":    round(eval_result.weighted_match_rate, 4),
            "gradient_distance":      round(dist, 4),
            "distance_mode":          distance_mode,
            "epsilon_mode":           epsilon_mode,
            "epsilon":                round(fixed_epsilon, 4),
            "acceptance_distance":     round(strict_parts["soft_distance"] if acceptance_rule == "strict_all" else dist, 4),
            "core_required_passed":    strict_parts["core_required_passed"],
            "soft_distance":           round(strict_parts["soft_distance"], 4),
            "accepted_by_epsilon":    accepted,
            "acceptance_rule":        acceptance_rule,
            "guide_tradeoff_class":   param_set.get("guide_tradeoff_class", ""),
            "selfing_tradeoff_class": param_set.get("selfing_tradeoff_class", ""),
            # Per-pattern match data — used by identifiability.pattern_contribution()
            "per_pattern_matched": {m.pattern: (m.matched, m.weight)
                                    for m in eval_result.matches},
            "per_pattern_distance": {m.pattern: (m.distance if m.distance is not None else (0.0 if m.matched else 1.0), m.weight)
                                     for m in eval_result.matches},
            **pop_trait_cols,
        }

        # Store ALL evaluated rows for unbiased OC_k computation.
        evaluated_rows.append(row)
        if epsilon_mode == "fixed" and accepted:
            accepted_rows.append(row)

        if progress_callback:
            _el = _time.monotonic() - t_start
            _done = draw_idx + 1
            _eta = (_el / _done) * (total_steps - _done) if _done > 0 else 0
            progress_callback(
                _done, total_steps,
                f"ABM draw {_done}/{total_steps} · "
                f"accepted: {len(accepted_rows)} · "
                f"elapsed {_el:.0f}s · ETA {_eta:.0f}s"
            )

    if epsilon_mode == "adaptive_percentile":
        selected = select_adaptive_epsilon(
            [r.get("acceptance_distance", r["gradient_distance"]) for r in evaluated_rows],
            percentile=adaptive_percentile,
            min_accept=min_accept,
        )
        eps = selected["epsilon"]
        for row in evaluated_rows:
            row["epsilon"] = round(eps, 4) if math.isfinite(eps) else eps
            row["accepted_by_epsilon"] = (
                bool(row.get("core_required_passed")) and row.get("soft_distance", row["gradient_distance"]) <= eps
                if acceptance_rule == "strict_all"
                else row["gradient_distance"] <= eps
            )
            row["adaptive_epsilon_warning"] = selected.get("warning", "")
        accepted_rows = [r for r in evaluated_rows if r["accepted_by_epsilon"]]

    for row in accepted_rows:
        row["structure_prior_weight"] = structure_prior_weight(row, switches, structure_prior_lambda)
        row["structure_prior_lambda"] = structure_prior_lambda

    rejected_count = (
        len(constraint_rejected) + len(constraint_passed) - len(accepted_rows)
    )
    posterior_table = compute_switch_posterior_table(
        accepted_rows, switches, weight_key="structure_prior_weight" if structure_prior_lambda > 0 else None
    )

    return SwitchPosteriorResult(
        accepted_rows=accepted_rows,
        evaluated_rows=evaluated_rows,
        rejected_count=rejected_count,
        n_attempts=n_attempts,
        posterior_table=posterior_table,
    )
