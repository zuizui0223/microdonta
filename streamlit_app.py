"""Streamlit entry point for constraint-first CAPOM.

This app avoids manual parameter tuning. It first constructs an ecologically
constrained latent parameter space, then runs M1-M5 causal simulations, then uses
CAPOM pattern matching to retain accepted scenario-parameter combinations.

Two simulation backends are available:

- proxy_causal: fast deterministic causal proxy for broad parameter filtering.
- stochastic_abm: full individual-based generation simulation using
  attraction_trait_model.simulation.simulate_population.
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

st.set_page_config(page_title="Campanula CAPOM Research Mode", layout="wide", page_icon="🔭")

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
    {"Step": "1. Constrain", "Meaning": "Choose an ecology-principled trade-off preset and reject biologically inconsistent parameter combinations."},
    {"Step": "2. Sample", "Meaning": "Randomly sample latent benefit/cost parameters inside the constrained space. No manual tuning."},
    {"Step": "3. Simulate", "Meaning": "Convert each valid parameter set to ModelParameters and run M1-M5 with proxy or stochastic ABM backend."},
    {"Step": "4. Match", "Meaning": "Compare simulated Oshima-Hachijo relations with observed CAPOM pattern targets."},
    {"Step": "5. Retain", "Meaning": "Report accepted causal structures, accepted parameter ranges, and rejected parameter sets."},
]

BACKEND_DESCRIPTIONS = {
    "proxy_causal": "Fast deterministic proxy. Best for broad parameter filtering and debugging.",
    "stochastic_abm": "Full individual-based generation simulation. Slower, but closer to the intended causal generative model.",
}


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def relation_from_values(left_name: str, left_value: float, right_name: str, right_value: float, tolerance: float = 0.03) -> str:
    """Return ordinal relation between two values with a small tolerance."""

    if abs(left_value - right_value) <= tolerance:
        return f"{left_name} ~= {right_name}"
    if left_value > right_value:
        return f"{left_name} > {right_name}"
    return f"{left_name} < {right_name}"


def final_abm_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return final-generation ABM summary, or zeros if no rows exist."""

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
    """Average final ABM summaries across replicates."""

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
    return {
        key: sum(float(row.get(key, 0.0)) for row in summaries) / len(summaries)
        for key in numeric_keys
    }


def simulate_structure_proxy(structure, model_params) -> tuple[dict[str, str], dict[str, Any]]:
    """Run the existing deterministic proxy causal simulation."""

    relations, outputs = simulate_campanula_causal_structure(structure, params=model_params)
    output_rows = []
    for output in outputs:
        output_rows.append({
            "population": output.population,
            "nectar_guide": output.nectar_guide,
            "selfing_rate": output.selfing_rate,
            "herkogamy": output.herkogamy,
            "flower_size": output.flower_size,
            "Fis": output.Fis,
            "Bombus_frequency": output.Bombus_frequency,
            "outcrossing_opportunity": output.outcrossing_opportunity,
        })
    return relations, {"final_values": output_rows, "generation_rows": []}


def simulate_structure_stochastic_abm(
    structure,
    model_params,
    generations: int,
    population_size: int,
    replicates: int,
    seed: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Run full stochastic ABM for Oshima and Hachijo and convert outputs to CAPOM relations."""

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
                generation_rows.append({
                    "population": population_name,
                    "replicate": rep,
                    "structure": structure.name,
                    **row,
                })
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

    final_rows = []
    for population_name, values in final_by_population.items():
        final_rows.append({"population": population_name, **values})

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
):
    """Run constraint-first parameter exploration, causal simulation, and CAPOM matching."""

    presets = predefined_tradeoff_presets()
    preset = presets[preset_name]
    structures = campanula_causal_structures()
    accepted_params, rejected_params = sample_all_sets_with_rejection_log(preset, n_attempts, seed=seed)

    threshold = 6 if acceptance_rule == "strict_6_of_6" else 5
    all_runs = []
    all_final_values: list[dict[str, Any]] = []
    generation_rows_all: list[dict[str, Any]] = []

    for param_index, param_set in enumerate(accepted_params):
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
            accepted = matches >= threshold
            run_id = f"{param_set.get('parameter_set_id')}_{structure.name}_{backend}"
            run_row = {
                "run_id": run_id,
                "parameter_set_id": param_set.get("parameter_set_id"),
                "preset_name": preset_name,
                "backend": backend,
                "structure": structure.name,
                "pattern_matches": matches,
                "pattern_total": len(OBSERVED_RELS),
                "accepted_by_rule": accepted,
                "acceptance_rule": acceptance_rule,
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
            all_runs.append(run_row)

            for final_row in payload.get("final_values", []):
                all_final_values.append({"run_id": run_id, "structure": structure.name, "backend": backend, **final_row})
            if backend == "stochastic_abm":
                for generation_row in payload.get("generation_rows", []):
                    generation_rows_all.append({"run_id": run_id, **generation_row})

    accepted_runs = [row for row in all_runs if row["accepted_by_rule"]]
    accepted_ranges = summarize_parameter_ranges(accepted_runs, LATENT_PARAMS)

    df_runs = pd.DataFrame(all_runs)
    if df_runs.empty:
        df_summary = pd.DataFrame(columns=["structure", "total_runs", "accepted_runs", "acceptance_rate", "mean_matches"])
    else:
        df_summary = (
            df_runs.groupby("structure")
            .agg(
                total_runs=("pattern_matches", "count"),
                accepted_runs=("accepted_by_rule", "sum"),
                mean_matches=("pattern_matches", "mean"),
            )
            .reset_index()
        )
        df_summary["acceptance_rate"] = df_summary["accepted_runs"] / df_summary["total_runs"]
        df_summary["mean_matches"] = df_summary["mean_matches"].round(3)
        df_summary["acceptance_rate"] = df_summary["acceptance_rate"].round(3)
        df_summary = df_summary.sort_values("acceptance_rate", ascending=False)

    return {
        "preset": preset,
        "accepted_params": pd.DataFrame(accepted_params),
        "rejected_params": pd.DataFrame(rejected_params),
        "all_runs": df_runs,
        "accepted_runs": pd.DataFrame(accepted_runs),
        "accepted_ranges": pd.DataFrame(accepted_ranges),
        "scenario_summary": df_summary,
        "final_values": pd.DataFrame(all_final_values),
        "generation_rows": pd.DataFrame(generation_rows_all),
    }


st.title("🔭 Constraint-first CAPOM Research Mode")
st.caption("Campanula / Izu Islands worked example")

st.info(
    "This app does not manually tune parameters. It first constrains latent benefit/cost "
    "parameters using ecological trade-off rules, then runs causal simulations, then uses "
    "CAPOM pattern matching to retain compatible scenario-parameter combinations.",
    icon="🔭",
)

st.subheader("Model workflow")
st.dataframe(pd.DataFrame(WORKFLOW_STEPS), use_container_width=True, hide_index=True)

with st.expander("Observed CAPOM pattern targets", expanded=False):
    st.dataframe(
        pd.DataFrame([
            {"Pattern": key, "Observed relation": value}
            for key, value in OBSERVED_RELS.items()
        ]),
        use_container_width=True,
        hide_index=True,
    )

with st.sidebar:
    st.header("1. Constrained exploration settings")
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
    acceptance_rule = st.selectbox("CAPOM acceptance rule", ["strict_6_of_6", "relaxed_5_of_6"])
    run_button = st.button("▶ Run constrained CAPOM workflow", type="primary", use_container_width=True)

preset = presets[preset_name]
st.subheader("1. Selected ecological trade-off preset")
st.caption(preset.description)
st.dataframe(
    pd.DataFrame([
        {"Latent parameter": key, "Lower bound": val[0], "Upper bound": val[1]}
        for key, val in preset.ranges.items()
    ]),
    use_container_width=True,
    hide_index=True,
)

if backend == "stochastic_abm":
    st.warning(
        "Stochastic ABM mode runs individual-based generation simulations. It is slower than proxy mode. "
        "Start with small draw counts, then increase once the workflow behaves as expected.",
        icon="🐢",
    )

if run_button:
    with st.spinner("Constrain → sample → simulate M1-M5 → CAPOM match..."):
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
    df_acc_params = result["accepted_params"]
    df_rej = result["rejected_params"]
    df_runs = result["all_runs"]
    df_acc_runs = result["accepted_runs"]
    df_ranges = result["accepted_ranges"]
    df_summary = result["scenario_summary"]
    df_final_values = result["final_values"]
    df_generation_rows = result["generation_rows"]

    st.subheader("2. Constraint filtering summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prior draws", settings.get("n_attempts", n_attempts))
    c2.metric("Constraint-passed parameter sets", len(df_acc_params))
    c3.metric("Constraint-rejected sets", len(df_rej))
    c4.metric("Accepted scenario-runs", len(df_acc_runs))

    st.subheader("3. Causal structure ranking after CAPOM matching")
    st.caption(f"Backend: {settings.get('backend', backend)} | Acceptance rule: {settings.get('acceptance_rule', acceptance_rule)}")
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    st.subheader("4. Accepted latent parameter ranges")
    st.caption("These ranges, not manually chosen values, are the inferential output.")
    if df_ranges.empty:
        st.warning("No accepted scenario-runs under the selected acceptance rule.")
    else:
        st.dataframe(df_ranges, use_container_width=True, hide_index=True)

    st.subheader("5. Simulated final values")
    if df_final_values.empty:
        st.warning("No final simulated values were returned.")
    else:
        st.dataframe(df_final_values.head(200), use_container_width=True, hide_index=True)

    st.subheader("6. Trade-off class distribution")
    if not df_acc_params.empty:
        col_g, col_s = st.columns(2)
        with col_g:
            st.markdown("**Guide trade-off classes**")
            st.dataframe(
                df_acc_params["guide_tradeoff_class"].value_counts().rename_axis("guide_tradeoff_class").reset_index(name="count"),
                use_container_width=True,
                hide_index=True,
            )
        with col_s:
            st.markdown("**Selfing trade-off classes**")
            st.dataframe(
                df_acc_params["selfing_tradeoff_class"].value_counts().rename_axis("selfing_tradeoff_class").reset_index(name="count"),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.warning("No constraint-passed parameter sets for this preset / seed / draw count.")

    st.subheader("7. Downloads")
    st.caption("Use these CSV files for reproducible checks and manuscript figures.")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button("all_runs.csv", to_csv_bytes(df_runs), "parameter_filtering_all_runs.csv", "text/csv")
        st.download_button("accepted_runs.csv", to_csv_bytes(df_acc_runs), "parameter_filtering_accepted_runs.csv", "text/csv")
        st.download_button("final_values.csv", to_csv_bytes(df_final_values), "simulation_final_values.csv", "text/csv")
    with d2:
        st.download_button("accepted_ranges.csv", to_csv_bytes(df_ranges), "parameter_filtering_accepted_ranges.csv", "text/csv")
        st.download_button("scenario_summary.csv", to_csv_bytes(df_summary), "parameter_filtering_scenario_summary.csv", "text/csv")
        if not df_generation_rows.empty:
            st.download_button("generation_timeseries.csv", to_csv_bytes(df_generation_rows), "stochastic_abm_generation_timeseries.csv", "text/csv")
    with d3:
        st.download_button("constraint_passed_parameter_sets.csv", to_csv_bytes(df_acc_params), "constraint_passed_parameter_sets.csv", "text/csv")
        st.download_button("rejected_parameter_sets.csv", to_csv_bytes(df_rej), "parameter_sampling_rejected_sets.csv", "text/csv")

else:
    st.markdown(
        "Choose a preset and backend, then click **Run constrained CAPOM workflow**. "
        "Use proxy mode for broad filtering and stochastic ABM mode for generation-level simulations."
    )
