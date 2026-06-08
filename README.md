# RACH: Restricted Admissible Causal Hypotheses

**RACH** stands for **Restricted Admissible Causal Hypotheses**.

RACH is a constraint-first generative inference framework for identifying which causal hypotheses remain admissible after latent ecological trade-offs are constrained and simulated patterns are compared with observed ecological patterns.

日本語では、RACHは **「制約下で許容される因果仮説を抽出する生成推論フレームワーク」** です。

このリポジトリは、シマホタルブクロ / `Campanula punctata` 系の伊豆諸島集団を worked example として、RACH framework を実装するためのプロトタイプです。

## One-sentence definition

> **RACH identifies the restricted set of admissible causal hypotheses that can generate observed ecological patterns under biologically motivated constraints.**

日本語:

> **RACHは、生態学的制約のもとで観察パターンを生成可能な因果仮説だけを抽出するモデルである。**

## Why RACH?

このモデルは、手動スライダーで都合のよいパラメータを探すABMではありません。

RACHの基本的な流れは以下です。

```text
1. 生態学的原理に基づく ecological constraint grammar を定義する
2. パラメータ間制約で不自然な組み合わせを除外する
3. 制約内で潜在的な利益・コストをランダムサンプリングする
4. 有効な parameter set を ModelParameters に変換する
5. M1-M5 の candidate causal hypotheses をシミュレーションする
6. シミュレーション出力を観察パターンと照合する
7. 観察パターンを再現できる admissible causal hypotheses と compatible parameter ranges を残す
```

短く言うと:

```text
ecological constraint grammar
-> constrained latent parameter sampling
-> causal simulation
-> pattern-distance filtering
-> restricted admissible causal hypotheses
```

この順番が重要です。先にシミュレーションを手で合わせるのではなく、**先に生態学的にあり得る潜在パラメータ空間を定義し、その制約内でどの因果仮説が観察パターンを生成できるかを見る** というモデルです。

## Streamlit app

メインのStreamlitアプリは RACH Research App です。

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

アプリでは以下を行います。

```text
trade-off preset selection
-> constrained random sampling
-> M1-M5 causal simulation
-> observed pattern matching / pattern distance
-> scenario ranking
-> compatible parameter ranges
-> CSV download
```

手動パラメータスライダーは、メインアプリから意図的に外しています。

## RACH and existing methods

RACHは、ABM・POM・ABCを単に並べたものではありません。これらはRACHの内部部品です。

| Existing method | Role inside RACH |
|---|---|
| ABM | candidate causal hypothesesを生成するシミュレーター |
| POM | 複数の観察パターンでモデルを制約する評価原理 |
| ABC-style filtering | 距離関数と受理閾値に基づく潜在パラメータ領域の近似 |
| Ecological constraint grammar | シミュレーション前に許容される潜在パラメータ空間を定義する制約規則 |

重要なのは、野外データを単なる「入力値」として扱わないことです。野外データは、モデルが再現すべき **observable patterns** です。RACHは、見えないパラメータを一点推定する機械ではなく、観察パターンと矛盾しない **admissible causal hypotheses** と **compatible latent parameter regions** を絞るための generative filter です。

## Core components

1. **Observable patterns**
   野外で測れるもの: `nectar_guide`, `flower_size`, Bombus frequency, small pollinator frequency, effective selfing rate, fruit set, germination, `Fis`, `Fst`, `Ne`, `Pst`, island distance.

2. **Latent trade-offs**
   野外で直接測りにくいもの: `guide_cost`, `outcrossing_benefit`, `selfing_benefit`, `inbreeding_depression`, `drift_strength`, `small_pollinator_efficiency`, `direct_pollinator_guide_benefit`, `cost_of_waiting_for_pollinators`.

3. **Ecological constraint grammar**
   パラメータ間の生態学的制約: 自殖利益と近交弱勢の関係、小型送粉者効率と自殖利益の関係、ガイド維持コストと他殖利益の関係など。

4. **Candidate causal hypotheses**
   M1-M5 の候補因果仮説: direct pollinator effect, selfing-mediated effect, direct + mediated, common island cause, drift/null.

5. **Pattern-distance filtering**
   simulated patterns と observed patterns を比較し、pattern distance / epsilon に基づいて admissible hypotheses と compatible parameter ranges を抽出する。

## Current software layers

The repository distinguishes three software layers:

1. **Biological generator**
   `attraction_trait_model` defines individual plant agents, environments, provisional latent parameters, reproduction probabilities, fitness components, inheritance helpers, and stochastic ABM simulation.

2. **RACH evaluation layer**
   `streamlit_app.py`, `constraint_abm`, and Campanula example workflows compare simulated outputs with observed field/literature patterns, then filter plausible latent parameter ranges.

3. **Latent causal framing**
   `causal_model` represents alternative causal hypotheses, trade-off presets, parameter constraints, pathway switches, direct effects, mediated effects, common-cause explanations, and drift/null explanations.

The Campanula / Izu Islands case is the first worked example. Bombus loss, selfing increase, and nectar-guide reduction may overlap in the field, but that overlap is not treated as direct causal proof. RACH asks which candidate causal hypotheses can generate the same observable pattern overlap while also matching additional patterns such as flower size, herkogamy, Fis, Fst, Ne, and pollinator composition.

See also:

- [Constraint-first CAPOM workflow](docs/constraint_first_capom.md)
- [Latent causal generative model](docs/latent_causal_generative_model.md)
- [Generative model vs path model](docs/generative_model_vs_path_model.md)
- [ABM design policy](docs/abm_design_policy.md)
- [Package roadmap](docs/package_roadmap.md)
- [Methods workflow](paper/methods_workflow.md)
- [ODD protocol draft](paper/odd_protocol_draft.md)
- [MEE submission plan](paper/mee_submission_plan.md)
- [Campanula Izu worked example](examples/campanula_izu/README.md)
- [Campanula causal structure comparison](examples/campanula_izu/run_causal_structure_comparison.py)
- [Parameter filtering runner](examples/campanula_izu/run_parameter_filtering.py)

## Candidate causal hypotheses

```text
M1_direct_pollinator_to_guide
M2_selfing_mediated
M3_direct_plus_mediated
M4_common_island_cause
M5_drift_null
```

これらの候補は、Bombus欠落・自殖率上昇・ネクターガイド低下の共起を説明しうる複数の因果経路を表します。

## Observable pattern targets

現在の worked example では、大島と八丈島の関係として以下の観察パターンを照合します。

```text
nectar_guide:      Oshima > Hachijo
selfing_rate:      Oshima < Hachijo
herkogamy:         Oshima > Hachijo
flower_size:       Oshima > Hachijo
Fis:               Oshima < Hachijo
Bombus_frequency:  Oshima > Hachijo
```

## Trade-off presets

アプリでは、以下の制約付き探索プリセットを使います。

```text
broad_prior
reproductive_assurance
outcrossing_benefit
high_guide_cost
drift_dominated
```

各プリセットは、潜在的な利益・コストパラメータの範囲を定義します。さらに、パラメータ間制約によって生態学的に不自然な組み合わせを除外します。

## Manuscript framing

> We propose RACH, a Restricted Admissible Causal Hypotheses framework. RACH first defines an admissible latent trade-off space using ecological constraint grammar, then simulates candidate causal hypotheses within that space, and finally extracts the restricted set of admissible hypotheses by comparing simulated outputs with multiple observed ecological patterns.

日本語:

> 本研究では、RACH（Restricted Admissible Causal Hypotheses）を提案する。RACHは、生態学的制約文法によって許容される潜在トレードオフ空間を先に定義し、その空間内で候補因果仮説を生成シミュレーションし、複数の観察パターンとの照合によって制約下で許容される因果仮説集合を抽出するフレームワークである。
