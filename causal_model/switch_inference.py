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

    M1  direct_pollinator_to_guide=1  selfing_mediation=0  island_common_cause=0  drift_null=0
    M2  direct_pollinator_to_guide=0  selfing_mediation=1  island_common_cause=0  drift_null=0
    M3  direct_pollinator_to_guide=1  selfing_mediation=1  island_common_cause=0  drift_null=0
    M4  direct_pollinator_to_guide=~  selfing_mediation=~  island_common_cause=1  drift_null=~
    M5  direct_pollinator_to_guide=0  selfing_mediation=0  island_common_cause=0  drift_null=1

The switch posterior subsumes and extends structure ranking.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Sequence

from causal_model.abc_distance import compute_run_distances
from causal_model.parameter_constraints import (
    predefined_tradeoff_presets,
    sample_all_sets_with_rejection_log,
)
from causal_model.parameter_sampling import param_set_to_model_parameters
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

# Bombus_frequency is environmental (always matches observed); inject directly.
_ABM_BOMBUS: dict[str, float] = {"Oshima": 0.35, "Hachijo": 0.00}

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
    BiologicalSwitch(
        name="drift_drives_guide_loss",
        pathway_key="drift_null",
        biological_question=(
            "Is guide loss on isolated islands primarily stochastic (genetic drift in "
            "small populations) rather than driven by natural selection?"
        ),
        description=(
            "Small effective population size on isolated islands amplifies genetic "
            "drift. If guide expression is selectively neutral or nearly neutral, "
            "loss may occur by drift alone, independent of pollinator service. "
            "This is the null hypothesis."
        ),
    ),
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
        drift_null=key_to_value.get("drift_null", 0.0),
        small_pollinator_pathway=key_to_value.get("small_pollinator_pathway", 0.0),
    )


def switch_state_to_nearest_structure(state: dict[str, bool]) -> str:
    """Return the M1-M5 label nearest to a binary switch state.

    Useful for annotating accepted runs with their closest named structure.
    """

    dp = state.get("guide_attracts_bombus", False)
    sm = state.get("selfing_syndrome_active", False)
    ic = state.get("island_isolation_common_cause", False)
    dn = state.get("drift_drives_guide_loss", False)

    if ic:
        return "M4_common_island_cause"
    if dn and not dp and not sm:
        return "M5_drift_null"
    if dp and sm:
        return "M3_direct_plus_mediated"
    if dp:
        return "M1_direct_pollinator_to_guide"
    if sm:
        return "M2_selfing_mediated"
    return "M5_drift_null"  # all-OFF ≈ null


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
    rejected_count:
        Total rejected samples (parameter constraint failures + ABC rejections).
    n_attempts:
        Total draws from the joint prior.
    posterior_table:
        One row per switch: P(ON|accepted), P(ON|prior), Bayes factor, etc.
    """

    accepted_rows: list[dict]
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

    rows = []
    for sw in switches:
        n_on = sum(1 for r in accepted_rows if r.get(sw.name))
        p_post = n_on / n
        p_prior = sw.prior_on_prob

        # Bayes factor for ON vs OFF
        if p_post in (0.0, 1.0) or p_prior in (0.0, 1.0):
            bf = float("nan")
        else:
            posterior_odds = p_post / (1.0 - p_post)
            prior_odds = p_prior / (1.0 - p_prior)
            bf = posterior_odds / prior_odds

        if not isinstance(bf, float) or (bf == bf):  # not nan
            if bf > 3.0:
                interp = "supported (BF>3)"
            elif bf > 1.0:
                interp = "weakly supported"
            elif bf > 0.33:
                interp = "weakly opposed"
            else:
                interp = "opposed (BF<1/3)"
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
# Bombus_frequency is injected from the environment, not simulated).
#
# Rule name semantics (for the 6-pattern gradient POM):
#   strict_all       → 1.000  (all 6 must match by weight)
#   relaxed_5_of_6   → 5/6    (≥5/6 weighted)
#   relaxed_4_of_6   → 4/6    (≥4/6 weighted)
#   weighted_strict  → 1.000
#   weighted_lax     → 0.800
#
# Kept under legacy names ("strict_6_of_6" etc.) so existing UI widgets
# and CSV exports remain unchanged.
GRADIENT_THRESH_MAP: dict[str, float] = {
    "strict_6_of_6":   1.000,
    "relaxed_5_of_6":  5 / 6,
    "relaxed_4_of_6":  4 / 6,
    "weighted_strict": 1.000,
    "weighted_lax":    0.800,
}

# Number of gradient POM patterns (used for epsilon display in UI)
GRADIENT_N_PATTERNS: int = 6


def _acceptance_threshold(acceptance_rule: str) -> float:
    """Map an ABC acceptance rule name to a minimum weighted_match_rate threshold."""
    return GRADIENT_THRESH_MAP.get(acceptance_rule, 1.000)


def run_switch_posterior_inference(
    preset_name: str,
    n_attempts: int,
    acceptance_rule: str,
    seed: int,
    observed_rels: dict[str, str],   # kept for API compat; not used for gradient eval
    pattern_weights: dict[str, float],  # kept for API compat
    switches: Sequence[BiologicalSwitch] = CAMPANULA_SWITCHES,
    progress_callback=None,  # callable(done, total, status_text) or None
) -> SwitchPosteriorResult:
    """Run switch posterior inference via ABC rejection — 4-population gradient POM.

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
    observed_rels / pattern_weights:
        Kept for backward-compatible call signature; gradient evaluation uses
        load_observed_pattern_table() and load_population_env() directly.
    switches:
        Switch definitions.  Defaults to CAMPANULA_SWITCHES.
    """

    from examples.campanula_izu.observed_data import (
        observed_gradient_only_patterns,
    )
    from examples.campanula_izu.pattern_evaluator import (
        evaluate_patterns,
        weighted_pattern_distance,
    )
    from examples.campanula_izu.proxy_simulation import (
        simulate_campanula_isolation_gradient,
    )

    rng = random.Random(seed)
    preset = predefined_tradeoff_presets()[preset_name]
    threshold = _acceptance_threshold(acceptance_rule)

    # POM = gradient-direction patterns only (gradient_slope + rank_order).
    # The simulation uses a continuous isolation gradient (no named populations).
    all_patterns = observed_gradient_only_patterns()

    constraint_passed, constraint_rejected = sample_all_sets_with_rejection_log(
        preset, n_attempts, seed=seed
    )

    import time as _time
    accepted_rows: list[dict] = []
    total_steps = len(constraint_passed)
    t_start = _time.monotonic()

    for _step, param_set in enumerate(constraint_passed):
        model_params = param_set_to_model_parameters(param_set)
        state = sample_switch_state(rng, switches)
        pw = pathway_switches_from_state(state, switches)

        try:
            outputs_dict, synth_pop_env = simulate_campanula_isolation_gradient(
                pw, params=model_params, n_points=8,
            )
            outputs_list = list(outputs_dict.values())
            eval_result = evaluate_patterns(outputs_list, all_patterns, synth_pop_env)
        except Exception:
            if progress_callback:
                _el = _time.monotonic() - t_start
                progress_callback(_step + 1, total_steps,
                    f"draw {_step+1}/{total_steps} · accepted: {len(accepted_rows)} · elapsed {_el:.0f}s")
            continue

        dist = weighted_pattern_distance(eval_result)
        accepted = eval_result.weighted_match_rate >= threshold

        # Build relation strings for the 4 populations for diagnostics
        pop_trait_cols: dict = {}
        for pop, out in outputs_dict.items():
            for var in ("nectar_guide", "selfing_rate", "herkogamy", "flower_size", "Fis", "Bombus_frequency"):
                pop_trait_cols[f"{pop}_{var}"] = round(getattr(out, var, float("nan")), 4)

        row = {
            "sample_id": str(uuid.uuid4()),
            "preset_name": preset_name,
            "backend": "proxy_causal",
            "nearest_structure": switch_state_to_nearest_structure(state),
            **state,
            **{p: param_set.get(p) for p in (
                "guide_cost", "outcrossing_benefit", "selfing_benefit",
                "inbreeding_depression", "small_pollinator_efficiency",
                "drift_strength", "direct_pollinator_guide_benefit",
                "cost_of_waiting_for_pollinators",
            )},
            "pattern_matches":          eval_result.n_matched,
            "pattern_total":            eval_result.n_total,
            "weighted_match_rate":      round(eval_result.weighted_match_rate, 4),
            "gradient_distance":        round(dist, 4),
            "accepted_by_epsilon":      accepted,
            "acceptance_rule":          acceptance_rule,
            "guide_tradeoff_class":     param_set.get("guide_tradeoff_class", ""),
            "selfing_tradeoff_class":   param_set.get("selfing_tradeoff_class", ""),
            **pop_trait_cols,
        }

        if accepted:
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

    rejected_count = len(constraint_rejected) + len(constraint_passed) - len(accepted_rows)
    posterior_table = compute_switch_posterior_table(accepted_rows, switches)

    return SwitchPosteriorResult(
        accepted_rows=accepted_rows,
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
    # Bombus_frequency is fixed by the environment — always matches
    b_o = _ABM_BOMBUS["Oshima"]
    b_h = _ABM_BOMBUS["Hachijo"]
    relations["Bombus_frequency"] = (
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
    observed_rels: dict[str, str],
    pattern_weights: dict[str, float],
    generations: int = 40,
    population_size: int = 150,
    replicates: int = 3,
    switches: Sequence[BiologicalSwitch] = CAMPANULA_SWITCHES,
    progress_callback=None,  # callable(done, total, status_text) or None
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
    observed_rels:
        {variable_name: relation_string} from empirical data.
    pattern_weights:
        {variable_name: weight} for weighted ABC distance.
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
    from examples.campanula_izu.observed_data import (
        observed_gradient_only_patterns,
    )
    from examples.campanula_izu.pattern_evaluator import (
        ABMPopulationProxy,
        evaluate_patterns,
        weighted_pattern_distance,
    )
    from examples.campanula_izu.proxy_simulation import (
        env_from_isolation,
    )

    rng = random.Random(seed)
    preset = predefined_tradeoff_presets()[preset_name]
    threshold = _acceptance_threshold(acceptance_rule)

    # POM = gradient-direction patterns only (island syndrome gradient).
    all_patterns = observed_gradient_only_patterns()

    # Build a continuous isolation gradient (4 points for ABM performance).
    _abm_n_points = 4
    _abm_iso_values = [i / (_abm_n_points - 1) for i in range(_abm_n_points)]
    _abm_envs = {f"iso_{iso:.3f}": env_from_isolation(iso) for iso in _abm_iso_values}
    _abm_synth_pop_env = {
        name: {
            "isolation": env.island_distance,
            "distance_from_mainland": round(env.island_distance * 290.0, 1),
            "Bombus_frequency": env.bombus_frequency,
        }
        for name, env in _abm_envs.items()
    }
    environments = _abm_envs

    constraint_passed, constraint_rejected = sample_all_sets_with_rejection_log(
        preset, n_attempts, seed=seed
    )

    import time as _time
    accepted_rows: list[dict] = []
    total_steps = len(constraint_passed)
    t_start = _time.monotonic()

    for draw_idx, param_set in enumerate(constraint_passed):
        model_params = param_set_to_model_parameters(param_set)
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
            avg["Bombus_frequency"] = env.bombus_frequency  # inject from environment
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

        dist = weighted_pattern_distance(eval_result)
        accepted = eval_result.weighted_match_rate >= threshold

        pop_trait_cols: dict = {}
        for pop, fd in pop_finals.items():
            pop_trait_cols[f"{pop}_nectar_guide"]  = round(float(fd.get("mean_nectar_guide", float("nan"))), 4)
            pop_trait_cols[f"{pop}_selfing_rate"]  = round(float(fd.get("selfing_rate",      float("nan"))), 4)
            pop_trait_cols[f"{pop}_herkogamy"]     = round(float(fd.get("mean_herkogamy",    float("nan"))), 4)
            pop_trait_cols[f"{pop}_flower_size"]   = round(float(fd.get("mean_flower_size",  float("nan"))), 4)
            pop_trait_cols[f"{pop}_Fis"]           = round(float(fd.get("Fis_proxy",         float("nan"))), 4)
            pop_trait_cols[f"{pop}_Bombus_frequency"] = round(float(fd.get("Bombus_frequency", float("nan"))), 4)

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
                "inbreeding_depression", "small_pollinator_efficiency",
                "drift_strength", "direct_pollinator_guide_benefit",
                "cost_of_waiting_for_pollinators",
            )},
            "pattern_matches":        eval_result.n_matched,
            "pattern_total":          eval_result.n_total,
            "weighted_match_rate":    round(eval_result.weighted_match_rate, 4),
            "gradient_distance":      round(dist, 4),
            "accepted_by_epsilon":    accepted,
            "acceptance_rule":        acceptance_rule,
            "guide_tradeoff_class":   param_set.get("guide_tradeoff_class", ""),
            "selfing_tradeoff_class": param_set.get("selfing_tradeoff_class", ""),
            **pop_trait_cols,
        }

        if accepted:
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

    rejected_count = (
        len(constraint_rejected) + len(constraint_passed) - len(accepted_rows)
    )
    posterior_table = compute_switch_posterior_table(accepted_rows, switches)

    return SwitchPosteriorResult(
        accepted_rows=accepted_rows,
        rejected_count=rejected_count,
        n_attempts=n_attempts,
        posterior_table=posterior_table,
    )
