# RACH: Restricted Admissible Causal Hypotheses

**RACH** stands for **Restricted Admissible Causal Hypotheses**.

RACH は、生態学的制約を先に定義し、制約内で複数の因果仮説をシミュレーションし、観察パターンと照合することで **「観察パターンを生成できる因果仮説の制約集合」** を推定する生成推論フレームワークです。

このリポジトリは、シマホタルブクロ *Campanula punctata* 伊豆諸島集団を worked example として実装したプロトタイプです。

---

## One-sentence definition

> **RACH identifies the restricted set of admissible causal hypotheses that can generate observed ecological patterns under biologically motivated constraints.**

> **RACHは、生態学的制約のもとで観察パターンを生成可能な因果仮説だけを抽出するフレームワークである。**

---

## Core workflow

```
1. 生態学的原理に基づく制約文法を定義  (ecological constraint grammar)
       ↓
2. 制約内で潜在パラメータをランダムサンプリング  (constrained prior sampling)
       ↓
3. 因果スイッチ状態をサンプリング  (binary switch state sampling)
       ↓
4. シミュレーション  (proxy / stochastic ABM)
       ↓
5. 観察パターンとの照合  (ABC gradient-POM acceptance)
       ↓
6. 受理サンプルからスイッチ事後確率を推定  (Switch Posterior Inference)
```

**重要**: パラメータを手動で調整して観察データに合わせるのではなく、  
**先に生態学的に許容されるパラメータ空間を定義し、その制約内でどの因果経路が観察パターンを生成できるかを推論する。**

---

## Switch Posterior Inference — the core original contribution

RACHの最も重要な推論モジュールです。

### 従来手法との違い

従来のABCや因果推論では、候補モデル M1, M2, … Mk を事前に定義し、どのモデルがデータに最もフィットするかを比較します（モデル選択）。

RACHのSwitch Posterior Inferenceは**モデルを事前に固定しません**。代わりに、各生物学的メカニズムを独立な潜在二値変数（スイッチ）として扱い、その**同時事後分布**を推定します。

```
P(スイッチ ON | 観察パターンが一致) を各経路について推定する
```

これにより：
- M1〜M5のどれにも収まらない経路の組み合わせも自動的に発見できる
- 複数経路が同時に活性化している場合（共活性化）を同定できる
- どの経路が支配的か（高Bayes因子）を直接評価できる

### 5つの生物学的スイッチ

| スイッチ | 経路 | 生物学的問い |
|---|---|---|
| **S1** `guide_attracts_bombus` | 誘引形質 → Bombus誘引 → 他殖 | ネクターガイドがBombus訪花を因果的に増加させるか？ |
| **S2** `selfing_syndrome_active` | 送粉者不足 → 繁殖保証 → 自殖症候群共進化 | 送粉者減少が、自殖・花柱離隔・花サイズの共進化を引き起こすか？ |
| **S3** `island_isolation_common_cause` | 島の孤立 → 複数形質への共通上流原因 | 島の孤立が（Bombusの有無を経由せず）直接複数形質を同時に変化させるか？ |
| **S4** `drift_drives_guide_loss` | 小集団 → 遺伝的浮動 → ガイド消失 | ガイド消失は自然選択ではなく遺伝的浮動が主因か？ |
| **S5** `small_pollinator_substitution` | ハナバチ類 → Bombus代替 → 繁殖保証圧の緩和 | 小型送粉者がBombusを代替し自殖圧を抑制するか？ |

### アルゴリズム

```python
for each draw:
    θ ~ constrained_ecological_prior()      # 生態学的制約内でパラメータサンプリング
    s ~ Bernoulli(0.5) for each switch      # 各スイッチを独立にサンプリング（無情報事前分布）
    y = simulate(θ, s)                      # プロキシまたはABMでシミュレーション
    if pattern_match(y, observed_POM) >= ε: # 勾配POMと照合
        accept(θ, s)

P(switch ON | accepted) = accepted_ON / n_accepted  # スイッチ事後確率
BF = posterior_odds / prior_odds                    # Bayes因子
```

**Bayes因子の解釈**:
- BF > 3: そのスイッチがONであることが観察パターンを支持
- BF < 1/3: そのスイッチがONであることが観察パターンに反する
- 1/3 < BF < 3: 証拠不十分

---

## Pattern of Moment (POM) — gradient-based

RACHのPOMは、**集団名に依存しない勾配方向パターン**です。

### なぜペアワイズ比較でなく勾配か

「八丈島の方が大島より自殖率が高い」という文献記述は有用ですが、これは特定の2集団の比較です。RACHが検証したい仮説は「アイランドシンドローム」——**孤立距離に沿った形質変化の勾配そのもの**——です。

```
POM: 孤立距離が増加するにつれて…
  nectar_guide  が単調減少する  (gradient_slope: negative)
  selfing_rate  が単調増加する  (gradient_slope: positive)
  herkogamy     が単調減少する  (gradient_slope: negative)
  Fis           が単調増加する  (gradient_slope: positive)
  nectar_guide  のランク順が降順 (rank_order: decreasing)
  selfing_rate  のランク順が昇順 (rank_order: increasing)
```

この6パターンが現在のABC受理基準です。

### 集団名なしの連続的孤立勾配シミュレーション

シミュレーションは「mainland / Oshima / Kozushima / Hachijo」という固定集団名を使いません。  
`isolation ∈ [0, 1]` を唯一の入力として、N点の環境を生成します。

```python
# isolation から全環境変数を導出
primary_pollinator_frequency    = max(0, 0.80 - 0.94 * isolation)
community_pollinator_abundance  = 0.88 - 0.635 * isolation
effective_population_size       = 1.00 - 0.765 * isolation
# ...
```

これにより、伊豆諸島以外の島嶼系にも同じフレームワークがそのまま適用できます。

---

## データ設計 — input_context と response_target の分離（Issue #7）

RACHは2種類のデータを明確に区別します。

| ファイル | 役割 | 内容 | ABCに使うか |
|---|---|---|---|
| `ecological_context.csv` | **input_context** | 孤立距離・送粉者頻度・有効集団サイズなど、シミュレーションに「投入」する環境変数 | **使わない** — 投入値を予測値と照合するのは循環論法 |
| `observed_patterns.csv`（`role=response_target`） | **response_target** | ネクターガイド・自殖率・花柱離隔・Fis の勾配方向など、シミュレーションが**再現すべき**パターン | **使う** — ABC採否基準 |

`observed_patterns.csv` の各行には `role` 列があります：

```
role = response_target  ← ABCの採否に使う（形質の勾配パターン）
role = input_context    ← ABCに使わない（予測変数、例: primary_pollinator_frequency）
```

`evaluate_patterns()` は `role=input_context` 行を**自動的にスキップ**します（ディフェンシブガード付き）。`response_target_patterns()` を呼べば、ABCに渡すべき行だけを取得できます。

### 循環論法の防止

`primary_pollinator_frequency`（Bombus頻度）は `ecological_context.csv` からシミュレーションに**注入**される値です。これを同時にABCの採否基準にすると、スイッチの状態に関係なく常にマッチしてしまいます（Bombus頻度はシミュレーションで生成されるのではなく与えられるため）。

`role=input_context` のラベルはこの構造的欠陥を**機械的に**防ぎます。

---

## 送粉者変数の設計（3機能的役割）

Environment は送粉者を**機能的役割**で分類します（種名に依存しない汎用設計）。

| 変数 | 機能的役割 | 伊豆系での対応 |
|---|---|---|
| `primary_pollinator_frequency` | **誘引形質応答型・高効率** — ネクターガイドを強く使い、一訪花あたりの花粉移送効率が高い | Bombus (マルハナバチ) |
| `background_pollinator_frequency` | **形質非応答・背景送粉者** — ガイドへの応答は低いが他殖に貢献する | Halictidae (コハナバチ) |
| `community_pollinator_abundance` | **群集全体のアバンダンス** — 両チャネルを乗算するスケーラー | 全体的な送粉者豊富度 |

他殖確率の式:

```
P_outcross = base_rate
  + community_pollinator_abundance × [
      primary_freq × primary_eff × (1 + guide_response × G)       ← S1が機能する経路
      + background_freq × bg_eff × access(F) × (1 + bg_guide_response × G)
    ]
```

**S1の識別可能性**: ネクターガイド `G` が他殖に影響するのは主に primary チャンネル（`guide_response = 0.7`）を通じてであり、background チャンネルへの影響は微小（`bg_guide_response = 0.1`）。よってガイドの低下が他殖を大きく下げるかどうかはS1（primary pollinator の存在）に依存し、S1が識別可能になる。

---

## 生態学的制約文法（パラメータ制約）

シミュレーション前に、生態学的に許容されないパラメータ組み合わせを除外します。

| 制約 | 内容 | 根拠 |
|---|---|---|
| **C1** | `selfing_benefit - inbreeding_depression >= -0.30` | 自殖が極端に不利な場合、自殖症候群の進化は起きない（Lloyd 1979） |
| **C2** | `NOT (bg_eff > 0.55 AND selfing_benefit > 0.55)` | 背景送粉者が十分な代替機能を持つなら繁殖保証圧は低く、高い自殖利益との同時成立は矛盾 |
| **C3** | `NOT (guide_cost > 0.20 AND outcrossing_benefit < 0.05 AND guide_benefit > 0.80)` | コスト高・他殖利益ゼロでガイドが著しく送粉者を引きつけるという組み合わせは内部矛盾 |
| **C4** | `background_pollinator_efficiency < 0.80` | 背景送粉者の効率が主要送粉者以上になれば機能的区別が崩壊（Larsson 2005） |

各制約には文献引用が付いており、「手で合わせた」のではなく生態学的原理から導出されています。

---

## M1-M5 候補因果構造（参照用）

Switch Posterior Inferenceがスイッチの同時事後分布を推定するのに対し、M1-M5は特定のスイッチ組み合わせに名前を付けたもので、事後推論の結果を解釈する際の参照ラベルとして使います。

```
M1  direct_pollinator_to_guide=1  (S1のみ)
M2  selfing_mediation=1           (S2のみ)
M3  S1=1, S2=1                    (S1+S2)
M4  island_common_cause=1         (S3のみ ― 孤立が単一上流原因)
M5  drift_null=1                  (S4のみ ― 浮動ヌル)
```

Switch Posterior Inference は M1-M5 に収まらない組み合わせも自動的に扱います。

---

## Streamlit app

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

アプリの主要タブ:

| タブ | 内容 |
|---|---|
| **Switch Posterior Inference** | 5スイッチの事後確率とBayes因子をABC拒絶法で推定 (proxy / stochastic ABM) |
| **Causal Structure Comparison** | M1-M5固定構造のシミュレーション比較 |
| **Parameter Space** | 受理サンプルの潜在パラメータ分布の可視化 |

手動パラメータスライダーは意図的に除外しています。

---

## Repository structure

```
attraction_trait_model/     個体ベース生物モデル（送粉・適応度・遺伝）
causal_model/               因果構造・スイッチ・パラメータ制約・ABC推論
  simulation.py             決定論的プロキシシミュレーション（S1-S5スイッチロジック）
  switch_inference.py       Switch Posterior Inference（ABCリジェクション）
  parameter_constraints.py  生態学的制約文法（C1-C4、文献引用付き）
  switches.py               PathwaySwitches定義
examples/campanula_izu/     伊豆諸島worked example
  data/observed_patterns.csv  勾配POMパターン定義（role列: response_target / input_context）
  data/ecological_context.csv 集団の生態的文脈データ（input_context; ABC採否には使わない）
  proxy_simulation.py         連続孤立勾配シミュレーション（env_from_isolation）
  pattern_evaluator.py        勾配パターン評価（gradient_slope, rank_order; role filterつき）
  observed_data.py            データローダー（response_target_patterns / load_ecological_context）
  test_ecological_invariants.py  生態不変量テスト（5項目、input_context除外を含む）
streamlit_app.py            メインアプリ
```

---

## RACH and existing methods

| Existing method | Role inside RACH |
|---|---|
| ABM | candidate causal hypotheses を生成するシミュレーター |
| POM | 複数観察パターンでモデルを制約する評価原理 |
| ABC-rejection | 距離関数と受理閾値に基づく潜在パラメータ領域の近似 |
| Ecological constraint grammar | シミュレーション前に許容パラメータ空間を定義する制約規則 |

RACHの独自性は、これらを**因果仮説の事後確率推定**という目的のもとで統合し、かつ「モデルを先に固定しない」Switch Posterior Inference を核に据えた点にあります。

---

## Manuscript framing

> We propose RACH, a Restricted Admissible Causal Hypotheses framework. RACH first defines an admissible latent trade-off space using ecological constraint grammar, then simulates candidate causal hypotheses within that space using a switch-based generative model, and finally infers the posterior probability of each biological pathway being active via ABC rejection — without pre-specifying causal structures.

日本語:

> 本研究では、RACH（Restricted Admissible Causal Hypotheses）を提案する。RACHは、生態学的制約文法によって許容潜在トレードオフ空間を先に定義し、スイッチベースの生成モデルでその空間内を探索し、ABCリジェクション法によって各生物学的経路の事後確率を推定する。因果構造を事前に固定する必要がない点が、従来の構造比較アプローチとの本質的な違いである。

---

See also:

- [Constraint-first CAPOM workflow](docs/constraint_first_capom.md)
- [Latent causal generative model](docs/latent_causal_generative_model.md)
- [Generative model vs path model](docs/generative_model_vs_path_model.md)
- [ABM design policy](docs/abm_design_policy.md)
- [Methods workflow](paper/methods_workflow.md)
- [ODD protocol draft](paper/odd_protocol_draft.md)
- [Campanula Izu worked example](examples/campanula_izu/README.md)
