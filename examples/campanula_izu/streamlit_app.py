"""Campanula izu: CAPOM interactive explorer (Streamlit).

Run locally:
    streamlit run examples/campanula_izu/streamlit_app.py

Agent-level visualization uses TenSnap (WebSocket renderer).
Start the TenSnap server separately:
    python abm/shimahotarubukuro_tensnap_abm.py
Then open https://tensnap.netlify.app/ in your browser.
"""

import streamlit as st

st.set_page_config(page_title="シマホタルブクロ CAPOM", layout="wide")
st.title("シマホタルブクロ — CAPOM 推定ビューア")

# ── TenSnap agent visualization ──────────────────────────────────────────────
st.header("エージェント可視化 (TenSnap)")
st.info(
    "エージェントのリアルタイム可視化は **TenSnap** で行います。\n\n"
    "1. ローカルで ABM サーバーを起動:\n"
    "   ```\n   python abm/shimahotarubukuro_tensnap_abm.py\n   ```\n"
    "2. 下のボタンからレンダラーを開く。",
    icon="🌿",
)
st.link_button(
    "TenSnap レンダラーを開く →",
    "https://tensnap.netlify.app/",
    use_container_width=True,
)

st.divider()

# ── Pattern comparison ────────────────────────────────────────────────────────
st.header("観察パターン比較")
try:
    from examples.campanula_izu.observed_patterns import POPULATION_OBSERVED, POPULATION_FIXED_PARAMS

    for pop_name, patterns in POPULATION_OBSERVED.items():
        with st.expander(pop_name):
            fixed = POPULATION_FIXED_PARAMS.get(pop_name, {})
            st.json(fixed)
            for p in patterns:
                st.write(f"- **{p.name}** ({p.variable}): {p.expected_relation}")
except ImportError:
    st.warning("observed_patterns モジュールが見つかりません。リポジトリルートから起動してください。")

st.divider()

# ── Inference results ─────────────────────────────────────────────────────────
st.header("ABC 推定結果")
import pathlib, pandas as pd

outputs_dir = pathlib.Path("examples/campanula_izu/outputs")
csvs = sorted(outputs_dir.glob("*.csv")) if outputs_dir.exists() else []
if csvs:
    chosen = st.selectbox("CSVを選択", [f.name for f in csvs])
    df = pd.read_csv(outputs_dir / chosen)
    st.dataframe(df, use_container_width=True)
else:
    st.info("outputs/ に CSV がありません。run_inference.py を実行してください。")