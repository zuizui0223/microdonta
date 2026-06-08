# シマホタルブクロの制約付き因果生成モデル

**CAPOM (Constraint-Aware Pattern-Oriented Modelling)** の一言定義:

> 見えるパターンで、見えないメカニズムを縛る方法。

More formally:

> CAPOM uses observable field patterns to constrain latent ecological trade-offs that are difficult to measure directly.

このリポジトリは、シマホタルブクロ / `Campanula punctata` 系の伊豆諸島集団を worked example として、**生態学的制約先行型CAPOM (constraint-first CAPOM)** を構築するためのプロトタイプです。

## 新しいモデルの流れ

このモデルは、手動スライダーで都合のよいパラメータを探すABMではありません。

研究用の流れは以下です。

```text
1. 生態学的原理に基づく trade-off preset を選ぶ
2. パラメータ間制約で不自然な組み合わせを除外する
3. 制約内で潜在的な利益・コストをランダムサンプリングする
4. 有効なparameter setを ModelParameters に変換する
5. M1-M5 の候補因果構造をシミュレーションする
6. シミュレーション出力を観察パターンと照合する
7. 観察パターンを再現できる因果構造とparameter rangeを残す
```

短く言うと:

```text
constrained parameter exploration
-> causal simulation
-> CAPOM pattern matching
-> accepted causal structures and latent parameter ranges
```

この順番が重要です。先にシミュレーションを手で合わせるのではなく、**先に生態学的にあり得る潜在パラメータ空間を定義し、その制約内でどの因果構造が観察パターンを生成できるかを見る** というモデルです。

詳しくは [`docs/constraint_first_capom.md`](docs/constraint_first_capom.md) を参照してください。

## Streamlit app

メインのStreamlitアプリはResearch Mode専用です。

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

アプリでは以下を行います。

```text
trade-off preset selection
-> constrained random sampling
-> M1-M5 causal simulation
-> observed pattern matching
-> scenario ranking
-> accepted parameter ranges
-> CSV download
```

手動パラメータスライダーは、メインアプリから意図的に外しています。

## CAPOMとは

CAPOMは、Pattern-Oriented Modelling (POM) と Agent-Based Modelling (ABM) を土台にしつつ、野外で直接測りにくい潜在トレードオフを、複数の観察可能パターンで制約するためのワークフローです。

| Approach | Short definition | Main question |
|---|---|---|
| Ordinary ABM | ルールを作って、パターンが出るかを見る | この個体ルールからどんな集団パターンが出るか |
| POM | 見えるパターンに合うモデルを探す | 複数の観察パターンを再現できるモデルか |
| Constraint-first CAPOM | 先に潜在パラメータ空間を生態学的に制約し、その中で因果構造を比較する | 観察パターンを再現できる因果構造と潜在パラメータ範囲はどれか |

重要なのは、野外データを単なる「入力値」として扱わないことです。野外データは、モデルが再現すべき **observable patterns** です。モデルは、見えないパラメータを証明する機械ではなく、観察パターンと矛盾しない潜在パラメータ範囲と因果シナリオを絞るための **generative filter** です。

## Five CAPOM Layers

1. **Observable patterns**
   野外で測れるもの: `nectar_guide`, `flower_size`, Bombus frequency, small pollinator frequency, effective selfing rate, fruit set, germination, `Fis`, `Fst`, `Ne`, `Pst`, island distance.

2. **Latent trade-offs**
   野外で直接測りにくいもの: `guide_cost`, `outcrossing_benefit`, `selfing_benefit`, `inbreeding_depression`, `drift_strength`, `small_pollinator_efficiency`, `direct_pollinator_guide_benefit`, `cost_of_waiting_for_pollinators`.

3. **Ecological constraints**
   パラメータ間の生態学的制約: 自殖利益と近交弱勢の関係、小型送粉者効率と自殖利益の関係、ガイド維持コストと他殖利益の関係など。

4. **Causal simulations**
   M1-M5 の候補因果構造: direct pollinator effect, selfing-mediated effect, direct + mediated, common island cause, drift/null.

5. **Pattern matching**
   simulated patterns と observed patterns を比較し、scenario ranking と latent-parameter filtering を行う。

## Latent causal generative model layer

The repository distinguishes three layers:

1. **Biological generator**
   `attraction_trait_model` defines individual plant agents, environments, provisional latent parameters, reproduction probabilities, fitness components, inheritance helpers, and diagnostics for attraction-trait evolution.

2. **CAPOM evaluation**
   `constraint_abm` and the Campanula example workflows compare simulated outputs with observed field/literature patterns, then filter plausible latent parameter ranges.

3. **Latent causal generative framing**
   `causal_model` represents alternative causal structures, trade-off presets, parameter constraints, pathway switches, direct effects, mediated effects, common-cause explanations, and drift/null explanations.

The Campanula / Izu Islands case is the first worked example. Bombus loss, selfing increase, and nectar-guide reduction may overlap in the field, but that overlap is not treated as direct causal proof. The causal layer asks which candidate structures can generate the same observable pattern overlap while also matching additional patterns such as flower size, herkogamy, Fis, Fst, Ne, and pollinator composition.

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

## Candidate causal structures

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

> We did not manually tune latent parameters to reproduce the observed island pattern. Instead, we first defined biologically motivated trade-off ranges and parameter-to-parameter constraints, sampled latent benefit/cost parameters from this constrained space, and then evaluated which causal structures could generate the observed ecological, reproductive, and genetic patterns.

日本語:

> 本研究では、観察パターンに合うように潜在パラメータを手動調整するのではなく、まず生態学的に動機づけられたトレードオフ範囲とパラメータ間制約を定義し、その制約付き空間から利益・コストパラメータをサンプリングした。そのうえで、どの因果構造が観察された生態・繁殖・遺伝パターンを生成できるかを評価した。
