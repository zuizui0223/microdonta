"""Streamlit app for RACH: Restricted Admissible Causal Hypotheses.

Workflow
--------
1. Constrain  -- ecological constraint grammar rejects implausible latent parameter combos
2. Sample     -- random draws from ecology-principled trade-off priors
3. Simulate   -- named causal structure hypotheses via proxy or stochastic ABM backend
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
from causal_model.parameter_sampling import param_set_to_model_parameters
from causal_model.range_summary import summarize_parameter_ranges
from causal_model.switch_inference import (
    CAMPANULA_SWITCHES,
    compute_coactivation_table,
    run_switch_posterior_inference,
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
)
from examples.campanula_izu.pattern_evaluator import (
    ABMPopulationProxy,
    EvaluationResult,
    evaluate_patterns,
    weighted_pattern_distance,
)
from examples.campanula_izu.proxy_simulation import (
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
    {"Step": "1. Constrain",
     "Meaning": "Ecological constraint grammar rejects implausible latent parameter combinations."},
    {"Step": "2. Sample",
     "Meaning": "Randomly sample latent benefit/cost parameters from ecology-principled trade-off priors."},
    {"Step": "3. Simulate",
     "Meaning": "Run named causal structure hypotheses (proxy fast-screen or stochastic ABM main model)."},
    {"Step": "4. Filter",
     "Meaning": "ABC rejection against observable ecological gradient pattern targets (response_target rows only; input_context predictors excluded)."},
    {"Step": "5. Retain",
     "Meaning": "Restricted admissible causal hypotheses and compatible latent parameter ranges."},
    {"Step": "6. Infer switches",
     "Meaning": "PathwaySwitch posterior: infer P(mechanism ON | patterns matched) without pre-defined structures."},
]

BACKEND_DESCRIPTIONS = {
    "proxy_causal": (
        "Fast deterministic proxy -- use for broad screening and debugging. "
        "Approximates population outcomes without generation-level dynamics."
    ),
    "stochastic_abm": (
        "Stochastic individual-based ABM -- the main causal generative model. "
        "Models heritable trait evolution, drift, selection, and reproduction "
        "explicitly across generations."
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def stretch_df(df: pd.DataFrame, **kwargs) -> None:
    st.dataframe(df, width="stretch", **kwargs)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


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
    Works with both PopulationProxyOutput objects (proxy) and plain dicts (ABM).
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

def simulate_structure_proxy(structure, model_params) -> tuple[dict, dict[str, Any]]:
    """Run proxy simulation on a continuous isolation gradient (no named populations)."""
    from causal_model.switches import switches_for_structure as _sfs
    _sw = _sfs(structure.name)
    outputs_dict, synth_env = simulate_campanula_isolation_gradient(
        _sw, params=model_params, n_points=8,
    )
    outputs_list = list(outputs_dict.values())

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
        "synth_pop_env": synth_env,
    }


def simulate_structure_stochastic_abm(
    structure, model_params,
    generations: int, population_size: int, replicates: int, seed: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Run ABM on a continuous isolation gradient (4 points)."""
    from examples.campanula_izu.proxy_simulation import env_from_isolation
    _n_abm = 4
    _grad_envs = {
        f"iso_{i / (_n_abm - 1):.3f}": env_from_isolation(i / (_n_abm - 1))
        for i in range(_n_abm)
    }
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
        for structure_index, structure in enumerate(structures):
            run_seed = seed + param_index * 10_000 + structure_index * 100
            try:
                if backend == "stochastic_abm":
                    rels, payload = simulate_structure_stochastic_abm(
                        structure, model_params,
                        generations=generations, population_size=population_size,
                        replicates=replicates, seed=run_seed,
                    )
                else:
                    rels, payload = simulate_structure_proxy(structure, model_params)
            except Exception:
                rels = {}
                payload = {"final_values": [], "generation_rows": []}

            # --- Primary gradient pattern targets ---
            # Acceptance is driven by response_target gradient patterns
            # (gradient_slope + rank_order across the isolation axis).
            # input_context rows (predictor variables) are excluded automatically.
            _outputs_list = payload.get("outputs_list", [])
            _is_abm = payload.get("abm", False)
            _grad_pats = observed_gradient_only_patterns()
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

st.title("RACH -- Restricted Admissible Causal Hypotheses")
st.caption("Campanula punctata / Izu Islands isolation gradient worked example")
st.info(
    "RACH constrains latent ecological trade-offs, simulates named causal structure hypotheses, "
    "then retains only the hypotheses and parameter regions compatible with "
    "observable ecological gradient pattern targets simultaneously. "
    "No parameter was manually tuned to reproduce the target patterns."
)

with st.expander("RACH workflow", expanded=True):
    stretch_df(pd.DataFrame(WORKFLOW_STEPS), hide_index=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Settings")
    presets = predefined_tradeoff_presets()
    preset_name = st.selectbox("Trade-off preset", list(presets.keys()))
    backend = st.selectbox(
        "Simulation backend",
        ["proxy_causal", "stochastic_abm"],
        format_func=lambda x: (
            "proxy_causal (fast screen)" if x == "proxy_causal"
            else "stochastic_abm (main model)"
        ),
    )
    st.caption(BACKEND_DESCRIPTIONS[backend])

    if backend == "stochastic_abm":
        n_attempts = st.slider("Prior parameter draws", 20, 500, 80, 20, key="n_attempts_abm")
        generations = st.slider("ABM generations", 10, 100, 40, 10)
        population_size = st.slider("ABM population size", 50, 500, 150, 50)
        replicates = st.slider("ABM replicates per island", 1, 5, 1, 1)
    else:
        n_attempts = st.slider("Prior parameter draws", 100, 3000, 500, 100, key="n_attempts_proxy")
        generations = 0
        population_size = 0
        replicates = 0

    seed = st.number_input("Random seed", 0, 999999, 42, 1)
    _rules = available_rules()
    acceptance_rule = st.selectbox(
        "ABC acceptance rule",
        _rules,
        index=_rules.index("strict_6_of_6") if "strict_6_of_6" in _rules else 0,
        format_func=lambda r: {
            "strict_6_of_6":   "strict (all 6 gradient patterns must match)",
            "relaxed_5_of_6":  "relaxed (>=5/6 gradient patterns)",
            "relaxed_4_of_6":  "lax (>=4/6 gradient patterns)",
            "weighted_strict": "weighted strict (weighted match = 1.0)",
            "weighted_lax":    "weighted lax (weighted match >= 0.80)",
        }.get(r, r),
    )
    from causal_model.switch_inference import GRADIENT_N_PATTERNS as _N_PAT
    _thresh_display = GRADIENT_THRESH_MAP.get(acceptance_rule, 1.0)
    st.caption(
        f"Gradient pattern targets: {_N_PAT} response_target patterns · "
        f"threshold = weighted_match_rate >= {_thresh_display:.3f}"
    )
    run_button = st.button("Run RACH workflow", type="primary", use_container_width=True)

    st.divider()
    st.subheader("Switch Posterior Inference")
    st.caption(
        "Infers P(pathway ON | patterns matched) without pre-defining M1-M5 structures. "
        "Jointly samples binary switch states and latent parameters."
    )
    sp_backend = st.selectbox(
        "Inference backend",
        ["proxy_causal", "stochastic_abm"],
        format_func=lambda x: (
            "proxy (fast, ~1500 draws)" if x == "proxy_causal"
            else "stochastic ABM (slow, ~200-500 draws, sharper BF)"
        ),
        key="sp_backend",
    )
    if sp_backend == "stochastic_abm":
        sp_n_attempts = st.slider(
            "Switch inference draws", 50, 1000, 200, 50,
            key="sp_n_abm",
            help="Each draw runs ABM across the isolation gradient. ~289ms/draw. 200 draws ≈ 1 min.",
        )
        sp_abm_generations = st.slider("ABM generations", 10, 80, 30, 10, key="sp_gen")
        sp_abm_popsize    = st.slider("ABM population size", 50, 300, 100, 50, key="sp_pop")
        sp_abm_replicates = st.slider("ABM replicates", 1, 5, 3, 1, key="sp_rep")
        _est_sec = int(sp_n_attempts * 0.30 * sp_abm_replicates / 3)
        st.caption(
            f"Estimated runtime: ~{_est_sec}s "
            f"({sp_n_attempts} draws × {sp_abm_replicates} rep × isolation gradient)"
        )
    else:
        sp_n_attempts = st.slider(
            "Switch inference draws", 200, 3000, 1500, 100,
            key="sp_n_proxy",
            help="More draws give sharper posteriors. 1500+ recommended for stable BF estimates.",
        )
        sp_abm_generations = 0
        sp_abm_popsize = 0
        sp_abm_replicates = 0
    run_switch_button = st.button(
        "Run Switch Posterior", use_container_width=True
    )

preset = presets[preset_name]
st.subheader("Ecological trade-off preset")
st.caption(preset.description)
_lit_map = {src.parameter: src for src in LITERATURE_SOURCES}
_prior_rows = []
for key, (lo, hi) in preset.ranges.items():
    src = _lit_map.get(key)
    _prior_rows.append({
        "Parameter": key,
        "Lower": lo,
        "Upper": hi,
        "Empirical basis": src.empirical_range if src else "broad (unmeasured)",
        "Source": src.citation if src else "n/a",
    })
st.dataframe(pd.DataFrame(_prior_rows), width="stretch", hide_index=True)

if preset.literature_sources:
    with st.expander("Literature sources for prior ranges", expanded=False):
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
else:
    st.caption(
        "broad_prior: ranges are maximally broad for sensitivity analysis. "
        "Compare results with literature_grounded to check prior sensitivity."
    )

if backend == "stochastic_abm":
    st.warning(
        "Stochastic ABM mode is slower. Start with small draw counts (<=80) "
        "then increase after confirming the workflow runs correctly."
    )

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

    if sp_backend == "stochastic_abm":
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
    else:
        sp_result = run_switch_posterior_inference(
            preset_name=preset_name,
            n_attempts=int(sp_n_attempts),
            acceptance_rule=acceptance_rule,
            seed=int(seed) + 1,
            observed_rels=OBSERVED_RELS,
            pattern_weights=PATTERN_WEIGHTS,
            progress_callback=_sp_progress,
        )
    _sp_bar.progress(1.0, text="Switch Posterior: Done ✓")
    _sp_stat.empty()
    st.session_state["sp_result"] = sp_result
    st.session_state["sp_backend_used"] = sp_backend

# ---------------------------------------------------------------------------
# M1-M5 Results
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

    st.subheader("Causal Structure Comparison Results")
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
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("all_runs.csv", to_csv_bytes(df_runs),
                               "rach_all_runs.csv", "text/csv")
            st.download_button("admissible_runs.csv", to_csv_bytes(df_acc_runs),
                               "rach_admissible_runs.csv", "text/csv")
            st.download_button("final_values.csv", to_csv_bytes(df_final_values),
                               "rach_simulation_final_values.csv", "text/csv")
        with d2:
            st.download_button("compatible_ranges.csv", to_csv_bytes(df_ranges),
                               "rach_compatible_ranges.csv", "text/csv")
            st.download_button("hypothesis_summary.csv", to_csv_bytes(df_summary),
                               "rach_hypothesis_summary.csv", "text/csv")
            if not df_generation_rows.empty:
                st.download_button(
                    "generation_timeseries.csv",
                    to_csv_bytes(df_generation_rows),
                    "rach_stochastic_abm_generation_timeseries.csv",
                    "text/csv",
                )
        with d3:
            st.download_button(
                "constraint_passed_params.csv",
                to_csv_bytes(df_acc_params),
                "rach_constraint_passed_parameter_sets.csv",
                "text/csv",
            )
            st.download_button(
                "rejected_params.csv",
                to_csv_bytes(df_rej),
                "rach_rejected_parameter_sets.csv",
                "text/csv",
            )

else:
    st.markdown(
        "Configure settings in the sidebar and click **Run RACH workflow** to begin.  \n"
        "Use **proxy_causal** for fast broad screening, "
        "then confirm with **stochastic_abm** for the main causal generative model."
    )

# ============================================================================
# Switch Posterior Results
# ============================================================================
if "sp_result" in st.session_state:
    sp = st.session_state["sp_result"]
    _sp_backend_used = st.session_state.get("sp_backend_used", "proxy_causal")
    st.divider()
    st.header("Switch Posterior Inference Results")
    st.info(
        "These results infer which biological pathways were active in parameter-space "
        "regions that reproduced the observable ecological gradient pattern targets -- without any "
        "pre-defined M1-M5 structure. The posterior P(switch ON | accepted) is the "
        "primary inferential output."
    )
    if _sp_backend_used == "stochastic_abm":
        st.success(
            "Stochastic ABM backend: acceptance rate reflects genuine biological "
            "discriminability, not proxy model determinism. "
            "BF > 3 is now achievable with sufficient draws."
        )
    else:
        st.caption("Backend: proxy_causal (fast screen)")

    if len(sp.accepted_rows) < 30:
        st.warning(
            f"Only {len(sp.accepted_rows)} accepted samples — BF estimates are unstable. "
            "Increase draws or use a more relaxed acceptance rule for reliable inference."
        )

    sp_c1, sp_c2, sp_c3, sp_c4 = st.columns(4)
    sp_c1.metric("Joint prior draws", sp.n_attempts)
    sp_c2.metric("ABC-accepted", len(sp.accepted_rows))
    sp_c3.metric("Acceptance rate", f"{sp.acceptance_rate:.1%}")
    sp_c4.metric("Switches inferred", len(CAMPANULA_SWITCHES))

    if not sp.accepted_rows:
        st.warning(
            "No samples were accepted. "
            "Try a more relaxed acceptance rule (e.g. relaxed_5_of_6) or more draws."
        )
    else:
        sp_tab1, sp_tab2, sp_tab3, sp_tab4, sp_tab5 = st.tabs([
            "Posterior P(ON)",
            "Co-activation",
            "RACH Theory Metrics",
            "Parameter space",
            "Downloads",
        ])

        with sp_tab1:
            st.markdown("### P(switch ON | patterns matched)")
            st.caption(
                "Posterior probability that each biological mechanism is active "
                "in parameter-space regions compatible with observed patterns. "
                "Prior = 0.5 (uninformative). BF > 3 = supported; BF < 1/3 = opposed."
            )
            df_post = pd.DataFrame(sp.posterior_table)
            if not df_post.empty:
                st.bar_chart(
                    df_post.set_index("switch")[["P_prior_ON", "P_posterior_ON"]],
                    width="stretch",
                )
                st.caption(
                    "Left bar = prior (0.5). Right bar = posterior. "
                    "Posterior > 0.5 means the switch being ON is associated "
                    "with matching the observed patterns."
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
                        "[SUPPORTED]" if interp.startswith("supported")
                        else "[weak]" if interp.startswith("weakly s")
                        else "[OPPOSED]" if interp.startswith("opposed")
                        else "[-]"
                    )
                    bf = row.get("Bayes_factor")
                    bf_str = f"BF={bf:.2f}" if bf is not None else "BF=n/a"
                    st.markdown(
                        f"**{icon} {row['switch']}** -- "
                        f"P(ON)={row['P_posterior_ON']:.3f} ({bf_str})  \n"
                        f"*{row['biological_question'][:90]}*"
                    )

        with sp_tab2:
            st.markdown("### Switch co-activation")
            st.caption(
                "P(switch A ON and switch B ON | accepted). "
                "High co-activation = two pathways tend to be simultaneously active "
                "in pattern-compatible parameter regions."
            )
            coact = compute_coactivation_table(sp.accepted_rows)
            if coact:
                df_coact = pd.DataFrame(coact)
                stretch_df(df_coact, hide_index=True)
                try:
                    pivot = df_coact.pivot(
                        index="switch_A", columns="switch_B", values="P_both_ON"
                    )
                    st.markdown("#### Co-activation matrix (P both ON)")
                    st.dataframe(pivot.round(3), width="stretch")
                except Exception:
                    pass
            else:
                st.info("Not enough accepted samples for co-activation table.")

        with sp_tab3:
            st.markdown("### RACH Theory Metrics — mechanism identifiability & causal degeneracy")
            st.caption(
                "Formal quantification of how much the gradient pattern targets (A_ε) constrain "
                "the causal mechanism space. Derived from the accepted ABC sample."
            )
            try:
                from causal_model.identifiability import (
                    compute_rach_theory_metrics,
                    identifiability_summary,
                    pattern_contribution_table,
                )
                _rach_metrics = compute_rach_theory_metrics(sp.accepted_rows, CAMPANULA_SWITCHES)
                _id_summary   = identifiability_summary(sp.accepted_rows, CAMPANULA_SWITCHES)

                # --- Top-level degeneracy metrics ---
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric(
                    "H(S|A_ε) causal degeneracy",
                    f"{_rach_metrics.causal_degeneracy:.3f} bits",
                    help="Joint entropy of accepted switch vectors. 0 = single mechanism; "
                         f"max = {_rach_metrics.n_switches} bits."
                )
                mc2.metric(
                    "Degeneracy reduction",
                    f"{_rach_metrics.degeneracy_reduction:.3f} bits",
                    help=f"K − H(S|A_ε) where K={_rach_metrics.n_switches} bits. "
                         "How much A_ε constrains mechanism combinations."
                )
                mc3.metric(
                    "Total identifiability",
                    f"{_rach_metrics.total_identifiability:.3f} bits",
                    help="Sum of I_j over all switches (marginal information gained)."
                )
                mc4.metric(
                    "Max degeneracy K",
                    f"{_rach_metrics.max_degeneracy:.0f} bits",
                    help=f"K = {_rach_metrics.n_switches} bits (uninformative prior over all switches)."
                )

                # --- Per-switch identifiability table & chart ---
                st.markdown("#### Mechanism identifiability I_j (bits per switch)")
                st.caption(
                    "I_j = H(prior) − H(posterior | A_ε).  "
                    "I_j = 1 → fully identified.  I_j = 0 → posterior equals prior (unidentified)."
                )
                df_id = pd.DataFrame(_id_summary)
                if not df_id.empty:
                    st.bar_chart(
                        df_id.set_index("switch")[["I_j (bits)"]],
                        width="stretch",
                    )
                    stretch_df(
                        df_id[[
                            "switch", "P_prior_ON", "P_posterior_ON",
                            "H_posterior", "I_j (bits)", "n_ON", "n_accepted", "interpretation",
                        ]],
                        hide_index=True,
                    )

                # --- Pattern contribution (LOO) ---
                st.markdown("#### Pattern contribution C_k(j) — leave-one-out identifiability")
                st.caption(
                    "C_k(j) = I_j(all patterns) − I_j(LOO-k). "
                    "Positive = pattern k increases identifiability of switch j. "
                    "Requires per_pattern_matched data from the accepted sample."
                )
                _contrib = pattern_contribution_table(sp.accepted_rows, CAMPANULA_SWITCHES)
                if _contrib:
                    df_contrib = pd.DataFrame(_contrib)
                    # Show only non-trivial rows (|C_k_j| > 0.001)
                    df_contrib_nz = df_contrib[df_contrib["C_k_j"].abs() > 0.001].sort_values(
                        "C_k_j", ascending=False
                    )
                    if not df_contrib_nz.empty:
                        st.bar_chart(
                            df_contrib_nz.set_index(
                                df_contrib_nz["pattern"] + " → " + df_contrib_nz["switch"]
                            )[["C_k_j"]],
                            width="stretch",
                        )
                        stretch_df(df_contrib_nz, hide_index=True)
                    else:
                        st.info(
                            "All |C_k(j)| ≈ 0 — either every pattern is redundant or "
                            "no per_pattern_matched data was captured. "
                            "Re-run with proxy_causal backend to populate pattern-level data."
                        )
                else:
                    st.info(
                        "Pattern contribution requires per_pattern_matched data. "
                        "This is populated automatically on the next inference run."
                    )

            except ImportError as _e:
                st.error(f"causal_model.identifiability not available: {_e}")
            except Exception as _e:
                st.warning(f"Could not compute RACH theory metrics: {_e}")

        with sp_tab4:
            st.markdown("### Accepted switch states in parameter space")
            df_sp = pd.DataFrame(sp.accepted_rows)
            sw_names = [sw.name for sw in CAMPANULA_SWITCHES]
            avail = [
                p for p in [
                    "guide_cost", "outcrossing_benefit",
                    "selfing_benefit", "inbreeding_depression", "drift_strength",
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
                    x_p = st.selectbox("X axis", avail, key="sp_x")
                with col_y:
                    y_p = st.selectbox(
                        "Y axis", avail,
                        index=min(1, len(avail) - 1),
                        key="sp_y",
                    )
                plot_df = df_sp[[x_p, y_p, color_switch]].dropna().copy()
                plot_df[color_switch] = plot_df[color_switch].map(
                    {True: "ON", False: "OFF"}
                )
                st.scatter_chart(plot_df, x=x_p, y=y_p, color=color_switch, size=40)

            if "nearest_structure" in df_sp.columns:
                st.markdown("#### Nearest M-structure distribution")
                st.bar_chart(
                    df_sp["nearest_structure"].value_counts(),
                    width="stretch",
                )
                st.caption(
                    "Maps accepted switch states to the nearest M1-M5 label, "
                    "connecting switch inference back to conventional structure comparison."
                )

        with sp_tab5:
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    "switch_posterior_accepted.csv",
                    pd.DataFrame(sp.accepted_rows).to_csv(index=False).encode(),
                    "rach_switch_posterior_accepted.csv",
                    "text/csv",
                )
            with col_dl2:
                st.download_button(
                    "switch_posterior_table.csv",
                    pd.DataFrame(sp.posterior_table).to_csv(index=False).encode(),
                    "rach_switch_posterior_table.csv",
                    "text/csv",
                )

