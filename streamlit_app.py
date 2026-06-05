from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Microdonta nectar-guide ABM",
    page_icon="🌿",
    layout="wide",
)


FIELD_COLUMNS = [
    "population",
    "nectar_guide",
    "bombus_frequency",
    "small_bee_frequency",
    "selfing_ability",
    "inbreeding_load",
    "seed_set_selfing",
    "seed_set_outcrossing",
    "germination_selfed",
    "germination_outcrossed",
    "migration_rate",
    "Fis_observed",
    "Fst_observed",
]


DEFAULT_FIELD_DATA = pd.DataFrame(
    [
        ["Mainland", 0.62, 0.72, 0.18, 0.22, 0.32, 0.46, 0.92, 0.54, 0.86, 0.100, np.nan, np.nan],
        ["Oshima", 0.55, 0.45, 0.38, 0.36, 0.25, 0.55, 0.84, 0.60, 0.82, 0.050, np.nan, np.nan],
        ["Kozu", 0.42, 0.00, 0.58, 0.52, 0.18, 0.64, 0.76, 0.66, 0.78, 0.025, np.nan, np.nan],
        ["Hachijo", 0.28, 0.00, 0.74, 0.68, 0.12, 0.72, 0.68, 0.70, 0.74, 0.010, np.nan, np.nan],
    ],
    columns=FIELD_COLUMNS,
)


LITERATURE = [
    {
        "title": "Inoue & Amano 1986, Plant Species Biology",
        "url": "https://cir.nii.ac.jp/crid/2051714791885953664",
        "point": (
            "Campanula punctata in Honshu, Oshima, and other Izu islands differs in "
            "pollinator fauna and breeding system. Honshu is mainly Bombus-pollinated "
            "and highly self-incompatible; Hachijo plants are self-compatible and "
            "potentially autogamous."
        ),
    },
    {
        "title": "Inoue 1989, Bumblebee-Absence Hypothesis",
        "url": "https://cir.nii.ac.jp/crid/2051714791885965312",
        "point": (
            "Bagging experiments across mainland Honshu and six Izu islands support "
            "the hypothesis that bumblebee absence outside Oshima reduces pollination "
            "efficiency and drives breeding-system evolution in Campanula."
        ),
    },
    {
        "title": "Nagano et al. 2014, Ecology and Evolution",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4228614/",
        "point": (
            "Local bumblebee assemblages are associated with floral-size variation in "
            "C. punctata var. hondoensis, supporting pollinator-mediated selection on "
            "floral traits."
        ),
    },
    {
        "title": "Leonard & Papaj 2011, Functional Ecology",
        "url": "https://doi.org/10.1111/j.1365-2435.2011.01885.x",
        "point": (
            "Nectar guides can alter bee search and handling behaviour, giving a "
            "mechanistic basis for maintaining guide patterns when effective "
            "pollinators remain."
        ),
    },
    {
        "title": "Goodwillie et al. 2010, floral signposts",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3248739/",
        "point": (
            "Experimental work on visual floral guides connects pollinator orientation "
            "with components of plant fitness."
        ),
    },
    {
        "title": "Wright et al. 2013, evolutionary consequences of selfing",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3652455/",
        "point": (
            "Selfing can provide reproductive assurance when pollinators or mates are "
            "rare, but it changes genetic diversity, gene flow, and inbreeding load."
        ),
    },
    {
        "title": "Barrett 1996, island plant reproduction and genetics",
        "url": "https://barrett.eeb.utoronto.ca/publications/files/2020/06/schb_134.pdf",
        "point": (
            "Island populations often differ from mainland populations in reproductive "
            "biology and genetics; pollinator limitation, drift, and gene flow are all "
            "central."
        ),
    },
]


@dataclass
class Plant:
    guide: float
    diversity: float
    mode: str = "outcrossing"
    seed_output: float = 1.0
    germination: float = 1.0
    fitness: float = 1.0


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    if math.isnan(float(value)):
        return low
    return max(low, min(high, float(value)))


def load_field_data() -> pd.DataFrame:
    uploaded = st.sidebar.file_uploader("実データ CSV をアップロード", type=["csv"])
    if uploaded is None:
        return DEFAULT_FIELD_DATA.copy()
    data = pd.read_csv(uploaded)
    for column in FIELD_COLUMNS:
        if column not in data.columns:
            data[column] = np.nan if column != "population" else ""
    return data[FIELD_COLUMNS].copy()


def evaluate_population(population: list[Plant], params: dict[str, float], rng: np.random.Generator) -> None:
    for plant in population:
        outcross_prob = clamp(
            params["base_outcross"]
            + params["small_bee_frequency"] * params["pollinator_efficiency_small_bee"]
            + params["bombus_frequency"] * params["pollinator_efficiency_bombus"] * plant.guide
        )
        outcrossing = rng.random() < outcross_prob
        selfing = (not outcrossing) and (rng.random() < params["selfing_ability"])
        plant.mode = "outcrossing" if outcrossing else "selfing" if selfing else "failed"

        if outcrossing:
            plant.seed_output = params["seed_set_outcrossing"]
            plant.germination = params["germination_outcrossed"]
            inbreeding_penalty = 0.0
        elif selfing:
            plant.seed_output = params["seed_set_selfing"]
            plant.germination = params["germination_selfed"]
            inbreeding_penalty = params["inbreeding_load"]
        else:
            plant.seed_output = 0.02
            plant.germination = 0.02
            inbreeding_penalty = 0.0

        plant.fitness = max(
            0.001,
            plant.seed_output * plant.germination * (1.0 - inbreeding_penalty)
            - params["guide_cost"] * plant.guide,
        )


def record_generation(generation: int, population: list[Plant], params: dict[str, float]) -> dict[str, float]:
    guides = np.array([plant.guide for plant in population])
    fitness = np.array([plant.fitness for plant in population])
    diversity = np.array([plant.diversity for plant in population])
    selfing_rate = np.mean([plant.mode == "selfing" for plant in population])
    outcrossing_rate = np.mean([plant.mode == "outcrossing" for plant in population])
    failed_rate = np.mean([plant.mode == "failed" for plant in population])
    fis = clamp(selfing_rate * (1.0 - 0.5 * params["migration_rate"]))
    fst = clamp((1.0 - params["migration_rate"]) * (1.0 - outcrossing_rate) * (1.0 - np.mean(diversity)))
    return {
        "generation": generation,
        "mean_nectar_guide": float(np.mean(guides)),
        "guide_threshold_0_5": 0.5,
        "selfing_rate": float(selfing_rate),
        "outcrossing_rate": float(outcrossing_rate),
        "failed_rate": float(failed_rate),
        "mean_fitness": float(np.mean(fitness)),
        "seed_output": float(np.mean([plant.seed_output for plant in population])),
        "germination": float(np.mean([plant.germination for plant in population])),
        "mean_neutral_diversity": float(np.mean(diversity)),
        "Fis": fis,
        "Fst": fst,
    }


def run_abm(params: dict[str, float], generations: int, population_size: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    guide_start = clamp(params["nectar_guide"])
    population = [
        Plant(
            guide=clamp(rng.normal(guide_start, 0.12)),
            diversity=clamp(rng.normal(0.78, 0.08)),
        )
        for _ in range(population_size)
    ]

    history = []
    evaluate_population(population, params, rng)
    history.append(record_generation(0, population, params))

    for generation in range(1, generations + 1):
        total_fitness = sum(plant.fitness for plant in population)
        weights = np.array([plant.fitness / total_fitness for plant in population])
        parents = rng.choice(population, size=population_size, replace=True, p=weights)
        next_population = []
        for parent in parents:
            guide = clamp(parent.guide + rng.normal(0.0, params["mutation_sd"]))
            if parent.mode == "outcrossing":
                diversity = parent.diversity + 0.045
            elif parent.mode == "selfing":
                diversity = parent.diversity * (1.0 - 0.5 * params["inbreeding_load"])
            else:
                diversity = parent.diversity * 0.96
            diversity += params["migration_rate"] * (0.82 - diversity)
            diversity += rng.normal(0.0, params["genetic_drift_strength"])
            next_population.append(Plant(guide=guide, diversity=clamp(diversity)))
        population = next_population
        evaluate_population(population, params, rng)
        history.append(record_generation(generation, population, params))

    return pd.DataFrame(history)


def field_row_to_params(row: pd.Series) -> dict[str, float]:
    return {
        "nectar_guide": clamp(row["nectar_guide"]),
        "bombus_frequency": clamp(row["bombus_frequency"]),
        "small_bee_frequency": clamp(row["small_bee_frequency"]),
        "selfing_ability": clamp(row["selfing_ability"]),
        "inbreeding_load": clamp(row["inbreeding_load"]),
        "seed_set_selfing": clamp(row["seed_set_selfing"]),
        "seed_set_outcrossing": clamp(row["seed_set_outcrossing"]),
        "germination_selfed": clamp(row["germination_selfed"]),
        "germination_outcrossed": clamp(row["germination_outcrossed"]),
        "migration_rate": clamp(row["migration_rate"], 0.0, 0.25),
        "guide_cost": 0.06,
        "base_outcross": 0.10,
        "pollinator_efficiency_small_bee": 0.22,
        "pollinator_efficiency_bombus": 0.78,
        "mutation_sd": 0.055,
        "genetic_drift_strength": 0.035,
    }


st.title("シマホタルブクロ ネクターガイド進化 ABM")
st.caption("実データをあとから穴埋めしながら、大島以外のマルハナバチ不在・自殖保証・近交弱勢・遺伝的多様性の仮説を検討する Streamlit アプリ")

with st.expander("仮説", expanded=True):
    st.markdown(
        """
        **通常状態、本土**: マルハナバチあり → 他殖が成立 → ネクターガイド維持 → 遺伝的多様性維持

        **島状態、大島**: `Bombus ardens` とコハナバチ類あり → 他殖機会は本土より変化するがゼロではない → ネクターガイド維持の余地が残る

        **島状態、大島以外**: マルハナバチ不在・コハナバチ類優占 → 他殖機会が不安定化 → 繁殖保証として自殖が重要になる → でも自殖は近交弱勢を生む → 完全自殖には移行できない → 他殖チャンスを残す個体ではネクターガイドが維持される → 他殖チャンスがほぼない場所ではネクターガイドが退化する
        """
    )

field_data = load_field_data()

st.sidebar.header("Simulation")
population_choice = st.sidebar.selectbox("Population preset", field_data["population"].astype(str).tolist())
generations = st.sidebar.slider("Generations", 10, 300, 80, 10)
population_size = st.sidebar.slider("Population size", 50, 600, 180, 10)
seed = st.sidebar.number_input("Random seed", value=20260605, step=1)

data_tab, sim_tab, evidence_tab, fieldwork_tab = st.tabs(
    ["Data template", "ABM results", "Literature", "Fieldwork plan"]
)

with data_tab:
    st.subheader("野外データ穴埋めテンプレート")
    edited_data = st.data_editor(
        field_data,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "population": st.column_config.TextColumn("population"),
            "nectar_guide": st.column_config.NumberColumn("斑点面積率", min_value=0.0, max_value=1.0),
            "bombus_frequency": st.column_config.NumberColumn("マルハナバチ訪花回数/時間", min_value=0.0, max_value=1.0),
            "small_bee_frequency": st.column_config.NumberColumn("小型ハナバチ訪花回数/時間", min_value=0.0, max_value=1.0),
            "selfing_ability": st.column_config.NumberColumn("袋掛け結実率", min_value=0.0, max_value=1.0),
            "inbreeding_load": st.column_config.NumberColumn("自殖種子と自然種子の発芽率差", min_value=0.0, max_value=1.0),
            "Fis_observed": st.column_config.NumberColumn("Fis observed"),
            "Fst_observed": st.column_config.NumberColumn("Fst observed"),
        },
    )
    st.download_button(
        "Download filled template CSV",
        edited_data.to_csv(index=False).encode("utf-8"),
        file_name="microdonta_field_data_template.csv",
        mime="text/csv",
    )

working_data = edited_data.copy()
matched_rows = working_data[working_data["population"].astype(str) == population_choice]
selected_row = matched_rows.iloc[0] if not matched_rows.empty else working_data.iloc[0]
base_params = field_row_to_params(selected_row)

with st.sidebar.expander("Manual parameter overrides", expanded=False):
    for key in [
        "bombus_frequency",
        "small_bee_frequency",
        "selfing_ability",
        "inbreeding_load",
        "guide_cost",
        "migration_rate",
    ]:
        upper = 0.5 if key == "guide_cost" else 0.25 if key == "migration_rate" else 1.0
        base_params[key] = st.slider(key, 0.0, upper, float(base_params[key]), 0.01)

with sim_tab:
    results = run_abm(base_params, generations, population_size, int(seed))
    latest = results.iloc[-1]
    cols = st.columns(5)
    cols[0].metric("mean_nectar_guide", f"{latest['mean_nectar_guide']:.3f}")
    cols[1].metric("selfing_rate", f"{latest['selfing_rate']:.3f}")
    cols[2].metric("outcrossing_rate", f"{latest['outcrossing_rate']:.3f}")
    cols[3].metric("Fis", f"{latest['Fis']:.3f}")
    cols[4].metric("Fst", f"{latest['Fst']:.3f}")

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.line_chart(results.set_index("generation")[["mean_nectar_guide", "guide_threshold_0_5"]])
        st.line_chart(results.set_index("generation")[["selfing_rate", "outcrossing_rate", "failed_rate"]])
    with chart_right:
        st.line_chart(results.set_index("generation")[["mean_fitness", "seed_output", "germination"]])
        st.line_chart(results.set_index("generation")[["mean_neutral_diversity", "Fis", "Fst"]])

    st.download_button(
        "Download ABM results CSV",
        results.to_csv(index=False).encode("utf-8"),
        file_name=f"microdonta_abm_{population_choice}.csv",
        mime="text/csv",
    )
    st.dataframe(results.tail(12), use_container_width=True)

with evidence_tab:
    st.subheader("生態学的根拠")
    for item in LITERATURE:
        st.markdown(f"**[{item['title']}]({item['url']})**")
        st.write(item["point"])

    st.subheader("ABM 変数と野外データ")
    st.dataframe(
        pd.DataFrame(
            [
                ["nectar_guide", "斑点面積率", "個体の guide trait と mean_nectar_guide"],
                ["bombus_frequency", "マルハナバチ訪花回数/時間", "他殖確率の主要項"],
                ["small_bee_frequency", "小型ハナバチ訪花回数/時間", "補助的な他殖機会"],
                ["selfing_ability", "袋掛け結実率", "他殖失敗時の自殖成功確率"],
                ["inbreeding_load", "自殖種子と自然種子の発芽率差", "自殖 fitness penalty"],
                ["fitness", "種子数・発芽率", "次世代親の重み"],
                ["Fis", "SNP", "自殖率・移住率からの近交指標"],
                ["Fst", "SNP", "多様性低下・移住率・他殖低下からの分化指標"],
            ],
            columns=["ABM variable", "field data", "model role"],
        ),
        use_container_width=True,
    )

with fieldwork_tab:
    st.subheader("野外で取るデータ")
    st.dataframe(
        pd.DataFrame(
            [
                ["斑点面積率", "nectar_guide", "各集団 30-50 個体、各個体 3-5 花", "目的形質。退化/維持の直接測定"],
                ["訪花者の種類と訪花回数/時間", "bombus_frequency, small_bee_frequency", "各集団 20-30 時間以上", "送粉者相と他殖機会"],
                ["自然結実率・種子数", "fitness baseline", "各集団 30-50 花以上", "自然条件での適応度"],
                ["袋掛け結実率", "selfing_ability", "各集団 30-50 花以上", "送粉者なしの繁殖保証"],
                ["人工自殖/人工他殖の種子数", "seed_set_selfing, seed_set_outcrossing", "各集団 20-30 母株、各処理 1-3 花", "繁殖様式ごとの種子生産"],
                ["自殖/他殖種子の発芽率", "germination_selfed, germination_outcrossed, inbreeding_load", "各集団 20-30 母株", "近交弱勢"],
                ["SNP", "Fis, Fst", "各集団 20-30 個体以上", "近交・集団分化・多様性"],
            ],
            columns=["データ", "ABM変数", "最低サンプル感", "目的"],
        ),
        use_container_width=True,
    )
    st.markdown(
        """
        **最小セット**: 各地域 1 集団、各集団 30 個体、訪花観察 20 時間。仮説の方向を見る。

        **検定向け**: 各地域 2-3 集団、各集団 40-60 個体、訪花観察 30-50 時間、交配実験 30 母株程度。

        **ABM パラメータ推定向け**: 各地域 3 集団以上、各集団 60 個体前後、訪花観察 50 時間以上、人工自殖/他殖/袋掛け/自然結実を同一個体群で揃え、SNP は各集団 30 個体以上。

        優先順位は、1. 訪花者組成、2. 袋掛け結実率、3. 自殖/他殖の発芽率差、4. 斑点面積率、5. SNP。
        """
    )
