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

def run_switch_posterior_inference(
    preset_name: str,
    n_attempts: int,
    acceptance_rule: str,
    seed: int,
    observed_rels: dict[str, str],
    pattern_weights: dict[str, float],
    switches: Sequence[BiologicalSwitch] = CAMPANULA_SWITCHES,
) -> SwitchPosteriorResult:
    """Run switch posterior inference via ABC rejection.

    Jointly samples binary switch states and continuous ecological parameters,
    simulates the proxy model, and retains samples where the simulated
    Oshima-Hachijo relations match the observed pattern targets.

    Parameters
    ----------
    preset_name:
        Name of the trade-off preset for ecological parameter sampling.
    n_attempts:
        Total joint draws from the (switch, parameter) prior.
    acceptance_rule:
        ABC acceptance rule name; passed to compute_run_distances.
    seed:
        RNG seed for reproducibility.
    observed_rels:
        {pattern_name: relation_string} from empirical data.
    pattern_weights:
        {pattern_name: weight} for weighted ABC distance.
    switches:
        Switch definitions.  Defaults to CAMPANULA_SWITCHES.

    Returns
    -------
    SwitchPosteriorResult
    """

    # Import here to avoid circular dependency at module level
    from examples.campanula_izu.proxy_simulation import (
        default_campanula_proxy_environments,
        simulate_campanula_with_switches,
    )

    rng = random.Random(seed)
    preset = predefined_tradeoff_presets()[preset_name]

    # Draw all parameter sets with constraint filtering first
    constraint_passed, constraint_rejected = sample_all_sets_with_rejection_log(
        preset, n_attempts, seed=seed
    )

    accepted_rows: list[dict] = []
    total_abc_attempts = 0

    for param_set in constraint_passed:
        total_abc_attempts += 1
        model_params = param_set_to_model_parameters(param_set)

        # Sample switch state from joint prior
        state = sample_switch_state(rng, switches)
        pw = pathway_switches_from_state(state, switches)

        # Simulate with these switches
        try:
            rels, _ = simulate_campanula_with_switches(pw, params=model_params)
        except Exception:
            continue

        # ABC distance
        dist_metrics = compute_run_distances(
            observed_rels=observed_rels,
            simulated_rels=rels,
            weights=pattern_weights,
            rule=acceptance_rule,
        )

        row = {
            "sample_id": str(uuid.uuid4()),
            "preset_name": preset_name,
            "nearest_structure": switch_state_to_nearest_structure(state),
            **state,
            **{p: param_set.get(p) for p in (
                "guide_cost", "outcrossing_benefit", "selfing_benefit",
                "inbreeding_depression", "small_pollinator_efficiency",
                "drift_strength", "direct_pollinator_guide_benefit",
                "cost_of_waiting_for_pollinators",
            )},
            **dist_metrics,
            **{f"relation_{k}": v for k, v in rels.items()},
            "guide_tradeoff_class": param_set.get("guide_tradeoff_class", ""),
            "selfing_tradeoff_class": param_set.get("selfing_tradeoff_class", ""),
        }

        if dist_metrics["accepted_by_epsilon"]:
            accepted_rows.append(row)

    rejected_count = len(constraint_rejected) + (total_abc_attempts - len(accepted_rows))
    posterior_table = compute_switch_posterior_table(accepted_rows, switches)

    return SwitchPosteriorResult(
        accepted_rows=accepted_rows,
        rejected_count=rejected_count,
        n_attempts=n_attempts,
        posterior_table=posterior_table,
    )
