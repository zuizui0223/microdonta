"""Standalone Research Mode page for constrained parameter filtering.

Run:
    streamlit run streamlit_research_mode.py

This page avoids manual parameter tuning. It samples latent benefit/cost
parameters from ecology-principled trade-off presets, runs M1-M5 proxy causal
structures, and reports scenario rankings plus accepted parameter ranges.
"""

from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from causal_model.parameter_constraints import (
    predefined_tradeoff_presets,
    sample_all_sets_with_rejection_log,
)
from causal_model.parameter_sampling import param_set_to_model_parameters
from causal_model.range_summary import summarize_parameter_ranges
from examples.campanula_izu.causal_structures import campanula_causal_structures
from examples.campanula_izu.proxy_simulation import simulate_campanula_causal_structure

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


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def run_research_mode(preset_name: str, n_attempts: int, seed: int, acceptance_rule: str):
    presets = predefined_tradeoff_presets()
    preset = presets[preset_name]
    structures = campanula_causal_structures()
    accepted_params, rejected_params = sample_all_sets_with_rejection_log(preset, n_attempts, seed=seed)

    threshold = 6 if acceptance_rule == "strict_6_of_6" else 5
    all_runs = []
    for param_set in accepted_params:
        model_params = param_set_to_model_parameters(param_set)
        for structure in structures:
            rels, _outputs = simulate_campanula_causal_structure(structure, params=model_params)
            matches = sum(1 for var, obs in OBSERVED_RELS.items() if rels.get(var) == obs)
            accepted = matches >= threshold
            all_runs.append({
                "parameter_set_id": param_set.get("parameter_set_id"),
                "preset_name": preset_name,
                "structure": structure.name,
                "pattern_matches": matches,
                "pattern_total": len(OBSERVED_RELS),
                "accepted_by_rule": accepted,
                "acceptance_rule": acceptance_rule,
                **{p: param_set.get(p) for p in LATENT_PARAMS},
                "guide_tradeoff_class": param_set.get("guide_tradeoff_class", ""),
                "selfing_tradeoff_class": param_set.get("selfing_tradeoff_class", ""),
                "guide_net_benefit": param_set.get("guide_net_benefit", ""),
                "selfing_net_benefit": param_set.get("selfing_net_benefit", ""),
                **{f"relation_{k}": v for k, v in rels.items()},
            })

    accepted_runs = [r for r in all_runs if r["accepted_by_rule"]]
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
    }


st.title("🔭 Research Mode — constrained parameter filtering")
st.info(
    "This mode does not manually tune parameters. It samples latent benefit/cost "
    "parameters from predefined trade-off ranges and ecological constraints, runs "
    "M1-M5 causal scenarios, and retains parameter sets that reproduce observed patterns.",
    icon="🔭",
)

with st.sidebar:
    st.header("Sampling settings")
    presets = predefined_tradeoff_presets()
    preset_name = st.selectbox("Trade-off preset", list(presets.keys()))
    n_attempts = st.slider("Prior draws", min_value=100, max_value=3000, value=500, step=100)
    seed = st.number_input("Random seed", min_value=0, max_value=999999, value=42, step=1)
    acceptance_rule = st.selectbox("Acceptance rule", ["strict_6_of_6", "relaxed_5_of_6"])
    run_button = st.button("▶ Run Research Mode", type="primary", use_container_width=True)

preset = presets[preset_name]
st.subheader("Selected trade-off preset")
st.caption(preset.description)
st.dataframe(
    pd.DataFrame([
        {"Parameter": key, "Lower": val[0], "Upper": val[1]}
        for key, val in preset.ranges.items()
    ]),
    use_container_width=True,
    hide_index=True,
)

if run_button:
    with st.spinner("Sampling constrained parameter sets and running M1-M5 scenarios..."):
        result = run_research_mode(preset_name, n_attempts, int(seed), acceptance_rule)
    st.session_state["research_result"] = result

if "research_result" in st.session_state:
    result = st.session_state["research_result"]
    df_acc_params = result["accepted_params"]
    df_rej = result["rejected_params"]
    df_runs = result["all_runs"]
    df_acc_runs = result["accepted_runs"]
    df_ranges = result["accepted_ranges"]
    df_summary = result["scenario_summary"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prior draws", n_attempts)
    c2.metric("Constraint-passed parameter sets", len(df_acc_params))
    c3.metric("Constraint-rejected sets", len(df_rej))
    c4.metric("Accepted scenario-runs", len(df_acc_runs))

    st.subheader("Causal structure ranking")
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    st.subheader("Accepted parameter ranges")
    if df_ranges.empty:
        st.warning("No accepted scenario-runs under the selected acceptance rule.")
    else:
        st.dataframe(df_ranges, use_container_width=True, hide_index=True)

    st.subheader("Trade-off class distribution")
    if not df_acc_params.empty:
        col_g, col_s = st.columns(2)
        with col_g:
            st.dataframe(
                df_acc_params["guide_tradeoff_class"].value_counts().rename_axis("guide_tradeoff_class").reset_index(name="count"),
                use_container_width=True,
                hide_index=True,
            )
        with col_s:
            st.dataframe(
                df_acc_params["selfing_tradeoff_class"].value_counts().rename_axis("selfing_tradeoff_class").reset_index(name="count"),
                use_container_width=True,
                hide_index=True,
            )

    st.subheader("Downloads")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button("all_runs.csv", to_csv_bytes(df_runs), "parameter_filtering_all_runs.csv", "text/csv")
        st.download_button("accepted_runs.csv", to_csv_bytes(df_acc_runs), "parameter_filtering_accepted_runs.csv", "text/csv")
    with d2:
        st.download_button("accepted_ranges.csv", to_csv_bytes(df_ranges), "parameter_filtering_accepted_ranges.csv", "text/csv")
        st.download_button("scenario_summary.csv", to_csv_bytes(df_summary), "parameter_filtering_scenario_summary.csv", "text/csv")
    with d3:
        st.download_button("constraint_passed_parameter_sets.csv", to_csv_bytes(df_acc_params), "constraint_passed_parameter_sets.csv", "text/csv")
        st.download_button("rejected_parameter_sets.csv", to_csv_bytes(df_rej), "parameter_sampling_rejected_sets.csv", "text/csv")

else:
    st.markdown(
        "Choose a preset and click **Run Research Mode**. The strict rule requires all 6 observed "
        "relations to match; the relaxed rule accepts 5/6 matches."
    )
