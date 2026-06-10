"""Streamlit app for RACH: Restricted Admissible Causal Hypotheses.

Workflow
--------
1. Constrain  -- ecological constraint grammar rejects implausible latent parameter combos
2. Sample     -- random draws from ecology-principled trade-off priors
3. Simulate   -- stochastic ABM: the canonical RACH f(θ,s) for this system
4. Filter     -- ABC rejection against observable gradient pattern targets (response_target only)
5. Retain     -- restricted admissible causal hypotheses + compatible parameter ranges
6. Infer switches -- PathwaySwitch posterior: which biological mechanisms are active?

Reference: Inoue & Amano (1986) -- pollinator change and breeding system evolution, Izu Islands.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any

_ROOT = pathlib.Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from attraction_trait_model.simulation import simulate_population
from causal_model.abc_distance import (
    available_rules,
    compute_run_distances,
    epsilon_for_rule,
)
from causal_model.switch_inference import GRADIENT_THRESH_MAP  # single source of truth
from causal_model.parameter_constraints import (
    LITERATURE_SOURCES,
    predefined_tradeoff_presets,
    sample_all_sets_with_rejection_log,
)
from causal_model.parameter_sampling import (
    param_set_to_model_parameters,
    env_slopes_from_param_set,
)
from causal_model.range_summary import summarize_parameter_ranges
from causal_model.switch_inference import (
    CAMPANULA_SWITCHES,
    compute_coactivation_table,
    run_switch_posterior_inference_abm,
)
from causal_model.switches import switches_for_structure
from examples.campanula_izu.causal_structures import campanula_causal_structures
from examples.campanula_izu.observed_data import (
    load_observed_pattern_table,
    load_observed_patterns,
    load_pattern_weights,
    load_population_env,
    observed_gradient_only_patterns,
    observed_gradient_patterns,
    observed_pairwise_relations,
    ordered_populations,
    response_target_patterns,
)
from examples.campanula_izu.pattern_evaluator import (
    ABMPopulationProxy,
    EvaluationResult,
    evaluate_patterns,
    weighted_pattern_distance,
)
from examples.campanula_izu.campanula_phenomenological import (
    default_campanula_gradient_environments,
    env_from_isolation,
    simulate_campanula_gradient,
    simulate_campanula_isolation_gradient,
)

st.set_page_config(
    page_title="RACH -- Campanula / Izu Islands",
    layout="wide",
    page_icon=":telescope:",
)

# ---------------------------------------------------------------------------
# Observed patterns
# ---------------------------------------------------------------------------
try:
    _OBS_TABLE = load_observed_pattern_table()
    OBSERVED_RELS = load_observed_patterns()
    PATTERN_WEIGHTS = load_pattern_weights()
except Exception:
    OBSERVED_RELS = {
        "nectar_guide": "Oshima > Hachijo",
        "selfing_rate": "Oshima < Hachijo",
        "herkogamy": "Oshima > Hachijo",
        "flower_size": "Oshima > Hachijo",
        "Fis": "Oshima < Hachijo",
        "primary_pollinator_frequency": "Oshima > Hachijo",
    }
    PATTERN_WEIGHTS = {k: 1.0 for k in OBSERVED_RELS}
    _OBS_TABLE = [
        {"pattern": k, "relation": v, "weight": "1.0",
         "source": "hard-coded fallback", "notes": ""}
        for k, v in OBSERVED_RELS.items()
    ]

# ---------------------------------------------------------------------------
# Gradient / multi-population data
# ---------------------------------------------------------------------------
try:
    _POP_ENV = load_population_env()
    _GRADIENT_PATTERNS = observed_gradient_patterns()
    _PAIRWISE_RELS = observed_pairwise_relations()
    _POP_ORDER = ordered_populations()
except Exception:
    _POP_ENV = {}
    _GRADIENT_PATTERNS = []
    _PAIRWISE_RELS = {}
    _POP_ORDER = ["mainland", "Oshima", "Kozushima", "Hachijo"]

LATENT_PARAMS = [
    "guide_cost",
    "outcrossing_benefit",
    "selfing_benefit",
    "inbreeding_depression",
    "background_pollinator_efficiency",
    "drift_strength",
    "direct_pollinator_guide_benefit",
    "cost_of_waiting_for_pollinators",
]

WORKFLOW_STEPS = [
    {"Step": "1. Constrain",   "RACH object": "G(θ)",      "Meaning": "Ecological constraint grammar — biological feasibility constraints on θ. Implausible parameter combinations are rejected before simulation."},
    {"Step": "2. Sample",      "RACH object": "θ ~ prior",  "Meaning": "Draw latent parameters θ (benefit/cost trade-offs, env slopes) from ecology-principled priors. Also sample causal switch states s ∈ {0,1}^K."},
    {"Step": "3. Simulate",    "RACH object": "f(x_obs;θ,s)", "Meaning": "Run generative dynamics with fixed empirical context x_obs (island distance, Bombus presence) and sampled (θ,s). Stochastic ABM is the canonical f for this example."},
    {"Step": "4. Accept",      "RACH object": "d ≤ ε",      "Meaning": "Accept if simulated patterns P_sim match independent observations y_obs (5 field-derived pairwise patterns, Inoue 1986) within tolerance ε. hypothesis_prediction and input_context rows excluded."},
    {"Step": "5. A_ε",         "RACH object": "A_ε(y_obs,x_obs)", "Meaning": "The admissible causal region: all (θ,s) that satisfy G(θ)=1 and d≤ε. This is the core RACH inferential object."},
    {"Step": "6. Quantify",    "RACH object": "CA_j, D, R, OC_k, NOV", "Meaning": "Compute the 5 core RACH quantities from A_ε: causal admissibility, degeneracy, resolvability, observation contribution, next-observation value."},
]

BACKEND_DESCRIPTIONS = {
    "stochastic_abm": (
        "Stochastic individual-based ABM — the canonical RACH f(θ,s) for this system. "
        "Models heritable trait evolution, drift, selection, and reproduction "
        "explicitly across generations. Switch posteriors P(S|A_ε) reflect "
        "emergent population dynamics, not hand-coded assumptions."
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def stretch_df(df: pd.DataFrame, **kwargs) -> None:
    st.dataframe(df, width="stretch", **kwargs)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _run_tag(settings: dict) -> str:
    """Short tag for file names: YYYYMMDD_HHMMSS_preset_seed_rule."""
    import datetime
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    preset = settings.get("preset_name", "unknown").replace("_", "")[:12]
    seed   = settings.get("seed", 0)
    rule   = settings.get("acceptance_rule", "unknown").replace("_", "").replace(".", "")[:10]
    return f"{ts}_{preset}_s{seed}_{rule}"


def _build_zip(files: dict[str, pd.DataFrame]) -> bytes:
    """Pack multiple DataFrames into an in-memory ZIP.

    Parameters
    ----------
    files : {filename_without_ext: DataFrame}
    """
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, df in files.items():
            if df is not None and not df.empty:
                zf.writestr(f"{name}.csv", df.to_csv(index=False).encode("utf-8"))
    return buf.getvalue()


def relation_from_values(
    left_name: str, left_value: float,
    right_name: str, right_value: float,
    tolerance: float = 0.03,
) -> str:
    if abs(left_value - right_value) <= tolerance:
        return f"{left_name} ~= {right_name}"
    if left_value > right_value:
        return f"{left_name} > {right_name}"
    return f"{left_name} < {right_name}"


def final_abm_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "mean_nectar_guide": 0.0, "selfing_rate": 0.0,
            "mean_herkogamy": 0.0, "mean_flower_size": 0.0, "Fis_proxy": 0.0,
        }
    return rows[-1]


def average_summaries(summaries: list[dict[str, Any]]) -> dict[str, float]:
    numeric_keys = [
        "mean_nectar_guide", "selfing_rate", "mean_herkogamy",
        "mean_flower_size", "Fis_proxy", "outcrossing_rate",
        "failed_rate", "mean_fitness", "mean_selfing_ability", "mean_neutral_diversity",
    ]
    if not summaries:
        return {key: 0.0 for key in numeric_keys}
    return {
        key: sum(float(row.get(key, 0.0)) for row in summaries) / len(summaries)
        for key in numeric_keys
    }


# ---------------------------------------------------------------------------
# Gradient trait columns helper
# ---------------------------------------------------------------------------

_GRAD_VARS = ["nectar_guide", "selfing_rate", "herkogamy", "flower_size", "Fis", "primary_pollinator_frequency"]
_GRAD_POPS = ["mainland", "Oshima", "Kozushima", "Hachijo"]


def _gradient_columns(outputs_by_pop: dict[str, Any], abm: bool = False) -> dict[str, float]:
    """Return per-population trait values as flat columns for the run row.

    Keys: e.g. 'mainland_nectar_guide', 'Oshima_selfing_rate', ...
    Works with both PhenomenologicalOutput objects and plain dicts (ABM).
    """
    cols: dict[str, float] = {}
    _abm_map = {
        "nectar_guide": "mean_nectar_guide",
        "selfing_rate": "selfing_rate",
        "herkogamy": "mean_herkogamy",
        "flower_size": "mean_flower_size",
        "Fis": "Fis_proxy",
        "primary_pollinator_frequency": "primary_pollinator_frequency",
    }
    for pop in _GRAD_POPS:
        out = outputs_by_pop.get(pop)
        if out is None:
            for var in _GRAD_VARS:
                cols[f"{pop}_{var}"] = float("nan")
            continue
        for var in _GRAD_VARS:
            if abm:
                key = _abm_map.get(var, var)
                val = float(out.get(key, float("nan"))) if isinstance(out, dict) else float(getattr(out, var, float("nan")))
            else:
                val = float(getattr(out, var, float("nan")))
            cols[f"{pop}_{var}"] = round(val, 4)
    return cols


# ---------------------------------------------------------------------------
# Simulation backends
# ---------------------------------------------------------------------------

def simulate_structure_proxy(
    structure, model_params, env_slopes: dict | None = None
) -> tuple[dict, dict[str, Any]]:
    """Run proxy simulation on the four named gradient populations.

    Uses simulate_campanula_gradient() so outputs are keyed by
    "mainland" / "Oshima" / "Kozushima" / "Hachijo" — matching
    the pairwise pattern population names used by evaluate_patterns().

    env_slopes (optional dict with keys ne_isolation_slope,
    migration_decay_rate, pollinator_loss_slope) is used to rebuild
    environments with the sampled θ slope values instead of defaults.
    """
    import math as _math
    from attraction_trait_model.environment import Environment
    from causal_model.switches import switches_for_structure as _sfs

    _sw = _sfs(structure.name)
    env_slopes = env_slopes or {}
    _ne_slope  = float(env_slopes.get("ne_isolation_slope",   0.765))
    _mig_rate  = float(env_slopes.get("migration_decay_rate", 3.19))
    _pol_slope = float(env_slopes.get("pollinator_loss_slope", 0.94))

    # Rebuild named environments with sampled θ slopes.
    # Canonical pollinator frequencies are kept from the literature-derived
    # defaults; only Ne (via ne_isolation_slope) and migration_rate
    # (via migration_decay_rate) are updated per draw.
    _base = default_campanula_gradient_environments()
    named_envs: dict[str, Environment] = {}
    for pop_name, base_env in _base.items():
        iso = base_env.island_distance
        mig = base_env.migration_rate if iso == 0.0 else (
            0.15 * _math.exp(-_mig_rate * iso)
        )
        named_envs[pop_name] = Environment(
            name=pop_name,
            primary_pollinator_frequency=base_env.primary_pollinator_frequency,
            background_pollinator_frequency=base_env.background_pollinator_frequency,
            community_pollinator_abundance=base_env.community_pollinator_abundance,
            migration_rate=mig,
            island_distance=iso,
            ne_isolation_slope=_ne_slope,
        )

    outputs_dict = simulate_campanula_gradient(_sw, params=model_params, environments=named_envs)
    outputs_list = list(outputs_dict.values())

    # Synthetic env table used by gradient_slope pattern evaluator
    synth_pop_env = {
        pop_name: {
            "isolation": env.island_distance,
            "distance_from_mainland": round(env.island_distance * 290.0, 1),
            "primary_pollinator_frequency": env.primary_pollinator_frequency,
        }
        for pop_name, env in named_envs.items()
    }

    output_rows = [
        {
            "population": out.population,
            "nectar_guide": out.nectar_guide,
            "selfing_rate": out.selfing_rate,
            "herkogamy": out.herkogamy,
            "flower_size": out.flower_size,
            "Fis": out.Fis,
            "primary_pollinator_frequency": out.primary_pollinator_frequency,
            "outcrossing_opportunity": out.outcrossing_opportunity,
        }
        for out in outputs_list
    ]
    return {}, {
        "final_values": output_rows,
        "generation_rows": [],
        "outputs_list": outputs_list,
        "outputs_by_pop": outputs_dict,
        "synth_pop_env": synth_pop_env,
    }


def simulate_structure_stochastic_abm(
    structure, model_params,
    generations: int, population_size: int, replicates: int, seed: int,
    env_slopes: dict | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Run ABM on the four named gradient populations.

    Population names match pairwise pattern targets (mainland, Oshima,
    Kozushima, Hachijo) so evaluate_patterns() can find them.

    env_slopes is forwarded from run_research_mode so the sampled θ
    slopes are used when rebuilding environments per draw.
    """
    import math as _math
    from attraction_trait_model.environment import Environment

    env_slopes = env_slopes or {}
    _ne_slope  = float(env_slopes.get("ne_isolation_slope",   0.765))
    _mig_rate  = float(env_slopes.get("migration_decay_rate", 3.19))

    # Rebuild named environments with sampled θ slopes
    _base = default_campanula_gradient_environments()
    _grad_envs: dict[str, Environment] = {}
    for pop_name, base_env in _base.items():
        iso = base_env.island_distance
        mig = base_env.migration_rate if iso == 0.0 else (
            0.15 * _math.exp(-_mig_rate * iso)
        )
        _grad_envs[pop_name] = Environment(
            name=pop_name,
            primary_pollinator_frequency=base_env.primary_pollinator_frequency,
            background_pollinator_frequency=base_env.background_pollinator_frequency,
            community_pollinator_abundance=base_env.community_pollinator_abundance,
            migration_rate=mig,
            island_distance=iso,
            ne_isolation_slope=_ne_slope,
        )
    switches = switches_for_structure(structure.name)
    final_by_population: dict[str, dict[str, float]] = {}
    generation_rows: list[dict[str, Any]] = []

    for pop_index, (population_name, env) in enumerate(_grad_envs.items()):
        replicate_finals: list[dict[str, Any]] = []
        for rep in range(replicates):
            run_seed = seed + pop_index * 100_000 + rep * 1_000
            rows = simulate_population(
                env=env, params=model_params, switches=switches,
                generations=generations, population_size=population_size,
                seed=run_seed,
            )
            for row in rows:
                generation_rows.append({
                    "population": population_name, "replicate": rep,
                    "structure": structure.name, **row,
                })
            replicate_finals.append(final_abm_summary(rows))
        # Inject primary_pollinator_frequency from environment (ABM doesn't track it)
        avg = average_summaries(replicate_finals)
        avg["primary_pollinator_frequency"] = env.primary_pollinator_frequency
        final_by_population[population_name] = avg

    _abm_synth_env = {
        name: {
            "isolation": env.island_distance,
            "distance_from_mainland": round(env.island_distance * 290.0, 1),
            "primary_pollinator_frequency": env.primary_pollinator_frequency,
        }
        for name, env in _grad_envs.items()
    }
    abm_outputs_list = [
        ABMPopulationProxy(pop, final_dict, _abm_synth_env.get(pop))
        for pop, final_dict in final_by_population.items()
    ]

    final_rows = [{"population": n, **v} for n, v in final_by_population.items()]
    return {}, {
        "final_values": final_rows,
        "generation_rows": generation_rows,
        "outputs_list": abm_outputs_list,
        "synth_pop_env": _abm_synth_env,
        "outputs_by_pop": final_by_population,
        "abm": True,
    }


# ---------------------------------------------------------------------------
# Core RACH workflow
# ---------------------------------------------------------------------------

def run_research_mode(
    preset_name: str, n_attempts: int, seed: int,
    acceptance_rule: str, backend: str,
    generations: int, population_size: int, replicates: int,
    progress_callback=None,   # callable(done, total, status_text) or None
) -> dict[str, pd.DataFrame]:
    import time as _time
    preset = predefined_tradeoff_presets()[preset_name]
    structures = campanula_causal_structures()
    constraint_passed, rejected_params = sample_all_sets_with_rejection_log(
        preset, n_attempts, seed=seed
    )

    n_structures = len(structures)
    total_steps = len(constraint_passed) * n_structures
    done_steps = 0
    t_start = _time.monotonic()

    all_runs: list[dict[str, Any]] = []
    final_values: list[dict[str, Any]] = []
    generation_rows: list[dict[str, Any]] = []

    for param_index, param_set in enumerate(constraint_passed):
        model_params = param_set_to_model_parameters(param_set)
        _env_slopes = env_slopes_from_param_set(param_set)
        for structure_index, structure in enumerate(structures):
            run_seed = seed + param_index * 10_000 + structure_index * 100
            try:
                if backend == "stochastic_abm":
                    rels, payload = simulate_structure_stochastic_abm(
                        structure, model_params,
                        generations=generations, population_size=population_size,
                        replicates=replicates, seed=run_seed,
                        env_slopes=_env_slopes,
                    )
                else:
                    rels, payload = simulate_structure_proxy(
                        structure, model_params, env_slopes=_env_slopes
                    )
            except Exception:
                rels = {}
                payload = {"final_values": [], "generation_rows": []}

            # --- Primary gradient pattern targets ---
            # Acceptance is driven by response_target gradient patterns
            # (gradient_slope + rank_order across the isolation axis).
            # input_context rows (predictor variables) are excluded automatically.
            _outputs_list = payload.get("outputs_list", [])
            _is_abm = payload.get("abm", False)
            # Use observed_target (response_target) patterns as y_obs.
            # observed_gradient_only_patterns() returns hypothesis_prediction rows
            # which are skipped by evaluate_patterns() → pattern_total=0 → 0 accepted.
            _grad_pats = response_target_patterns()
            _synth_env  = payload.get("synth_pop_env", _POP_ENV)
            if _outputs_list and _grad_pats:
                try:
                    _eval   = evaluate_patterns(_outputs_list, _grad_pats, _synth_env)
                    _wrate  = _eval.weighted_match_rate
                    _thresh = GRADIENT_THRESH_MAP.get(acceptance_rule, 1.0)
                    _ok     = _wrate >= _thresh - 1e-9
                    dist_metrics = {
                        "pattern_matches":       _eval.n_matched,
                        "pattern_total":         _eval.n_total,
                        "abc_distance":          round(1.0 - _wrate, 4),
                        "weighted_abc_distance": round(1.0 - _wrate, 4),
                        "epsilon":               round(1.0 - _thresh, 4),
                        "accepted_by_epsilon":   _ok,
                        "weighted_accepted":     _ok,
                        "acceptance_rule":       acceptance_rule,
                    }
                except Exception as _exc:
                    import traceback as _tb
                    print(f"[WARN] evaluate_patterns failed: {_exc}\n{_tb.format_exc()}")
                    dist_metrics = {
                        "pattern_matches": 0, "pattern_total": len(_grad_pats),
                        "abc_distance": 1.0, "weighted_abc_distance": 1.0,
                        "epsilon": 0.0, "accepted_by_epsilon": False,
                        "weighted_accepted": False, "acceptance_rule": acceptance_rule,
                    }
            else:
                dist_metrics = {
                    "pattern_matches": 0, "pattern_total": 0,
                    "abc_distance": 1.0, "weighted_abc_distance": 1.0,
                    "epsilon": 0.0, "accepted_by_epsilon": False,
                    "weighted_accepted": False, "acceptance_rule": acceptance_rule,
                }
            _grad_eval_cols: dict = {}  # gradient IS the main eval; no separate tracking needed

            # Per-population trait value columns for gradient visualization
            _outputs_by_pop = payload.get("outputs_by_pop", {})
            _grad_trait_cols = _gradient_columns(_outputs_by_pop, abm=_is_abm)

            run_id = f"{param_set.get('parameter_set_id', '')}_{structure.name}_{backend}"
            row = {
                "run_id": run_id,
                "parameter_set_id": param_set.get("parameter_set_id"),
                "preset_name": preset_name,
                "backend": backend,
                "causal_hypothesis": structure.name,
                "structure": structure.name,
                **dist_metrics,
                "admissible_by_epsilon": dist_metrics["accepted_by_epsilon"],
                "generations": generations if backend == "stochastic_abm" else None,
                "population_size": population_size if backend == "stochastic_abm" else None,
                "replicates": replicates if backend == "stochastic_abm" else None,
                **{p: param_set.get(p) for p in LATENT_PARAMS},
                "guide_tradeoff_class": param_set.get("guide_tradeoff_class", ""),
                "selfing_tradeoff_class": param_set.get("selfing_tradeoff_class", ""),
                "guide_net_benefit": param_set.get("guide_net_benefit", ""),
                "selfing_net_benefit": param_set.get("selfing_net_benefit", ""),
                **_grad_eval_cols,
                **_grad_trait_cols,
            }
            all_runs.append(row)

            # --- progress callback ---
            done_steps += 1
            if progress_callback is not None:
                elapsed = _time.monotonic() - t_start
                avg_s = elapsed / done_steps
                remain = avg_s * (total_steps - done_steps)
                admissible_so_far = sum(1 for r in all_runs if r.get("admissible_by_epsilon"))
                progress_callback(
                    done_steps, total_steps,
                    f"param {param_index+1}/{len(constraint_passed)} · "
                    f"{structure.name} · "
                    f"admissible so far: {admissible_so_far} · "
                    f"elapsed {elapsed:.0f}s · "
                    f"ETA {remain:.0f}s"
                )

            for final_row in payload.get("final_values", []):
                final_values.append({
                    "run_id": run_id, "causal_hypothesis": structure.name,
                    "structure": structure.name, "backend": backend, **final_row,
                })
            if backend == "stochastic_abm":
                for gen_row in payload.get("generation_rows", []):
                    generation_rows.append({"run_id": run_id, **gen_row})

    admissible_runs = [r for r in all_runs if r.get("admissible_by_epsilon")]
    compatible_ranges = summarize_parameter_ranges(admissible_runs, LATENT_PARAMS)
    df_runs = pd.DataFrame(all_runs)

    if df_runs.empty:
        df_summary = pd.DataFrame(columns=[
            "causal_hypothesis", "total_runs", "admissible_runs",
            "admissibility_rate", "mean_matches", "mean_abc_distance",
            "mean_weighted_abc_distance",
        ])
    else:
        df_summary = (
            df_runs.groupby("causal_hypothesis")
            .agg(
                total_runs=("pattern_matches", "count"),
                admissible_runs=("admissible_by_epsilon", "sum"),
                mean_matches=("pattern_matches", "mean"),
                mean_abc_distance=("abc_distance", "mean"),
                mean_weighted_abc_distance=("weighted_abc_distance", "mean"),
            )
            .reset_index()
        )
        df_summary["admissibility_rate"] = (
            df_summary["admissible_runs"] / df_summary["total_runs"]
        ).round(3)
        df_summary["mean_matches"] = df_summary["mean_matches"].round(3)
        df_summary["mean_abc_distance"] = df_summary["mean_abc_distance"].round(3)
        df_summary["mean_weighted_abc_distance"] = (
            df_summary["mean_weighted_abc_distance"].round(3)
        )
        df_summary = df_summary.sort_values(
            ["admissibility_rate", "mean_matches"], ascending=False
        )

    return {
        "constraint_passed_params": pd.DataFrame(constraint_passed),
        "rejected_params": pd.DataFrame(rejected_params),
        "all_runs": df_runs,
        "admissible_runs": pd.DataFrame(admissible_runs),
        "compatible_ranges": pd.DataFrame(compatible_ranges),
        "hypothesis_summary": df_summary,
        "final_values": pd.DataFrame(final_values),
        "generation_rows": pd.DataFrame(generation_rows),
    }


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def parameter_space_chart(df_runs: pd.DataFrame, x: str, y: str) -> None:
    if df_runs.empty or x not in df_runs or y not in df_runs:
        st.info("No parameter-space data to plot.")
        return
    plot_df = df_runs[[x, y, "admissible_by_epsilon", "causal_hypothesis"]].dropna().copy()
    plot_df["admissible"] = plot_df["admissible_by_epsilon"].map(
        {True: "admissible", False: "rejected"}
    )
    st.scatter_chart(plot_df, x=x, y=y, color="admissible", size=40)


def final_values_long(df_final_values: pd.DataFrame) -> pd.DataFrame:
    if df_final_values.empty:
        return pd.DataFrame()
    mappings = {
        "nectar_guide": ["nectar_guide", "mean_nectar_guide"],
        "selfing_rate": ["selfing_rate"],
        "herkogamy": ["herkogamy", "mean_herkogamy"],
        "flower_size": ["flower_size", "mean_flower_size"],
        "Fis": ["Fis", "Fis_proxy"],
    }
    rows: list[dict[str, Any]] = []
    for _, row in df_final_values.iterrows():
        for variable, candidates in mappings.items():
            for candidate in candidates:
                if candidate in row and pd.notna(row[candidate]):
                    rows.append({
                        "causal_hypothesis": row.get(
                            "causal_hypothesis", row.get("structure", "")),
                        "structure": row.get("structure", ""),
                        "population": row.get("population", ""),
                        "variable": variable,
                        "value": float(row[candidate]),
                    })
                    break
    return pd.DataFrame(rows)


def generation_timeseries_long(df_generation_rows: pd.DataFrame) -> pd.DataFrame:
    if df_generation_rows.empty:
        return pd.DataFrame()
    value_columns = {
        "mean_nectar_guide": "nectar_guide",
        "selfing_rate": "selfing_rate",
        "mean_herkogamy": "herkogamy",
        "mean_flower_size": "flower_size",
        "Fis_proxy": "Fis",
    }
    rows: list[dict[str, Any]] = []
    for _, row in df_generation_rows.iterrows():
        for source, variable in value_columns.items():
            if source in row and pd.notna(row[source]):
                rows.append({
                    "generation": int(row.get("generation", 0)),
                    "structure": row.get("structure", ""),
                    "population": row.get("population", ""),
                    "variable": variable,
                    "value": float(row[source]),
                })
    return pd.DataFrame(rows)


# ============================================================================
# UI
# ============================================================================

st.title("RACH — Causal Admissibility & Degeneracy Framework")
st.markdown(
    "**RACH** (*Restricted Admissible Causal Hypotheses*) defines the **admissible causal region** "
    "A_ε — the subset of latent parameter–mechanism space that satisfies biological constraints "
    "and reproduces independent observations — then quantifies **which mechanisms remain admissible** "
    "and **how degenerate the causal explanation is**."
)
st.info(
    "**Worked example:** *Campanula punctata* (シマホタルブクロ) along the Izu Islands isolation gradient.  \n"
    "The Campanula system illustrates RACH theory. The framework itself is general — "
    "any ecological system with a generative model f, constraint grammar G, "
    "and independent observations y_obs can be analysed with RACH."
)

# --- Theory panel -------------------------------------------------------
with st.expander("RACH formal definition", expanded=False):
    st.markdown(r"""
**Core RACH object — admissible causal region:**

```
A_ε(y_obs, x_obs) = { (θ, s) ∈ Θ × S :  G(θ)=1,  d(P_sim(f(x_obs; θ, s)), P_obs(y_obs)) ≤ ε }
```

| Symbol | Name | This example |
|--------|------|-------------|
| x_obs | Fixed ecological context | island distance, island area, observed Bombus frequency |
| θ | Latent parameters | guide_cost, selfing_benefit, Ne_isolation_slope, … |
| s | Causal switch state {0,1}^K | S1 guide→Bombus, S2 selfing syndrome, S3 common cause, S5 small pollinator |
| G(θ) | Constraint grammar | biological feasibility constraints C1–C5 |
| f | Generative dynamics | Wright-Fisher drift + selection + stochastic ABM |
| y_obs | Independent observations | 5 pairwise field measurements (Inoue 1986) |

**Five core RACH quantities:**

| Quantity | Symbol | Meaning |
|----------|--------|---------|
| Causal admissibility | CA_j = P(s_j=1 \| A_ε) | Prob. mechanism j is active in admissible region |
| Causal degeneracy | D = H(S \| A_ε) | Remaining entropy of mechanism combinations (bits) |
| Causal resolvability | R = 1 − D/K | Fraction of causal uncertainty resolved (0→1) |
| Observation contribution | OC_k = R(O) − R(O\\{k}) | How much pattern k adds to resolvability |
| Next-observation value | NOV(q) ≈ E[R(O∪q)−R(O)] | Expected resolvability gain from new measurement q |
""")

# --- Worked example context panel ----------------------------------------
with st.expander("Worked example — シマホタルブクロ / Izu Islands context", expanded=False):
    col_yobs, col_xobs = st.columns(2)
    with col_yobs:
        st.markdown("**y_obs — independent observations used for ABC acceptance**")
        _rtp = response_target_patterns()
        _yobs_rows = [
            {
                "pattern": r["pattern"],
                "observed relation": r.get("relation", ""),
                "weight": r.get("weight", ""),
                "source": r.get("source", ""),
            }
            for r in _rtp
        ]
        if _yobs_rows:
            stretch_df(pd.DataFrame(_yobs_rows), hide_index=True)
        st.caption(
            "These 5 field-derived pairwise comparisons (Oshima vs Hachijo, Inoue 1986) "
            "are the ONLY patterns used as y_obs in ABC acceptance. "
            "hypothesis_prediction and input_context rows are excluded."
        )
    with col_xobs:
        st.markdown("**x_obs — fixed empirical context fed into f(x_obs; θ, s)**")
        _xobs_rows = [
            {"variable": "island_distance", "role": "input_context", "notes": "normalised isolation index (0=mainland, 1=Hachijo)"},
            {"variable": "primary_pollinator_frequency", "role": "input_context", "notes": "Bombus ardens presence/frequency per island (field/literature)"},
            {"variable": "island_area", "role": "input_context", "notes": "km² (approximate, affects Ne prior)"},
        ]
        stretch_df(pd.DataFrame(_xobs_rows), hide_index=True)
        st.caption(
            "x_obs is injected into f as fixed empirical context. "
            "It is not part of θ (not inferred) and not part of y_obs (not an ABC target)."
        )

# --- Workflow steps -------------------------------------------------------
with st.expander("RACH inference workflow", expanded=False):
    stretch_df(pd.DataFrame(WORKFLOW_STEPS), hide_index=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("RACH inference settings")

    # --- Shared: preset and acceptance rule ---
    presets = predefined_tradeoff_presets()
    _preset_keys = list(presets.keys())
    preset_name = st.selectbox(
        "θ prior preset",
        _preset_keys,
        index=_preset_keys.index("literature_grounded") if "literature_grounded" in _preset_keys else 0,
        format_func=lambda k: {
            "literature_grounded": "literature_grounded  (empirical prior — primary)",
            "broad_prior":         "broad_prior  (sensitivity sweep)",
        }.get(k, k),
        help="literature_grounded uses ranges calibrated from Izu Campanula literature. "
             "broad_prior is for prior-sensitivity comparison.",
    )
    _rules = available_rules()
    acceptance_rule = st.selectbox(
        "ε (ABC acceptance rule)",
        _rules,
        index=_rules.index("weighted_lax") if "weighted_lax" in _rules else 0,
        format_func=lambda r: {
            "strict_all":      "strict — all 5 patterns must match (ε=0)",
            "weighted_strict": "weighted strict — weighted match = 1.0",
            "weighted_lax":    "weighted lax — weighted match ≥ 0.80  ← recommended",
            "relaxed_0.83":    "relaxed — ≥4/5 patterns",
            "relaxed_0.67":    "lax — ≥3/5 patterns",
        }.get(r, r),
    )
    from causal_model.switch_inference import GRADIENT_N_PATTERNS as _N_PAT
    _thresh_display = GRADIENT_THRESH_MAP.get(acceptance_rule, 1.0)
    st.caption(
        f"y_obs: {_N_PAT} response_target patterns · "
        f"ε threshold: weighted_match_rate ≥ {_thresh_display:.3f}"
    )
    seed = st.number_input("Random seed", 0, 999999, 42, 1)

    st.divider()

    # =========================================================
    # PRIMARY: RACH inference — switch posterior (CA_j, D, R)
    # =========================================================
    st.subheader("RACH inference — A_ε & core quantities")
    st.caption(
        "Jointly samples (θ, s) from the prior, runs f(x_obs; θ, s), "
        "and accepts draws with d ≤ ε to approximate A_ε. "
        "Computes CA_j, D, R, OC_k, NOV from the accepted sample."
    )
    sp_backend = "stochastic_abm"
    st.caption(BACKEND_DESCRIPTIONS[sp_backend])
    sp_n_attempts = st.slider(
        "Joint prior draws  (θ, s)",
        50, 1000, 200, 50,
        key="sp_n_abm",
        help="Each draw samples (θ, s) jointly and runs the ABM across the 4-island gradient. "
             "≥200 draws recommended for stable CA_j; ≥500 for stable D.",
    )
    sp_abm_generations = st.slider("ABM generations", 10, 80, 30, 10, key="sp_gen")
    sp_abm_popsize    = st.slider("ABM population size", 50, 300, 100, 50, key="sp_pop")
    sp_abm_replicates = st.slider("ABM replicates per island", 1, 5, 3, 1, key="sp_rep")
    _est_sec = int(sp_n_attempts * 0.30 * sp_abm_replicates / 3)
    st.caption(
        f"Estimated runtime: ~{_est_sec}s "
        f"({sp_n_attempts} draws × {sp_abm_replicates} rep × 4 islands)"
    )
    run_switch_button = st.button(
        "Run RACH inference", type="primary", use_container_width=True
    )

    st.divider()

    # =========================================================
    # SECONDARY: Structure comparison (M1-M5 enumeration)
    # =========================================================
    with st.expander("Supplementary: M1-M5 structure comparison", expanded=False):
        st.caption(
            "Compares pre-defined causal structures by admissibility rate. "
            "Useful for connecting switch posterior results to conventional "
            "hypothesis enumeration. This is a secondary analysis — "
            "the switch posterior above is the primary RACH output."
        )
        backend = "stochastic_abm"
        st.caption(BACKEND_DESCRIPTIONS[backend])
        n_attempts = st.slider("Prior parameter draws", 20, 500, 80, 20, key="n_attempts_abm")
        generations = st.slider("ABM generations", 10, 100, 40, 10, key="m5_gen")
        population_size = st.slider("ABM population size", 50, 500, 150, 50, key="m5_pop")
        replicates = st.slider("ABM replicates per island", 1, 5, 1, 1, key="m5_rep")
        run_button = st.button("Run structure comparison", use_container_width=True)

preset = presets[preset_name]
with st.expander(f"θ prior ranges — {preset_name}", expanded=False):
    st.caption(preset.description)
    _lit_map = {src.parameter: src for src in LITERATURE_SOURCES}
    _prior_rows = []
    for key, (lo, hi) in preset.ranges.items():
        src = _lit_map.get(key)
        _prior_rows.append({
            "Parameter": key,
            "Lower": lo,
            "Upper": hi,
            "Empirical basis": src.empirical_range if src else "broad",
            "Source": src.citation if src else "n/a",
        })
    st.dataframe(pd.DataFrame(_prior_rows), width="stretch", hide_index=True)
    if preset.literature_sources:
        st.markdown("**Literature sources**")
        _src_rows = [
            {
                "Parameter": s.parameter,
                "Modelled range": f"({s.modelled_range[0]}, {s.modelled_range[1]})",
                "Empirical range": s.empirical_range,
                "Citation": s.citation,
                "Notes": s.notes,
            }
            for s in preset.literature_sources
        ]
        st.dataframe(pd.DataFrame(_src_rows), width="stretch", hide_index=True)

# ---------------------------------------------------------------------------
# Run M1-M5 comparison
# ---------------------------------------------------------------------------
if run_button:
    _prog_bar  = st.progress(0.0, text="Starting…")
    _stat_text = st.empty()

    def _update_progress(done: int, total: int, status: str) -> None:
        frac = done / total if total > 0 else 0.0
        _prog_bar.progress(frac, text=f"{done}/{total} runs ({100*frac:.0f}%)")
        _stat_text.caption(status)

    result = run_research_mode(
        preset_name=preset_name,
        n_attempts=n_attempts,
        seed=int(seed),
        acceptance_rule=acceptance_rule,
        backend=backend,
        generations=generations,
        population_size=population_size,
        replicates=replicates,
        progress_callback=_update_progress,
    )
    _prog_bar.progress(1.0, text="Done ✓")
    _stat_text.empty()
    st.session_state["research_result"] = result
    st.session_state["research_settings"] = {
        "preset_name": preset_name,
        "n_attempts": n_attempts,
        "seed": int(seed),
        "acceptance_rule": acceptance_rule,
        "backend": backend,
        "generations": generations,
        "population_size": population_size,
        "replicates": replicates,
    }

# ---------------------------------------------------------------------------
# Run island gradient inference
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Run switch posterior inference
# ---------------------------------------------------------------------------
if run_switch_button:
    import time as _sptime
    _sp_bar  = st.progress(0.0, text="Switch Posterior: starting…")
    _sp_stat = st.empty()

    def _sp_progress(done: int, total: int, status: str) -> None:
        _sp_bar.progress(done / total if total > 0 else 0.0,
                         text=f"Switch Posterior: {done}/{total} ({100*done//max(total,1)}%)")
        _sp_stat.caption(status)

    sp_result = run_switch_posterior_inference_abm(
        preset_name=preset_name,
        n_attempts=int(sp_n_attempts),
        acceptance_rule=acceptance_rule,
        seed=int(seed) + 1,
        observed_rels=OBSERVED_RELS,
        pattern_weights=PATTERN_WEIGHTS,
        generations=sp_abm_generations,
        population_size=sp_abm_popsize,
        replicates=sp_abm_replicates,
        progress_callback=_sp_progress,
    )
    _sp_bar.progress(1.0, text="Switch Posterior: Done ✓")
    _sp_stat.empty()
    st.session_state["sp_result"] = sp_result
    st.session_state["sp_backend_used"] = sp_backend
    st.session_state["sp_settings"] = {
        "preset_name": preset_name,
        "seed": int(seed) + 1,
        "acceptance_rule": acceptance_rule,
        "backend": sp_backend,
    }

# ---------------------------------------------------------------------------
# M1-M5 Results  (supplementary)
# ---------------------------------------------------------------------------
if "research_result" in st.session_state:
    result = st.session_state["research_result"]
    settings = st.session_state.get("research_settings", {})
    df_acc_params = result["constraint_passed_params"]
    df_rej = result["rejected_params"]
    df_runs = result["all_runs"]
    df_acc_runs = result["admissible_runs"]
    df_ranges = result["compatible_ranges"]
    df_summary = result["hypothesis_summary"]
    df_final_values = result["final_values"]
    df_generation_rows = result["generation_rows"]

    st.divider()
    st.subheader("Supplementary: M1-M5 structure comparison")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Prior draws", settings.get("n_attempts", n_attempts))
    c2.metric("Constraint-passed", len(df_acc_params))
    c3.metric("Constraint-rejected", len(df_rej))
    c4.metric("Admissible runs", len(df_acc_runs))
    if not df_summary.empty:
        best = df_summary.iloc[0]
        c5.metric(
            "Best hypothesis",
            str(best["causal_hypothesis"]),
            f"admissibility {best['admissibility_rate']:.2f}",
        )
    else:
        c5.metric("Best hypothesis", "none")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Hypothesis ranking",
        "Parameter space",
        "Compatible ranges",
        "Simulated values",
        "ABM time series",
        "Tables & downloads",
    ])

    with tab1:
        st.markdown("### Restricted admissible causal hypotheses")
        st.caption(
            "Admissibility = fraction of parameter-set runs where gradient pattern targets "
            f"were matched (rule: {settings.get('acceptance_rule', acceptance_rule)})."
        )
        if df_summary.empty:
            st.warning("No runs completed.")
        else:
            st.bar_chart(
                df_summary.set_index("causal_hypothesis")[["admissibility_rate"]],
                width="stretch",
            )
            col_a, col_b = st.columns(2)
            with col_a:
                st.bar_chart(
                    df_summary.set_index("causal_hypothesis")[["mean_abc_distance"]],
                    width="stretch",
                )
                st.caption("Unweighted ABC distance (1 - matches/6)")
            with col_b:
                st.bar_chart(
                    df_summary.set_index("causal_hypothesis")[["mean_weighted_abc_distance"]],
                    width="stretch",
                )
                st.caption("Weighted ABC distance")
            stretch_df(df_summary, hide_index=True)
        if not df_runs.empty:
            show_cols = [
                "causal_hypothesis", "pattern_matches", "pattern_total",
                "abc_distance", "weighted_abc_distance", "admissible_by_epsilon",
            ]
            stretch_df(
                df_runs[[c for c in show_cols if c in df_runs.columns]].head(200),
                hide_index=True,
            )

    with tab2:
        st.markdown("### Admissible vs rejected runs in latent parameter space")
        if df_runs.empty:
            st.warning("No run data.")
        else:
            c_a, c_b = st.columns(2)
            with c_a:
                st.markdown("**Guide cost vs outcrossing benefit**")
                parameter_space_chart(df_runs, "guide_cost", "outcrossing_benefit")
            with c_b:
                st.markdown("**Selfing benefit vs inbreeding depression**")
                parameter_space_chart(df_runs, "selfing_benefit", "inbreeding_depression")
            c_c, c_d = st.columns(2)
            with c_c:
                st.markdown("**Small-pollinator efficiency vs selfing benefit**")
                parameter_space_chart(df_runs, "background_pollinator_efficiency", "selfing_benefit")
            with c_d:
                st.markdown("**Drift strength vs guide cost**")
                parameter_space_chart(df_runs, "drift_strength", "guide_cost")

    with tab3:
        st.markdown("### Compatible latent parameter ranges")
        st.caption(
            "These ranges are the inferential output of RACH -- "
            "the admissible region of latent parameter space, not manually chosen values."
        )
        if df_ranges.empty:
            st.warning("No admissible runs. Try a more relaxed acceptance rule or more draws.")
        else:
            stretch_df(df_ranges, hide_index=True)
            st.bar_chart(df_ranges.set_index("Parameter")[["Median"]], width="stretch")

    with tab4:
        st.markdown("### Simulated trait values along isolation gradient")
        st.caption(
            ":information_source: **Fis** shown here is a computational proxy "
            "(heterozygosity deficit estimate), not a true genetic Fis from microsatellite data. "
            "Interpret Fis values as indicative trends only."
        )
        long_values = final_values_long(df_final_values)
        if long_values.empty:
            st.warning("No final simulated values available.")
        else:
            sel_var = st.selectbox("Variable", sorted(long_values["variable"].unique()), key="tab4_var")
            sel_hyp = st.selectbox(
                "Causal hypothesis", sorted(long_values["causal_hypothesis"].unique()),
                key="tab4_hyp",
            )
            sub = long_values[
                (long_values["variable"] == sel_var) &
                (long_values["causal_hypothesis"] == sel_hyp)
            ]
            if not sub.empty:
                st.bar_chart(
                    sub.groupby("population")["value"].mean().to_frame(),
                    width="stretch",
                )
            stretch_df(df_final_values.head(300), hide_index=True)

    with tab5:
        st.markdown("### Stochastic ABM generation trajectories")
        ts = generation_timeseries_long(df_generation_rows)
        if ts.empty:
            st.info("Run in stochastic_abm mode to see generation trajectories.")
        else:
            col_ts1, col_ts2 = st.columns(2)
            with col_ts1:
                var = st.selectbox("Variable", sorted(ts["variable"].unique()), key="tab5_var")
            with col_ts2:
                structure_ts = st.selectbox(
                    "Hypothesis", sorted(ts["structure"].unique()), key="tab5_hyp",
                )
            sub = ts[(ts["variable"] == var) & (ts["structure"] == structure_ts)]
            if not sub.empty:
                line_df = sub.groupby(
                    ["generation", "population"], as_index=False
                )["value"].mean()
                line_wide = line_df.pivot(
                    index="generation", columns="population", values="value"
                )
                st.line_chart(line_wide, width="stretch")
            stretch_df(df_generation_rows.head(300), hide_index=True)

    with tab6:
        st.markdown("### Raw tables and downloads")
        stretch_df(df_runs.head(200), hide_index=True)
        _tag = _run_tag(settings)

        # --- Bulk ZIP download (all tables in one click) ---
        _zip_files = {
            f"{_tag}_all_runs":               df_runs,
            f"{_tag}_admissible_runs":        df_acc_runs,
            f"{_tag}_final_values":           df_final_values,
            f"{_tag}_compatible_ranges":      df_ranges,
            f"{_tag}_hypothesis_summary":     df_summary,
            f"{_tag}_constraint_passed_params": df_acc_params,
            f"{_tag}_rejected_params":        df_rej,
        }
        if not df_generation_rows.empty:
            _zip_files[f"{_tag}_generation_timeseries"] = df_generation_rows
        st.download_button(
            "⬇ Download ALL tables as ZIP",
            _build_zip(_zip_files),
            f"{_tag}_rach_all.zip",
            "application/zip",
            use_container_width=True,
            type="primary",
        )
        st.divider()

        # --- Individual downloads ---
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("all_runs.csv", to_csv_bytes(df_runs),
                               f"{_tag}_all_runs.csv", "text/csv")
            st.download_button("admissible_runs.csv", to_csv_bytes(df_acc_runs),
                               f"{_tag}_admissible_runs.csv", "text/csv")
            st.download_button("final_values.csv", to_csv_bytes(df_final_values),
                               f"{_tag}_final_values.csv", "text/csv")
        with d2:
            st.download_button("compatible_ranges.csv", to_csv_bytes(df_ranges),
                               f"{_tag}_compatible_ranges.csv", "text/csv")
            st.download_button("hypothesis_summary.csv", to_csv_bytes(df_summary),
                               f"{_tag}_hypothesis_summary.csv", "text/csv")
            if not df_generation_rows.empty:
                st.download_button(
                    "generation_timeseries.csv",
                    to_csv_bytes(df_generation_rows),
                    f"{_tag}_generation_timeseries.csv",
                    "text/csv",
                )
        with d3:
            st.download_button(
                "constraint_passed_params.csv",
                to_csv_bytes(df_acc_params),
                f"{_tag}_constraint_passed_params.csv",
                "text/csv",
            )
            st.download_button(
                "rejected_params.csv",
                to_csv_bytes(df_rej),
                f"{_tag}_rejected_params.csv",
                "text/csv",
            )

else:
    st.markdown(
        "Configure settings in the sidebar and click **Run RACH inference** to begin.  \n"
        "This runs the primary RACH workflow: samples (θ, s) jointly, simulates f(x_obs; θ, s), "
        "and computes CA_j, D, R, OC_k, NOV from the admissible causal region A_ε."
    )

# ============================================================================
# RACH Inference Results  (Switch Posterior / A_ε quantities)
# ============================================================================
if "sp_result" in st.session_state:
    sp = st.session_state["sp_result"]
    st.divider()
    st.header("RACH Inference Results")
    st.caption(
        "Worked example: *Campanula punctata* / Izu Islands · "
        "y_obs = 5 field-derived pairwise patterns (Inoue 1986) · "
        "f = stochastic ABM · K = 4 causal switches"
    )
    st.info(
        "**What this shows:** RACH samples (θ, s) jointly from the prior, runs f(x_obs; θ, s), "
        "and retains draws where simulated patterns match y_obs (d ≤ ε). "
        "The retained sample approximates A_ε. "
        "The five core quantities — CA_j, D, R, OC_k, NOV — are computed from A_ε.  \n"
        "No structure was pre-defined. The posterior reflects which mechanisms are "
        "jointly present in biologically feasible, observation-compatible parameter space."
    )

    if len(sp.accepted_rows) < 30:
        st.warning(
            f"Only {len(sp.accepted_rows)} accepted samples — estimates are unstable. "
            "Increase draws or use a more relaxed ε for reliable inference."
        )

    # --- A_ε summary metrics ---
    sp_c1, sp_c2, sp_c3, sp_c4 = st.columns(4)
    sp_c1.metric("|A_ε| accepted", len(sp.accepted_rows),
                 help="Number of (θ,s) draws retained in the admissible causal region.")
    sp_c2.metric("Total draws", sp.n_attempts,
                 help="Total joint (θ,s) prior draws attempted.")
    sp_c3.metric("Acceptance rate", f"{sp.acceptance_rate:.1%}",
                 help="Fraction of draws accepted into A_ε. Low rate → tighter causal constraint.")
    sp_c4.metric("K (switches)", len(CAMPANULA_SWITCHES),
                 help="Dimension of the causal switch space S = {0,1}^K.")

    if not sp.accepted_rows:
        st.warning(
            "No samples were accepted. "
            "Try a more relaxed acceptance rule (e.g. relaxed_5_of_6) or more draws."
        )
    else:
        sp_tab1, sp_tab2, sp_tab3, sp_tab4, sp_tab5, sp_tab6 = st.tabs([
            "CA_j — causal admissibility",
            "D · R — degeneracy & resolvability",
            "OC_k — observation contribution",
            "NOV — next-observation value",
            "Parameter space A_ε",
            "Downloads",
        ])

        with sp_tab1:
            st.markdown("### CA_j = P(s_j = 1 | A_ε)")
            st.caption(
                "Causal admissibility: the fraction of observation-compatible, "
                "biologically feasible (θ,s) space in which mechanism j is active.  \n"
                "Prior = 0.5 (Bernoulli). **BF > 3** → admissible. **BF < 1/3** → inadmissible. "
                "CA_j ≈ 0.5 → current y_obs is non-informative about mechanism j."
            )
            df_post = pd.DataFrame(sp.posterior_table)
            if not df_post.empty:
                st.bar_chart(
                    df_post.set_index("switch")[["P_prior_ON", "P_posterior_ON"]],
                    width="stretch",
                )
                st.caption(
                    "Left bar = prior P(ON) = 0.5.  Right bar = CA_j = P(ON | A_ε).  \n"
                    "A bar shift away from 0.5 means the accepted sample favours "
                    "that mechanism being ON (shift up) or OFF (shift down)."
                )
                stretch_df(
                    df_post[[
                        "switch", "biological_question", "P_prior_ON",
                        "P_posterior_ON", "Bayes_factor", "interpretation",
                        "n_ON", "n_accepted",
                    ]],
                    hide_index=True,
                )
                st.markdown("#### Biological interpretation")
                for row in sp.posterior_table:
                    interp = str(row.get("interpretation", ""))
                    icon = (
                        "✅ supported" if interp.startswith("supported")
                        else "〜 weakly supported" if interp.startswith("weakly s")
                        else "❌ opposed" if interp.startswith("opposed")
                        else "— uninformative"
                    )
                    bf = row.get("Bayes_factor")
                    bf_str = f"BF={bf:.2f}" if bf is not None else "BF=n/a"
                    st.markdown(
                        f"**{icon} · {row['switch']}** "
                        f"CA_j={row['P_posterior_ON']:.3f} ({bf_str})  \n"
                        f"*{row.get('biological_question', '')[:100]}*"
                    )

            # Co-activation as secondary detail
            with st.expander("Switch co-activation P(A ON ∩ B ON | A_ε)", expanded=False):
                st.caption(
                    "High co-activation = two mechanisms tend to be simultaneously ON "
                    "in observation-compatible parameter regions."
                )
                coact = compute_coactivation_table(sp.accepted_rows)
                if coact:
                    df_coact = pd.DataFrame(coact)
                    stretch_df(df_coact, hide_index=True)
                    try:
                        pivot = df_coact.pivot(
                            index="switch_A", columns="switch_B", values="P_both_ON"
                        )
                        st.dataframe(pivot.round(3), width="stretch")
                    except Exception:
                        pass
                else:
                    st.info("Not enough accepted samples.")

        # ------------------------------------------------------------------
        # Load RACH modules once (shared across tabs)
        # ------------------------------------------------------------------
        try:
            from causal_model.causal_admissibility import (
                rach_summary as _rach_summary_fn,
                causal_degeneracy as _cd_fn,
                causal_resolvability as _cr_fn,
                observation_contribution as _oc_fn,
                next_observation_value as _nov_fn,
                compute_causal_admissibility_table as _ca_table_fn,
            )
            from causal_model.identifiability import compute_rach_theory_metrics as _rach_metrics_fn
            _rs = _rach_summary_fn(sp.accepted_rows, CAMPANULA_SWITCHES)
            _rach_metrics = _rach_metrics_fn(sp.accepted_rows, CAMPANULA_SWITCHES)
            # Pre-compute OC_k and heuristic NOV once (used in tabs AND downloads)
            _oc_source = getattr(sp, "evaluated_rows", None) or sp.accepted_rows
            _oc_results = _oc_fn(_oc_source, CAMPANULA_SWITCHES, threshold=_thresh_display)
            _nov_results = _nov_fn(sp.accepted_rows, CAMPANULA_SWITCHES)
            _rach_modules_ok = True
        except Exception as _rach_err:
            _rach_modules_ok = False
            _oc_results = []
            _nov_results = []

        # ---- sp_tab2: D · R — causal degeneracy & resolvability -----------
        with sp_tab2:
            st.markdown("### D = H(S | A_ε) — causal degeneracy")
            st.markdown("### R = 1 − D/K — causal resolvability")
            st.caption(
                "**D** measures remaining uncertainty about mechanism combinations after "
                "conditioning on y_obs and G(θ). High D = many switch combos remain admissible.  \n"
                "**R** normalises D to [0,1]. R=0: no resolution. R=1: unique mechanism identified.  \n"
                "High D is **not a failure** — it means the current observation set cannot yet "
                "distinguish competing mechanisms. This is itself a scientific finding."
            )
            if _rach_modules_ok:
                mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                mc1.metric("R — causal resolvability", f"{_rs.causal_resolvability:.3f}",
                           help="R = 1 − D/K. Fraction of causal uncertainty resolved by y_obs.")
                mc2.metric("D — causal degeneracy", f"{_rs.causal_degeneracy:.3f} bits",
                           help=f"H(S|A_ε). Max = K = {_rs.n_switches} bits.")
                mc3.metric("K — max degeneracy", f"{_rs.max_degeneracy:.0f} bits",
                           help=f"{_rs.n_switches} switches → {_rs.n_switches} bits max entropy.")
                mc4.metric("|A_ε|", f"{_rs.n_accepted}",
                           help="Number of accepted (θ,s) draws.")
                mc5.metric("Total I_j", f"{_rach_metrics.total_identifiability:.3f} bits",
                           help="Sum of per-switch marginal entropy reduction I_j.")

                st.divider()
                st.markdown("#### ε sensitivity — how D and R change with acceptance threshold")
                st.caption(
                    "Stricter ε → smaller A_ε → lower D → higher R.  \n"
                    "Re-filtered from the accepted sample — no re-simulation needed."
                )
                _thresh_map = {
                    "weighted_lax (≥0.800)":   0.800,
                    "relaxed_0.83 (≥0.833)":   5 / 6,
                    "weighted_strict (=1.000)": 1.000,
                    "relaxed_0.67 (≥0.667)":   4 / 6,
                }
                _sens_rows = []
                for _rule_label, _thr in _thresh_map.items():
                    _filtered = [
                        r for r in sp.accepted_rows
                        if r.get("weighted_match_rate", 0.0) >= _thr - 1e-9
                    ]
                    _n = len(_filtered)
                    if _n >= 3:
                        _D = _cd_fn(_filtered, CAMPANULA_SWITCHES)
                        _R = _cr_fn(_filtered, CAMPANULA_SWITCHES)
                        _m = _rach_metrics_fn(_filtered, CAMPANULA_SWITCHES)
                        _sens_rows.append({
                            "ε rule": _rule_label,
                            "|A_ε|": _n,
                            "D (bits)": round(_D, 3),
                            "R": round(_R, 3),
                            "total I_j": round(_m.total_identifiability, 3),
                        })
                    else:
                        _sens_rows.append({
                            "ε rule": _rule_label, "|A_ε|": _n,
                            "D (bits)": float("nan"), "R": float("nan"),
                            "total I_j": float("nan"),
                        })
                _sens_df = pd.DataFrame(_sens_rows)
                for _col in ("D (bits)", "R", "total I_j"):
                    if _col in _sens_df.columns:
                        _sens_df[_col] = pd.to_numeric(_sens_df[_col], errors="coerce")
                stretch_df(_sens_df, hide_index=True)

                st.divider()
                st.markdown("#### Per-switch identifiability I_j")
                st.caption(
                    "I_j = H(s_j prior) − H(s_j | A_ε) = 1 − H(CA_j). "
                    "How much the accepted sample reduces uncertainty about switch j. "
                    "I_j = 1 → fully identified. I_j = 0 → uninformative."
                )
                if hasattr(_rach_metrics, "identifiability_table") and _rach_metrics.identifiability_table:
                    df_ij = pd.DataFrame(_rach_metrics.identifiability_table)
                    if not df_ij.empty and "switch" in df_ij.columns:
                        _ij_col = [c for c in df_ij.columns if "identifiability" in c.lower() or c == "I_j"]
                        if _ij_col:
                            st.bar_chart(df_ij.set_index("switch")[[_ij_col[0]]], width="stretch")
                        stretch_df(df_ij, hide_index=True)
            else:
                st.error(f"Could not load RACH modules: {_rach_err}")

        # ---- sp_tab3: OC_k — observation contribution ----------------------
        with sp_tab3:
            st.markdown("### OC_k = R(O) − R(O \\ {k})")
            st.caption(
                "**Observation contribution**: how much each pattern in y_obs contributes "
                "to causal resolvability, estimated by leave-one-out (LOO).  \n"
                "**OC_k > 0** → removing this pattern reduces R (it adds information).  \n"
                "**OC_k ≈ 0** → pattern is redundant with others.  \n"
                "**OC_k < 0** → rare; pattern may confound inference."
            )
            if _rach_modules_ok:
                if _oc_results:
                    df_oc = pd.DataFrame([
                        {"pattern": r.pattern, "switch": r.switch,
                         "OC_k": round(r.OC_k, 4),
                         "R_full": round(r.R_full, 4),
                         "R_loo": round(r.R_loo, 4),
                         "n_loo": r.n_loo}
                        for r in _oc_results
                    ])
                    df_oc_nz = df_oc[df_oc["OC_k"].abs() > 0.0001].sort_values("OC_k", ascending=False)
                    if not df_oc_nz.empty:
                        st.bar_chart(
                            df_oc_nz.set_index(df_oc_nz["pattern"] + " → " + df_oc_nz["switch"])[["OC_k"]],
                            width="stretch",
                        )
                        stretch_df(df_oc_nz, hide_index=True)
                    else:
                        st.info(
                            "All OC_k ≈ 0. Each individual pattern has low marginal contribution "
                            "to resolvability — expected when patterns are correlated or |A_ε| is small. "
                            "Adding independent observations (genetic, manipulative) increases OC_k variance."
                        )
                    stretch_df(df_oc, hide_index=True)
                else:
                    st.info("No per-pattern data available. Run inference to populate OC_k.")
            else:
                st.error(f"Could not load RACH modules: {_rach_err}")

        # ---- sp_tab4: NOV — next-observation value -------------------------
        with sp_tab4:
            st.markdown("### NOV(q) ≈ E[ R(O ∪ q) − R(O) ]")

            _nov_mode = st.radio(
                "NOV estimation method",
                ["Heuristic (instant)", "Simulation (accurate)"],
                horizontal=True,
                help=(
                    "**Heuristic**: estimates ΔR from current CA_j ambiguity — instant but approximate.  \n"
                    "**Simulation**: re-runs ABC for each candidate's possible outcomes and "
                    "integrates over outcome probabilities — accurate but takes several minutes."
                ),
            )

            if _nov_mode == "Heuristic (instant)":
                st.caption(
                    "**Next-observation value**: expected increase in causal resolvability "
                    "if candidate observation q is added to y_obs.  \n"
                    "Ranked by estimated ΔR. Computed from current CA_j via heuristic approximation "
                    "(most ambiguous switches → most gain).  \n"
                    "⚠ Heuristic, not the true expectation over q's outcome distribution. "
                    "Use as a priority guide for future data collection."
                )
                if _rach_modules_ok:
                    if _nov_results:
                        df_nov = pd.DataFrame([
                            {
                                "priority":        r.priority,
                                "candidate":       r.candidate,
                                "ΔR (approx)":     round(r.expected_resolvability_gain, 4),
                                "target switches": ", ".join(r.target_switches),
                                "rationale":       r.rationale[:120],
                            }
                            for r in _nov_results
                        ])
                        st.bar_chart(df_nov.set_index("candidate")[["ΔR (approx)"]], width="stretch")
                        st.caption(
                            f"Current R = {_rs.causal_resolvability:.3f}.  "
                            "Top-ranked candidate is expected to increase R most. "
                            "Collecting all candidates would approach R → 1."
                        )
                        stretch_df(df_nov, hide_index=True)
                    else:
                        st.info("No candidate observations configured.")
                else:
                    st.error(f"Could not load RACH modules: {_rach_err}")

            else:  # Simulation NOV
                st.caption(
                    "**Simulation NOV**: for each candidate observation q, enumerates its possible "
                    "empirical outcomes (e.g. 'monotone gradient' vs 'stepped gradient'), re-runs "
                    "ABC with each augmented y_obs, and integrates R over outcomes weighted by "
                    "prior probability.  \n"
                    "NOV(q) = Σ_v  p(v) · R(O ∪ {q=v})  −  R(O)  \n"
                    "Each candidate requires 2–3 ABC runs. Total ≈ "
                    f"{8 * 2} runs × n_attempts draws."
                )
                _nov_n = st.slider(
                    "Draws per outcome (n_attempts)",
                    min_value=50, max_value=300, value=100, step=50,
                    help="More draws = more stable R estimate per outcome. 100 is usually sufficient.",
                )
                _nov_seed_inp = st.number_input("Seed", value=42, step=1)

                if st.button("▶ Run Simulation NOV", type="primary"):
                    if not _rach_modules_ok:
                        st.error(f"Could not load RACH modules: {_rach_err}")
                    else:
                        from causal_model.causal_admissibility import next_observation_value_simulation
                        from examples.campanula_izu.observed_data import (
                            load_observed_patterns as _load_obs,
                            load_pattern_weights as _load_pw,
                        )
                        _obs_rels = _load_obs()
                        _pw_weights = _load_pw()

                        _nov_progress = st.progress(0.0, text="Starting NOV simulation…")
                        _nov_status = st.empty()
                        _nov_done_count = [0]
                        _nov_total = sum(
                            len(c.outcomes)
                            for c in __import__(
                                "causal_model.causal_admissibility",
                                fromlist=["CAMPANULA_CANDIDATE_OBSERVATIONS"]
                            ).CAMPANULA_CANDIDATE_OBSERVATIONS
                            if c.outcomes
                        )

                        def _nov_cb(cand_name, outcome_name, done, total):
                            _nov_done_count[0] = done
                            pct = done / max(total, 1)
                            _nov_progress.progress(pct, text=f"{cand_name} / {outcome_name} ({done}/{total})")
                            _nov_status.caption(f"Running: {cand_name} → {outcome_name}")

                        with st.spinner("Running simulation NOV…"):
                            _nov_sim_results = next_observation_value_simulation(
                                observed_rels=_obs_rels,
                                pattern_weights=_pw_weights,
                                switches=CAMPANULA_SWITCHES,
                                n_attempts=_nov_n,
                                preset_name=st.session_state.get("preset_name", "literature_grounded"),
                                acceptance_rule=st.session_state.get("acceptance_rule", "weighted_lax"),
                                seed=int(_nov_seed_inp),
                                threshold=_thresh_display,
                                progress_callback=_nov_cb,
                                current_accepted_rows=sp.accepted_rows,
                            )

                        _nov_progress.progress(1.0, text="Done")
                        _nov_status.empty()
                        st.session_state["_nov_sim_results"] = _nov_sim_results

                if "_nov_sim_results" in st.session_state:
                    _sim_res = st.session_state["_nov_sim_results"]
                    df_nov_sim = pd.DataFrame([
                        {
                            "priority":        r.priority,
                            "candidate":       r.candidate,
                            "NOV (ΔR)":        round(r.expected_resolvability_gain, 4),
                            "R_current":       round(r.current_R, 4),
                            "R_expected":      round(r.current_R + r.expected_resolvability_gain, 4),
                            "target switches": ", ".join(r.target_switches),
                        }
                        for r in _sim_res
                    ])
                    st.bar_chart(df_nov_sim.set_index("candidate")[["NOV (ΔR)"]], width="stretch")
                    st.caption(
                        f"Baseline R = {_sim_res[0].current_R:.3f} (same A_ε).  "
                        "NOV > 0 = collecting this observation expected to improve causal resolution."
                    )
                    stretch_df(df_nov_sim, hide_index=True)
                    with st.expander("Outcome details (rationale)"):
                        for r in _sim_res:
                            st.markdown(f"**{r.candidate}** (priority={r.priority}): {r.rationale[:300]}")

        # ---- sp_tab5: Parameter space A_ε ----------------------------------
        with sp_tab5:
            st.markdown("### Accepted (θ, s) in latent parameter space")
            st.caption(
                "Each point is one accepted (θ, s) draw — a member of A_ε. "
                "Colour by switch state to see which θ regions are compatible with "
                "each mechanism being ON vs OFF."
            )
            df_sp = pd.DataFrame(sp.accepted_rows)
            sw_names = [sw.name for sw in CAMPANULA_SWITCHES]
            avail = [
                p for p in [
                    "guide_cost", "outcrossing_benefit",
                    "selfing_benefit", "inbreeding_depression", "drift_strength",
                    "Ne_isolation_slope", "migration_decay_rate", "pollinator_loss_slope",
                ]
                if p in df_sp.columns
            ]
            if len(avail) >= 2:
                col_sw, col_x, col_y = st.columns(3)
                with col_sw:
                    color_switch = st.selectbox(
                        "Colour by switch",
                        [s for s in sw_names if s in df_sp.columns],
                        key="sp_color",
                    )
                with col_x:
                    x_p = st.selectbox("X axis (θ parameter)", avail, key="sp_x")
                with col_y:
                    y_p = st.selectbox(
                        "Y axis (θ parameter)", avail,
                        index=min(1, len(avail) - 1),
                        key="sp_y",
                    )
                plot_df = df_sp[[x_p, y_p, color_switch]].dropna().copy()
                plot_df[color_switch] = plot_df[color_switch].map({True: "ON", False: "OFF"})
                st.scatter_chart(plot_df, x=x_p, y=y_p, color=color_switch, size=40)
            else:
                st.info("No parameter columns found in accepted rows.")

            if "nearest_structure" in df_sp.columns:
                with st.expander("Nearest M-structure distribution", expanded=False):
                    st.bar_chart(df_sp["nearest_structure"].value_counts(), width="stretch")
                    st.caption(
                        "Maps each accepted switch state to the nearest M1-M5 label — "
                        "connecting switch posterior back to conventional structure comparison."
                    )

        # ---- sp_tab6: Downloads --------------------------------------------
        with sp_tab6:
            import json as _json

            _sp_settings = st.session_state.get("sp_settings", {})
            _sp_tag = _run_tag(_sp_settings)

            # --- helpers to serialize special columns -----------------------
            def _serialize_per_pattern(rows: list[dict]) -> list[dict]:
                """Copy rows, serialising per_pattern_matched dicts to JSON strings."""
                out = []
                for r in rows:
                    row = dict(r)
                    ppm = row.get("per_pattern_matched")
                    if isinstance(ppm, dict):
                        # tuples (matched, weight) → JSON arrays for CSV portability
                        row["per_pattern_matched"] = _json.dumps(
                            {k: [bool(v[0]), float(v[1])] for k, v in ppm.items()}
                        )
                    out.append(row)
                return out

            _df_sp_accepted  = pd.DataFrame(_serialize_per_pattern(sp.accepted_rows))
            _df_sp_posterior = pd.DataFrame(sp.posterior_table)

            _evaluated_rows = getattr(sp, "evaluated_rows", None) or sp.accepted_rows
            _df_sp_evaluated = pd.DataFrame(_serialize_per_pattern(_evaluated_rows))

            # OC_k table (pattern-level; switch column is repeated for each switch)
            if _rach_modules_ok and _oc_results:
                _df_oc = pd.DataFrame([
                    {"pattern": r.pattern, "switch": r.switch,
                     "OC_k": round(r.OC_k, 4),
                     "R_full": round(r.R_full, 4), "R_loo": round(r.R_loo, 4),
                     "n_full": r.n_full, "n_loo": r.n_loo}
                    for r in _oc_results
                ])
            else:
                _df_oc = pd.DataFrame()

            # Heuristic NOV table
            if _rach_modules_ok and _nov_results:
                _df_nov = pd.DataFrame([
                    {"priority": r.priority, "candidate": r.candidate,
                     "NOV_delta_R": round(r.expected_resolvability_gain, 4),
                     "R_current": round(r.current_R, 4),
                     "target_switches": ", ".join(r.target_switches),
                     "rationale": r.rationale[:300]}
                    for r in _nov_results
                ])
            else:
                _df_nov = pd.DataFrame()

            # RACH summary
            if _rach_modules_ok:
                _df_rach_summary = pd.DataFrame([{
                    "n_switches": _rs.n_switches,
                    "n_accepted": _rs.n_accepted,
                    "D_RACH": round(_rs.causal_degeneracy, 4),
                    "K_max": round(_rs.max_degeneracy, 4),
                    "R_RACH": round(_rs.causal_resolvability, 4),
                    "total_Ij": round(_rach_metrics.total_identifiability, 4),
                    "threshold": _thresh_display,
                    "acceptance_rule": _sp_settings.get("acceptance_rule", ""),
                    "preset": _sp_settings.get("preset_name", ""),
                    "n_attempts": _sp_settings.get("n_attempts", ""),
                    "seed": _sp_settings.get("seed", ""),
                }])
            else:
                _df_rach_summary = pd.DataFrame()

            _zip_contents = {
                f"{_sp_tag}_accepted_rows":           _df_sp_accepted,
                f"{_sp_tag}_evaluated_rows":          _df_sp_evaluated,
                f"{_sp_tag}_posterior_table":         _df_sp_posterior,
                f"{_sp_tag}_observation_contribution": _df_oc,
                f"{_sp_tag}_nov_table":               _df_nov,
                f"{_sp_tag}_rach_summary":            _df_rach_summary,
            }

            st.download_button(
                "⬇ Download ALL RACH inference tables as ZIP",
                _build_zip(_zip_contents),
                f"{_sp_tag}_rach_inference.zip",
                "application/zip",
                use_container_width=True,
                type="primary",
            )
            st.caption(
                "ZIP contains: accepted_rows · evaluated_rows · posterior_table · "
                "observation_contribution · nov_table · rach_summary  \n"
                "`evaluated_rows.csv` is required to reproduce OC_k (LOO re-acceptance "
                "can recover previously-rejected draws that become accepted when a pattern is removed)."
            )
            st.divider()

            col_dl1, col_dl2, col_dl3 = st.columns(3)
            with col_dl1:
                st.download_button(
                    "accepted_rows.csv  (A_ε sample)",
                    _df_sp_accepted.to_csv(index=False).encode("utf-8"),
                    f"{_sp_tag}_accepted_rows.csv", "text/csv",
                )
                st.download_button(
                    "evaluated_rows.csv  (all draws)",
                    _df_sp_evaluated.to_csv(index=False).encode("utf-8"),
                    f"{_sp_tag}_evaluated_rows.csv", "text/csv",
                    help="Required for unbiased OC_k reproduction.",
                )
            with col_dl2:
                st.download_button(
                    "posterior_table.csv  (CA_j, BF)",
                    _df_sp_posterior.to_csv(index=False).encode("utf-8"),
                    f"{_sp_tag}_posterior_table.csv", "text/csv",
                )
                if not _df_oc.empty:
                    st.download_button(
                        "observation_contribution.csv  (OC_k)",
                        _df_oc.to_csv(index=False).encode("utf-8"),
                        f"{_sp_tag}_observation_contribution.csv", "text/csv",
                    )
            with col_dl3:
                if not _df_nov.empty:
                    st.download_button(
                        "nov_table.csv  (heuristic NOV)",
                        _df_nov.to_csv(index=False).encode("utf-8"),
                        f"{_sp_tag}_nov_table.csv", "text/csv",
                    )
                if not _df_rach_summary.empty:
                    st.download_button(
                        "rach_summary.csv",
                        _df_rach_summary.to_csv(index=False).encode("utf-8"),
                        f"{_sp_tag}_rach_summary.csv", "text/csv",
                    )

