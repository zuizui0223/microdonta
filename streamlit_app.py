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
    "flower_size",
    "herkogamy",
    "pollen_ovule_ratio",
    "pollinator_environment",
    "bombus_present",
    "bombus_frequency",
    "bombus_pollination_efficiency",
    "other_pollinator_efficiency",
    "bombus_guide_dependence",
    "other_pollinator_guide_use",
    "selfing_ability",
    "inbreeding_load",
    "seed_set_selfing",
    "seed_set_outcrossing",
    "germination_selfed",
    "germination_outcrossed",
    "migration_rate",
    "Fis_observed",
    "Fst_observed",
    "Pst_nectar_guide",
    "Pst_flower_size",
    "admixture_index",
    "colonization_history",
]


DEFAULT_FIELD_DATA = pd.DataFrame(
    [
        ["Mainland", 0.62, 0.82, 0.78, 0.78, 0.78, 1.0, 0.78, 0.86, 0.34, 0.75, 0.12, 0.22, 0.32, 0.46, 0.92, 0.54, 0.86, 0.100, np.nan, np.nan, np.nan, np.nan, 0.00, "source/mainland"],
        ["Oshima", 0.55, 0.72, 0.62, 0.64, 0.58, 1.0, 0.35, 0.78, 0.34, 0.65, 0.16, 0.36, 0.25, 0.55, 0.84, 0.57, 0.82, 0.050, np.nan, np.nan, np.nan, np.nan, 0.20, "island with Bombus ardens"],
        ["Kozu", 0.42, 0.58, 0.44, 0.48, 0.42, 0.0, 0.00, 0.86, 0.30, 0.00, 0.18, 0.52, 0.18, 0.64, 0.76, 0.60, 0.78, 0.025, np.nan, np.nan, np.nan, np.nan, 0.35, "bumblebee-free island"],
        ["Hachijo", 0.28, 0.46, 0.30, 0.34, 0.36, 0.0, 0.00, 0.86, 0.30, 0.00, 0.18, 0.68, 0.12, 0.72, 0.68, 0.62, 0.74, 0.010, np.nan, np.nan, np.nan, np.nan, 0.45, "bumblebee-free island"],
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
        "title": "Lunau et al. 2006, Naturwissenschaften",
        "url": "https://doi.org/10.1007/s00114-006-0105-2",
        "point": (
            "Flower-naive Bombus terrestris visually target components of floral colour "
            "patterns, supporting the assumption that bumblebees can use guide-like "
            "patterns during close-range orientation."
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
        "title": "Sicard & Lenhard 2011, the selfing syndrome",
        "url": "https://doi.org/10.1093/aob/mcr023",
        "point": (
            "Selfing syndrome evolution commonly involves reduced floral display, "
            "changes in anther-stigma distance, and altered allocation to male versus "
            "female function. The app therefore tracks flower_size, herkogamy, and "
            "pollen_ovule_ratio as field-fillable syndrome traits."
        ),
    },
    {
        "title": "Shimizu & Tsuchimatsu 2022, selfing syndrome and beyond",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9149797/",
        "point": (
            "Transitions to selfing often reduce traits involved in pollinator attraction "
            "and promote reproductive traits enabling autonomous selfing. This supports "
            "treating nectar-guide decline as part of a broader syndrome, not as a lone trait."
        ),
    },
    {
        "title": "Pannell et al. 2015, Baker's law revisited",
        "url": "https://academic.oup.com/evolut/article-pdf/52/3/657/47938066/evolut0657.pdf",
        "point": (
            "Baker's law links self-compatibility and uniparental reproduction to "
            "successful colonization after long-distance dispersal, matching the island "
            "syndrome part of the scenario."
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


FIELD_CHECKLIST = [
    ["準備", "調査集団を決める", "本土・大島・神津島・八丈島など。大島はマルハナバチありの島として別扱いする。"],
    ["準備", "個体IDを振る", "各集団 30-60 個体。可能なら同じ個体で形質・交配・SNPを結びつける。"],
    ["準備", "花IDを振る", "個体内で 3-5 花を目安。処理花と観察花を分ける。"],
    ["準備", "天候・時刻・気温・風を記録する", "訪花頻度の補正に使う。"],
    ["斑点計測", "花冠内面を撮影する", "スケールを入れ、花の向き・距離を揃える。"],
    ["斑点計測", "斑点面積率を測る", "nectar_guide。画像解析で斑点面積/花冠対象面積。"],
    ["斑点計測", "花サイズも測る", "花冠長、花冠幅、開口部径。送粉者サイズとの対応を見る。"],
    ["訪花観察", "訪花者を分類する", "マルハナバチ、コハナバチ類、その他に最低分類。可能なら種/属まで。"],
    ["訪花観察", "訪花回数と観察時間を記録する", "pollinator_environment を作る材料。訪花者種別、回数、花粉接触、滞在時間を記録。"],
    ["訪花観察", "訪花行動を記録する", "正当訪花、盗蜜、接触部位、滞在時間、花粉接触の有無。"],
    ["訪花観察", "時間帯を分散する", "午前/午後、開花期前半/中盤/後半を偏らせない。"],
    ["自然結実", "無処理花をマークする", "自然条件での fruit set と seed set。"],
    ["自然結実", "果実成熟後に回収する", "種子数、しいな率、果実成熟失敗も記録。"],
    ["袋掛け", "開花前つぼみを袋掛けする", "selfing_ability。送粉者なしで結実するか。"],
    ["袋掛け", "袋の破損・開閉を記録する", "処理失敗を除外できるようにする。"],
    ["人工自殖", "同一花または同一個体花粉で授粉する", "seed_set_selfing, germination_selfed。"],
    ["人工他殖", "別個体・可能なら別パッチ花粉で授粉する", "seed_set_outcrossing, germination_outcrossed。"],
    ["交配実験", "処理ごとの花数を揃える", "各母株で袋掛け/自然/人工自殖/人工他殖をできるだけ揃える。"],
    ["発芽試験", "処理別に種子を播く", "発芽率、発芽日、カビ/死亡を記録。"],
    ["発芽試験", "同じ条件で管理する", "温度、光、培地、水分を揃える。"],
    ["SNP", "葉サンプルを採る", "各集団 20-30 個体以上。シリカゲル保存など。"],
    ["SNP", "個体IDと表現型IDを対応させる", "Fis/Fst と斑点面積率・自殖能力を結びつける。"],
    ["SNP", "位置情報を記録する", "集団内空間構造や近縁個体の偏りを確認する。"],
    ["Pst/Qst", "集団ごとの表現型平均と分散を記録する", "まず Pst。斑点面積率、花サイズ、花冠形状を対象にする。"],
    ["Pst/Qst", "可能なら common garden 用の種子を採る", "環境効果を減らして Qst に近づける。母株IDを必ず残す。"],
    ["Pst/Qst", "家系/母株構造を残す", "半きょうだい・母株内分散があると Qst 推定に進みやすい。"],
    ["履歴", "移入経緯を記録する", "島・集団の由来、植栽/持ち込みの可能性、過去採集記録。"],
    ["履歴", "交雑履歴を疑う証拠を記録する", "形態の中間性、SNP admixture、近隣分類群、園芸由来の可能性。"],
    ["データ管理", "欠測理由を記録する", "未開花、食害、袋破損、果実脱落、サンプル紛失など。"],
    ["データ管理", "写真ファイル名を個体ID/花IDに対応させる", "後から斑点面積率を再計算できるようにする。"],
    ["データ管理", "CSVを毎日バックアップする", "field template に合わせて入力する。"],
]


@dataclass
class Plant:
    guide: float
    diversity: float
    x: float
    y: float
    mode: str = "outcrossing"
    seed_output: float = 1.0
    germination: float = 1.0
    fitness: float = 1.0


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    if math.isnan(float(value)):
        return low
    return max(low, min(high, float(value)))


def row_clamped(row: pd.Series, key: str, fallback_key: str | None = None, default: float = 0.0) -> float:
    """Read a field-data value with backwards-compatible fallback."""

    if key in row.index and not pd.isna(row[key]):
        return clamp(row[key])
    if fallback_key is not None and fallback_key in row.index and not pd.isna(row[fallback_key]):
        return clamp(row[fallback_key])
    return clamp(default)


def evaluate_population(population: list[Plant], params: dict[str, float], rng: np.random.Generator) -> None:
    bombus_frequency = clamp(params.get("bombus_frequency", params.get("bombus_present", 0.0)))
    effective_selfing_ability = clamp(params["selfing_ability"] * (1.0 - params["herkogamy"]))
    constrained_guide_cost = params["guide_cost"] * params["flower_size"]
    for plant in population:
        pollinator_efficiency = (
            bombus_frequency * params["bombus_pollination_efficiency"]
            + (1.0 - bombus_frequency) * params["other_pollinator_efficiency"]
        )
        guide_alignment = (
            bombus_frequency * params["bombus_guide_dependence"]
            + (1.0 - bombus_frequency) * params["other_pollinator_guide_use"]
        )
        outcross_prob = clamp(
            params["base_outcross"]
            + params["pollinator_environment"]
            * pollinator_efficiency
            * (
                params["pollinator_environment_outcross_effect"]
                + guide_alignment * plant.guide
            )
        )
        outcrossing = rng.random() < outcross_prob
        selfing = (not outcrossing) and (rng.random() < effective_selfing_ability)
        plant.mode = "outcrossing" if outcrossing else "selfing" if selfing else "failed"

        if outcrossing:
            plant.seed_output = params["seed_set_outcrossing"]
            plant.germination = params["germination_outcrossed"]
            inbreeding_penalty = 0.0
        elif selfing:
            plant.seed_output = params["seed_set_selfing"]
            plant.germination = max(
                0.0,
                min(
                    params["germination_selfed"],
                    params["germination_outcrossed"] - params["inbreeding_load"],
                ),
            )
            inbreeding_penalty = 0.0
        else:
            plant.seed_output = 0.02
            plant.germination = 0.02
            inbreeding_penalty = 0.0

        plant.fitness = max(
            0.001,
            plant.seed_output * plant.germination * (1.0 - inbreeding_penalty)
            - constrained_guide_cost * plant.guide,
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
    effective_selfing_ability = clamp(params["selfing_ability"] * (1.0 - params["herkogamy"]))
    constrained_guide_cost = params["guide_cost"] * params["flower_size"]
    selfing_syndrome_score = clamp(
        (
            selfing_rate
            + (1.0 - outcrossing_rate)
            + (1.0 - params["nectar_guide"])
            + (1.0 - params["flower_size"])
            + (1.0 - params["herkogamy"])
            + (1.0 - params["pollen_ovule_ratio"])
        )
        / 6.0
    )
    island_syndrome_score = clamp(
        (
            (1.0 - params["pollinator_environment"])
            + (1.0 - params["bombus_frequency"])
            + params["selfing_ability"]
            + (1.0 - np.mean(diversity))
            + (1.0 - params["migration_rate"] / 0.25)
            + params["admixture_index"]
        )
        / 6.0
    )
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
        "bombus_frequency": float(params["bombus_frequency"]),
        "effective_selfing_ability": float(effective_selfing_ability),
        "constrained_guide_cost": float(constrained_guide_cost),
        "selfing_syndrome_score": float(selfing_syndrome_score),
        "island_syndrome_score": float(island_syndrome_score),
    }


def simulate_abm(
    params: dict[str, float],
    generations: int,
    population_size: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    guide_start = clamp(params["nectar_guide"])
    population = [
        Plant(
            guide=clamp(rng.normal(guide_start, 0.12)),
            diversity=clamp(rng.normal(0.78, 0.08)),
            x=float(rng.uniform(0, 1)),
            y=float(rng.uniform(0, 1)),
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
            next_population.append(
                Plant(
                    guide=guide,
                    diversity=clamp(diversity),
                    x=clamp(parent.x + rng.normal(0.0, 0.055)),
                    y=clamp(parent.y + rng.normal(0.0, 0.055)),
                )
            )
        population = next_population
        evaluate_population(population, params, rng)
        history.append(record_generation(generation, population, params))

    agent_rows = [
        {
            "x": plant.x,
            "y": plant.y,
            "nectar_guide": plant.guide,
            "fitness": plant.fitness,
            "reproduction_mode": plant.mode,
            "neutral_diversity": plant.diversity,
        }
        for plant in population
    ]
    return pd.DataFrame(history), pd.DataFrame(agent_rows)


def run_abm(params: dict[str, float], generations: int, population_size: int, seed: int) -> pd.DataFrame:
    history, _ = simulate_abm(params, generations, population_size, seed)
    return history


def run_threshold_sweep(
    base_params: dict[str, float],
    generations: int,
    population_size: int,
    seed: int,
    grid_size: int,
    guide_criterion: float,
    sweep_axis: str,
    replicates: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    selfing_values = np.linspace(0.0, 1.0, grid_size)
    pollinator_values = np.linspace(0.0, 1.0, grid_size)
    for selfing_ability in selfing_values:
        for pollinator_frequency in pollinator_values:
            params = {
                **base_params,
                "selfing_ability": float(selfing_ability),
                sweep_axis: float(pollinator_frequency),
            }
            finals = [
                run_abm(params, generations, population_size, seed + replicate).iloc[-1]
                for replicate in range(replicates)
            ]
            rows.append(
                {
                    "selfing_ability": float(selfing_ability),
                    sweep_axis: float(pollinator_frequency),
                    "final_mean_nectar_guide": float(
                        np.mean([final["mean_nectar_guide"] for final in finals])
                    ),
                    "final_selfing_rate": float(
                        np.mean([final["selfing_rate"] for final in finals])
                    ),
                    "final_outcrossing_rate": float(
                        np.mean([final["outcrossing_rate"] for final in finals])
                    ),
                    "maintained": bool(
                        np.mean([final["mean_nectar_guide"] for final in finals])
                        >= guide_criterion
                    ),
                }
            )
    sweep = pd.DataFrame(rows)
    boundary_rows = []
    for selfing_ability, group in sweep.groupby("selfing_ability"):
        maintained = group[group["maintained"]].sort_values(sweep_axis)
        if maintained.empty:
            boundary_rows.append(
                {
                    "selfing_ability": selfing_ability,
                    f"min_{sweep_axis}_for_guide_maintenance": np.nan,
                    "selfing_rate_at_boundary": np.nan,
                    "outcrossing_rate_at_boundary": np.nan,
                    "threshold_interpretation": f"not maintained even at {sweep_axis}=1",
                }
            )
        else:
            row = maintained.iloc[0]
            boundary_rows.append(
                {
                    "selfing_ability": selfing_ability,
                    f"min_{sweep_axis}_for_guide_maintenance": row[sweep_axis],
                    "selfing_rate_at_boundary": row["final_selfing_rate"],
                    "outcrossing_rate_at_boundary": row["final_outcrossing_rate"],
                    "threshold_interpretation": f"guide maintained above this {sweep_axis}",
                }
            )
    return sweep, pd.DataFrame(boundary_rows)


def run_robustness_grid(
    base_params: dict[str, float],
    generations: int,
    population_size: int,
    seed: int,
    guide_criterion: float,
    grid_size: int,
) -> pd.DataFrame:
    guide_cost_values = np.linspace(0.01, 0.16, grid_size)
    bombus_efficiency_values = np.linspace(0.55, 1.00, grid_size)
    other_efficiency_values = np.linspace(0.10, 0.55, grid_size)
    rows = []
    for guide_cost in guide_cost_values:
        for bombus_efficiency in bombus_efficiency_values:
            for other_efficiency in other_efficiency_values:
                params = {
                    **base_params,
                    "guide_cost": float(guide_cost),
                    "bombus_pollination_efficiency": float(bombus_efficiency),
                    "other_pollinator_efficiency": float(other_efficiency),
                }
                result = run_abm(params, generations, population_size, seed)
                final = result.iloc[-1]
                rows.append(
                    {
                        "guide_cost": float(guide_cost),
                        "bombus_pollination_efficiency": float(bombus_efficiency),
                        "other_pollinator_efficiency": float(other_efficiency),
                        "final_mean_nectar_guide": float(final["mean_nectar_guide"]),
                        "final_selfing_rate": float(final["selfing_rate"]),
                        "final_outcrossing_rate": float(final["outcrossing_rate"]),
                        "maintained": bool(final["mean_nectar_guide"] >= guide_criterion),
                    }
                )
    return pd.DataFrame(rows)


def field_row_to_params(row: pd.Series) -> dict[str, float]:
    return {
        "nectar_guide": row_clamped(row, "nectar_guide"),
        "flower_size": row_clamped(row, "flower_size"),
        "herkogamy": row_clamped(row, "herkogamy"),
        "pollen_ovule_ratio": row_clamped(row, "pollen_ovule_ratio"),
        "pollinator_environment": row_clamped(row, "pollinator_environment"),
        "bombus_present": row_clamped(row, "bombus_present"),
        "bombus_frequency": row_clamped(row, "bombus_frequency", fallback_key="bombus_present"),
        "bombus_pollination_efficiency": row_clamped(row, "bombus_pollination_efficiency"),
        "other_pollinator_efficiency": row_clamped(row, "other_pollinator_efficiency"),
        "bombus_guide_dependence": row_clamped(row, "bombus_guide_dependence"),
        "other_pollinator_guide_use": row_clamped(row, "other_pollinator_guide_use"),
        "selfing_ability": row_clamped(row, "selfing_ability"),
        "inbreeding_load": row_clamped(row, "inbreeding_load"),
        "seed_set_selfing": row_clamped(row, "seed_set_selfing"),
        "seed_set_outcrossing": row_clamped(row, "seed_set_outcrossing"),
        "germination_selfed": row_clamped(row, "germination_selfed"),
        "germination_outcrossed": row_clamped(row, "germination_outcrossed"),
        "migration_rate": clamp(row["migration_rate"], 0.0, 0.25),
        "admixture_index": row_clamped(row, "admixture_index"),
        "guide_cost": 0.06,
        "base_outcross": 0.10,
        "pollinator_environment_outcross_effect": 0.42,
        "mutation_sd": 0.055,
        "genetic_drift_strength": 0.035,
    }


def estimate_pst_from_population_means(
    data: pd.DataFrame,
    trait_column: str,
    within_variance: float = 0.02,
    c_over_h2: float = 1.0,
) -> float:
    values = pd.to_numeric(data[trait_column], errors="coerce").dropna()
    if len(values) < 2:
        return np.nan
    between_variance = float(np.var(values, ddof=1))
    denominator = between_variance + 2.0 * c_over_h2 * within_variance
    if denominator <= 0:
        return np.nan
    return between_variance / denominator


def make_pst_fst_diagnostics(data: pd.DataFrame) -> pd.DataFrame:
    observed_fst = pd.to_numeric(data.get("Fst_observed"), errors="coerce")
    mean_fst = float(observed_fst.mean(skipna=True)) if observed_fst.notna().any() else np.nan
    pst_ng_observed = pd.to_numeric(data.get("Pst_nectar_guide"), errors="coerce")
    pst_flower_observed = pd.to_numeric(data.get("Pst_flower_size"), errors="coerce")
    pst_ng = (
        float(pst_ng_observed.mean(skipna=True))
        if pst_ng_observed.notna().any()
        else estimate_pst_from_population_means(data, "nectar_guide")
    )
    pst_flower = (
        float(pst_flower_observed.mean(skipna=True))
        if pst_flower_observed.notna().any()
        else np.nan
    )

    rows = []
    for trait, pst_value in [
        ("nectar_guide", pst_ng),
        ("flower_size", pst_flower),
    ]:
        if np.isnan(pst_value) or np.isnan(mean_fst):
            interpretation = "need Pst/Qst and Fst data"
            delta = np.nan
        else:
            delta = pst_value - mean_fst
            if delta > 0.10:
                interpretation = "Pst > Fst: divergent selection is plausible"
            elif delta < -0.10:
                interpretation = "Pst < Fst: stabilizing selection or constraint is plausible"
            else:
                interpretation = "Pst ~= Fst: drift/history cannot be rejected"
        rows.append(
            {
                "trait": trait,
                "Pst_or_Qst": pst_value,
                "mean_Fst": mean_fst,
                "Pst_minus_Fst": delta,
                "interpretation": interpretation,
            }
        )
    return pd.DataFrame(rows)


st.title("CAPOM: シマホタルブクロ ネクターガイド進化 ABM")
st.caption(
    "Constraint-Aware Pattern-Oriented Modelling: 見えるパターンで、見えないメカニズムを縛る方法。"
    "実データを入れて予測するモデルではなく、実データと比較するための仮説生成器です。"
)

with st.expander("CAPOM framework", expanded=True):
    st.markdown(
        """
        **POM**: 見えるパターンに合うモデルを探す。

        **普通のABM**: ルールを作って、パターンが出るかを見る。

        **CAPOM**: 観察パターンを先に定義し、そのパターンを再現できる潜在パラメータ範囲と因果シナリオを絞る。

        野外データは入力値ではなく、ABMが再現すべき観察パターンとして扱います。
        このアプリでは、`nectar_guide`, `flower_size`, Bombus頻度・寄与率、自殖率、発芽率、`Fis`, `Fst`, `Pst` などを
        **Observable patterns** として扱い、`guide_cost`, `outcrossing_benefit`, `inbreeding_depression`,
        `drift_strength`, `small_pollinator_efficiency` などの **Latent trade-offs** をシナリオ比較と感度分析で制約します。

        CAPOM制約として、`bombus_frequency` は送粉効率とネクターガイド利用を連続的に重みづけ、
        `herkogamy` は実効自殖能力を制約し、`flower_size` はネクターガイド維持コストを制約します。
        `selfing_syndrome_score` と `island_syndrome_score` は診断指標であり、fitness計算には入れません。
        """
    )

with st.expander("仮説", expanded=True):
    st.markdown(
        """
        **通常状態、本土**: マルハナバチあり → 他殖が成立 → ネクターガイド維持 → 遺伝的多様性維持

        **島状態、大島**: `Bombus ardens` とコハナバチ類あり → 他殖機会は本土より変化するがゼロではない → ネクターガイド維持の余地が残る

        **島状態、大島以外**: マルハナバチ不在・コハナバチ類優占 → 他殖機会が不安定化 → 繁殖保証として自殖が重要になる → でも自殖は近交弱勢を生む → 完全自殖には移行できない → 他殖チャンスを残す個体ではネクターガイドが維持される → 他殖チャンスがほぼない場所ではネクターガイドが退化する
        """
    )

scenario_data = DEFAULT_FIELD_DATA.copy()

st.sidebar.header("Simulation")
population_choice = st.sidebar.selectbox("Scenario preset", scenario_data["population"].astype(str).tolist())
generations = st.sidebar.slider("Generations", 10, 300, 80, 10)
population_size = st.sidebar.slider("Population size", 50, 600, 180, 10)
seed = st.sidebar.number_input("Random seed", value=20260605, step=1)

sim_tab, threshold_tab, robustness_tab, pst_tab, evidence_tab, fieldwork_tab = st.tabs(
    [
        "ABM results",
        "Threshold sweep",
        "Robustness",
        "Pst/Fst diagnostics",
        "Literature",
        "Fieldwork plan",
    ]
)

working_data = scenario_data.copy()
matched_rows = working_data[working_data["population"].astype(str) == population_choice]
selected_row = matched_rows.iloc[0] if not matched_rows.empty else working_data.iloc[0]
base_params = field_row_to_params(selected_row)

with st.sidebar.expander("Manual parameter overrides", expanded=False):
    for key in [
        "pollinator_environment",
        "bombus_frequency",
        "bombus_pollination_efficiency",
        "other_pollinator_efficiency",
        "bombus_guide_dependence",
        "other_pollinator_guide_use",
        "flower_size",
        "herkogamy",
        "pollen_ovule_ratio",
        "selfing_ability",
        "inbreeding_load",
        "guide_cost",
        "migration_rate",
    ]:
        upper = 0.5 if key == "guide_cost" else 0.25 if key == "migration_rate" else 1.0
        base_params[key] = st.slider(key, 0.0, upper, float(base_params[key]), 0.01)

with sim_tab:
    results, agents = simulate_abm(base_params, generations, population_size, int(seed))
    latest = results.iloc[-1]
    above_threshold = results["mean_nectar_guide"] >= results["guide_threshold_0_5"]
    above_count = int(above_threshold.sum())
    below_count = int((~above_threshold).sum())
    threshold_status = "above 0.5" if latest["mean_nectar_guide"] >= latest["guide_threshold_0_5"] else "below 0.5"

    cols = st.columns(6)
    cols[0].metric("mean_nectar_guide", f"{latest['mean_nectar_guide']:.3f}")
    cols[1].metric("selfing_rate", f"{latest['selfing_rate']:.3f}")
    cols[2].metric("outcrossing_rate", f"{latest['outcrossing_rate']:.3f}")
    cols[3].metric("Fis", f"{latest['Fis']:.3f}")
    cols[4].metric("Fst", f"{latest['Fst']:.3f}")
    cols[5].metric("threshold status", threshold_status)
    st.caption(f"Threshold check: mean_nectar_guide >= 0.5 for {above_count} generations; below 0.5 for {below_count} generations.")
    st.caption(
        f"Selfing syndrome score: {latest['selfing_syndrome_score']:.3f}; "
        f"island syndrome score: {latest['island_syndrome_score']:.3f}."
    )
    with st.expander("この値の出し方", expanded=False):
        st.markdown(
            f"""
            表示値は、左の `Scenario preset`、手動パラメータ、`Generations = {generations}`、
            `Population size = {population_size}`、`Random seed = {int(seed)}` で回した
            ABM の最終世代の集計です。実測値を入力して予測した値ではありません。

            - `mean_nectar_guide`: 最終世代の全個体の `nectar_guide` 平均。
            - `outcrossing_rate`: 最終世代で他殖になった個体の割合。
            - `selfing_rate`: 最終世代で自殖成功になった個体の割合。モデル内では、他殖しなかった個体だけが `selfing_ability * (1 - herkogamy)` の実効自殖能力で自殖判定に進みます。
            - `Fis`: `selfing_rate * (1 - 0.5 * migration_rate)` を 0-1 に丸めた近交診断。
            - `Fst`: `(1 - migration_rate) * (1 - outcrossing_rate) * (1 - mean_neutral_diversity)` を 0-1 に丸めた分化診断。
            - `threshold status`: `mean_nectar_guide >= 0.5` なら `above 0.5`、下回れば `below 0.5`。

            各個体の繁殖モードは、送粉者環境、Bombus頻度・寄与率、ネクターガイド値から他殖確率を作り、
            乱数で `outcrossing` / `selfing` / `failed` に分岐させています。次世代の親は、
            種子数・発芽率・近交弱勢・`guide_cost * flower_size` で制約されたガイド維持コストから作った `fitness` を重みとして選ばれます。
            """
        )

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.line_chart(results.set_index("generation")[["mean_nectar_guide", "guide_threshold_0_5"]])
        st.line_chart(results.set_index("generation")[["selfing_rate", "outcrossing_rate", "failed_rate"]])
    with chart_right:
        st.line_chart(results.set_index("generation")[["mean_fitness", "seed_output", "germination"]])
        st.line_chart(results.set_index("generation")[["mean_neutral_diversity", "Fis", "Fst"]])
        st.line_chart(results.set_index("generation")[["selfing_syndrome_score", "island_syndrome_score"]])

    st.subheader("Agent scatter view")
    st.caption("Streamlit 上の簡易可視化です。TenSnap 本体ではありません。各点は Plant 個体で、色は nectar_guide、サイズは fitness を表します。")
    view_agents = agents.copy()
    view_agents["guide_color_value"] = view_agents["nectar_guide"]
    view_agents["fitness_size"] = 60 + 220 * view_agents["fitness"]
    st.scatter_chart(
        view_agents,
        x="x",
        y="y",
        color="guide_color_value",
        size="fitness_size",
        width="stretch",
    )
    st.dataframe(
        view_agents[
            [
                "x",
                "y",
                "nectar_guide",
                "fitness",
                "reproduction_mode",
                "neutral_diversity",
            ]
        ].head(40),
        width="stretch",
    )

    st.download_button(
        "Download ABM results CSV",
        results.to_csv(index=False).encode("utf-8"),
        file_name=f"microdonta_abm_{population_choice}.csv",
        mime="text/csv",
    )
    st.dataframe(results.tail(12), width="stretch")

with threshold_tab:
    st.subheader("維持/退化の ecological threshold")
    default_axis = "pollinator_environment"
    sweep_axis = st.radio(
        "sweep axis",
        ["pollinator_environment", "bombus_frequency", "bombus_guide_dependence"],
        index=["pollinator_environment", "bombus_frequency", "bombus_guide_dependence"].index(default_axis),
        horizontal=True,
    )
    st.write(
        "ここでは `mean_nectar_guide >= guide criterion` を「ネクターガイド維持」と定義し、"
        f"`selfing_ability` ごとに、維持に必要な最小 `{sweep_axis}` を探索します。"
    )
    if sweep_axis == "bombus_guide_dependence" and base_params["bombus_frequency"] == 0:
        st.warning(
            "この集団では Bombus 頻度が 0 なので、Bombus guide dependence の sweep は反実仮想です。"
            "現実の閾値としては pollinator_environment または実測 outcrossing_rate を見てください。"
        )
    sweep_cols = st.columns(5)
    sweep_generations = sweep_cols[0].slider("sweep generations", 20, 180, 80, 10)
    sweep_population = sweep_cols[1].slider("sweep population", 40, 260, 120, 20)
    grid_size = sweep_cols[2].slider("grid size", 6, 21, 11, 1)
    guide_criterion = sweep_cols[3].slider("guide criterion", 0.1, 0.9, 0.5, 0.05)
    sweep_replicates = sweep_cols[4].slider("replicates", 1, 10, 3, 1)
    sweep, boundary = run_threshold_sweep(
        base_params,
        generations=sweep_generations,
        population_size=sweep_population,
        seed=int(seed),
        grid_size=grid_size,
        guide_criterion=guide_criterion,
        sweep_axis=sweep_axis,
        replicates=sweep_replicates,
    )
    st.dataframe(boundary, width="stretch")
    st.caption(
        f"Interpretation: 自殖能力が高くても、`{sweep_axis}` が十分低いと他殖機会が減り、"
        "ネクターガイドの維持境界を下回ります。近交弱勢が強いほど、完全自殖だけでは fitness が伸びにくくなります。"
    )
    heatmap = sweep.pivot(
        index="selfing_ability",
        columns=sweep_axis,
        values="final_mean_nectar_guide",
    )
    st.write("final_mean_nectar_guide heatmap")
    st.dataframe(
        heatmap.round(3),
        width="stretch",
    )
    st.download_button(
        "Download threshold sweep CSV",
        sweep.to_csv(index=False).encode("utf-8"),
        file_name=f"microdonta_threshold_sweep_{population_choice}.csv",
        mime="text/csv",
    )

with robustness_tab:
    st.subheader("Unobserved-parameter robustness")
    st.write(
        "野外で直接取りにくい `guide_cost`、送粉環境から他殖確率への変換、Bombus の guide 利用強度を範囲で振り、"
        "ネクターガイド維持/退化の傾向がどれだけ安定かを見ます。"
    )
    robust_cols = st.columns(4)
    robust_generations = robust_cols[0].slider("robust generations", 20, 160, 60, 10)
    robust_population = robust_cols[1].slider("robust population", 40, 220, 100, 20)
    robust_grid = robust_cols[2].slider("robust grid size", 3, 8, 5, 1)
    robust_criterion = robust_cols[3].slider("robust guide criterion", 0.1, 0.9, 0.5, 0.05)
    robustness = run_robustness_grid(
        base_params,
        generations=robust_generations,
        population_size=robust_population,
        seed=int(seed),
        guide_criterion=robust_criterion,
        grid_size=robust_grid,
    )
    maintained_fraction = robustness["maintained"].mean()
    st.metric("fraction maintained across unobserved parameter grid", f"{maintained_fraction:.2f}")
    st.caption(
        "この値が本土・大島で高く、神津島・八丈島で低いなら、測れないパラメータを振ってもシナリオの傾向が比較的安定、という読み方ができます。"
    )
    grouped = (
        robustness.groupby(["guide_cost", "bombus_pollination_efficiency", "other_pollinator_efficiency"], as_index=False)
        .agg(
            maintained_fraction=("maintained", "mean"),
            mean_final_guide=("final_mean_nectar_guide", "mean"),
            mean_selfing_rate=("final_selfing_rate", "mean"),
            mean_outcrossing_rate=("final_outcrossing_rate", "mean"),
        )
    )
    st.dataframe(grouped, width="stretch")
    st.download_button(
        "Download robustness grid CSV",
        robustness.to_csv(index=False).encode("utf-8"),
        file_name=f"microdonta_robustness_{population_choice}.csv",
        mime="text/csv",
    )

with pst_tab:
    st.subheader("Pst/Fst-Qst diagnostics")
    st.write(
        "`Pst` や `Qst` は、いまの ABM の fitness ルールには直接入れず、"
        "ネクターガイド分化が選択で説明できるのか、移入経緯・交雑履歴・漂流で説明すべきなのかを診断するために使います。"
    )
    st.caption(
        "まずは population mean からの Pst を仮置きし、後で common garden / half-sib などのデータがあれば Qst に置き換えます。"
    )
    pst_diagnostics = make_pst_fst_diagnostics(working_data)
    st.dataframe(pst_diagnostics, width="stretch")

    st.subheader("移入経緯・交雑履歴メモ")
    history_cols = [
        "population",
        "admixture_index",
        "colonization_history",
        "Fis_observed",
        "Fst_observed",
        "Pst_nectar_guide",
    ]
    st.dataframe(working_data[history_cols], width="stretch")
    st.markdown(
        """
        **読み方**

        - `Pst > Fst`: 形質分化が中立分化より大きい。ネクターガイドに分化選択がかかった可能性。
        - `Pst ≈ Fst`: 漂流、創始者効果、移入経緯、集団構造だけでも説明できる可能性。
        - `Pst < Fst`: 安定化選択、制約、強い遺伝子流動などの可能性。

        **注意**: Pst は環境効果・可塑性を含むので、Qst そのものではありません。まず探索指標として使い、必要なら common garden / reciprocal transplant / 家系デザインで Qst に近づけます。
        """
    )
    st.download_button(
        "Download Pst/Fst diagnostics CSV",
        pst_diagnostics.to_csv(index=False).encode("utf-8"),
        file_name="microdonta_pst_fst_diagnostics.csv",
        mime="text/csv",
    )

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
                ["pollinator_environment", "訪花者組成・訪花頻度・花粉接触から作る他殖機会", "他殖確率の主要項"],
                ["bombus_frequency", "Bombus頻度・寄与率", "送粉効率とネクターガイド選択の連続的な重み"],
                ["bombus_present", "後方互換用の在/不在列", "bombus_frequency が無いCSVのfallback"],
                ["bombus_guide_dependence", "Bombus がネクターガイドを利用する強さ", "guide trait が他殖に効く強さ"],
                ["other_pollinator_guide_use", "コハナバチ類などの guide 利用", "Bombus 不在時の弱い guide 効果"],
                ["selfing_ability", "袋掛け結実率", "他殖失敗時の自殖成功確率"],
                ["inbreeding_load", "自殖種子と自然種子の発芽率差", "自殖 fitness penalty"],
                ["fitness", "種子数・発芽率", "次世代親の重み"],
                ["Fis", "SNP", "自殖率・移住率からの近交指標"],
                ["Fst", "SNP", "多様性低下・移住率・他殖低下からの分化指標"],
            ],
            columns=["ABM variable", "field data", "model role"],
        ),
        width="stretch",
    )
    st.subheader("Selfing / island syndrome variables added for diagnosis")
    st.dataframe(
        pd.DataFrame(
            [
                ["flower_size", "corolla size / floral display", "selfing syndrome: reduced attraction traits"],
                ["herkogamy", "anther-stigma separation", "selfing syndrome: reduced separation can enable autonomous selfing"],
                ["pollen_ovule_ratio", "pollen grains per ovule", "selfing syndrome: reduced male allocation"],
                ["bombus_pollination_efficiency", "Bombus seed/pollen-transfer efficiency", "efficient-pollinator channel weighted by bombus_frequency"],
                ["other_pollinator_efficiency", "halictid/small-bee efficiency", "uncertain non-Bombus channel; explored in robustness"],
                ["selfing_syndrome_score", "combined diagnosis", "higher when selfing and reduced outcrossing floral traits co-occur"],
                ["island_syndrome_score", "combined diagnosis", "higher when pollinator loss, isolation, selfing, and diversity loss co-occur"],
            ],
            columns=["variable", "field data to fill", "why it is included"],
        ),
        width="stretch",
    )

with fieldwork_tab:
    st.subheader("野外で取るデータ")
    st.dataframe(
        pd.DataFrame(
            [
                ["斑点面積率", "nectar_guide", "各集団 30-50 個体、各個体 3-5 花", "目的形質。退化/維持の直接測定"],
                ["訪花者の種類と訪花回数/時間", "pollinator_environment, bombus_frequency", "各集団 20-30 時間以上", "送粉者相と他殖機会"],
                ["自然結実率・種子数", "fitness baseline", "各集団 30-50 花以上", "自然条件での適応度"],
                ["袋掛け結実率", "selfing_ability", "各集団 30-50 花以上", "送粉者なしの繁殖保証"],
                ["人工自殖/人工他殖の種子数", "seed_set_selfing, seed_set_outcrossing", "各集団 20-30 母株、各処理 1-3 花", "繁殖様式ごとの種子生産"],
                ["自殖/他殖種子の発芽率", "germination_selfed, germination_outcrossed, inbreeding_load", "各集団 20-30 母株", "近交弱勢"],
                ["SNP", "Fis, Fst", "各集団 20-30 個体以上", "近交・集団分化・多様性"],
            ],
            columns=["データ", "ABM変数", "最低サンプル感", "目的"],
        ),
        width="stretch",
    )
    st.markdown(
        """
        **最小セット**: 各地域 1 集団、各集団 30 個体、訪花観察 20 時間。仮説の方向を見る。

        **検定向け**: 各地域 2-3 集団、各集団 40-60 個体、訪花観察 30-50 時間、交配実験 30 母株程度。

        **ABM パラメータ推定向け**: 各地域 3 集団以上、各集団 60 個体前後、訪花観察 50 時間以上、人工自殖/他殖/袋掛け/自然結実を同一個体群で揃え、SNP は各集団 30 個体以上。

        優先順位は、1. 訪花者組成、2. 袋掛け結実率、3. 自殖/他殖の発芽率差、4. 斑点面積率、5. SNP。
        """
    )

    st.subheader("野外調査チェックリスト")
    checklist = pd.DataFrame(FIELD_CHECKLIST, columns=["カテゴリ", "項目", "メモ"])
    selected_categories = st.multiselect(
        "表示するカテゴリ",
        checklist["カテゴリ"].unique().tolist(),
        default=checklist["カテゴリ"].unique().tolist(),
    )
    filtered_checklist = checklist[checklist["カテゴリ"].isin(selected_categories)]
    st.data_editor(
        filtered_checklist.assign(完了=False),
        width="stretch",
        hide_index=True,
        column_config={
            "完了": st.column_config.CheckboxColumn("完了"),
            "カテゴリ": st.column_config.TextColumn("カテゴリ", disabled=True),
            "項目": st.column_config.TextColumn("項目", disabled=True),
            "メモ": st.column_config.TextColumn("メモ", disabled=True),
        },
    )
    st.download_button(
        "Download fieldwork checklist CSV",
        checklist.to_csv(index=False).encode("utf-8"),
        file_name="microdonta_fieldwork_checklist.csv",
        mime="text/csv",
    )
