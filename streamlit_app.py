"""Streamlit app for RACH: Restricted Admissible Causal Hypotheses.

Workflow
--------
1. Constrain  -- ecological constraint grammar rejects implausible latent parameter combos
2. Sample     -- random draws from ecology-principled trade-off priors
3. Simulate   -- M1-M5 causal hypotheses via proxy or stochastic ABM backend
4. Filter     -- ABC-style pattern-distance rejection against empirical observed patterns
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
from causal_model.parameter_constraints import (
    predefined_tradeoff_presets,
    sample_all_sets_with_rejection_log,
)
from causal_model.parameter_sampling import param_set_to_model_parameters
from causal_model.range_summary import summarize_parameter_ranges
from causal_model.switch_inference import (
    CAMPANULA_SWITCHES,
    compute_coactivation_table,
    run_switch_posterior_inference,
)
from causal_model.switches import switches_for_structure
from examples.campanula_izu.causal_structures import campanula_causal_structures
from examples.campanula_izu.observed_data import (
    load_observed_pattern_table,
    load_observed_patterns,
    load_pattern_weights,
)
from examples.campanula_izu.proxy_simulation import (
    default_campanula_proxy_environments,
    simulate_campanula_causal_structure,
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
        "Bombus_frequency": "Oshima > Hachijo",
    }
    PATTERN_WEIGHTS = {k: 1.0 for k in OBSERVED_RELS}
    _OBS_TABLE = [
        {"pattern": k, "relation": v, "weight": "1.0",
         "source": "hard-coded fallback", "notes": ""}
        for k, v in OBSERVED_RELS.items()
    ]

LATENT_PARAMS = [
    "guide_cost",
    "outcrossing_benefit",
    "selfing_benefit",
    "inbreeding_depression",
    "small_pollinator_efficiency",
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
     "Meaning": "Run M1-M5 candidate causal hypotheses (proxy fast-screen or stochastic ABM main model)."},
    {"Step": "4. Filter",
     "Meaning": "ABC-style pattern-distance rejection against empirical observed Oshima-Hachijo patterns."},
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
# Simulation backends
# ---------------------------------------------------------------------------

def simulate_structure_proxy(structure, model_params) -> tuple[dict[str, str], dict[str, Any]]:
    relations, outputs = simulate_campanula_causal_structure(structure, params=model_params)
    output_rows = [
        {
            "population": output.population,
            "nectar_guide": output.nectar_guide,
            "selfing_rate": output.selfing_rate,
            "herkogamy": output.herkogamy,
            "flower_size": output.flower_size,
            "Fis": output.Fis,
            "Bombus_frequency": output.Bombus_frequency,
            "outcrossing_opportunity": output.outcrossing_opportunity,
        }
        for output in outputs
    ]
    return relations, {"final_values": output_rows, "generation_rows": []}


def simulate_structure_stochastic_abm(
    structure, model_params,
    generations: int, population_size: int, replicates: int, seed: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    environments = default_campanula_proxy_environments()
    switches = switches_for_structure(structure.name)
    final_by_population: dict[str, dict[str, float]] = {}
    generation_rows: list[dict[str, Any]] = []

    for pop_index, (population_name, env) in enumerate(environments.items()):
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
        final_by_population[population_name] = average_summaries(replicate_finals)

    oshima = final_by_population.get("Oshima", {})
    hachijo = final_by_population.get("Hachijo", {})
    relations = {
        "nectar_guide": relation_from_values(
            "Oshima", oshima.get("mean_nectar_guide", 0.5),
            "Hachijo", hachijo.get("mean_nectar_guide", 0.5)),
        "selfing_rate": relation_from_values(
            "Oshima", oshima.get("selfing_rate", 0.5),
            "Hachijo", hachijo.get("selfing_rate", 0.5)),
        "herkogamy": relation_from_values(
            "Oshima", oshima.get("mean_herkogamy", 0.5),
            "Hachijo", hachijo.get("mean_herkogamy", 0.5)),
        "flower_size": relation_from_values(
            "Oshima", oshima.get("mean_flower_size", 0.5),
            "Hachijo", hachijo.get("mean_flower_size", 0.5)),
        "Fis": relation_from_values(
            "Oshima", oshima.get("Fis_proxy", 0.5),
            "Hachijo", hachijo.get("Fis_proxy", 0.5)),
        "Bombus_frequency": "Oshima > Hachijo",
    }
    final_rows = [{"population": n, **v} for n, v in final_by_population.items()]
    return relations, {"final_values": final_rows, "generation_rows": generation_rows}


# ---------------------------------------------------------------------------
# Core RACH workflow
# ---------------------------------------------------------------------------

def run_research_mode(
    preset_name: str, n_attempts: int, seed: int,
    acceptance_rule: str, backend: str,
    generations: int, population_size: int, replicates: int,
) -> dict[str, pd.DataFrame]:
    preset = predefined_tradeoff_presets()[preset_name]
    structures = campanula_causal_structures()
    constraint_passed, rejected_params = sample_all_sets_with_rejection_log(
        preset, n_attempts, seed=seed
    )

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

            dist_metrics = compute_run_distances(
                observed_rels=OBSERVED_RELS,
                simulated_rels=rels,
                weights=PATTERN_WEIGHTS,
                rule=acceptance_rule,
            )

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
                **{f"relation_{k}": v for k, v in rels.items()},
            }
            all_runs.append(row)

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
    "RACH constrains latent ecological trade-offs, simulates candidate causal hypotheses "
    "(M1-M5), then retains only the hypotheses and parameter regions compatible with "
    "multiple empirical observed patterns simultaneously. "
    "No parameter was manually tuned to reproduce the target patterns."
)

with st.expander("RACH workflow", expanded=True):
    stretch_df(pd.DataFrame(WORKFLOW_STEPS), hide_index=True)

with st.expander("Observed pattern targets (empirical data)", expanded=False):
    _obs_cols = ["pattern", "relation", "weight", "left_value",
                 "right_value", "source", "notes"]
    _obs_df = pd.DataFrame(_OBS_TABLE)
    _obs_display = _obs_df[[c for c in _obs_cols if c in _obs_df.columns]]
    stretch_df(_obs_display, hide_index=True)
    st.caption(
        "Left = Oshima (less isolated), Right = Hachijo (most isolated). "
        "Weights are used for weighted ABC distance. Source: Inoue & Amano (1986) + field."
    )

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
        n_attempts = st.slider("Prior parameter draws", 20, 500, 80, 20)
        generations = st.slider("ABM generations", 10, 100, 40, 10)
        population_size = st.slider("ABM population size", 50, 500, 150, 50)
        replicates = st.slider("ABM replicates per island", 1, 5, 1, 1)
    else:
        n_attempts = st.slider("Prior parameter draws", 100, 3000, 500, 100)
        generations = 0
        population_size = 0
        replicates = 0

    seed = st.number_input("Random seed", 0, 999999, 42, 1)
    acceptance_rule = st.selectbox(
        "ABC acceptance rule",
        available_rules(),
        format_func=lambda r: {
            "strict_6_of_6":   "strict (eps=0, all 6 must match)",
            "relaxed_5_of_6":  "relaxed (eps=1/6, >=5 must match)",
            "relaxed_4_of_6":  "lax (eps=2/6, >=4 must match)",
            "weighted_strict": "weighted strict (weighted eps=0)",
            "weighted_lax":    "weighted lax (weighted eps=0.20)",
        }.get(r, r),
    )
    st.caption(
        f"eps = {epsilon_for_rule(acceptance_rule, len(OBSERVED_RELS)):.4f} "
        f"| distance = 1 - matches / {len(OBSERVED_RELS)}"
    )
    run_button = st.button("Run RACH workflow", type="primary", use_container_width=True)

    st.divider()
    st.subheader("Switch Posterior Inference")
    st.caption(
        "Infers P(pathway ON | patterns matched) without pre-defining M1-M5 structures. "
        "Jointly samples binary switch states and latent parameters."
    )
    sp_n_attempts = st.slider(
        "Switch inference draws", 100, 2000, 400, 100,
        key="sp_n",
        help="Total joint (switch, parameter) draws from the prior",
    )
    run_switch_button = st.button(
        "Run Switch Posterior", use_container_width=True
    )

preset = presets[preset_name]
st.subheader("Ecological trade-off preset")
st.caption(preset.description)
st.dataframe(
    pd.DataFrame([
        {"Latent parameter": key, "Lower": val[0], "Upper": val[1]}
        for key, val in preset.ranges.items()
    ]),
    width="stretch",
    hide_index=True,
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
    with st.spinner("Constrain -> sample -> simulate -> filter admissible hypotheses..."):
        result = run_research_mode(
            preset_name=preset_name,
            n_attempts=n_attempts,
            seed=int(seed),
            acceptance_rule=acceptance_rule,
            backend=backend,
            generations=generations,
            population_size=population_size,
            replicates=replicates,
        )
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
# Run switch posterior inference
# ---------------------------------------------------------------------------
if run_switch_button:
    with st.spinner("Sampling (params, switches) jointly -> ABC filter -> posterior..."):
        sp_result = run_switch_posterior_inference(
            preset_name=preset_name,
            n_attempts=int(sp_n_attempts),
            acceptance_rule=acceptance_rule,
            seed=int(seed) + 1,
            observed_rels=OBSERVED_RELS,
            pattern_weights=PATTERN_WEIGHTS,
        )
    st.session_state["sp_result"] = sp_result

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

    st.subheader("M1-M5 Comparison Results")
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
            "Admissibility = fraction of parameter-set runs where all "
            f"patterns were matched (rule: {settings.get('acceptance_rule', acceptance_rule)})."
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
            relation_cols = [c for c in df_runs.columns if c.startswith("relation_")]
            show_cols = [
                "causal_hypothesis", "pattern_matches", "abc_distance",
                "weighted_abc_distance", "admissible_by_epsilon",
            ] + relation_cols
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
                parameter_space_chart(df_runs, "small_pollinator_efficiency", "selfing_benefit")
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
        st.markdown("### Simulated Oshima vs Hachijo trait values")
        long_values = final_values_long(df_final_values)
        if long_values.empty:
            st.warning("No final simulated values available.")
        else:
            sel_var = st.selectbox("Variable", sorted(long_values["variable"].unique()))
            sel_hyp = st.selectbox(
                "Causal hypothesis", sorted(long_values["causal_hypothesis"].unique())
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
                var = st.selectbox("Variable", sorted(ts["variable"].unique()))
            with col_ts2:
                structure_ts = st.selectbox(
                    "Hypothesis", sorted(ts["structure"].unique())
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
    st.divider()
    st.header("Switch Posterior Inference Results")
    st.info(
        "These results infer which biological pathways were active in parameter-space "
        "regions that reproduced the observed Oshima-Hachijo patterns -- without any "
        "pre-defined M1-M5 structure. The posterior P(switch ON | accepted) is the "
        "primary inferential output."
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
        sp_tab1, sp_tab2, sp_tab3, sp_tab4 = st.tabs([
            "Posterior P(ON)",
            "Co-activation",
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

        with sp_tab4:
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
