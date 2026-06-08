"""Streamlit app for RACH: Restricted Admissible Causal Hypotheses.

Workflow:
    ecological constraint grammar
    -> constrained latent parameter sampling
    -> proxy or stochastic ABM causal simulation
    -> pattern-distance filtering
    -> restricted admissible causal hypotheses
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
from causal_model.parameter_constraints import (
    predefined_tradeoff_presets,
    sample_all_sets_with_rejection_log,
)
from causal_model.parameter_sampling import param_set_to_model_parameters
from causal_model.range_summary import summarize_parameter_ranges
from causal_model.switches import switches_for_structure
from examples.campanula_izu.causal_structures import campanula_causal_structures
from examples.campanula_izu.proxy_simulation import (
    default_campanula_proxy_environments,
    simulate_campanula_causal_structure,
)

st.set_page_config(page_title="RACH Research App", layout="wide", page_icon="🔭")

OBSERVED_RELS = {
    "nectar_guide": "Oshima > Hachijo",
    "selfing_rate": "Oshima < Hachijo",
    "herkogamy": "Oshima > Hachijo",
    "flower_size": "Oshima > Hachijo",
    "Fis": "Oshima < Hachijo",
    "Bombus_frequency": "Oshima > Hachijo",
}

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
    {"Step": "1. Constrain", "Meaning": "Define ecological constraint grammar and reject inconsistent latent parameter combinations."},
    {"Step": "2. Sample", "Meaning": "Randomly sample latent benefit/cost parameters inside the admissible space."},
    {"Step": "3. Simulate", "Meaning": "Run M1-M5 candidate causal hypotheses with proxy or stochastic ABM backend."},
    {"Step": "4. Filter", "Meaning": "Compare simulated Oshima-Hachijo relations with observed pattern targets using pattern distance."},
    {"Step": "5. Retain", "Meaning": "Report restricted admissible causal hypotheses and compatible latent parameter ranges."},
]

BACKEND_DESCRIPTIONS = {
    "proxy_causal": "Fast deterministic proxy for broad screening and debugging.",
    "stochastic_abm": "Individual-based generation simulation; slower, but closer to the intended causal generative model.",
}


def stretch_df(df: pd.DataFrame, **kwargs) -> None:
    """Display a dataframe with the current Streamlit width API."""

    st.dataframe(df, width="stretch", **kwargs)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def relation_from_values(left_name: str, left_value: float, right_name: str, right_value: float, tolerance: float = 0.03) -> str:
    if abs(left_value - right_value) <= tolerance:
        return f"{left_name} ~= {right_name}"
    if left_value > right_value:
        return f"{left_name} > {right_name}"
    return f"{left_name} < {right_name}"


def final_abm_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "mean_nectar_guide": 0.0,
            "selfing_rate": 0.0,
            "mean_herkogamy": 0.0,
            "mean_flower_size": 0.0,
            "Fis_proxy": 0.0,
        }
    return rows[-1]


def average_summaries(summaries: list[dict[str, Any]]) -> dict[str, float]:
    numeric_keys = [
        "mean_nectar_guide",
        "selfing_rate",
        "mean_herkogamy",
        "mean_flower_size",
        "Fis_proxy",
        "outcrossing_rate",
        "failed_rate",
        "mean_fitness",
        "mean_selfing_ability",
        "mean_neutral_diversity",
    ]
    if not summaries:
        return {key: 0.0 for key in numeric_keys}
    return {key: sum(float(row.get(key, 0.0)) for row in summaries) / len(summaries) for key in numeric_keys}


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
    structure,
    model_params,
    generations: int,
    population_size: int,
    replicates: int,
    seed: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    environments = default_campanula_proxy_environments()
    switches = switches_for_structure(structure.name)
    final_by_population: dict[str, dict[str, float]] = {}
    generation_rows: list[dict[str, Any]] = []

    for pop_index, (population_name, env) in enumerate(environments.items()):
        replicate_finals: list[dict[str, Any]] = []
        for rep in range(replicates):
            run_seed = seed + pop_index * 100000 + rep * 1000
            rows = simulate_population(
                env=env,
                params=model_params,
                switches=switches,
                generations=generations,
                population_size=population_size,
                seed=run_seed,
            )
            for row in rows:
                generation_rows.append({"population": population_name, "replicate": rep, "structure": structure.name, **row})
            replicate_finals.append(final_abm_summary(rows))
        final_by_population[population_name] = average_summaries(replicate_finals)

    oshima = final_by_population["Oshima"]
    hachijo = final_by_population["Hachijo"]
    relations = {
        "nectar_guide": relation_from_values("Oshima", oshima["mean_nectar_guide"], "Hachijo", hachijo["mean_nectar_guide"]),
        "selfing_rate": relation_from_values("Oshima", oshima["selfing_rate"], "Hachijo", hachijo["selfing_rate"]),
        "herkogamy": relation_from_values("Oshima", oshima["mean_herkogamy"], "Hachijo", hachijo["mean_herkogamy"]),
        "flower_size": relation_from_values("Oshima", oshima["mean_flower_size"], "Hachijo", hachijo["mean_flower_size"]),
        "Fis": relation_from_values("Oshima", oshima["Fis_proxy"], "Hachijo", hachijo["Fis_proxy"]),
        "Bombus_frequency": "Oshima > Hachijo",
    }
    final_rows = [{"population": name, **values} for name, values in final_by_population.items()]
    return relations, {"final_values": final_rows, "generation_rows": generation_rows}


def run_research_mode(
    preset_name: str,
    n_attempts: int,
    seed: int,
    acceptance_rule: str,
    backend: str,
    generations: int,
    population_size: int,
    replicates: int,
) -> dict[str, pd.DataFrame]:
    preset = predefined_tradeoff_presets()[preset_name]
    structures = campanula_causal_structures()
    constraint_passed, rejected_params = sample_all_sets_with_rejection_log(preset, n_attempts, seed=seed)

    threshold = 6 if acceptance_rule == "strict_6_of_6" else 5
    epsilon = 1.0 - threshold / len(OBSERVED_RELS)
    all_runs: list[dict[str, Any]] = []
    final_values: list[dict[str, Any]] = []
    generation_rows: list[dict[str, Any]] = []

    for param_index, param_set in enumerate(constraint_passed):
        model_params = param_set_to_model_parameters(param_set)
        for structure_index, structure in enumerate(structures):
            run_seed = seed + param_index * 10000 + structure_index * 100
            if backend == "stochastic_abm":
                rels, payload = simulate_structure_stochastic_abm(
                    structure,
                    model_params,
                    generations=generations,
                    population_size=population_size,
                    replicates=replicates,
                    seed=run_seed,
                )
            else:
                rels, payload = simulate_structure_proxy(structure, model_params)

            matches = sum(1 for var, obs in OBSERVED_RELS.items() if rels.get(var) == obs)
            pattern_distance = 1.0 - matches / len(OBSERVED_RELS)
            admissible = pattern_distance <= epsilon
            run_id = f"{param_set.get('parameter_set_id')}_{structure.name}_{backend}"
            row = {
                "run_id": run_id,
                "parameter_set_id": param_set.get("parameter_set_id"),
                "preset_name": preset_name,
                "backend": backend,
                "causal_hypothesis": structure.name,
                "structure": structure.name,
                "pattern_matches": matches,
                "pattern_total": len(OBSERVED_RELS),
                "pattern_distance": round(pattern_distance, 4),
                "abc_distance": round(pattern_distance, 4),
                "epsilon": round(epsilon, 4),
                "admissible_by_epsilon": admissible,
                "accepted_by_epsilon": admissible,
                "accepted_by_rule": admissible,
                "acceptance_rule": acceptance_rule,
                "generations": generations if backend == "stochastic_abm" else None,
                "population_size": population_size if backend == "stochastic_abm" else None,
                "replicates": replicates if backend == "stochastic_abm" else None,
                **{p: param_set.get(p) for p in LATENT_PARAMS},
                "guide_tradeoff_class": param_set.get("guide_tradeoff_class", ""),
                "selfing_tradeoff_class": param_set.get("selfing_tradeoff_class", ""),
                "guide_net_benefit": param_set.get("guide_net_benefit", ""),
                "selfing_net_benefit": param_set.get("selfing_net_benefit", ""),
                **{f"relation_{key}": val for key, val in rels.items()},
            }
            all_runs.append(row)

            for final_row in payload.get("final_values", []):
                final_values.append({"run_id": run_id, "causal_hypothesis": structure.name, "structure": structure.name, "backend": backend, **final_row})
            if backend == "stochastic_abm":
                for gen_row in payload.get("generation_rows", []):
                    generation_rows.append({"run_id": run_id, **gen_row})

    admissible_runs = [row for row in all_runs if row["admissible_by_epsilon"]]
    compatible_ranges = summarize_parameter_ranges(admissible_runs, LATENT_PARAMS)
    df_runs = pd.DataFrame(all_runs)

    if df_runs.empty:
        df_summary = pd.DataFrame(columns=["causal_hypothesis", "total_runs", "admissible_runs", "admissibility_rate", "mean_matches", "mean_pattern_distance"])
    else:
        df_summary = (
            df_runs.groupby("causal_hypothesis")
            .agg(
                total_runs=("pattern_matches", "count"),
                admissible_runs=("admissible_by_epsilon", "sum"),
                mean_matches=("pattern_matches", "mean"),
                mean_pattern_distance=("pattern_distance", "mean"),
            )
            .reset_index()
        )
        df_summary["admissibility_rate"] = (df_summary["admissible_runs"] / df_summary["total_runs"]).round(3)
        df_summary["mean_matches"] = df_summary["mean_matches"].round(3)
        df_summary["mean_pattern_distance"] = df_summary["mean_pattern_distance"].round(3)
        df_summary = df_summary.sort_values(["admissibility_rate", "mean_matches"], ascending=False)

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


def parameter_space_chart(df_runs: pd.DataFrame, x: str, y: str) -> None:
    if df_runs.empty or x not in df_runs or y not in df_runs:
        st.info("No parameter-space data to plot.")
        return
    plot_df = df_runs[[x, y, "admissible_by_epsilon", "causal_hypothesis"]].dropna().copy()
    plot_df["admissible"] = plot_df["admissible_by_epsilon"].map({True: "admissible", False: "rejected"})
    st.scatter_chart(plot_df, x=x, y=y, color="admissible", size=40)


def final_values_long(df_final_values: pd.DataFrame) -> pd.DataFrame:
    if df_final_values.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    mappings = {
        "nectar_guide": ["nectar_guide", "mean_nectar_guide"],
        "selfing_rate": ["selfing_rate"],
        "herkogamy": ["herkogamy", "mean_herkogamy"],
        "flower_size": ["flower_size", "mean_flower_size"],
        "Fis": ["Fis", "Fis_proxy"],
    }
    for _, row in df_final_values.iterrows():
        for variable, candidates in mappings.items():
            for candidate in candidates:
                if candidate in row and pd.notna(row[candidate]):
                    rows.append({
                        "causal_hypothesis": row.get("causal_hypothesis", row.get("structure", "")),
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


st.title("🔭 RACH Research App")
st.caption("Restricted Admissible Causal Hypotheses — Campanula / Izu Islands worked example")
st.info(
    "RACH first constrains latent ecological trade-offs, then simulates candidate causal hypotheses, "
    "then retains only the hypotheses and parameter regions compatible with observed patterns.",
    icon="🔭",
)

with st.expander("RACH workflow", expanded=True):
    stretch_df(pd.DataFrame(WORKFLOW_STEPS), hide_index=True)

with st.expander("Observed pattern targets", expanded=False):
    stretch_df(pd.DataFrame([{"Pattern": key, "Observed relation": value} for key, value in OBSERVED_RELS.items()]), hide_index=True)

with st.sidebar:
    st.header("1. Settings")
    presets = predefined_tradeoff_presets()
    preset_name = st.selectbox("Trade-off preset", list(presets.keys()))
    backend = st.selectbox("Simulation backend", ["proxy_causal", "stochastic_abm"])
    st.caption(BACKEND_DESCRIPTIONS[backend])
    if backend == "stochastic_abm":
        n_attempts = st.slider("Prior parameter draws", min_value=20, max_value=500, value=80, step=20)
        generations = st.slider("ABM generations", min_value=10, max_value=100, value=40, step=10)
        population_size = st.slider("ABM population size", min_value=50, max_value=500, value=150, step=50)
        replicates = st.slider("ABM replicates", min_value=1, max_value=5, value=1, step=1)
    else:
        n_attempts = st.slider("Prior parameter draws", min_value=100, max_value=3000, value=500, step=100)
        generations = 0
        population_size = 0
        replicates = 0
    seed = st.number_input("Random seed", min_value=0, max_value=999999, value=42, step=1)
    acceptance_rule = st.selectbox("Pattern-distance rule", ["strict_6_of_6", "relaxed_5_of_6"])
    run_button = st.button("▶ Run RACH workflow", type="primary", width="stretch")

preset = presets[preset_name]
st.subheader("Ecological trade-off preset")
st.caption(preset.description)
st.dataframe(
    pd.DataFrame([{"Latent parameter": key, "Lower": val[0], "Upper": val[1]} for key, val in preset.ranges.items()]),
    width="stretch",
    hide_index=True,
)

if backend == "stochastic_abm":
    st.warning("Stochastic ABM mode is slower. Start with small draw counts, then increase.", icon="🐢")

if run_button:
    with st.spinner("Constrain → sample → simulate candidate hypotheses → filter admissible hypotheses..."):
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

    st.subheader("Result overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Prior draws", settings.get("n_attempts", n_attempts))
    c2.metric("Constraint-passed", len(df_acc_params))
    c3.metric("Constraint-rejected", len(df_rej))
    c4.metric("Admissible runs", len(df_acc_runs))
    if not df_summary.empty:
        best = df_summary.iloc[0]
        c5.metric("Best hypothesis", str(best["causal_hypothesis"]), f"admissibility {best['admissibility_rate']:.2f}")
    else:
        c5.metric("Best hypothesis", "none")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏆 Hypothesis ranking",
        "🧭 Parameter space",
        "📌 Compatible ranges",
        "🌱 Simulated values",
        "⏱ ABM time series",
        "📦 Tables & downloads",
    ])

    with tab1:
        st.markdown("### Which causal hypothesis remains admissible?")
        if df_summary.empty:
            st.warning("No hypothesis summary available.")
        else:
            st.bar_chart(df_summary.set_index("causal_hypothesis")[["admissibility_rate"]], width="stretch")
            st.caption("Mean number of matched observed patterns out of 6.")
            st.bar_chart(df_summary.set_index("causal_hypothesis")[["mean_matches"]], width="stretch")
            stretch_df(df_summary, hide_index=True)
        if not df_runs.empty:
            st.markdown("### Pattern match table")
            relation_cols = [col for col in df_runs.columns if col.startswith("relation_")]
            show_cols = ["causal_hypothesis", "pattern_matches", "pattern_distance", "admissible_by_epsilon"] + relation_cols
            stretch_df(df_runs[show_cols].head(200), hide_index=True)

    with tab2:
        st.markdown("### Admissible vs rejected parameter space")
        st.caption("These plots show where admissible hypothesis-runs sit in latent benefit/cost space.")
        if df_runs.empty:
            st.warning("No run data available.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Guide cost vs outcrossing benefit**")
                parameter_space_chart(df_runs, "guide_cost", "outcrossing_benefit")
            with col_b:
                st.markdown("**Selfing benefit vs inbreeding depression**")
                parameter_space_chart(df_runs, "selfing_benefit", "inbreeding_depression")
            col_c, col_d = st.columns(2)
            with col_c:
                st.markdown("**Small-pollinator efficiency vs selfing benefit**")
                parameter_space_chart(df_runs, "small_pollinator_efficiency", "selfing_benefit")
            with col_d:
                st.markdown("**Drift strength vs guide cost**")
                parameter_space_chart(df_runs, "drift_strength", "guide_cost")

    with tab3:
        st.markdown("### Compatible latent parameter ranges")
        st.caption("These ranges, not manually chosen values, are the inferential output of RACH.")
        if df_ranges.empty:
            st.warning("No admissible hypothesis-runs under the selected rule.")
        else:
            stretch_df(df_ranges, hide_index=True)
            st.bar_chart(df_ranges.set_index("Parameter")[["Median"]], width="stretch")

    with tab4:
        st.markdown("### Simulated Oshima vs Hachijo values")
        long_values = final_values_long(df_final_values)
        if long_values.empty:
            st.warning("No final simulated values were returned.")
        else:
            selected_var = st.selectbox("Variable to visualize", sorted(long_values["variable"].unique()))
            selected_hypothesis = st.selectbox("Hypothesis to visualize", sorted(long_values["causal_hypothesis"].unique()))
            sub = long_values[(long_values["variable"] == selected_var) & (long_values["causal_hypothesis"] == selected_hypothesis)]
            if sub.empty:
                st.info("No values for this combination.")
            else:
                st.bar_chart(sub.groupby("population", as_index=True)["value"].mean().to_frame(), width="stretch")
            stretch_df(df_final_values.head(300), hide_index=True)

    with tab5:
        st.markdown("### Stochastic ABM generation-level trajectories")
        ts = generation_timeseries_long(df_generation_rows)
        if ts.empty:
            st.info("Generation-level trajectories are available only in stochastic_abm mode.")
        else:
            var = st.selectbox("Time-series variable", sorted(ts["variable"].unique()))
            structure = st.selectbox("Time-series hypothesis", sorted(ts["structure"].unique()))
            sub = ts[(ts["variable"] == var) & (ts["structure"] == structure)]
            if sub.empty:
                st.info("No time-series data for this combination.")
            else:
                line_df = sub.groupby(["generation", "population"], as_index=False)["value"].mean()
                line_wide = line_df.pivot(index="generation", columns="population", values="value")
                st.line_chart(line_wide, width="stretch")
            stretch_df(df_generation_rows.head(300), hide_index=True)

    with tab6:
        st.markdown("### Raw tables and downloads")
        stretch_df(df_runs.head(200), hide_index=True)
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("all_runs.csv", to_csv_bytes(df_runs), "rach_all_runs.csv", "text/csv")
            st.download_button("admissible_runs.csv", to_csv_bytes(df_acc_runs), "rach_admissible_runs.csv", "text/csv")
            st.download_button("final_values.csv", to_csv_bytes(df_final_values), "rach_simulation_final_values.csv", "text/csv")
        with d2:
            st.download_button("compatible_ranges.csv", to_csv_bytes(df_ranges), "rach_compatible_ranges.csv", "text/csv")
            st.download_button("hypothesis_summary.csv", to_csv_bytes(df_summary), "rach_hypothesis_summary.csv", "text/csv")
            if not df_generation_rows.empty:
                st.download_button("generation_timeseries.csv", to_csv_bytes(df_generation_rows), "rach_stochastic_abm_generation_timeseries.csv", "text/csv")
        with d3:
            st.download_button("constraint_passed_parameter_sets.csv", to_csv_bytes(df_acc_params), "rach_constraint_passed_parameter_sets.csv", "text/csv")
            st.download_button("rejected_parameter_sets.csv", to_csv_bytes(df_rej), "rach_rejected_parameter_sets.csv", "text/csv")
else:
    st.markdown(
        "Choose a preset and backend, then click **Run RACH workflow**. "
        "Use proxy mode for broad filtering and stochastic ABM mode for generation-level simulations."
    )
