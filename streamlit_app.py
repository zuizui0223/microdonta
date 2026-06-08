"""CAPOM — シマホタルブクロ インタラクティブシミュレーター.

実行: streamlit run streamlit_app.py
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
    page_title="シマホタルブクロ CAPOM",
    layout="wide",
    page_icon="🌿",
)

# ── ページ選択 ────────────────────────────────────────────────────────────────
page = st.sidebar.radio(
    "ページ",
    [
        "🧪 シミュレーション実行",
        "📊 観察パターン",
        "🔍 因果構造比較 (M1–M5)",
        "📈 ABC 事後分布",
        "🌿 TenSnap 可視化",
    ],
)

# ── プリセット ─────────────────────────────────────────────────────────────────
PRESETS: dict[str, dict[str, float]] = {
    "Mainland (本州)": dict(
        nectar_guide=0.62, flower_size=0.82, herkogamy=0.78, selfing_ability=0.22,
        bombus_frequency=1.0, pollinator_environment=0.78, migration_rate=0.10,
        guide_cost=0.06, genetic_drift_strength=0.035, mutation_sd=0.055,
        inbreeding_load=0.32,
    ),
    "Oshima (大島)": dict(
        nectar_guide=0.55, flower_size=0.72, herkogamy=0.62, selfing_ability=0.36,
        bombus_frequency=0.35, pollinator_environment=0.58, migration_rate=0.05,
        guide_cost=0.06, genetic_drift_strength=0.035, mutation_sd=0.055,
        inbreeding_load=0.25,
    ),
    "Kozu (神津島)": dict(
        nectar_guide=0.42, flower_size=0.58, herkogamy=0.44, selfing_ability=0.52,
        bombus_frequency=0.0, pollinator_environment=0.42, migration_rate=0.025,
        guide_cost=0.06, genetic_drift_strength=0.05, mutation_sd=0.055,
        inbreeding_load=0.18,
    ),
    "Hachijo (八丈島)": dict(
        nectar_guide=0.28, flower_size=0.46, herkogamy=0.30, selfing_ability=0.68,
        bombus_frequency=0.0, pollinator_environment=0.36, migration_rate=0.01,
        guide_cost=0.06, genetic_drift_strength=0.07, mutation_sd=0.055,
        inbreeding_load=0.12,
    ),
}

OBSERVED: dict[str, dict[str, float]] = {
    "Mainland (本州)": dict(nectar_guide=0.62, selfing_rate=0.22, Fis=0.08, outcrossing_rate=0.65),
    "Oshima (大島)":   dict(nectar_guide=0.55, selfing_rate=0.35, Fis=0.14, outcrossing_rate=0.50),
    "Kozu (神津島)":   dict(nectar_guide=0.42, selfing_rate=0.52, Fis=0.28, outcrossing_rate=0.32),
    "Hachijo (八丈島)": dict(nectar_guide=0.28, selfing_rate=0.68, Fis=0.42, outcrossing_rate=0.18),
}

TRAIT_JP = {
    "mean_nectar_guide": "蜜腺標識",
    "mean_flower_size": "花サイズ",
    "mean_herkogamy": "雌雄異熟",
    "mean_selfing_ability": "自殖能力",
    "selfing_rate": "自殖率",
    "outcrossing_rate": "外交配率",
    "Fis": "Fis (近交係数)",
    "Fst": "Fst (集団間分化)",
    "mean_fitness": "平均適応度",
}


# ── ABM 軌跡シミュレーター (インライン実装) ────────────────────────────────────
def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else math.nan


def run_trajectory(params: dict, generations: int, population_size: int, seed: int) -> pd.DataFrame:
    """世代ごとの統計を返す DataFrame を生成する。"""
    try:
        from attraction_trait_model.agents import PlantAgent
        from attraction_trait_model.environment import Environment
        from attraction_trait_model.fitness import fitness as compute_fitness
        from attraction_trait_model.inheritance import drift_strength, inherit_trait
        from attraction_trait_model.parameters import ModelParameters
        from attraction_trait_model.reproduction import (
            clamp,
            outcrossing_probability,
            selfing_probability,
        )
    except ImportError as e:
        st.error(f"attraction_trait_model が見つかりません: {e}")
        return pd.DataFrame()

    rng = random.Random(seed)
    bombus = _clamp(params.get("bombus_frequency", 0.0))
    env = Environment(
        name=params.get("population_name", "sim"),
        bombus_frequency=bombus,
        small_pollinator_frequency=_clamp(1.0 - bombus),
        pollinator_environment=_clamp(params.get("pollinator_environment", 0.5)),
        migration_rate=_clamp(params.get("migration_rate", 0.05), 0, 1),
        effective_population_size=float(params.get("effective_population_size", 100)),
        island_distance=float(params.get("island_distance", 0)),
    )
    mu = params.get("mutation_sd", 0.055)
    mu_t = mu * 0.5
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
        mutation_sd_flower_size=mu_t,
        mutation_sd_herkogamy=mu_t,
        mutation_sd_selfing_ability=mu_t,
        base_drift_strength=params.get("genetic_drift_strength", 0.035),
    )

    def init_agent() -> PlantAgent:
        def g(k, d, s): return _clamp(rng.gauss(params.get(k, d), s))
        return PlantAgent(
            nectar_guide=g("nectar_guide", 0.5, 0.08),
            flower_size=g("flower_size", 0.65, 0.08),
            herkogamy=g("herkogamy", 0.55, 0.08),
            selfing_ability=g("selfing_ability", 0.40, 0.06),
            neutral_diversity=_clamp(rng.gauss(0.78, 0.08)),
            x=rng.uniform(0, 1),
            y=rng.uniform(0, 1),
        )

    def evaluate(pop):
        for a in pop:
            p_out = outcrossing_probability(a, env, mp)
            p_self = selfing_probability(a, p_out)
            r = rng.random()
            if r < p_out:
                a.reproduction_mode = "outcrossing"
            elif r < p_out + p_self:
                a.reproduction_mode = "selfing"
            else:
                a.reproduction_mode = "failed"
            a.fitness = compute_fitness(a, mp)

    def make_offspring(parent) -> PlantAgent:
        d_sd = drift_strength(env, mp)
        div = parent.neutral_diversity
        if parent.reproduction_mode == "outcrossing":
            div += 0.045
        elif parent.reproduction_mode == "selfing":
            div *= (1.0 - 0.5 * mp.inbreeding_depression)
        else:
            div *= 0.96
        div += env.migration_rate * (0.82 - div)
        return PlantAgent(
            nectar_guide=inherit_trait(parent.nectar_guide, mp.mutation_sd_guide, d_sd, rng),
            flower_size=inherit_trait(parent.flower_size, mp.mutation_sd_flower_size, d_sd, rng),
            herkogamy=inherit_trait(parent.herkogamy, mp.mutation_sd_herkogamy, d_sd, rng),
            selfing_ability=inherit_trait(parent.selfing_ability, mp.mutation_sd_selfing_ability, d_sd, rng),
            neutral_diversity=_clamp(div + rng.gauss(0, d_sd)),
            x=_clamp(parent.x + rng.gauss(0, 0.055)),
            y=_clamp(parent.y + rng.gauss(0, 0.055)),
        )

    def snapshot(gen, pop) -> dict:
        selfing = _mean([1.0 if a.reproduction_mode == "selfing" else 0.0 for a in pop])
        outcross = _mean([1.0 if a.reproduction_mode == "outcrossing" else 0.0 for a in pop])
        div = _mean([a.neutral_diversity for a in pop])
        fis = _clamp(selfing * (1.0 - 0.5 * env.migration_rate))
        fst = _clamp((1.0 - env.migration_rate) * (1.0 - outcross) * (1.0 - div))
        return {
            "generation": gen,
            "mean_nectar_guide": _mean([a.nectar_guide for a in pop]),
            "mean_flower_size": _mean([a.flower_size for a in pop]),
            "mean_herkogamy": _mean([a.herkogamy for a in pop]),
            "mean_selfing_ability": _mean([a.selfing_ability for a in pop]),
            "selfing_rate": selfing,
            "outcrossing_rate": outcross,
            "Fis": fis,
            "Fst": fst,
            "mean_fitness": _mean([a.fitness for a in pop]),
        }

    pop = [init_agent() for _ in range(population_size)]
    evaluate(pop)
    records = [snapshot(0, pop)]

    for gen in range(1, generations + 1):
        total_fit = sum(a.fitness for a in pop)
        if total_fit <= 0:
            break
        weights = [a.fitness / total_fit for a in pop]
        parents = rng.choices(pop, weights=weights, k=population_size)
        pop = [make_offspring(p) for p in parents]
        evaluate(pop)
        records.append(snapshot(gen, pop))

    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════════════════
# ページ: シミュレーション実行
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🧪 シミュレーション実行":
    st.title("ABM シミュレーション実行")

    col_param, col_result = st.columns([1, 2], gap="large")

    with col_param:
        st.subheader("パラメータ設定")

        preset_name = st.selectbox(
            "プリセット",
            ["カスタム"] + list(PRESETS.keys()),
            index=1,
        )
        p = PRESETS.get(preset_name, PRESETS["Mainland (本州)"]).copy()

        st.markdown("**環境パラメータ**")
        p["bombus_frequency"] = st.slider("マルハナバチ頻度", 0.0, 1.0, float(p["bombus_frequency"]), 0.05)
        p["pollinator_environment"] = st.slider("伝播者環境密度", 0.0, 1.0, float(p["pollinator_environment"]), 0.05)
        p["migration_rate"] = st.slider("移住率", 0.0, 0.20, float(p["migration_rate"]), 0.005)

        st.markdown("**潜在パラメータ (推定対象)**")
        p["guide_cost"] = st.slider("蜜腺標識維持コスト", 0.01, 0.20, float(p["guide_cost"]), 0.005)
        p["genetic_drift_strength"] = st.slider("遺伝的浮動強度", 0.005, 0.10, float(p["genetic_drift_strength"]), 0.005)
        p["mutation_sd"] = st.slider("突然変異 SD", 0.01, 0.12, float(p["mutation_sd"]), 0.005)
        p["inbreeding_load"] = st.slider("近交弱勢", 0.0, 0.60, float(p["inbreeding_load"]), 0.01)

        st.markdown("**初期形質 (世代 0 の平均)**")
        p["nectar_guide"] = st.slider("蜜腺標識 (初期)", 0.0, 1.0, float(p["nectar_guide"]), 0.05)
        p["selfing_ability"] = st.slider("自殖能力 (初期)", 0.0, 1.0, float(p["selfing_ability"]), 0.05)

        st.markdown("**シミュレーション設定**")
        generations = st.slider("世代数", 20, 200, 80, 10)
        population_size = st.select_slider("個体数", [40, 80, 120, 160, 240, 320], value=160)
        seed = st.number_input("乱数シード", 0, 9999, 42, 1)

        run_btn = st.button("▶ 実行", type="primary", use_container_width=True)

    with col_result:
        if run_btn or "sim_result" in st.session_state:
            if run_btn:
                with st.spinner("シミュレーション実行中..."):
                    df_traj = run_trajectory(p, generations, population_size, int(seed))
                st.session_state["sim_result"] = df_traj
                st.session_state["sim_preset"] = preset_name
            else:
                df_traj = st.session_state["sim_result"]
                preset_name = st.session_state.get("sim_preset", "")

            if df_traj.empty:
                st.stop()

            # ── 軌跡チャート ─────────────────────────────────────────────
            st.subheader("形質の世代変化")
            traj_traits = st.multiselect(
                "表示する形質",
                [c for c in df_traj.columns if c != "generation"],
                default=["mean_nectar_guide", "selfing_rate", "Fis", "mean_selfing_ability"],
                format_func=lambda x: TRAIT_JP.get(x, x),
            )
            if traj_traits:
                try:
                    import altair as alt
                    melted = df_traj[["generation"] + traj_traits].melt(
                        id_vars="generation", var_name="trait", value_name="value"
                    )
                    melted["形質"] = melted["trait"].map(TRAIT_JP)
                    chart = (
                        alt.Chart(melted)
                        .mark_line(strokeWidth=2)
                        .encode(
                            x=alt.X("generation:Q", title="世代"),
                            y=alt.Y("value:Q", scale=alt.Scale(domain=[0, 1.05]), title="値"),
                            color=alt.Color("形質:N"),
                            tooltip=["generation", "形質", alt.Tooltip("value:Q", format=".3f")],
                        )
                        .properties(height=320)
                        .interactive()
                    )
                    st.altair_chart(chart, use_container_width=True)
                except ImportError:
                    st.line_chart(df_traj.set_index("generation")[traj_traits])

            # ── 最終世代 vs 観察値 ─────────────────────────────────────
            st.subheader("最終世代 vs 観察値")
            final = df_traj.iloc[-1].to_dict()
            obs_key = preset_name if preset_name in OBSERVED else None

            compare_map = {
                "mean_nectar_guide": "nectar_guide",
                "selfing_rate": "selfing_rate",
                "outcrossing_rate": "outcrossing_rate",
                "Fis": "Fis",
            }
            rows = []
            for sim_key, obs_field in compare_map.items():
                sim_val = final.get(sim_key, float("nan"))
                obs_val = OBSERVED.get(obs_key, {}).get(obs_field) if obs_key else None
                rows.append({
                    "形質": TRAIT_JP.get(sim_key, sim_key),
                    "シミュレーション": round(sim_val, 3),
                    "観察値": round(obs_val, 3) if obs_val is not None else "—",
                    "差": round(abs(sim_val - obs_val), 3) if obs_val is not None else "—",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # ── 最終世代の全統計 ──────────────────────────────────────
            with st.expander("最終世代の全統計"):
                final_df = pd.DataFrame([
                    {"統計量": TRAIT_JP.get(k, k), "値": round(v, 4)}
                    for k, v in final.items() if k != "generation"
                ])
                st.dataframe(final_df, use_container_width=True, hide_index=True)

        else:
            st.info("左のパラメータを設定して「▶ 実行」を押してください。")
            st.markdown("""
**このシミュレーターでできること:**
- 本州→大島→神津島→八丈島の4プリセットを試す
- マルハナバチ頻度・蜜腺コスト・浮動強度などを変えて影響を確認
- 世代ごとの形質変化軌跡を可視化
- 最終状態を観察値と比較
""")


# ═══════════════════════════════════════════════════════════════════════════════
# ページ: 観察パターン
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊 観察パターン":
    st.title("伊豆諸島の観察勾配")
    st.markdown("""
本州 → 大島 → 神津島 → 八丈島 と島の隔離度が増すにつれ、
**蜜腺標識 ↓ ・花サイズ ↓ ・自殖能力 ↑ ・Fis ↑** の一貫した勾配が観察される。
""")

    POPULATION_ORDER = ["Mainland (本州)", "Oshima (大島)", "Kozu (神津島)", "Hachijo (八丈島)"]
    TRAIT_LABELS = {
        "nectar_guide": "蜜腺標識",
        "flower_size": "花サイズ",
        "herkogamy": "雌雄異熟",
        "selfing_ability": "自殖能力",
        "bombus_frequency": "マルハナバチ頻度",
        "pollinator_environment": "伝播者環境",
    }

    rows = [{"population": k, **v} for k, v in PRESETS.items()]
    df = pd.DataFrame(rows)
    df["population"] = pd.Categorical(df["population"], categories=POPULATION_ORDER, ordered=True)
    df = df.sort_values("population").reset_index(drop=True)

    traits = st.multiselect(
        "表示する形質",
        list(TRAIT_LABELS.keys()),
        default=["nectar_guide", "selfing_ability", "bombus_frequency", "pollinator_environment"],
        format_func=lambda x: TRAIT_LABELS.get(x, x),
    )

    if traits:
        try:
            import altair as alt
            melted = df[["population"] + traits].melt(id_vars="population", var_name="trait", value_name="value")
            melted["形質"] = melted["trait"].map(TRAIT_LABELS)
            chart = (
                alt.Chart(melted)
                .mark_line(point=True, strokeWidth=2.5)
                .encode(
                    x=alt.X("population:O", sort=POPULATION_ORDER, title="個体群"),
                    y=alt.Y("value:Q", scale=alt.Scale(domain=[0, 1.05]), title="値 [0–1]"),
                    color=alt.Color("形質:N"),
                    tooltip=["population", "形質", alt.Tooltip("value:Q", format=".3f")],
                )
                .properties(height=360)
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)
        except ImportError:
            st.line_chart(df.set_index("population")[traits].rename(columns=TRAIT_LABELS))

    with st.expander("固定パラメータ一覧 (POPULATION_FIXED_PARAMS)"):
        st.dataframe(df.set_index("population"), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ページ: 因果構造比較
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 因果構造比較 (M1–M5)":
    st.title("因果構造 M1–M5 比較")
    st.markdown("""
大島 vs 八丈島のパターン方向を**決定論的プロキシシミュレーション**で予測し、
観察と一致した数をスコアとします（ABMなし・即時実行）。

| モデル | 仮説 |
|--------|------|
| M1 | Bombus が直接、蜜腺標識の利益を高める（直接選択） |
| M2 | 自殖の増加を介した蜜腺標識喪失（媒介効果） |
| M3 | M1 + M2 の複合 |
| M4 | 島の隔離が複数形質を共通原因として駆動 |
| M5 | ドリフト・中立 null モデル |
""")

    try:
        from examples.campanula_izu.causal_structures import campanula_causal_structures
        from examples.campanula_izu.proxy_simulation import simulate_campanula_causal_structure

        structures = campanula_causal_structures()
        OBS = {
            "nectar_guide": "Oshima > Hachijo",
            "selfing_rate": "Oshima < Hachijo",
            "herkogamy": "Oshima > Hachijo",
            "flower_size": "Oshima > Hachijo",
            "Fis": "Oshima < Hachijo",
            "Bombus_frequency": "Oshima > Hachijo",
        }

        summary, detail_rows = [], []
        for s in structures:
            rels, outputs = simulate_campanula_causal_structure(s)
            matches = sum(1 for var, exp in OBS.items() if rels.get(var) == exp)
            summary.append({"モデル": s.name, "スコア": matches, "最大": len(OBS),
                             "割合": f"{matches}/{len(OBS)}", "説明": s.description})
            for var, obs in OBS.items():
                pred = rels.get(var, "—")
                detail_rows.append({"モデル": s.name, "変数": var, "観察": obs,
                                     "予測": pred, "一致": "✅" if pred == obs else "❌"})

        df_s = pd.DataFrame(summary).sort_values("スコア", ascending=False)
        st.subheader("スコアランキング")
        st.dataframe(df_s[["モデル", "割合", "説明"]], use_container_width=True, hide_index=True)

        try:
            import altair as alt
            bar = (
                alt.Chart(df_s)
                .mark_bar()
                .encode(
                    x=alt.X("スコア:Q", scale=alt.Scale(domain=[0, len(OBS)])),
                    y=alt.Y("モデル:O", sort="-x"),
                    color=alt.condition(
                        alt.datum["スコア"] == int(df_s["スコア"].max()),
                        alt.value("#2ecc71"), alt.value("#95a5a6"),
                    ),
                    tooltip=["モデル", "割合", "説明"],
                )
                .properties(height=200)
            )
            st.altair_chart(bar, use_container_width=True)
        except ImportError:
            pass

        with st.expander("予測 vs 観察 詳細"):
            df_d = pd.DataFrame(detail_rows)
            pivot = df_d.pivot(index="変数", columns="モデル", values="一致")
            st.dataframe(pivot, use_container_width=True)

        with st.expander("シミュレーション出力値"):
            val_rows = []
            for s in structures:
                _, outputs = simulate_campanula_causal_structure(s)
                for o in outputs:
                    val_rows.append({
                        "モデル": s.name, "個体群": o.population,
                        "蜜腺標識": round(o.nectar_guide, 3),
                        "自殖率": round(o.selfing_rate, 3),
                        "雌雄異熟": round(o.herkogamy, 3),
                        "Fis": round(o.Fis, 3),
                    })
            st.dataframe(pd.DataFrame(val_rows), use_container_width=True, hide_index=True)

    except ImportError as e:
        st.error(f"インポートエラー: {e}")
        st.code(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ページ: ABC 事後分布
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈 ABC 事後分布":
    st.title("ABC 推定結果ビューア")
    st.markdown("""
`python examples/campanula_izu/run_inference.py` を実行すると
`examples/campanula_izu/outputs/` に CSV が生成されます。
""")

    outputs_dir = _ROOT / "examples" / "campanula_izu" / "outputs"
    csvs = sorted(outputs_dir.glob("*.csv")) if outputs_dir.exists() else []

    if not csvs:
        st.info("outputs/ に CSV がありません。まず `run_inference.py` を実行してください。")
    else:
        chosen = st.selectbox("ファイルを選択", [f.name for f in csvs])
        df = pd.read_csv(outputs_dir / chosen)
        st.metric("採択サンプル数", f"{len(df):,}")

        param_cols = [c for c in df.select_dtypes("number").columns
                      if c not in ("acceptance_rate", "n_attempted", "epsilon")]
        selected = st.multiselect("パラメータを選択", param_cols,
                                   default=param_cols[:min(6, len(param_cols))])
        if selected:
            try:
                import altair as alt
                melted = df[selected].melt(var_name="パラメータ", value_name="値")
                hist = (
                    alt.Chart(melted)
                    .mark_bar(opacity=0.75)
                    .encode(
                        x=alt.X("値:Q", bin=alt.Bin(maxbins=30)),
                        y=alt.Y("count():Q"),
                        color="パラメータ:N",
                        facet=alt.Facet("パラメータ:N", columns=3),
                    )
                    .properties(width=260, height=160)
                    .resolve_scale(x="independent", y="independent")
                )
                st.altair_chart(hist)
            except ImportError:
                st.dataframe(df[selected].describe(), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ページ: TenSnap
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🌿 TenSnap 可視化":
    st.title("エージェントレベル可視化 — TenSnap")
    st.info(
        "**起動手順:**\n\n"
        "1. ローカルで ABM サーバーを起動:\n"
        "   ```\n   python abm/shimahotarubukuro_tensnap_abm.py\n   ```\n"
        "2. 下のボタンから TenSnap レンダラーを開く (`ws://localhost:8765` に接続)。",
        icon="🌿",
    )
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("TenSnap レンダラーを開く →", "https://tensnap.netlify.app/", use_container_width=True)
    with col2:
        st.link_button("ABM ソースを見る →",
                        "https://github.com/zuizui0223/microdonta/blob/main/abm/shimahotarubukuro_tensnap_abm.py",
                        use_container_width=True)

    st.markdown("""
| プリセット | マルハナバチ頻度 | 個体数 | 特徴 |
|-----------|----------------|-------|------|
| Mainland  | 1.0            | 160   | Bombus 支配、高外交配 |
| Oshima    | 0.35           | 140   | 混合送粉者 |
| Kozu      | 0.0            | 100   | Bombus 不在 |
| Hachijo   | 0.0            | 80    | 最高自殖率 |
""")
