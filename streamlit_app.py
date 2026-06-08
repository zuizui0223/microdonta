"""CAPOM — シマホタルブクロ伊豆諸島 インタラクティブビューア.

実行方法 (リポジトリルートから):
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import sys
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="シマホタルブクロ CAPOM",
    layout="wide",
    page_icon="🌿",
)

st.title("🌿 シマホタルブクロ — CAPOM 推定ビューア")
st.caption(
    "Campanula punctata var. hondoensis / microdonta: "
    "伊豆諸島における蜜腺標識喪失の生成的逆推定フレームワーク"
)

page = st.sidebar.radio(
    "ページ",
    ["観察パターン", "因果構造比較 (M1–M5)", "ABC 事後分布", "TenSnap 可視化"],
)

POPULATION_ORDER = ["Mainland", "Oshima", "Kozu", "Hachijo"]

TRAIT_LABELS: dict[str, str] = {
    "nectar_guide": "蜜腺標識",
    "flower_size": "花サイズ",
    "herkogamy": "雌雄異熟",
    "selfing_ability": "自殖能力",
    "bombus_frequency": "マルハナバチ頻度",
    "pollinator_environment": "伝播者環境",
    "migration_rate": "移住率",
    "admixture_index": "混血指数",
}


@st.cache_data
def load_population_data() -> pd.DataFrame:
    from examples.campanula_izu.observed_patterns import POPULATION_FIXED_PARAMS

    rows = [{"population": pop, **params} for pop, params in POPULATION_FIXED_PARAMS.items()]
    df = pd.DataFrame(rows)
    df["population"] = pd.Categorical(df["population"], categories=POPULATION_ORDER, ordered=True)
    return df.sort_values("population").reset_index(drop=True)


@st.cache_data
def run_causal_comparison() -> tuple[pd.DataFrame, pd.DataFrame]:
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

    summary_rows = []
    detail_rows = []

    for s in structures:
        rels, _ = simulate_campanula_causal_structure(s)
        matches = sum(1 for var, exp in OBS.items() if rels.get(var) == exp)
        summary_rows.append(
            {
                "モデル": s.name,
                "スコア": matches,
                "最大": len(OBS),
                "割合": f"{matches}/{len(OBS)}",
                "説明": s.description,
            }
        )
        for var, obs in OBS.items():
            pred = rels.get(var, "—")
            detail_rows.append(
                {
                    "モデル": s.name,
                    "変数": var,
                    "観察": obs,
                    "予測": pred,
                    "一致": "✅" if pred == obs else "❌",
                }
            )

    df_s = pd.DataFrame(summary_rows).sort_values("スコア", ascending=False)
    df_d = pd.DataFrame(detail_rows)
    return df_s, df_d


# ── 観察パターン ──────────────────────────────────────────────────────────────
if page == "観察パターン":
    st.header("伊豆諸島の観察勾配")
    st.markdown(
        """
本州 (Mainland) → 大島 (Oshima) → 神津島 (Kozu) → 八丈島 (Hachijo) と
島の隔離度・孤立度が増すにつれて、以下の一貫した勾配が観察されます:

- **蜜腺標識 ↓**、**花サイズ ↓**、**雌雄異熟 ↓**（送粉者誘引形質の喪失）
- **自殖能力 ↑**、**Fis ↑**（自殖系への移行）
- **マルハナバチ頻度 ↓**（大型送粉者の消失）
"""
    )

    try:
        df = load_population_data()
    except ImportError as e:
        st.error(f"インポートエラー: {e}")
        st.stop()

    traits = st.multiselect(
        "表示する形質",
        options=list(TRAIT_LABELS.keys()),
        default=["nectar_guide", "selfing_ability", "bombus_frequency", "pollinator_environment"],
        format_func=lambda x: TRAIT_LABELS.get(x, x),
    )

    if traits:
        try:
            import altair as alt

            melted = df[["population"] + traits].melt(
                id_vars="population", var_name="trait", value_name="value"
            )
            melted["形質"] = melted["trait"].map(TRAIT_LABELS)

            chart = (
                alt.Chart(melted)
                .mark_line(point=True, strokeWidth=2.5)
                .encode(
                    x=alt.X("population:O", sort=POPULATION_ORDER, title="個体群"),
                    y=alt.Y("value:Q", scale=alt.Scale(domain=[0, 1.05]), title="値 [0–1]"),
                    color=alt.Color("形質:N"),
                    tooltip=[
                        "population",
                        "形質",
                        alt.Tooltip("value:Q", format=".3f"),
                    ],
                )
                .properties(height=380)
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)
        except ImportError:
            st.line_chart(
                df.set_index("population")[traits].rename(columns=TRAIT_LABELS)
            )

    with st.expander("生データ (POPULATION_FIXED_PARAMS)"):
        cols = ["population"] + [c for c in df.columns if c != "population"]
        st.dataframe(df[cols].set_index("population"), use_container_width=True)

    st.divider()
    st.subheader("個体群ごとの観察パターン (CAPOM 入力)")
    st.markdown("各個体群の観察値と ABC 受理の許容範囲 (tolerance):")

    try:
        from examples.campanula_izu.observed_patterns import POPULATION_OBSERVED

        for pop in POPULATION_ORDER:
            if pop not in POPULATION_OBSERVED:
                continue
            with st.expander(pop):
                rows = [
                    {
                        "パターン名": p.name,
                        "種別": p.kind,
                        "目標値": p.target,
                        "許容範囲": p.tolerance,
                        "重み": p.weight,
                    }
                    for p in POPULATION_OBSERVED[pop]
                ]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"観察パターン読み込みエラー: {e}")


# ── 因果構造比較 ───────────────────────────────────────────────────────────────
elif page == "因果構造比較 (M1–M5)":
    st.header("因果構造 M1–M5: Stage 3 比較")
    st.markdown(
        """
**大島 vs 八丈島** のパターン方向（どちらが大きいか）を
決定論的プロキシシミュレーションで予測し、観察と一致した数をスコアとします。

| モデル | 仮説 |
|--------|------|
| M1 | Bombus が直接、蜜腺標識の利益を高める（直接選択） |
| M2 | 自殖の増加を介した蜜腺標識喪失（媒介効果） |
| M3 | M1 + M2 の複合 |
| M4 | 島の隔離が複数形質を共通原因として駆動 |
| M5 | ドリフト・中立 null モデル |
"""
    )

    try:
        df_summary, df_detail = run_causal_comparison()

        st.subheader("スコアランキング")
        st.dataframe(
            df_summary[["モデル", "割合", "説明"]],
            use_container_width=True,
            hide_index=True,
        )

        try:
            import altair as alt

            bar = (
                alt.Chart(df_summary)
                .mark_bar()
                .encode(
                    x=alt.X("スコア:Q", scale=alt.Scale(domain=[0, df_summary["最大"].max()])),
                    y=alt.Y("モデル:O", sort="-x"),
                    color=alt.condition(
                        alt.datum["スコア"] == df_summary["スコア"].max(),
                        alt.value("#2ecc71"),
                        alt.value("#95a5a6"),
                    ),
                    tooltip=["モデル", "割合", "説明"],
                )
                .properties(height=220)
            )
            st.altair_chart(bar, use_container_width=True)
        except ImportError:
            pass

        with st.expander("予測 vs 観察 詳細"):
            pivot = df_detail.pivot(index="変数", columns="モデル", values="一致")
            st.dataframe(pivot, use_container_width=True)
            st.dataframe(df_detail, use_container_width=True, hide_index=True)

    except ImportError as e:
        st.error(f"インポートエラー: {e}")
        st.info(
            "`examples/campanula_izu/proxy_simulation.py` が必要です。"
            "リポジトリが最新の状態かご確認ください。"
        )
    except Exception as e:
        st.error(f"シミュレーションエラー: {e}")
        import traceback
        st.code(traceback.format_exc())


# ── ABC 事後分布 ───────────────────────────────────────────────────────────────
elif page == "ABC 事後分布":
    st.header("ABC 推定結果")
    st.markdown(
        """
`python examples/campanula_izu/run_inference.py` を実行すると
`examples/campanula_izu/outputs/` にCSVが生成されます。
ここではその事後サンプルを可視化します。
"""
    )

    outputs_dir = _ROOT / "examples" / "campanula_izu" / "outputs"
    csvs = sorted(outputs_dir.glob("*.csv")) if outputs_dir.exists() else []

    if not csvs:
        st.info(
            "outputs/ にCSVがありません。\n\n"
            "```\npython examples/campanula_izu/run_inference.py\n```\n\nを実行してください。"
        )
    else:
        chosen = st.selectbox("ファイルを選択", [f.name for f in csvs])
        df = pd.read_csv(outputs_dir / chosen)

        col1, col2, col3 = st.columns(3)
        col1.metric("採択サンプル数", f"{len(df):,}")
        if "acceptance_rate" in df.columns:
            col2.metric("受理率", f"{df['acceptance_rate'].iloc[0]:.3%}")

        numeric_cols = df.select_dtypes("number").columns.tolist()
        # exclude metadata columns
        param_cols = [c for c in numeric_cols if c not in ("acceptance_rate", "n_attempted", "epsilon")]
        selected = st.multiselect("パラメータを選択", param_cols, default=param_cols[:min(6, len(param_cols))])

        if selected:
            try:
                import altair as alt

                melted = df[selected].melt(var_name="パラメータ", value_name="値")
                hist = (
                    alt.Chart(melted)
                    .mark_bar(opacity=0.75)
                    .encode(
                        x=alt.X("値:Q", bin=alt.Bin(maxbins=30)),
                        y=alt.Y("count():Q", title="頻度"),
                        color="パラメータ:N",
                        facet=alt.Facet("パラメータ:N", columns=3),
                    )
                    .properties(width=260, height=180)
                    .resolve_scale(x="independent", y="independent")
                )
                st.altair_chart(hist)
            except ImportError:
                st.dataframe(df[selected].describe(), use_container_width=True)

            with st.expander("統計量"):
                st.dataframe(df[selected].describe().round(4), use_container_width=True)


# ── TenSnap 可視化 ─────────────────────────────────────────────────────────────
elif page == "TenSnap 可視化":
    st.header("エージェントレベル可視化 — TenSnap")

    st.info(
        "**TenSnap** は WebSocket ベースのリアルタイム ABM 可視化ツールです。\n\n"
        "**起動手順:**\n"
        "1. ローカルで ABM サーバーを起動:\n"
        "   ```\n"
        "   python abm/shimahotarubukuro_tensnap_abm.py\n"
        "   ```\n"
        "2. 下のボタンから TenSnap レンダラーを開く (`ws://localhost:8765` に自動接続)。",
        icon="🌿",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.link_button(
            "TenSnap レンダラーを開く →",
            "https://tensnap.netlify.app/",
            use_container_width=True,
        )
    with col2:
        st.link_button(
            "ABM ソースを見る →",
            "https://github.com/zuizui0223/microdonta/blob/main/abm/shimahotarubukuro_tensnap_abm.py",
            use_container_width=True,
        )

    st.divider()
    st.subheader("ABM プリセット環境")
    st.markdown(
        """
`shimahotarubukuro_tensnap_abm.py` に定義された4つのプリセット:

| プリセット | マルハナバチ頻度 | 小型蜂頻度 | 個体群サイズ | 特徴 |
|-----------|----------------|-----------|------------|------|
| Mainland  | 1.0            | 0.3       | 160        | Bombus 支配、高外交配 |
| Oshima    | 0.35           | 0.55      | 140        | 混合送粉者環境 |
| Kozu      | 0.0            | 0.65      | 100        | Bombus 不在、小型蜂依存 |
| Hachijo   | 0.0            | 0.72      | 80         | 最高自殖率、最低蜜腺標識 |
"""
    )

    st.subheader("出力の見方")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
**エージェントの色:**
- 🟡 黄色 = 蜜腺標識が高い (nectar_guide ≈ 1)
- 🟣 紫色 = 蜜腺標識が低い (nectar_guide ≈ 0)
"""
        )
    with col_b:
        st.markdown(
            """
**ライブチャート:**
- 自殖率 (selfing rate)
- 近交係数 Fis
- 個体群分化指数 Fst
"""
        )
