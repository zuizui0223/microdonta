"""CAPOM — Campanula Izu Islands: Interactive Pattern-Oriented Modelling App.

Implements generative inverse estimation for the selfing-syndrome / nectar-guide
loss gradient across the Izu Islands (Mainland → Oshima → Kozu → Hachijo).

Run:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import math
import random
import sys
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Campanula CAPOM",
    layout="wide",
    page_icon="🌿",
)

# ── Sidebar navigation ────────────────────────────────────────────────────────
page = st.sidebar.radio(
    "Navigation",
    [
        "🧪 ABM Simulation",
        "🔬 ABC Inference",
        "📊 Observed Patterns",
        "🔍 Causal Structure Comparison",
        "🌿 TenSnap Visualisation",
    ],
)

st.sidebar.divider()
st.sidebar.caption(
    "CAPOM: Constraint-Aware Pattern-Oriented Modelling  \n"
    "*Campanula punctata* var. *hondoensis* / *microdonta*  \n"
    "Izu Islands pollination ecology"
)

# ── Shared constants ──────────────────────────────────────────────────────────
POPULATION_ORDER = ["Mainland", "Oshima", "Kozu", "Hachijo"]

PRESETS: dict[str, dict] = {
    "Mainland": dict(
        nectar_guide=0.62, flower_size=0.82, herkogamy=0.78, selfing_ability=0.22,
        bombus_frequency=1.0, pollinator_environment=0.78, migration_rate=0.10,
        guide_cost=0.06, genetic_drift_strength=0.035, mutation_sd=0.055,
        inbreeding_load=0.32, bombus_guide_dependence=0.75,
        other_pollinator_guide_use=0.12, base_outcross=0.10,
    ),
    "Oshima": dict(
        nectar_guide=0.55, flower_size=0.72, herkogamy=0.62, selfing_ability=0.36,
        bombus_frequency=0.35, pollinator_environment=0.58, migration_rate=0.05,
        guide_cost=0.06, genetic_drift_strength=0.035, mutation_sd=0.055,
        inbreeding_load=0.25, bombus_guide_dependence=0.75,
        other_pollinator_guide_use=0.12, base_outcross=0.10,
    ),
    "Kozu": dict(
        nectar_guide=0.42, flower_size=0.58, herkogamy=0.44, selfing_ability=0.52,
        bombus_frequency=0.0, pollinator_environment=0.42, migration_rate=0.025,
        guide_cost=0.06, genetic_drift_strength=0.05, mutation_sd=0.055,
        inbreeding_load=0.18, bombus_guide_dependence=0.0,
        other_pollinator_guide_use=0.18, base_outcross=0.10,
    ),
    "Hachijo": dict(
        nectar_guide=0.28, flower_size=0.46, herkogamy=0.30, selfing_ability=0.68,
        bombus_frequency=0.0, pollinator_environment=0.36, migration_rate=0.01,
        guide_cost=0.06, genetic_drift_strength=0.07, mutation_sd=0.055,
        inbreeding_load=0.12, bombus_guide_dependence=0.0,
        other_pollinator_guide_use=0.18, base_outcross=0.10,
    ),
}

OBSERVED: dict[str, dict] = {
    "Mainland": dict(mean_nectar_guide=0.62, selfing_rate=0.22, Fis=0.08, outcrossing_rate=0.65),
    "Oshima":   dict(mean_nectar_guide=0.55, selfing_rate=0.35, Fis=0.14, outcrossing_rate=0.50),
    "Kozu":     dict(mean_nectar_guide=0.42, selfing_rate=0.52, Fis=0.28, outcrossing_rate=0.32),
    "Hachijo":  dict(mean_nectar_guide=0.28, selfing_rate=0.68, Fis=0.42, outcrossing_rate=0.18),
}

TRAIT_LABELS: dict[str, str] = {
    "mean_nectar_guide": "nectar guide",
    "mean_flower_size": "flower size",
    "mean_herkogamy": "herkogamy",
    "mean_selfing_ability": "selfing ability",
    "selfing_rate": "selfing rate",
    "outcrossing_rate": "outcrossing rate",
    "Fis": "inbreeding coefficient (Fis)",
    "Fst": "population differentiation (Fst)",
    "mean_fitness": "mean fitness",
    "failed_rate": "pollination failure rate",
    "mean_neutral_diversity": "neutral diversity",
    "nectar_guide": "nectar guide",
    "flower_size": "flower size",
    "herkogamy": "herkogamy",
    "selfing_ability": "selfing ability",
    "bombus_frequency": "Bombus frequency",
    "pollinator_environment": "pollinator environment",
    "migration_rate": "migration rate",
    "admixture_index": "admixture index",
}


# ── Inline ABM trajectory (mirrors abm_core.simulate but records each gen) ────
def _clamp(v, lo=0.0, hi=1.0): return max(lo, min(hi, v))
def _mean(xs): return sum(xs) / len(xs) if xs else math.nan


def run_trajectory(
    params: dict, generations: int, population_size: int, seed: int
) -> pd.DataFrame:
    try:
        from attraction_trait_model.agents import PlantAgent
        from attraction_trait_model.environment import Environment
        from attraction_trait_model.fitness import fitness as compute_fitness
        from attraction_trait_model.inheritance import drift_strength, inherit_trait
        from attraction_trait_model.parameters import ModelParameters
        from attraction_trait_model.reproduction import (
            clamp, outcrossing_probability, selfing_probability,
        )
    except ImportError as e:
        st.error(f"attraction_trait_model not found: {e}")
        return pd.DataFrame()

    rng = random.Random(seed)
    bom = _clamp(params.get("bombus_frequency", 0.0))
    env = Environment(
        name=params.get("population_name", "sim"),
        bombus_frequency=bom,
        small_pollinator_frequency=_clamp(1.0 - bom),
        pollinator_environment=_clamp(params.get("pollinator_environment", 0.5)),
        migration_rate=_clamp(params.get("migration_rate", 0.05), 0, 1),
        effective_population_size=float(params.get("effective_population_size", 100)),
        island_distance=float(params.get("island_distance", 0)),
    )
    mu = params.get("mutation_sd", 0.055)
    mp = ModelParameters(
        base_outcross_rate=params.get("base_outcross", 0.10),
        bombus_efficiency=params.get("bombus_pollination_efficiency", 0.86),
        small_pollinator_efficiency=params.get("other_pollinator_efficiency", 0.34),
        bombus_guide_use=params.get("bombus_guide_dependence", 0.75),
        small_pollinator_guide_use=params.get("other_pollinator_guide_use", 0.12),
        seed_set_outcrossing=params.get("seed_set_outcrossing", 0.92),
        seed_set_selfing=params.get("seed_set_selfing", 0.46),
        germination_outcrossed=params.get("germination_outcrossed", 0.86),
        inbreeding_depression=params.get("inbreeding_load", 0.32),
        guide_cost=params.get("guide_cost", 0.06),
        flower_size_cost=params.get("flower_size_cost", 0.02),
        mutation_sd_guide=mu,
        mutation_sd_flower_size=mu * 0.5,
        mutation_sd_herkogamy=mu * 0.5,
        mutation_sd_selfing_ability=mu * 0.5,
        base_drift_strength=params.get("genetic_drift_strength", 0.035),
    )

    def new_agent():
        def g(k, d, s): return _clamp(rng.gauss(params.get(k, d), s))
        return PlantAgent(
            nectar_guide=g("nectar_guide", 0.5, 0.08),
            flower_size=g("flower_size", 0.65, 0.08),
            herkogamy=g("herkogamy", 0.55, 0.08),
            selfing_ability=g("selfing_ability", 0.40, 0.06),
            neutral_diversity=_clamp(rng.gauss(0.78, 0.08)),
            x=rng.uniform(0, 1), y=rng.uniform(0, 1),
        )

    def evaluate(pop):
        for a in pop:
            po = outcrossing_probability(a, env, mp)
            ps = selfing_probability(a, po)
            r = rng.random()
            a.reproduction_mode = "outcrossing" if r < po else "selfing" if r < po + ps else "failed"
            a.fitness = compute_fitness(a, mp)

    def offspring(parent):
        d = drift_strength(env, mp)
        div = parent.neutral_diversity
        div = div + 0.045 if parent.reproduction_mode == "outcrossing" else \
              div * (1 - 0.5 * mp.inbreeding_depression) if parent.reproduction_mode == "selfing" else \
              div * 0.96
        div += env.migration_rate * (0.82 - div)
        return PlantAgent(
            nectar_guide=inherit_trait(parent.nectar_guide, mp.mutation_sd_guide, d, rng),
            flower_size=inherit_trait(parent.flower_size, mp.mutation_sd_flower_size, d, rng),
            herkogamy=inherit_trait(parent.herkogamy, mp.mutation_sd_herkogamy, d, rng),
            selfing_ability=inherit_trait(parent.selfing_ability, mp.mutation_sd_selfing_ability, d, rng),
            neutral_diversity=_clamp(div + rng.gauss(0, d)),
            x=_clamp(parent.x + rng.gauss(0, 0.055)),
            y=_clamp(parent.y + rng.gauss(0, 0.055)),
        )

    def snap(gen, pop):
        sr = _mean([1.0 if a.reproduction_mode == "selfing" else 0.0 for a in pop])
        oc = _mean([1.0 if a.reproduction_mode == "outcrossing" else 0.0 for a in pop])
        dv = _mean([a.neutral_diversity for a in pop])
        fis = _clamp(sr * (1.0 - 0.5 * env.migration_rate))
        fst = _clamp((1.0 - env.migration_rate) * (1.0 - oc) * (1.0 - dv))
        return dict(
            generation=gen,
            mean_nectar_guide=_mean([a.nectar_guide for a in pop]),
            mean_flower_size=_mean([a.flower_size for a in pop]),
            mean_herkogamy=_mean([a.herkogamy for a in pop]),
            mean_selfing_ability=_mean([a.selfing_ability for a in pop]),
            selfing_rate=sr, outcrossing_rate=oc,
            failed_rate=_mean([1.0 if a.reproduction_mode == "failed" else 0.0 for a in pop]),
            mean_fitness=_mean([a.fitness for a in pop]),
            mean_neutral_diversity=dv, Fis=fis, Fst=fst,
        )

    pop = [new_agent() for _ in range(population_size)]
    evaluate(pop)
    records = [snap(0, pop)]
    for gen in range(1, generations + 1):
        tf = sum(a.fitness for a in pop)
        if tf <= 0: break
        parents = rng.choices(pop, weights=[a.fitness / tf for a in pop], k=population_size)
        pop = [offspring(p) for p in parents]
        evaluate(pop)
        records.append(snap(gen, pop))
    return pd.DataFrame(records)


# ── Inline ABC with progress bar ──────────────────────────────────────────────
def run_abc_inline(
    population_name: str,
    n_samples: int,
    epsilon: float,
    abm_generations: int,
    abm_population_size: int,
    seed: int,
    progress_bar,
    status_text,
) -> tuple[pd.DataFrame, float, int]:
    """Run ABC rejection sampling with Streamlit progress updates.

    Returns (samples_df, acceptance_rate, n_attempted).
    """
    try:
        from constraint_abm.abm_core import simulate as abm_simulate
        from examples.campanula_izu.observed_patterns import (
            POPULATION_FIXED_PARAMS,
            POPULATION_OBSERVED,
            LATENT_PARAMS,
            BIOLOGICAL_CONSTRAINTS,
        )
    except ImportError as e:
        st.error(f"Import error: {e}")
        return pd.DataFrame(), 0.0, 0

    fixed = POPULATION_FIXED_PARAMS[population_name]
    patterns = POPULATION_OBSERVED[population_name]
    latent_params = LATENT_PARAMS
    constraints = BIOLOGICAL_CONSTRAINTS

    rng = random.Random(seed)

    def simulate_fn(params, abm_seed):
        return abm_simulate(params, generations=abm_generations,
                            population_size=abm_population_size, seed=abm_seed)
    weight_sum = sum(p.weight for p in patterns) or 1.0
    accepted = []
    log_interval = max(1, n_samples // 20)

    for i in range(n_samples):
        candidate = {lp.name: rng.uniform(lp.lower, lp.upper) for lp in latent_params}
        full_params = {**fixed, **candidate}

        if not all(c.predicate(full_params) for c in constraints):
            continue

        try:
            simulated = simulate_fn(full_params, rng.randint(0, 99999))
        except Exception:
            continue

        # Use raw absolute error (not tolerance-normalised) so that ε is
        # interpretable as mean absolute deviation in [0, 1] trait space.
        total_dist = 0.0
        pat_dists = {}
        for pat in patterns:
            if pat.name not in simulated:
                d = 1.0
            else:
                try:
                    d = abs(float(simulated[pat.name]) - float(pat.target))
                except (TypeError, ValueError):
                    d = 1.0
            pat_dists[pat.name] = d
            total_dist += pat.weight * d
        total_dist /= weight_sum

        if total_dist <= epsilon:
            row = {**candidate, "distance": total_dist}
            row.update({f"d_{k}": v for k, v in pat_dists.items()})
            accepted.append(row)

        if (i + 1) % log_interval == 0:
            frac = (i + 1) / n_samples
            rate = len(accepted) / (i + 1)
            progress_bar.progress(frac)
            status_text.text(
                f"Sampling: {i+1}/{n_samples} | "
                f"Accepted: {len(accepted)} | "
                f"Acceptance rate: {rate:.3%}"
            )

    progress_bar.progress(1.0)
    latent_names = [lp.name for lp in latent_params]
    pat_cols = [f"d_{p.name}" for p in patterns]
    all_cols = latent_names + ["distance"] + pat_cols
    df = pd.DataFrame(accepted) if accepted else pd.DataFrame(columns=all_cols)
    rate = len(accepted) / max(1, n_samples)
    return df, rate, n_samples


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ABM Simulation
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🧪 ABM Simulation":
    st.title("Agent-Based Model — Forward Simulation")
    st.markdown(
        "Run the ABM forward in time to explore how environmental and mechanistic "
        "parameters drive evolutionary change in nectar-guide expression, mating system, "
        "and population genetic structure."
    )

    col_p, col_r = st.columns([1, 2], gap="large")

    with col_p:
        st.subheader("Parameters")
        preset = st.selectbox("Preset population", ["Custom"] + POPULATION_ORDER)
        p = PRESETS.get(preset, PRESETS["Mainland"]).copy()

        st.markdown("**Pollinator environment**")
        p["bombus_frequency"] = st.slider(
            "*Bombus* frequency", 0.0, 1.0, float(p["bombus_frequency"]), 0.05,
            help="Fraction of pollinator visits by Bombus (bumblebees)")
        p["pollinator_environment"] = st.slider(
            "Pollinator environment density", 0.0, 1.0, float(p["pollinator_environment"]), 0.05,
            help="Overall abundance of functional pollinators")
        p["migration_rate"] = st.slider(
            "Migration rate", 0.0, 0.20, float(p["migration_rate"]), 0.005)

        st.markdown("**Latent mechanistic parameters** *(inference targets)*")
        p["guide_cost"] = st.slider(
            "Nectar-guide maintenance cost", 0.01, 0.20, float(p["guide_cost"]), 0.005,
            help="Metabolic cost of maintaining nectar-guide pigmentation")
        p["genetic_drift_strength"] = st.slider(
            "Genetic drift strength", 0.005, 0.10, float(p["genetic_drift_strength"]), 0.005,
            help="Per-generation random perturbation; higher on small isolated islands")
        p["mutation_sd"] = st.slider(
            "Mutation SD (nectar guide)", 0.01, 0.12, float(p["mutation_sd"]), 0.005)
        p["inbreeding_load"] = st.slider(
            "Inbreeding depression", 0.0, 0.60, float(p["inbreeding_load"]), 0.01,
            help="Fitness reduction in selfed offspring")

        st.markdown("**Initial trait means (generation 0)**")
        p["nectar_guide"] = st.slider(
            "Nectar guide (initial)", 0.0, 1.0, float(p["nectar_guide"]), 0.05)
        p["selfing_ability"] = st.slider(
            "Selfing ability (initial)", 0.0, 1.0, float(p["selfing_ability"]), 0.05)

        st.markdown("**Simulation settings**")
        generations = st.slider("Generations", 20, 200, 80, 10)
        pop_size = st.select_slider("Population size", [40, 80, 120, 160, 240, 320], value=160)
        seed = st.number_input("Random seed", 0, 9999, 42, 1)

        run_btn = st.button("▶ Run simulation", type="primary", use_container_width=True)

    with col_r:
        if run_btn:
            with st.spinner("Running ABM…"):
                df_traj = run_trajectory(p, generations, int(pop_size), int(seed))
            st.session_state["sim_df"] = df_traj
            st.session_state["sim_preset"] = preset
        elif "sim_df" in st.session_state:
            df_traj = st.session_state["sim_df"]
            preset = st.session_state.get("sim_preset", preset)
        else:
            st.info("Set parameters on the left and click **▶ Run simulation**.")
            st.markdown("""
**What this shows:**
- How nectar-guide expression evolves under different *Bombus* environments
- The rise of selfing and inbreeding under pollinator loss
- Effect of genetic drift strength (smaller populations, more isolated islands)
- Interaction between guide maintenance cost and mating-system evolution
""")
            df_traj = None

        if df_traj is not None and not df_traj.empty:
            # Trait trajectory
            st.subheader("Trait trajectory over generations")
            traj_vars = st.multiselect(
                "Variables to display",
                [c for c in df_traj.columns if c != "generation"],
                default=["mean_nectar_guide", "selfing_rate", "Fis", "mean_selfing_ability"],
                format_func=lambda x: TRAIT_LABELS.get(x, x),
            )
            if traj_vars:
                try:
                    import altair as alt
                    melted = df_traj[["generation"] + traj_vars].melt(
                        id_vars="generation", var_name="variable", value_name="value")
                    melted["Variable"] = melted["variable"].map(TRAIT_LABELS)
                    chart = (
                        alt.Chart(melted).mark_line(strokeWidth=2)
                        .encode(
                            x=alt.X("generation:Q", title="Generation"),
                            y=alt.Y("value:Q", scale=alt.Scale(domain=[0, 1.05]), title="Value"),
                            color=alt.Color("Variable:N"),
                            tooltip=["generation", "Variable", alt.Tooltip("value:Q", format=".3f")],
                        ).properties(height=320).interactive()
                    )
                    st.altair_chart(chart, use_container_width=True)
                except ImportError:
                    st.line_chart(df_traj.set_index("generation")[traj_vars])

            # Final generation vs. observed
            st.subheader("Final generation vs. observed values")
            final = df_traj.iloc[-1].to_dict()
            obs = OBSERVED.get(preset, {})
            rows = []
            for sk, ok in [
                ("mean_nectar_guide", "mean_nectar_guide"),
                ("selfing_rate", "selfing_rate"),
                ("outcrossing_rate", "outcrossing_rate"),
                ("Fis", "Fis"),
            ]:
                sv = final.get(sk, float("nan"))
                ov = obs.get(ok)
                rows.append({
                    "Trait": TRAIT_LABELS.get(sk, sk),
                    "Simulated (final gen)": round(sv, 3),
                    "Observed": round(ov, 3) if ov is not None else "—",
                    "|Δ|": round(abs(sv - ov), 3) if ov is not None else "—",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            with st.expander("All final-generation statistics"):
                st.dataframe(
                    pd.DataFrame([
                        {"Statistic": TRAIT_LABELS.get(k, k), "Value": round(v, 4)}
                        for k, v in final.items() if k != "generation"
                    ]),
                    use_container_width=True, hide_index=True,
                )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ABC Inference
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔬 ABC Inference":
    st.title("ABC Rejection Sampling — Generative Inverse Estimation")
    st.markdown(
        "Approximate Bayesian Computation (ABC) estimates the posterior distribution "
        "of **latent mechanistic parameters** that cannot be measured directly in the "
        "field (guide maintenance cost, drift strength, etc.), using observable "
        "ecological and genetic patterns as constraints."
    )

    col_a, col_b = st.columns([1, 2], gap="large")

    with col_a:
        st.subheader("Inference settings")
        pop_name = st.selectbox("Target population", POPULATION_ORDER)

        with st.expander("Observed patterns used as constraints", expanded=False):
            obs_rows = []
            for k, v in OBSERVED[pop_name].items():
                obs_rows.append({"Pattern": TRAIT_LABELS.get(k, k), "Target value": v})
            st.dataframe(pd.DataFrame(obs_rows), use_container_width=True, hide_index=True)

        st.markdown("**ABC settings**")
        n_samples = st.slider(
            "Prior samples (n_samples)", 200, 3000, 800, 100,
            help="Total draws from the prior. More = better posterior but slower.")
        epsilon = st.slider(
            "Acceptance threshold (ε)", 0.05, 0.50, 0.15, 0.01,
            help=(
                "ε is the maximum *mean absolute error* across pattern targets. "
                "e.g. ε=0.15 accepts simulations where the average trait deviation "
                "from observed values is < 0.15 (on a 0–1 scale). "
                "Increase if no samples are accepted."
            ))

        st.markdown("**ABM settings** *(per simulation call)*")
        abm_gen = st.slider("Generations per ABM run", 20, 100, 60, 10,
                             help="More generations → slower but may reach equilibrium")
        abm_pop = st.select_slider("Population size per ABM run", [40, 60, 80, 120, 160], value=80)
        abc_seed = st.number_input("Random seed", 0, 9999, 42, 1)

        est_sec = n_samples * abm_gen * abm_pop * 2e-7
        st.caption(f"⏱ Estimated runtime: ~{est_sec:.0f}s (varies by machine)")
        st.caption("If acceptance rate is 0%, increase ε or check the ABM settings.")

        run_abc = st.button("▶ Run ABC inference", type="primary", use_container_width=True)

    with col_b:
        if run_abc:
            prog = st.progress(0.0)
            status = st.empty()
            df_abc, acc_rate, n_att = run_abc_inline(
                pop_name, n_samples, epsilon, abm_gen, abm_pop, int(abc_seed), prog, status
            )
            st.session_state["abc_df"] = df_abc
            st.session_state["abc_rate"] = acc_rate
            st.session_state["abc_pop"] = pop_name
            st.session_state["abc_epsilon"] = epsilon
        elif "abc_df" in st.session_state:
            df_abc = st.session_state["abc_df"]
            acc_rate = st.session_state["abc_rate"]
            pop_name = st.session_state.get("abc_pop", pop_name)
            epsilon = st.session_state.get("abc_epsilon", epsilon)
        else:
            st.info("Configure settings on the left and click **▶ Run ABC inference**.")
            st.markdown("""
**Latent parameters estimated:**
| Parameter | Ecological meaning |
|-----------|-------------------|
| `guide_cost` | Metabolic cost of nectar-guide maintenance |
| `bombus_guide_dependence` | Degree to which *Bombus* visits are guide-mediated |
| `other_pollinator_guide_use` | Guide utilisation by small bees |
| `genetic_drift_strength` | Random per-generation trait perturbation |
| `mutation_sd` | Mutational input to nectar-guide variation |
| `base_outcross` | Baseline outcrossing probability (wind/gravity) |
""")
            df_abc = None

        if df_abc is not None:
            latent_cols = [c for c in df_abc.columns
                           if not c.startswith("d_") and c != "distance"]

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Accepted samples", f"{len(df_abc):,}")
            col_m2.metric("Acceptance rate", f"{acc_rate:.3%}")
            col_m3.metric("ε threshold", f"{epsilon}")

            if df_abc.empty:
                st.warning(
                    "No samples accepted. Try increasing ε or reducing generations/population size. "
                    "The patterns may be too strict for the current ABM settings."
                )
            else:
                # Posterior distributions
                st.subheader("Posterior distributions")
                sel_params = st.multiselect(
                    "Parameters to display",
                    latent_cols,
                    default=latent_cols[:min(6, len(latent_cols))],
                )
                if sel_params:
                    try:
                        import altair as alt
                        melted = df_abc[sel_params].melt(
                            var_name="parameter", value_name="value")
                        hist = (
                            alt.Chart(melted).mark_bar(opacity=0.75)
                            .encode(
                                x=alt.X("value:Q", bin=alt.Bin(maxbins=25), title="Value"),
                                y=alt.Y("count():Q", title="Frequency"),
                                color="parameter:N",
                                facet=alt.Facet("parameter:N", columns=3),
                            )
                            .properties(width=250, height=160)
                            .resolve_scale(x="independent", y="independent")
                        )
                        st.altair_chart(hist)
                    except ImportError:
                        st.dataframe(df_abc[sel_params].describe(), use_container_width=True)

                # Posterior summary table
                st.subheader("Posterior summary")
                summary_rows = []
                for col in latent_cols:
                    s = df_abc[col]
                    summary_rows.append({
                        "Parameter": col,
                        "Mean": round(s.mean(), 4),
                        "SD": round(s.std(), 4),
                        "5th pct": round(s.quantile(0.05), 4),
                        "Median": round(s.quantile(0.50), 4),
                        "95th pct": round(s.quantile(0.95), 4),
                    })
                st.dataframe(
                    pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

                # Pattern distances
                with st.expander("Pattern distances of accepted samples"):
                    d_cols = [c for c in df_abc.columns if c.startswith("d_")]
                    if d_cols:
                        st.dataframe(df_abc[["distance"] + d_cols].describe().round(4),
                                     use_container_width=True)

                # Download
                csv_bytes = df_abc.to_csv(index=False).encode()
                st.download_button(
                    "⬇ Download posterior samples (CSV)",
                    csv_bytes,
                    file_name=f"posterior_{pop_name}_eps{epsilon}.csv",
                    mime="text/csv",
                )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Observed Patterns
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Observed Patterns":
    st.title("Observed Patterns — Izu Islands Isolation Gradient")
    st.markdown(
        "Moving from the mainland (Honshu) towards the most isolated island (Hachijo), "
        "a consistent gradient is observed: **nectar-guide expression ↓**, "
        "**flower size ↓**, **herkogamy ↓** (selfing-syndrome progression), "
        "**selfing rate ↑**, **inbreeding coefficient Fis ↑**, "
        "***Bombus* frequency ↓** (pollinator fauna simplification)."
    )

    obs_trait_opts = {
        "nectar_guide": "nectar guide",
        "flower_size": "flower size",
        "herkogamy": "herkogamy",
        "selfing_ability": "selfing ability",
        "bombus_frequency": "*Bombus* frequency",
        "pollinator_environment": "pollinator environment",
        "migration_rate": "migration rate",
    }
    rows = [{"population": k, **{kk: v for kk, v in vv.items() if kk in obs_trait_opts}}
            for k, vv in PRESETS.items()]
    df_obs = pd.DataFrame(rows)
    df_obs["population"] = pd.Categorical(df_obs["population"], POPULATION_ORDER, ordered=True)
    df_obs = df_obs.sort_values("population").reset_index(drop=True)

    selected_traits = st.multiselect(
        "Traits to display",
        list(obs_trait_opts.keys()),
        default=["nectar_guide", "selfing_ability", "bombus_frequency", "pollinator_environment"],
        format_func=lambda x: obs_trait_opts[x],
    )
    if selected_traits:
        try:
            import altair as alt
            melted = df_obs[["population"] + selected_traits].melt(
                id_vars="population", var_name="trait", value_name="value")
            melted["Trait"] = melted["trait"].map(obs_trait_opts)
            chart = (
                alt.Chart(melted).mark_line(point=True, strokeWidth=2.5)
                .encode(
                    x=alt.X("population:O", sort=POPULATION_ORDER, title="Population"),
                    y=alt.Y("value:Q", scale=alt.Scale(domain=[0, 1.05]), title="Value [0–1]"),
                    color=alt.Color("Trait:N"),
                    tooltip=["population", "Trait", alt.Tooltip("value:Q", format=".3f")],
                ).properties(height=360).interactive()
            )
            st.altair_chart(chart, use_container_width=True)
        except ImportError:
            st.line_chart(df_obs.set_index("population")[selected_traits])

    st.subheader("CAPOM pattern targets (used in ABC)")
    st.markdown(
        "The following quantitative patterns from each population constrain "
        "the ABC posterior. Weights reflect measurement reliability."
    )
    for pop in POPULATION_ORDER:
        obs = OBSERVED[pop]
        with st.expander(f"{pop}"):
            st.dataframe(
                pd.DataFrame([
                    {"Pattern": TRAIT_LABELS.get(k, k), "Target": v,
                     "Weight": 2.0 if "guide" in k else 1.5 if "selfing" in k or "outcross" in k else 1.0}
                    for k, v in obs.items()
                ]),
                use_container_width=True, hide_index=True,
            )

    with st.expander("Full fixed parameter table"):
        rows2 = [{"population": k, **v} for k, v in PRESETS.items()]
        st.dataframe(pd.DataFrame(rows2).set_index("population"), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Causal Structure Comparison
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Causal Structure Comparison":
    st.title("Causal Structure Comparison — M1–M5 (Stage 3)")
    st.markdown(
        "Five competing hypotheses are evaluated using a **deterministic proxy "
        "simulation** (no stochastic ABM) by predicting the direction of Oshima–Hachijo "
        "pattern contrasts and scoring them against observed ordinal relations."
    )

    st.markdown("""
| Model | Hypothesis | Mechanism |
|-------|-----------|-----------|
| **M1** | Direct pollinator effect | *Bombus* directly increases nectar-guide benefit through guide-dependent foraging |
| **M2** | Selfing-mediated | Reduced outcrossing opportunity → reproductive-assurance selfing → guide loss |
| **M3** | Combined M1 + M2 | Both direct selection and selfing-mediated pathways act simultaneously |
| **M4** | Common island cause | Island isolation drives multiple traits via shared causal factors (Ne, drift) |
| **M5** | Drift null | Neutral guide loss by genetic drift, no directional selection |
""")

    try:
        from examples.campanula_izu.causal_structures import campanula_causal_structures
        from examples.campanula_izu.proxy_simulation import simulate_campanula_causal_structure

        structures = campanula_causal_structures()
        OBS_RELS = {
            "nectar_guide": "Oshima > Hachijo",
            "selfing_rate": "Oshima < Hachijo",
            "herkogamy": "Oshima > Hachijo",
            "flower_size": "Oshima > Hachijo",
            "Fis": "Oshima < Hachijo",
            "Bombus_frequency": "Oshima > Hachijo",
        }

        summary_rows, detail_rows, val_rows = [], [], []
        for s in structures:
            rels, outputs = simulate_campanula_causal_structure(s)
            matches = sum(1 for var, exp in OBS_RELS.items() if rels.get(var) == exp)
            summary_rows.append({
                "Model": s.name, "Score": matches, "Max": len(OBS_RELS),
                "Fraction": f"{matches}/{len(OBS_RELS)}", "Description": s.description,
            })
            for var, obs_rel in OBS_RELS.items():
                pred = rels.get(var, "—")
                detail_rows.append({
                    "Model": s.name, "Variable": TRAIT_LABELS.get(var.lower(), var),
                    "Observed": obs_rel, "Predicted": pred,
                    "Match": "✅" if pred == obs_rel else "❌",
                })
            for o in outputs:
                val_rows.append({
                    "Model": s.name, "Population": o.population,
                    "Nectar guide": round(o.nectar_guide, 3),
                    "Selfing rate": round(o.selfing_rate, 3),
                    "Herkogamy": round(o.herkogamy, 3),
                    "Flower size": round(o.flower_size, 3),
                    "Fis": round(o.Fis, 3),
                })

        df_sum = pd.DataFrame(summary_rows).sort_values("Score", ascending=False)

        st.subheader("Score ranking")
        st.dataframe(df_sum[["Model", "Fraction", "Description"]],
                     use_container_width=True, hide_index=True)

        try:
            import altair as alt
            bar = (
                alt.Chart(df_sum).mark_bar()
                .encode(
                    x=alt.X("Score:Q", scale=alt.Scale(domain=[0, len(OBS_RELS)]),
                             title="Patterns correctly predicted"),
                    y=alt.Y("Model:O", sort="-x"),
                    color=alt.condition(
                        alt.datum["Score"] == int(df_sum["Score"].max()),
                        alt.value("#2ecc71"), alt.value("#95a5a6"),
                    ),
                    tooltip=["Model", "Fraction", "Description"],
                ).properties(height=220)
            )
            st.altair_chart(bar, use_container_width=True)
        except ImportError:
            pass

        with st.expander("Predicted vs. observed — detail matrix"):
            df_d = pd.DataFrame(detail_rows)
            pivot = df_d.pivot(index="Variable", columns="Model", values="Match")
            st.dataframe(pivot, use_container_width=True)

        with st.expander("Proxy simulation output values (Oshima / Hachijo)"):
            st.dataframe(pd.DataFrame(val_rows), use_container_width=True, hide_index=True)

    except ImportError as e:
        st.error(f"Import error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TenSnap Visualisation
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🌿 TenSnap Visualisation":
    st.title("Agent-Level Realtime Visualisation — TenSnap")
    st.markdown(
        "TenSnap streams agent positions and trait values over WebSocket "
        "(`ws://localhost:8765`) and renders them in the browser. "
        "This complements the Streamlit app: while Streamlit shows aggregate "
        "statistics, TenSnap shows individual-agent spatial dynamics."
    )

    st.info(
        "**How to use:**\n\n"
        "1. Start the ABM WebSocket server locally:\n"
        "   ```\n"
        "   python abm/shimahotarubukuro_tensnap_abm.py\n"
        "   ```\n"
        "2. Open the TenSnap renderer (connects to `ws://localhost:8765` automatically).",
        icon="🌿",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.link_button("Open TenSnap renderer →", "https://tensnap.netlify.app/",
                        use_container_width=True)
    with col2:
        st.link_button("View ABM source code →",
                        "https://github.com/zuizui0223/microdonta/blob/main/abm/shimahotarubukuro_tensnap_abm.py",
                        use_container_width=True)

    st.subheader("ABM presets")
    st.markdown("""
| Preset | *Bombus* freq. | Small-bee freq. | Pop. size | Expected outcome |
|--------|---------------|----------------|-----------|-----------------|
| Mainland | 1.0 | 0.3 | 160 | *Bombus*-dominated; high outcrossing; guide maintained |
| Oshima | 0.35 | 0.55 | 140 | Mixed pollinator community; intermediate guide expression |
| Kozu | 0.0 | 0.65 | 100 | *Bombus*-absent; small-bee dependent; guide partially lost |
| Hachijo | 0.0 | 0.72 | 80 | Highest selfing rate; lowest nectar-guide expression |
""")

    st.subheader("Visual encoding")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**Agent colour:**
- 🟡 Yellow = high nectar-guide expression (≈ 1.0)
- 🟣 Purple = low nectar-guide expression (≈ 0.0)
""")
    with col_b:
        st.markdown("""
**Live charts:**
- Selfing rate per generation
- Inbreeding coefficient (Fis)
- Population differentiation (Fst)
""")
