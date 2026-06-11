"""Streamlit app for RACH: Restricted Admissible Causal Hypotheses.

Workflow
--------
1. Constrain  -- ecological constraint grammar rejects implausible latent parameter combos
2. Sample     -- random draws from ecology-principled trade-off priors
3. Simulate   -- stochastic ABM: the canonical RACH f(θ,s) for this system
4. Filter     -- ABC rejection against independent Inoue-series gradient targets
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
    load_population_env,
    observed_gradient_patterns,
    observed_pairwise_relations,
    ordered_populations,
    response_target_patterns,
)
from examples.campanula_izu.pattern_evaluator import (
    ABMPopulationProxy,
    evaluate_patterns,
)
from examples.campanula_izu.campanula_phenomenological import (
    default_campanula_gradient_environments,
    simulate_campanula_gradient,
)

st.set_page_config(
    page_title="RACH -- Campanula / Izu Islands",
    layout="wide",
    page_icon=":telescope:",
)

# ---------------------------------------------------------------------------
# Observed patterns
# ---------------------------------------------------------------------------
# y_obs is the role-filtered observed_target set, loaded internally by the
# inference functions (response_target_patterns()). The app no longer threads a
# separate observed_rels/pattern_weights dict into inference — those arguments
# were ignored and have been removed.

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
    {"Step": "4. Accept",      "RACH object": "d ≤ ε",      "Meaning": "Accept if simulated patterns P_sim match independent y_obs gradients from the Inoue series within tolerance ε. hypothesis_prediction and input_context rows excluded."},
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
                    _, payload = simulate_structure_proxy(
                        structure, model_params, env_slopes=_env_slopes
                    )
            except Exception:
                payload = {"final_values": [], "generation_rows": []}

            # --- Primary gradient pattern targets ---
            # Acceptance is driven by observed_target gradient patterns
            # (gradient_slope + rank_order across the isolation axis).
            # input_context rows (predictor variables) are excluded automatically.
            _outputs_list = payload.get("outputs_list", [])
            _is_abm = payload.get("abm", False)
            # Use observed_target patterns as y_obs.
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

# ---------------------------------------------------------------------------
# Navigation steps
# ---------------------------------------------------------------------------
_STEPS = [
    "① Ensemble",
    "② RACH Inference",
    "③ CA_j",
    "④ D · R",
    "⑤ OC_k",
    "⑥ NOV",
    "⑦ Parameter A_ε",
    "⑧ Downloads",
]

_STEP_SUBTITLES = {
    "① Ensemble":        "Prior sensitivity grid — robustness check",
    "② RACH Inference":  "Run A_ε sampling (ABM backend)",
    "③ CA_j":            "Causal admissibility P(s_j=1 | A_ε)",
    "④ D · R":           "Degeneracy & resolvability",
    "⑤ OC_k":            "Observation contribution (LOO)",
    "⑥ NOV":             "Next-observation value",
    "⑦ Parameter A_ε":   "Accepted (θ,s) in parameter space",
    "⑧ Downloads":       "Export all tables as CSV / ZIP",
}

if "nav_step" not in st.session_state:
    st.session_state["nav_step"] = _STEPS[0]

# ---------------------------------------------------------------------------
# Page header (always shown)
# ---------------------------------------------------------------------------
st.title("RACH — Causal Admissibility & Degeneracy Framework")
st.caption(
    "**RACH** (*Restricted Admissible Causal Hypotheses*) — "
    "estimates the admissible causal region A_ε and quantifies "
    "CA_j, D, R, OC_k, NOV.  "
    "Worked example: Izu Islands *Campanula microdonta* system "
    "(older literature may refer to the broader *C. punctata* complex)."
)
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
| y_obs | Independent observations | Inoue-series gradients: flower_size decreases with isolation (Inoue & Amano 1986) + selfing/outcrossing shifts with isolation (Inoue 1990). Fis is excluded until independently source-confirmed; nectar_guide is planned own-field data; herkogamy is latent dichogamy. |

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
            "Rows shown above are the only patterns used as y_obs in ABC acceptance. "
            "input_context, hypothesis_prediction, excluded_from_ABC, diagnostic_only, "
            "and planned/pending rows are excluded."
        )
        st.warning(
            "Current empirical y_obs contains only 2 source-confirmed directional gradients: "
            "selfing_distance and flower_size_distance. Causal resolution is expected to be "
            "low until future observations are measured. This is a preliminary worked example, "
            "not an empirical resolution of the C. microdonta causal history."
        )
    with col_xobs:
        st.markdown("**x_obs — fixed empirical context fed into f(x_obs; θ, s)**")
        _xobs_rows = [
            {"variable": "island_distance", "role": "input_context", "notes": "normalised isolation index (0=mainland, 1=Hachijo)"},
            {"variable": "primary_pollinator_frequency", "role": "input_context", "notes": "Bombus ardens presence/frequency per island (Inoue-series context)"},
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
    st.header("⚙ 設定")

    # ── Shared inference settings ──────────────────────────────────────────
    presets = predefined_tradeoff_presets()
    _preset_keys = list(presets.keys())
    preset_name = st.selectbox(
        "θ prior preset",
        _preset_keys,
        index=_preset_keys.index("literature_grounded") if "literature_grounded" in _preset_keys else 0,
        format_func=lambda k: {
            "literature_grounded": "literature_grounded  (empirical — primary)",
            "broad_prior":         "broad_prior  (sensitivity sweep)",
        }.get(k, k),
    )
    _rules = available_rules()
    acceptance_rule = st.selectbox(
        "ε (ABC acceptance rule)",
        _rules,
        index=_rules.index("weighted_lax") if "weighted_lax" in _rules else 0,
        format_func=lambda r: {
            "strict_all":      "strict - all current y_obs patterns must match",
            "weighted_strict": "weighted strict — match = 1.0",
            "weighted_lax":    "weighted lax — match ≥ 0.80  ← recommended",
            "relaxed_0.83":    "relaxed — ≥4/5",
            "relaxed_0.67":    "lax — ≥3/5",
        }.get(r, r),
    )
    from causal_model.switch_inference import GRADIENT_N_PATTERNS as _N_PAT
    _thresh_display = GRADIENT_THRESH_MAP.get(acceptance_rule, 1.0)
    st.caption(f"y_obs: {_N_PAT} patterns · threshold ≥ {_thresh_display:.3f}")
    st.caption(
        "Current empirical y_obs contains only two source-confirmed directional "
        "gradients: selfing_distance and flower_size_distance. Causal resolution "
        "is expected to be low until future observations are measured."
    )
    seed = st.number_input("Random seed", 0, 999999, 42, 1)

    with st.expander("Advanced RACH options (optional)", expanded=False):
        distance_mode = st.selectbox("distance_mode", ["match_rate", "standardized", "hybrid"], index=0)
        epsilon_mode = st.selectbox("epsilon_mode", ["fixed", "adaptive_percentile"], index=0)
        adaptive_percentile = st.number_input("adaptive_percentile", 0.1, 50.0, 5.0, 0.5)
        min_accepted_adaptive = st.number_input("min_accepted", 1, 500, 20, 1, key="adaptive_min_accepted")
        structure_prior_lambda = st.number_input("structure_prior_lambda", 0.0, 5.0, 0.0, 0.1)
        show_distance_components = st.checkbox("show_distance_components", value=False)
        st.caption(
            "Optional sensitivity controls only. Unmeasured guide, herkogamy, Fis, "
            "seed set, and visitation remain NOV/future observations, not current y_obs."
        )

    # ── ABM settings ───────────────────────────────────────────────────────
    with st.expander("ABM 設定 (② で使用)", expanded=False):
        sp_n_attempts = st.slider(
            "Joint prior draws (θ,s)", 50, 1000, 200, 50, key="sp_n_abm",
        )
        sp_abm_generations = st.slider("ABM generations", 10, 80, 30, 10, key="sp_gen")
        sp_abm_popsize     = st.slider("ABM population size", 50, 300, 100, 50, key="sp_pop")
        sp_abm_replicates  = st.slider("ABM replicates / island", 1, 5, 3, 1, key="sp_rep")
        _est_sec = int(sp_n_attempts * 0.30 * sp_abm_replicates / 3)
        st.caption(f"推定実行時間: ~{_est_sec}s")

    st.divider()

    # ── Step navigation ────────────────────────────────────────────────────
    st.subheader("分析ステップ")

    _has_ens = "_ens_results" in st.session_state
    _has_inf = "sp_result" in st.session_state

    def _nav_icon(i: int) -> str:
        if i == 0:
            return "✅" if _has_ens else "▶"
        if i == 1:
            return "✅" if _has_inf else ("▶" if _has_ens else "⬜")
        return "🟢" if _has_inf else "🔒"

    _nav_labels = [f"{_nav_icon(i)}  {s}" for i, s in enumerate(_STEPS)]
    _cur_idx    = _STEPS.index(st.session_state.get("nav_step", _STEPS[0]))

    _sel_label = st.radio(
        "ステップ選択",
        _nav_labels,
        index=_cur_idx,
        label_visibility="collapsed",
    )
    for _i, _lbl in enumerate(_nav_labels):
        if _sel_label == _lbl:
            st.session_state["nav_step"] = _STEPS[_i]
            break

    st.divider()

    # ── θ prior ranges ─────────────────────────────────────────────────────
    _preset_obj = presets[preset_name]
    with st.expander(f"θ prior ranges — {preset_name}", expanded=False):
        st.caption(_preset_obj.description)
        _lit_map   = {src.parameter: src for src in LITERATURE_SOURCES}
        _prior_rows = []
        for key, (lo, hi) in _preset_obj.ranges.items():
            src = _lit_map.get(key)
            _prior_rows.append({
                "Parameter": key, "Lower": lo, "Upper": hi,
                "Empirical basis": src.empirical_range if src else "broad",
                "Source": src.citation if src else "n/a",
            })
        st.dataframe(pd.DataFrame(_prior_rows), width="stretch", hide_index=True)

    # ── Supplementary: M1-M5 ──────────────────────────────────────────────
    with st.expander("補足: M1-M5 構造比較", expanded=False):
        _m5_backend = "stochastic_abm"
        _m5_n       = st.slider("Prior draws", 20, 500, 80, 20, key="n_attempts_abm")
        _m5_gen     = st.slider("ABM generations", 10, 100, 40, 10, key="m5_gen")
        _m5_pop     = st.slider("ABM population size", 50, 500, 150, 50, key="m5_pop")
        _m5_rep     = st.slider("ABM replicates / island", 1, 5, 1, 1, key="m5_rep")
        run_button  = st.button("Run structure comparison", width="stretch")

# ---------------------------------------------------------------------------
# M1-M5 supplementary run (sidebar button)
# ---------------------------------------------------------------------------
if run_button:
    _m5_bar  = st.progress(0.0, text="M1-M5: starting…")
    _m5_stat = st.empty()

    def _m5_cb(done, total, status):
        _m5_bar.progress(done / total if total > 0 else 0.0,
                         text=f"M1-M5: {done}/{total} ({100*done//max(total,1)}%)")
        _m5_stat.caption(status)

    _m5_result = run_research_mode(
        preset_name=preset_name, n_attempts=_m5_n, seed=int(seed),
        acceptance_rule=acceptance_rule, backend=_m5_backend,
        generations=_m5_gen, population_size=_m5_pop, replicates=_m5_rep,
        progress_callback=_m5_cb,
    )
    _m5_bar.progress(1.0, text="Done ✓")
    _m5_stat.empty()
    st.session_state["research_result"] = _m5_result
    st.session_state["research_settings"] = {
        "preset_name": preset_name, "n_attempts": _m5_n,
        "seed": int(seed), "acceptance_rule": acceptance_rule,
        "backend": _m5_backend,
        "generations": _m5_gen, "population_size": _m5_pop, "replicates": _m5_rep,
    }

if "research_result" in st.session_state:
    _m5r = st.session_state["research_result"]
    with st.expander("補足結果: M1-M5 構造比較", expanded=False):
        _m5_df_sum = _m5r["hypothesis_summary"]
        if not _m5_df_sum.empty:
            st.bar_chart(_m5_df_sum.set_index("causal_hypothesis")[["admissibility_rate"]],
                         width="stretch")
            stretch_df(_m5_df_sum, hide_index=True)
        else:
            st.warning("No admissible runs.")

# ===========================================================================
# Main step content (vertical navigation)
# ===========================================================================
_current_step = st.session_state.get("nav_step", _STEPS[0])
_step_idx     = _STEPS.index(_current_step)
_has_ens      = "_ens_results" in st.session_state
_has_inf      = "sp_result" in st.session_state

st.divider()
st.subheader(_current_step)
st.caption(_STEP_SUBTITLES.get(_current_step, ""))


def _next_btn(label: str, next_step: str) -> None:
    if st.button(label, type="primary", width="stretch"):
        st.session_state["nav_step"] = next_step
        st.rerun()


# ===========================================================================
# ① Ensemble
# ===========================================================================
if _step_idx == 0:
    st.markdown(
        "複数の (θ-prior preset, ε ルール) を網羅的に走査し、先験依存しない結論だけを抽出します。  \n"
        "ここで得たベスト設定を ② RACH Inference に引き継ぎます。"
    )

    try:
        from causal_model.ensemble import (
            run_ensemble as _run_ensemble,
            select_best_ensemble_setting as _select_best,
            ensemble_ca_j as _ensemble_ca_j,
            sensitivity_range as _sensitivity_range,
            classify_switch_robustness as _classify_robustness,
        )
        from causal_model.switch_inference import GRADIENT_THRESH_MAP as _THRESH_MAP
        from causal_model.parameter_sampling import predefined_tradeoff_presets as _presets_fn
        _ensemble_ok = True
        _ensemble_err = ""
    except Exception as _e:
        _ensemble_ok = False
        _ensemble_err = str(_e)

    if not _ensemble_ok:
        st.error(f"Ensemble module load failed: {_ensemble_err}")
    else:
        _all_presets = list(_presets_fn().keys())
        _all_rules   = list(_THRESH_MAP.keys())

        _ec1, _ec2 = st.columns(2)
        with _ec1:
            _ens_presets = st.multiselect(
                "θ-prior presets", options=_all_presets, default=_all_presets,
            )
        with _ec2:
            _ens_rules = st.multiselect(
                "ε ルール", options=_all_rules,
                default=["weighted_lax", "relaxed_0.83", "relaxed_0.67"],
            )

        _ec3, _ec4, _ec5 = st.columns(3)
        with _ec3:
            _ens_backend_sel = st.radio(
                "Backend", ["proxy (fast)", "abm (slow)"], index=0, horizontal=True,
            )
            _ens_backend_key = "proxy" if _ens_backend_sel.startswith("proxy") else "abm"
        with _ec4:
            _ens_n = st.slider(
                "Draws / config", 50, 500,
                200 if _ens_backend_key == "proxy" else 100, 50,
            )
        with _ec5:
            _ens_min_n = st.number_input("Min accepted", 5, 100, 20, 5)
        _ens_seed = st.number_input("Seed", value=42, step=1, key="ens_seed")

        with st.expander("ベスト設定の安定性フィルタ (issue #25)"):
            _sf1, _sf2, _sf3 = st.columns(3)
            with _sf1:
                _ens_min_rate = st.number_input(
                    "Min acceptance rate", 0.0, 1.0, 0.02, 0.01, format="%.2f",
                    help="n_accepted / n_evaluated の下限。厳しすぎる設定（確率的アーティファクト）を除外。",
                )
            with _sf2:
                _ens_use_max_rate = st.checkbox("Max acceptance rate を有効化", value=False)
                _ens_max_rate = st.number_input(
                    "Max acceptance rate", 0.0, 1.0, 0.80, 0.05, format="%.2f",
                    disabled=not _ens_use_max_rate,
                    help="緩すぎる設定（A_ε がほぼ制約されない）を除外。",
                )
            with _sf3:
                _ens_mode_sel = st.radio(
                    "Selection criterion", ["max R_RACH", "max accepted"], index=0,
                    help="フィルタ通過設定の中から R_RACH 最大、または受容数最大を選ぶ。",
                )
        _ens_mode_key = "max_R" if _ens_mode_sel.startswith("max R") else "max_accepted"
        _ens_max_rate_val = _ens_max_rate if _ens_use_max_rate else None
        st.session_state["_ens_sel_criteria"] = {
            "min_accepted": int(_ens_min_n),
            "min_acceptance_rate": float(_ens_min_rate),
            "max_acceptance_rate": _ens_max_rate_val,
            "mode": _ens_mode_key,
        }

        if st.button("▶ Run Ensemble", type="primary", width="stretch"):
            if not _ens_presets or not _ens_rules:
                st.warning("プリセットとルールを1つ以上選択してください。")
            else:
                _n_configs  = len(_ens_presets) * len(_ens_rules)
                _ens_prog   = st.progress(0.0, text="Starting ensemble…")
                _ens_status = st.empty()

                def _ens_cb(done, total, preset, rule):
                    _ens_prog.progress(done / max(total, 1),
                                       text=f"{preset} / {rule}  ({done}/{total})")
                    _ens_status.caption(f"Running: {preset} + {rule}")

                with st.spinner(f"{_n_configs} configs 実行中…"):
                    _ens_results = _run_ensemble(
                        presets=_ens_presets, acceptance_rules=_ens_rules,
                        switches=CAMPANULA_SWITCHES,
                        n_attempts=_ens_n, seed=int(_ens_seed),
                        backend=_ens_backend_key,
                        distance_mode=distance_mode,
                        epsilon_mode=epsilon_mode,
                        adaptive_percentile=float(adaptive_percentile),
                        min_accept=int(min_accepted_adaptive),
                        structure_prior_lambda=float(structure_prior_lambda),
                        progress_callback=_ens_cb,
                    )
                _ens_prog.progress(1.0, text="Done ✓")
                _ens_status.empty()
                st.session_state["_ens_results"] = _ens_results
                try:
                    st.session_state["_ens_sens"] = _sensitivity_range(_ens_results)
                except Exception:
                    pass
                # Auto-advance to ②
                st.session_state["nav_step"] = _STEPS[1]
                st.rerun()

        if "_ens_results" in st.session_state:
            _ens_res  = st.session_state["_ens_results"]
            _sw_names = [sw.name for sw in CAMPANULA_SWITCHES]
            _ens_sens_cur = st.session_state.get("_ens_sens", {})
            _ca_avg   = _ensemble_ca_j(_ens_res, min_accepted=1)

            st.markdown("#### ロバスト結論サマリー")
            _rob_verdicts = _classify_robustness(_ens_res)
            st.session_state["_ens_robustness"] = _rob_verdicts
            if _rob_verdicts:
                def _badge(rv):
                    if rv.is_robust:
                        return "🔒 robust 結論"
                    if not rv.is_resolved:
                        return "❓ 未解決（要追加観測）"
                    return "⚠ 先験/ε 感度大"
                _rob_rows = [{
                    "switch": _rv.switch,
                    "ensemble CA_j": _rv.mean_ca_j,
                    "sensitivity": _rv.sensitivity_range,
                    "call": _rv.call,
                    "verdict": _badge(_rv),
                } for _rv in _rob_verdicts]
                stretch_df(pd.DataFrame(_rob_rows), hide_index=True)
                _n_robust = sum(1 for _rv in _rob_verdicts if _rv.is_robust)
                if _n_robust == 0:
                    st.warning(
                        "robust な結論ゼロ。全 switch が未解決 or 先験依存 = "
                        "現状の観測では因果が分離できていません（R_RACH も低いはず）。"
                        "⑥ NOV で次に測るべき観測を確認してください。"
                    )

            _sel_crit = st.session_state.get("_ens_sel_criteria", {})
            _sel = _select_best(
                _ens_res,
                min_accepted=int(_sel_crit.get("min_accepted", _ens_min_n)),
                min_acceptance_rate=float(_sel_crit.get("min_acceptance_rate", 0.02)),
                max_acceptance_rate=_sel_crit.get("max_acceptance_rate"),
                mode=_sel_crit.get("mode", "max_R"),
            )
            _best = _sel.best
            if _best:
                if _sel.passed_filters:
                    st.success(
                        f"**推奨設定 → ② で使用:** `{_best.preset_name}` + `{_best.acceptance_rule}`  "
                        f"(R={_best.R_RACH:.3f},  n={_best.n_accepted},  "
                        f"acc_rate={_best.acceptance_rate:.3f})"
                    )
                else:
                    st.warning(
                        f"**フォールバック設定 → ② で使用:** `{_best.preset_name}` + "
                        f"`{_best.acceptance_rule}`  (R={_best.R_RACH:.3f},  n={_best.n_accepted})"
                    )
                st.caption(_sel.rationale)

            st.divider()
            st.markdown("#### 設定比較テーブル")
            _ens_rows = []
            for _r in _ens_res:
                _row = {"preset": _r.preset_name, "rule": _r.acceptance_rule,
                        "ε": _r.threshold, "n_accepted": _r.n_accepted,
                        "D_RACH": _r.D_RACH, "R_RACH": _r.R_RACH,
                        "_is_best": (_r is _best)}
                for _sw in _sw_names:
                    _row[f"CA_{_sw[:10]}"] = _r.ca_j.get(_sw, float("nan"))
                _ens_rows.append(_row)
            _df_ens = pd.DataFrame(_ens_rows)
            _df_disp = _df_ens.drop(columns=["_is_best"])
            st.dataframe(
                _df_disp.style.apply(
                    lambda row: [
                        "background-color: #d4edda" if _ens_rows[row.name]["_is_best"] else ""
                        for _ in row
                    ], axis=1,
                ), width="stretch",
            )

            _c1, _c2 = st.columns(2)
            with _c1:
                st.markdown("**Ensemble CA_j**")
                if _ca_avg:
                    st.bar_chart(
                        pd.DataFrame([{"switch": k, "CA_j": v} for k, v in _ca_avg.items()])
                        .set_index("switch"), width="stretch",
                    )
            with _c2:
                st.markdown("**感度レンジ (max − min CA_j)**")
                if _ens_sens_cur:
                    st.bar_chart(
                        pd.DataFrame([{"switch": k, "sensitivity": v} for k, v in _ens_sens_cur.items()])
                        .set_index("switch"), width="stretch",
                    )
                    st.caption("< 0.20 → ロバスト。≥ 0.20 → 先験依存。")

            st.line_chart(
                pd.DataFrame([{"config": f"{_r.preset_name}/{_r.acceptance_rule}", **_r.ca_j}
                               for _r in _ens_res]).set_index("config"),
                width="stretch",
            )
            st.divider()
            st.download_button("⬇ ensemble_comparison.csv", _df_disp.to_csv(index=False).encode("utf-8"),
                               "ensemble_comparison.csv", "text/csv")
            st.divider()
            _next_btn("② RACH Inference へ進む →", _STEPS[1])


# ===========================================================================
# ② RACH Inference
# ===========================================================================
elif _step_idx == 1:
    if _has_ens:
        try:
            from causal_model.ensemble import best_config as _bc2
            _best2 = _bc2(st.session_state["_ens_results"], min_accepted=20)
            _sens2 = st.session_state.get("_ens_sens", {})
            if _best2:
                st.info(
                    f"**Ensemble 推奨設定:** `{_best2.preset_name}` + `{_best2.acceptance_rule}`  "
                    f"(R={_best2.R_RACH:.3f})  \nサイドバーの設定をこれに合わせてから実行してください。"
                )
            _sensitive2 = [k for k, v in _sens2.items() if v >= 0.20]
            if _sensitive2:
                st.warning(f"感度大 (≥0.20): **{', '.join(_sensitive2)}** — ⑥ NOV で追加観測計画を。")
        except Exception:
            pass
    else:
        st.info("① Ensemble を先に実行するとベスト設定が自動推奨されます。スキップも可。")

    st.markdown(
        f"**現在の設定:** `{preset_name}` + `{acceptance_rule}` · threshold ≥ {_thresh_display:.3f}  \n"
        f"ABM: {st.session_state.get('sp_n_abm', 200)} draws · "
        f"{st.session_state.get('sp_gen', 30)} gen · "
        f"{st.session_state.get('sp_pop', 100)} pop · "
        f"{st.session_state.get('sp_rep', 3)} rep"
    )

    if st.button("▶ Run Recommended RACH", type="primary", width="stretch"):
        _sp_bar  = st.progress(0.0, text="Switch Posterior: starting…")
        _sp_stat = st.empty()

        def _sp_progress(done: int, total: int, status: str) -> None:
            _sp_bar.progress(done / total if total > 0 else 0.0,
                             text=f"Switch Posterior: {done}/{total} ({100*done//max(total,1)}%)")
            _sp_stat.caption(status)

        sp_result = run_switch_posterior_inference_abm(
            preset_name=preset_name,
            n_attempts=int(st.session_state.get("sp_n_abm", 200)),
            acceptance_rule=acceptance_rule,
            seed=int(seed) + 1,
            generations=st.session_state.get("sp_gen", 30),
            population_size=st.session_state.get("sp_pop", 100),
            replicates=st.session_state.get("sp_rep", 3),
            distance_mode=distance_mode,
            epsilon_mode=epsilon_mode,
            adaptive_percentile=float(adaptive_percentile),
            min_accept=int(min_accepted_adaptive),
            structure_prior_lambda=float(structure_prior_lambda),
            progress_callback=_sp_progress,
        )
        _sp_bar.progress(1.0, text="Switch Posterior: Done ✓")
        _sp_stat.empty()
        st.session_state["sp_result"]   = sp_result
        st.session_state["sp_settings"] = {
            "preset_name": preset_name, "seed": int(seed) + 1,
            "acceptance_rule": acceptance_rule, "backend": "stochastic_abm",
            "distance_mode": distance_mode,
            "epsilon_mode": epsilon_mode,
            "adaptive_percentile": float(adaptive_percentile),
            "min_accept": int(min_accepted_adaptive),
            "structure_prior_lambda": float(structure_prior_lambda),
        }
        # Auto-advance to ③ CA_j
        st.session_state["nav_step"] = _STEPS[2]
        st.rerun()

    if _has_inf:
        _sp = st.session_state["sp_result"]
        st.success(
            f"✅ 推論完了 — |A_ε| = {len(_sp.accepted_rows)} accepted  "
            f"(acceptance rate {_sp.acceptance_rate:.1%})"
        )
        if len(_sp.accepted_rows) < 30:
            st.warning(f"accepted = {len(_sp.accepted_rows)} < 30 → 推定不安定。draws を増やすか ε を緩めてください。")
        _next_btn("③ CA_j で結果を見る →", _STEPS[2])


# ===========================================================================
# Steps ③–⑧ require inference results
# ===========================================================================
elif _step_idx >= 2 and not _has_inf:
    st.info("② RACH Inference を先に実行してください。")
    _next_btn("② RACH Inference へ", _STEPS[1])

# ===========================================================================
# ③ CA_j
# ===========================================================================
elif _step_idx == 2:
    sp = st.session_state["sp_result"]
    _sp_settings = st.session_state.get("sp_settings", {})
    _thresh_sp   = GRADIENT_THRESH_MAP.get(_sp_settings.get("acceptance_rule", acceptance_rule), 1.0)

    _mc1, _mc2, _mc3, _mc4 = st.columns(4)
    _mc1.metric("|A_ε| accepted", len(sp.accepted_rows))
    _mc2.metric("Total draws", sp.n_attempts)
    _mc3.metric("Acceptance rate", f"{sp.acceptance_rate:.1%}")
    _mc4.metric("K (switches)", len(CAMPANULA_SWITCHES))
    st.caption(
        f"distance_mode={_sp_settings.get('distance_mode', 'match_rate')} · "
        f"epsilon_mode={_sp_settings.get('epsilon_mode', 'fixed')} · "
        f"structure_prior_lambda={_sp_settings.get('structure_prior_lambda', 0.0)}"
    )
    if show_distance_components and sp.accepted_rows:
        _dc_rows = []
        for _r in sp.accepted_rows[:10]:
            for _pat, (_dist, _w) in _r.get("per_pattern_distance", {}).items():
                _dc_rows.append({
                    "sample_id": str(_r.get("sample_id", ""))[:8],
                    "pattern": _pat,
                    "distance": _dist,
                    "weight": _w,
                })
        if _dc_rows:
            stretch_df(pd.DataFrame(_dc_rows), hide_index=True)

    if len(sp.accepted_rows) < 30:
        st.warning(f"Only {len(sp.accepted_rows)} accepted — estimates unstable.")

    if not sp.accepted_rows:
        st.error("No accepted samples. Use a more relaxed ε or increase draws.")
    else:
        try:
            _n_acc = len(sp.accepted_rows)
            _ca_now = {
                sw.name: round(sum(1 for r in sp.accepted_rows if r.get(sw.name)) / _n_acc, 3)
                for sw in CAMPANULA_SWITCHES
            }
            _ens_sens_rc = st.session_state.get("_ens_sens", {})
            with st.expander("**Robust Conclusions** (A_ε サマリー)", expanded=True):
                _rc_cols = st.columns(len(CAMPANULA_SWITCHES))
                for _i, sw in enumerate(CAMPANULA_SWITCHES):
                    _cv  = _ca_now.get(sw.name, 0.5)
                    _sv  = _ens_sens_rc.get(sw.name)
                    _verd = "✅ ON" if _cv > 2/3 else ("❌ OFF" if _cv < 1/3 else "〜 不定")
                    _rlbl = (
                        "🔒 Robust" if _sv is not None and _sv < 0.20
                        else (f"⚠ 感度={_sv:.2f}" if _sv is not None else "(Ensemble未実行)")
                    )
                    _rc_cols[_i].metric(sw.name[:18], f"CA={_cv:.2f}",
                                        delta=f"{_verd}  {_rlbl}", delta_color="normal")
                _rob_sw = [k for k, v in _ens_sens_rc.items() if v < 0.20] if _ens_sens_rc else []
                _sen_sw = [k for k, v in _ens_sens_rc.items() if v >= 0.20] if _ens_sens_rc else []
                if _rob_sw:
                    st.success(f"**ロバスト結論** (感度 < 0.20): {', '.join(_rob_sw)}")
                if _sen_sw:
                    st.warning(f"**先験依存** (感度 ≥ 0.20): {', '.join(_sen_sw)}  \n→ ⑥ NOV で追加観測計画を。")
                if not _ens_sens_rc:
                    st.info("① Ensemble を先に実行するとロバスト性の判定が表示されます。")
        except Exception:
            pass

        st.markdown("### CA_j = P(s_j = 1 | A_ε)")
        st.caption(
            "Prior = 0.5 (Bernoulli). **BF > 3** → admissible (CA_j > 0.75). **BF < 1/3** → inadmissible (CA_j < 0.25)."
        )
        st.info(
            "**Known-truth benchmark 知見 (S3 注意):**  \n"
            "S3 (island_isolation_common_cause) が S1 (guide_attracts_bombus) と部分的に混同します。  \n"
            "S3 の guide 係数 (0.13) は S1=OFF+S3=ON の描出が S1=ON と競合します。S3 の CA_j は S1 と同時に確認してください。"
        )

        df_post = pd.DataFrame(sp.posterior_table)
        if not df_post.empty:
            st.bar_chart(df_post.set_index("switch")[["P_prior_ON", "P_posterior_ON"]], width="stretch")
            st.caption("左バー = 事前 P(ON) = 0.5.  右バー = CA_j = P(ON | A_ε).")
            stretch_df(df_post[[
                "switch", "biological_question", "P_prior_ON",
                "P_posterior_ON", "Bayes_factor", "interpretation", "n_ON", "n_accepted",
            ]], hide_index=True)
            st.markdown("#### Biological interpretation")
            for _row in sp.posterior_table:
                _interp = str(_row.get("interpretation", ""))
                _icon = (
                    "✅ supported"        if _interp.startswith("supported") else
                    "〜 weakly supported" if _interp.startswith("weakly s") else
                    "❌ opposed"          if _interp.startswith("opposed") else
                    "— uninformative"
                )
                _bf    = _row.get("Bayes_factor")
                _bfstr = f"BF={_bf:.2f}" if _bf is not None else "BF=n/a"
                st.markdown(
                    f"**{_icon} · {_row['switch']}** CA_j={_row['P_posterior_ON']:.3f} ({_bfstr})  \n"
                    f"*{_row.get('biological_question', '')[:100]}*"
                )

        with st.expander("Switch co-activation P(A ON ∩ B ON | A_ε)", expanded=False):
            _coact = compute_coactivation_table(sp.accepted_rows)
            if _coact:
                _df_coact = pd.DataFrame(_coact)
                stretch_df(_df_coact, hide_index=True)
                try:
                    _piv = _df_coact.pivot(index="switch_A", columns="switch_B", values="P_both_ON")
                    st.dataframe(_piv.round(3), width="stretch")
                except Exception:
                    pass
            else:
                st.info("Not enough accepted samples.")

        st.divider()
        _next_btn("④ D · R へ →", _STEPS[3])


# ===========================================================================
# ④ D · R
# ===========================================================================
elif _step_idx == 3:
    sp = st.session_state["sp_result"]

    try:
        from causal_model.causal_admissibility import (
            rach_summary as _rach_summary_fn,
            causal_degeneracy as _cd_fn,
            causal_resolvability as _cr_fn,
        )
        from causal_model.identifiability import compute_rach_theory_metrics as _rach_metrics_fn
        _rs           = _rach_summary_fn(sp.accepted_rows, CAMPANULA_SWITCHES)
        _rach_metrics = _rach_metrics_fn(sp.accepted_rows, CAMPANULA_SWITCHES)
        _dr_ok = True
    except Exception as _e:
        _dr_ok = False
        _dr_err = str(_e)

    st.markdown("### D = H(S | A_ε) · R = 1 − D/K")
    st.info(
        "**Known-truth benchmark 知見:** 複合スイッチ状態 (S1+S2, S1+S3 など) では "
        "R_RACH ≈ 0.19–0.24 が典型的。これは観測データ不足による縮退で、失敗ではなく発見です。"
    )

    if _dr_ok:
        _dm1, _dm2, _dm3, _dm4, _dm5 = st.columns(5)
        _dm1.metric("R — resolvability",  f"{_rs.causal_resolvability:.3f}")
        _dm2.metric("D — degeneracy",     f"{_rs.causal_degeneracy:.3f} bits")
        _dm3.metric("K — max entropy",    f"{_rs.max_degeneracy:.0f} bits")
        _dm4.metric("|A_ε|",              f"{_rs.n_accepted}")
        _dm5.metric("Total I_j",          f"{_rach_metrics.total_identifiability:.3f} bits")

        st.divider()
        st.markdown("#### ε 感度 — D と R の ε 依存性")
        _thresh_map2 = {
            "weighted_lax (≥0.800)":    0.800,
            "relaxed_0.83 (≥0.833)":    5/6,
            "weighted_strict (=1.000)": 1.000,
            "relaxed_0.67 (≥0.667)":    4/6,
        }
        _sens_rows2 = []
        for _lbl, _thr in _thresh_map2.items():
            _filt = [r for r in sp.accepted_rows if r.get("weighted_match_rate", 0.0) >= _thr - 1e-9]
            _n    = len(_filt)
            if _n >= 3:
                _sens_rows2.append({
                    "ε rule": _lbl, "|A_ε|": _n,
                    "D (bits)": round(_cd_fn(_filt, CAMPANULA_SWITCHES), 3),
                    "R":        round(_cr_fn(_filt, CAMPANULA_SWITCHES), 3),
                    "total I_j": round(_rach_metrics_fn(_filt, CAMPANULA_SWITCHES).total_identifiability, 3),
                })
            else:
                _sens_rows2.append({"ε rule": _lbl, "|A_ε|": _n,
                                    "D (bits)": float("nan"), "R": float("nan"), "total I_j": float("nan")})
        stretch_df(pd.DataFrame(_sens_rows2), hide_index=True)

        st.divider()
        st.markdown("#### Per-switch identifiability I_j")
        if hasattr(_rach_metrics, "identifiability_table") and _rach_metrics.identifiability_table:
            _df_ij = pd.DataFrame(_rach_metrics.identifiability_table)
            if not _df_ij.empty and "switch" in _df_ij.columns:
                _ijcol = [c for c in _df_ij.columns if "identifiability" in c.lower() or c == "I_j"]
                if _ijcol:
                    st.bar_chart(_df_ij.set_index("switch")[[_ijcol[0]]], width="stretch")
                stretch_df(_df_ij, hide_index=True)
    else:
        st.error(f"RACH modules failed: {_dr_err}")

    st.divider()
    _next_btn("⑤ OC_k へ →", _STEPS[4])


# ===========================================================================
# ⑤ OC_k
# ===========================================================================
elif _step_idx == 4:
    sp = st.session_state["sp_result"]

    try:
        from causal_model.causal_admissibility import observation_contribution as _oc_fn
        _oc_source  = getattr(sp, "evaluated_rows", None) or sp.accepted_rows
        _thresh_sp2 = GRADIENT_THRESH_MAP.get(
            st.session_state.get("sp_settings", {}).get("acceptance_rule", acceptance_rule), 1.0)
        _oc_results = _oc_fn(_oc_source, CAMPANULA_SWITCHES, threshold=_thresh_sp2)
        _oc_ok = True
    except Exception as _e:
        _oc_ok = False
        _oc_err = str(_e)

    st.markdown("### OC_k = R(O) − R(O \\ {k})")
    st.caption("LOO: パターン k を除いたときの R_RACH の低下量。OC_k > 0 → k は resolvability に貢献。")
    st.caption(
        "**OC_k は pattern-level**（switch 別ではありません）。R_RACH はスイッチ結合 "
        "s ∈ {0,1}^K の*同時*分解能なので、OC_k はパターン k がメカニズム結合全体の "
        "分解能をどれだけ変えるかを表し、パターンごとに 1 値です。"
    )

    if _oc_ok:
        if _oc_results:
            _df_oc = pd.DataFrame([
                {"pattern": r.pattern, "level": r.level, "OC_k": round(r.OC_k, 4),
                 "R_full": round(r.R_full, 4), "R_loo": round(r.R_loo, 4),
                 "n_loo": r.n_loo, "n_switches": r.n_switches}
                for r in _oc_results
            ])
            _df_oc_nz = _df_oc[_df_oc["OC_k"].abs() > 0.0001].sort_values("OC_k", ascending=False)
            if not _df_oc_nz.empty:
                st.bar_chart(
                    _df_oc_nz.set_index("pattern")[["OC_k"]],
                    width="stretch",
                )
                stretch_df(_df_oc_nz, hide_index=True)
            else:
                st.info("All OC_k ≈ 0. パターン間が相関しているか |A_ε| が小さい場合に起こります。")
            stretch_df(_df_oc, hide_index=True)
        else:
            st.info("OC_k データなし。推論を再実行してください。")
    else:
        st.error(f"OC_k computation failed: {_oc_err}")

    st.divider()
    _next_btn("⑥ NOV へ →", _STEPS[5])


# ===========================================================================
# ⑥ NOV
# ===========================================================================
elif _step_idx == 5:
    sp = st.session_state["sp_result"]

    _ens_sens_nov = st.session_state.get("_ens_sens", {})
    _sensitive_sw_names = [k for k, v in _ens_sens_nov.items() if v >= 0.20]
    if _ens_sens_nov:
        _sen_nov = {k: v for k, v in _ens_sens_nov.items() if v >= 0.20}
        if _sen_nov:
            st.info(
                "**Ensemble 感度分析 → 優先 NOV ターゲット:**  \n" +
                "  \n".join(f"- **{k}** (感度={v:.2f})"
                            for k, v in sorted(_sen_nov.items(), key=lambda x: -x[1]))
            )
        else:
            st.success("全スイッチ 感度 < 0.20 でロバストです。")
    else:
        st.caption("① Ensemble を実行すると、どのスイッチの NOV を優先すべきか自動推奨されます。")

    st.markdown("### NOV(q) ≈ E[ R(O ∪ q) − R(O) ]")

    try:
        from causal_model.causal_admissibility import (
            next_observation_value as _nov_fn,
            rach_summary as _rach_summary_fn2,
        )
        _rs2         = _rach_summary_fn2(sp.accepted_rows, CAMPANULA_SWITCHES)
        _nov_results = _nov_fn(sp.accepted_rows, CAMPANULA_SWITCHES,
                               sensitive_switches=_sensitive_sw_names)
        _nov_ok = True
    except Exception as _e:
        _nov_ok = False
        _nov_err = str(_e)

    _nov_mode = st.radio(
        "NOV estimation method", ["Heuristic (instant)", "Simulation (accurate)"],
        horizontal=True,
    )

    if _nov_mode == "Heuristic (instant)":
        if _nov_ok and _nov_results:
            _df_nov = pd.DataFrame([
                {"priority": r.priority, "candidate": r.candidate,
                 "→ sensitive": "⚠ " + ", ".join(r.sensitive_targets)
                                if r.targets_sensitive_switch else "",
                 "ΔR (approx)": round(r.expected_resolvability_gain, 4),
                 "target switches": ", ".join(r.target_switches),
                 "rationale": r.rationale[:120]}
                for r in _nov_results
            ])
            st.bar_chart(_df_nov.set_index("candidate")[["ΔR (approx)"]], width="stretch")
            st.caption(f"Current R = {_rs2.causal_resolvability:.3f}.")
            stretch_df(_df_nov, hide_index=True)
        elif not _nov_ok:
            st.error(f"NOV computation failed: {_nov_err}")
        else:
            st.info("No candidate observations configured.")

    else:
        _thresh_sp3 = GRADIENT_THRESH_MAP.get(
            st.session_state.get("sp_settings", {}).get("acceptance_rule", acceptance_rule), 1.0)
        _nov_backend_sel2 = st.radio(
            "Outcome backend", ["proxy (fast)", "abm (slow, high-fidelity)"],
            index=0, horizontal=True,
        )
        _nov_backend_key2 = "proxy" if _nov_backend_sel2.startswith("proxy") else "abm"
        _nov_n2  = st.slider("Draws / outcome", 50, 500, 200 if _nov_backend_key2 == "proxy" else 50, 50)
        _nov_seed2 = st.number_input("Seed", value=42, step=1, key="nov_seed2")

        if st.button("▶ Run Simulation NOV", type="primary"):
            from causal_model.causal_admissibility import next_observation_value_simulation
            _nov_prog2  = st.progress(0.0, text="Starting NOV simulation…")
            _nov_stat2  = st.empty()

            def _nov_cb2(cand_name, outcome_name, done, total):
                _nov_prog2.progress(done / max(total, 1),
                                    text=f"{cand_name} / {outcome_name} ({done}/{total})")
                _nov_stat2.caption(f"Running: {cand_name} → {outcome_name}")

            with st.spinner("NOV simulation 実行中…"):
                _nov_sim = next_observation_value_simulation(
                    switches=CAMPANULA_SWITCHES, n_attempts=_nov_n2,
                    preset_name=preset_name, acceptance_rule=acceptance_rule,
                    seed=int(_nov_seed2), threshold=_thresh_sp3,
                    progress_callback=_nov_cb2,
                    current_accepted_rows=sp.accepted_rows,
                    nov_backend=_nov_backend_key2,
                )
            _nov_prog2.progress(1.0, text="Done")
            _nov_stat2.empty()
            st.session_state["_nov_sim_results"] = _nov_sim

        if "_nov_sim_results" in st.session_state:
            _sim_res2 = st.session_state["_nov_sim_results"]
            _df_nov_sim = pd.DataFrame([
                {"priority": r.priority, "candidate": r.candidate,
                 "NOV (ΔR)": round(r.expected_resolvability_gain, 4),
                 "R_current": round(r.current_R, 4),
                 "R_expected": round(r.current_R + r.expected_resolvability_gain, 4),
                 "target switches": ", ".join(r.target_switches)}
                for r in _sim_res2
            ])
            st.bar_chart(_df_nov_sim.set_index("candidate")[["NOV (ΔR)"]], width="stretch")
            stretch_df(_df_nov_sim, hide_index=True)
            with st.expander("Outcome details"):
                for _r2 in _sim_res2:
                    st.markdown(f"**{_r2.candidate}** (p={_r2.priority}): {_r2.rationale[:300]}")

    st.divider()
    _next_btn("⑦ Parameter A_ε へ →", _STEPS[6])


# ===========================================================================
# ⑦ Parameter A_ε
# ===========================================================================
elif _step_idx == 6:
    sp = st.session_state["sp_result"]

    st.markdown("### 受容された (θ, s) の分布")
    _df_sp = pd.DataFrame(sp.accepted_rows)
    _sw_names2 = [sw.name for sw in CAMPANULA_SWITCHES]
    _avail = [p for p in [
        "guide_cost", "outcrossing_benefit", "selfing_benefit",
        "inbreeding_depression", "drift_strength",
        "Ne_isolation_slope", "migration_decay_rate", "pollinator_loss_slope",
    ] if p in _df_sp.columns]

    if len(_avail) >= 2:
        _sc1, _sc2, _sc3 = st.columns(3)
        with _sc1:
            _color_sw = st.selectbox(
                "Colour by switch", [s for s in _sw_names2 if s in _df_sp.columns], key="sp_color",
            )
        with _sc2:
            _xp = st.selectbox("X axis (θ)", _avail, key="sp_x")
        with _sc3:
            _yp = st.selectbox("Y axis (θ)", _avail, index=min(1, len(_avail)-1), key="sp_y")
        _pdf = _df_sp[[_xp, _yp, _color_sw]].dropna().copy()
        _pdf[_color_sw] = _pdf[_color_sw].map({True: "ON", False: "OFF"})
        st.scatter_chart(_pdf, x=_xp, y=_yp, color=_color_sw, size=40)
    else:
        st.info("No parameter columns in accepted rows.")

    if "nearest_structure" in _df_sp.columns:
        with st.expander("Nearest M-structure distribution", expanded=False):
            st.bar_chart(_df_sp["nearest_structure"].value_counts(), width="stretch")

    st.divider()
    _next_btn("⑧ Downloads へ →", _STEPS[7])


# ===========================================================================
# ⑧ Downloads
# ===========================================================================
elif _step_idx == 7:
    import json as _json
    sp = st.session_state["sp_result"]
    _sp_settings = st.session_state.get("sp_settings", {})
    _sp_tag = _run_tag(_sp_settings)

    def _ser(rows):
        out = []
        for r in rows:
            row = dict(r)
            ppm = row.get("per_pattern_matched")
            if isinstance(ppm, dict):
                row["per_pattern_matched"] = _json.dumps(
                    {k: [bool(v[0]), float(v[1])] for k, v in ppm.items()}
                )
            out.append(row)
        return out

    _df_accepted  = pd.DataFrame(_ser(sp.accepted_rows))
    _df_posterior = pd.DataFrame(sp.posterior_table)
    _evaluated    = getattr(sp, "evaluated_rows", None) or sp.accepted_rows
    _df_evaluated = pd.DataFrame(_ser(_evaluated))

    try:
        from causal_model.causal_admissibility import (
            observation_contribution as _oc_dl,
            next_observation_value   as _nov_dl,
            rach_summary             as _rs_dl,
        )
        from causal_model.identifiability import compute_rach_theory_metrics as _rm_dl
        _thresh_dl = GRADIENT_THRESH_MAP.get(_sp_settings.get("acceptance_rule", acceptance_rule), 1.0)
        _oc_dl_res  = _oc_dl(getattr(sp, "evaluated_rows", None) or sp.accepted_rows,
                             CAMPANULA_SWITCHES, threshold=_thresh_dl)
        _sens_dl = [k for k, v in st.session_state.get("_ens_sens", {}).items() if v >= 0.20]
        _nov_dl_res = _nov_dl(sp.accepted_rows, CAMPANULA_SWITCHES,
                              sensitive_switches=_sens_dl)
        _rs_dl_res  = _rs_dl(sp.accepted_rows, CAMPANULA_SWITCHES)
        _rm_dl_res  = _rm_dl(sp.accepted_rows, CAMPANULA_SWITCHES)
        _df_oc_dl = pd.DataFrame([
            {"pattern": r.pattern, "level": r.level, "n_switches": r.n_switches,
             "OC_k": round(r.OC_k, 4), "R_full": round(r.R_full, 4),
             "R_loo": round(r.R_loo, 4), "n_full": r.n_full, "n_loo": r.n_loo}
            for r in _oc_dl_res
        ]) if _oc_dl_res else pd.DataFrame()
        _df_nov_dl = pd.DataFrame([
            {"priority": r.priority, "candidate": r.candidate,
             "NOV_delta_R": round(r.expected_resolvability_gain, 4),
             "R_current": round(r.current_R, 4),
             "target_switches": ", ".join(r.target_switches),
             "targets_sensitive_switch": r.targets_sensitive_switch,
             "sensitive_targets": ", ".join(r.sensitive_targets),
             "rationale": r.rationale[:300]}
            for r in _nov_dl_res
        ]) if _nov_dl_res else pd.DataFrame()
        _df_summary_dl = pd.DataFrame([{
            "n_switches": _rs_dl_res.n_switches, "n_accepted": _rs_dl_res.n_accepted,
            "D_RACH": round(_rs_dl_res.causal_degeneracy, 4),
            "K_max": round(_rs_dl_res.max_degeneracy, 4),
            "R_RACH": round(_rs_dl_res.causal_resolvability, 4),
            "total_Ij": round(_rm_dl_res.total_identifiability, 4),
            "threshold": _thresh_dl,
            "acceptance_rule": _sp_settings.get("acceptance_rule", ""),
            "preset": _sp_settings.get("preset_name", ""),
            "seed": _sp_settings.get("seed", ""),
        }])
    except Exception:
        _df_oc_dl = pd.DataFrame()
        _df_nov_dl = pd.DataFrame()
        _df_summary_dl = pd.DataFrame()

    # Ensemble provenance: the main RACH result is reported from the
    # ensemble-selected best setting, so the reproducible ZIP must carry the
    # ensemble scan, the robust/sensitive verdicts, and the selected setting.
    _df_ens_dl = pd.DataFrame()
    _df_rob_dl = pd.DataFrame()
    _df_best_dl = pd.DataFrame()
    if "_ens_results" in st.session_state:
        try:
            from causal_model.ensemble import (
                classify_switch_robustness as _csr_dl,
                select_best_ensemble_setting as _sbs_dl,
            )
            _ens_dl_res = st.session_state["_ens_results"]
            _sw_dl = [sw.name for sw in CAMPANULA_SWITCHES]
            _ens_rows_dl = []
            for _r in _ens_dl_res:
                _row = {"preset": _r.preset_name, "acceptance_rule": _r.acceptance_rule,
                        "threshold": _r.threshold, "n_accepted": _r.n_accepted,
                        "n_evaluated": _r.n_evaluated,
                        "acceptance_rate": round(_r.acceptance_rate, 4),
                        "D_RACH": _r.D_RACH, "R_RACH": _r.R_RACH}
                for _sw in _sw_dl:
                    _row[f"CA_{_sw}"] = _r.ca_j.get(_sw, float("nan"))
                _ens_rows_dl.append(_row)
            _df_ens_dl = pd.DataFrame(_ens_rows_dl)

            _rob_dl = _csr_dl(_ens_dl_res)
            _df_rob_dl = pd.DataFrame([
                {"switch": r.switch, "mean_CA_j": r.mean_ca_j,
                 "sensitivity_range": r.sensitivity_range,
                 "classification": r.classification,
                 "is_robust": r.is_robust, "call": r.call, "verdict": r.verdict}
                for r in _rob_dl
            ])

            _crit_dl = st.session_state.get("_ens_sel_criteria", {})
            _sel_dl = _sbs_dl(
                _ens_dl_res,
                min_accepted=int(_crit_dl.get("min_accepted", 20)),
                min_acceptance_rate=float(_crit_dl.get("min_acceptance_rate", 0.02)),
                max_acceptance_rate=_crit_dl.get("max_acceptance_rate"),
                mode=_crit_dl.get("mode", "max_R"),
            )
            _best_dl = _sel_dl.best
            if _best_dl is not None:
                _best_row = {
                    "preset": _best_dl.preset_name,
                    "acceptance_rule": _best_dl.acceptance_rule,
                    "threshold": _best_dl.threshold,
                    "n_accepted": _best_dl.n_accepted,
                    "n_evaluated": _best_dl.n_evaluated,
                    "acceptance_rate": round(_best_dl.acceptance_rate, 4),
                    "D_RACH": _best_dl.D_RACH, "R_RACH": _best_dl.R_RACH,
                    "passed_stability_filters": _sel_dl.passed_filters,
                    "selection_rationale": _sel_dl.rationale,
                }
                for _sw in _sw_dl:
                    _best_row[f"CA_{_sw}"] = _best_dl.ca_j.get(_sw, float("nan"))
                _df_best_dl = pd.DataFrame([_best_row])
        except Exception:
            _df_ens_dl = pd.DataFrame()
            _df_rob_dl = pd.DataFrame()
            _df_best_dl = pd.DataFrame()

    _zip_contents = {
        f"{_sp_tag}_ensemble_results":         _df_ens_dl,
        f"{_sp_tag}_robustness_table":         _df_rob_dl,
        f"{_sp_tag}_best_setting_summary":     _df_best_dl,
        f"{_sp_tag}_accepted_rows":            _df_accepted,
        f"{_sp_tag}_evaluated_rows":           _df_evaluated,
        f"{_sp_tag}_posterior_table":          _df_posterior,
        f"{_sp_tag}_observation_contribution": _df_oc_dl,
        f"{_sp_tag}_nov_table":                _df_nov_dl,
        f"{_sp_tag}_rach_summary":             _df_summary_dl,
    }

    st.download_button(
        "⬇ Download ALL RACH inference tables as ZIP",
        _build_zip(_zip_contents),
        f"{_sp_tag}_rach_inference.zip",
        "application/zip",
        width="stretch", type="primary",
    )
    st.caption(
        "ZIP: ensemble_results · robustness_table · best_setting_summary · "
        "accepted_rows · evaluated_rows · posterior_table · "
        "observation_contribution · nov_table · rach_summary"
    )
    st.divider()

    _dl1, _dl2, _dl3 = st.columns(3)
    with _dl1:
        st.download_button("accepted_rows.csv",
            _df_accepted.to_csv(index=False).encode("utf-8"),
            f"{_sp_tag}_accepted_rows.csv", "text/csv")
        st.download_button("evaluated_rows.csv",
            _df_evaluated.to_csv(index=False).encode("utf-8"),
            f"{_sp_tag}_evaluated_rows.csv", "text/csv")
    with _dl2:
        st.download_button("posterior_table.csv",
            _df_posterior.to_csv(index=False).encode("utf-8"),
            f"{_sp_tag}_posterior_table.csv", "text/csv")
        if not _df_oc_dl.empty:
            st.download_button("observation_contribution.csv",
                _df_oc_dl.to_csv(index=False).encode("utf-8"),
                f"{_sp_tag}_observation_contribution.csv", "text/csv")
    with _dl3:
        if not _df_nov_dl.empty:
            st.download_button("nov_table.csv",
                _df_nov_dl.to_csv(index=False).encode("utf-8"),
                f"{_sp_tag}_nov_table.csv", "text/csv")
        if not _df_summary_dl.empty:
            st.download_button("rach_summary.csv",
                _df_summary_dl.to_csv(index=False).encode("utf-8"),
                f"{_sp_tag}_rach_summary.csv", "text/csv")

