# シマホタルブクロのネクターガイド進化ABM

シマホタルブクロ / `Campanula punctata` 系の島嶼集団で、送粉者環境、自殖、近交弱勢、遺伝的多様性、ネクターガイド退化をつなぐための仮説探索アプリです。

このABMは、実データを入れて予測するモデルではなく、実データと比較するための仮説生成器です。野外で直接一点推定しにくい送粉効率やガイド維持コストは、`Robustness` タブで範囲を振って、どの条件で観察パターンに近い傾向が出るかを見ます。

## 設計思想

このABMは一点予測器ではなく、伊豆諸島のネクターガイド勾配を説明する進化仮説デバッガーです。実測値をそのまま答えとして入れるのではなく、近交弱勢、送粉効率、ガイド維持コストなど野外で一点推定しにくい値を動かし、どの条件で観察パターンと比較できるシナリオが生じるかを調べます。

モデル内の変数は次の層に分けます。

| 層 | 役割 | 例 |
|---|---|---|
| 原因 | 環境側の入力 | `bombus_frequency`, `pollinator_environment`, 島距離、集団サイズ |
| 制約 | 形質や遺伝子流動の状態 | `flower_size`, `herkogamy`, `pollen_ovule_ratio`, `migration_rate` |
| 繁殖過程 | 繁殖モードの分岐 | 他殖確率、自殖確率、繁殖失敗 |
| 適応度 | 次世代親選択に使う値 | 種子数、発芽率、近交弱勢、ネクターガイド維持コスト |
| 診断 | 結果解釈に使う値 | `selfing_syndrome_score`, `island_syndrome_score`, `Fis`, `Fst`, `Pst` |

重要な原則として、`selfing_syndrome_score` と `island_syndrome_score` は原因変数でも選択圧でもなく、結果を読むための診断指標です。適応度計算には直接入れず、「自殖シンドロームらしい形質群が同じ向きに動いているか」「島嶼化に伴う複数の兆候が同時に出ているか」を確認するために使います。詳しい方針は [`docs/abm_design_policy.md`](docs/abm_design_policy.md) にまとめています。

## 使い方

Streamlit:

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

TenSnap:

```powershell
cd abm
python -m pip install -r requirements.txt
python shimahotarubukuro_tensnap_abm.py
```

TenSnap renderer/client から `ws://localhost:8765` に接続してください。

## 反映した仮説

通常状態: 本土

マルハナバチあり -> 高効率の他殖が成立 -> ネクターガイド維持 -> 遺伝的多様性維持

島状態: 伊豆諸島

大島は `Bombus ardens` あり。神津島・八丈島などはマルハナバチ不在として扱います。

マルハナバチ不在・コハナバチ類優占 -> 他殖機会が不安定化 -> 繁殖保証として自殖が重要になる -> でも自殖は近交弱勢を生む -> 完全自殖には移行しにくい -> 他殖チャンスを残す個体ではネクターガイドが維持される -> 他殖チャンスがほぼない場所ではネクターガイドが退化する

## 送粉者効率とネクターガイド

`bombus_frequency` と `small_bee_frequency` を横並びに直接使うのではなく、次のように分けました。

| 変数 | 意味 |
|---|---|
| `pollinator_environment` | 訪花頻度、花粉接触、結実率などから作る「他殖できる環境」 |
| `bombus_frequency` | マルハナバチの寄与率。0 は不在、1 は十分にいる状態。旧 `bombus_present` は後方互換の別名 |
| `bombus_pollination_efficiency` | マルハナバチがいた場合の送粉効率。文献上は高い想定 |
| `other_pollinator_efficiency` | コハナバチ類などの送粉効率。不確実なので感度分析対象 |
| `bombus_guide_dependence` | マルハナバチがネクターガイドを利用する強さ |
| `other_pollinator_guide_use` | その他の送粉者がネクターガイドを利用する強さ |

モデル式:

```text
pollinator_efficiency
  = bombus_frequency * bombus_pollination_efficiency
    + (1 - bombus_frequency) * other_pollinator_efficiency

guide_alignment
  = bombus_frequency * bombus_guide_dependence
    + (1 - bombus_frequency) * other_pollinator_guide_use

outcross_probability
  = base_outcross
    + pollinator_environment
      * pollinator_efficiency
      * (pollinator_environment_outcross_effect
         + guide_alignment * nectar_guide)
```

つまり、神津島・八丈島では `bombus_frequency = 0` なので、マルハナバチの高い送粉効率やガイド利用は計算に入りません。大島では `Bombus ardens` がいるため、Bombus チャンネルが残ります。TenSnap ABM では 0/1 だけでなく 0.35 のような中間値も扱えるため、在/不在から頻度勾配へ拡張できます。

## 自殖シンドローム

自殖シンドロームは、単に自殖率が高いことではなく、他殖に関わる花形質の縮小・自家受粉しやすい形態・雄機能の低下を含む複合的な変化として扱います。

診断として追跡する項目:

| 変数 | 野外データ |
|---|---|
| `flower_size` | 花冠サイズ、花冠長、開口径など |
| `herkogamy` | 葯と柱頭の距離、接触しやすさ |
| `pollen_ovule_ratio` | P/O比。雄機能配分の指標 |
| `selfing_syndrome_score` | 自殖率上昇、他殖低下、ネクターガイド・花サイズ・herkogamy・P/O低下をまとめた診断値 |

このスコアは、いまは適応度に直接入れていません。まずは「ネクターガイド退化が自殖シンドローム全体と同じ向きに出ているか」を確認する診断として使います。

## アイランドシンドローム

島では送粉者相の欠落だけでなく、創始者効果、遺伝的浮動、移入経緯、交雑履歴、集団間遺伝構造も効きます。そのため、次の列を診断として入れています。

| 変数 | 野外データ |
|---|---|
| `migration_rate` | 近似的な移入・遺伝子流動 |
| `Fis_observed` | SNPからの近交度 |
| `Fst_observed` | SNPからの集団分化 |
| `Pst_nectar_guide` | 斑点面積率の集団間分化 |
| `Pst_flower_size` | 花サイズの集団間分化 |
| `admixture_index` | 交雑・移入履歴の目安 |
| `colonization_history` | 移入経緯、植栽、交雑可能性のメモ |
| `island_syndrome_score` | 送粉者環境低下、Bombus不在、自殖能力上昇、遺伝的多様性低下、隔離をまとめた診断値 |

Pst/Fst-Qst は、ABMの選択ルールには直接入れていません。結果の解釈、つまり「ネクターガイド差が選択で説明できそうか、それとも移入・創始者効果・漂流で説明できそうか」を見る診断です。まず Pst と Fst で探索し、強いシグナルが出た形質を common garden / half-sib / reciprocal transplant で Qst に近づけるのが現実的です。

## フィットネスと近交弱勢

自殖は近交弱勢を通じて発芽率を下げます。二重カウントを避けるため、`inbreeding_load` は自殖種子の有効発芽率に一回だけ反映しています。

```text
selfing_fitness
  = seed_set_selfing * effective_germination_selfed
    - guide_cost * nectar_guide

effective_germination_selfed
  = min(germination_selfed, germination_outcrossed - inbreeding_load)
```

## 野外で優先して取りたいデータ

最小セット:

| 優先 | データ | 目的 |
|---|---|---|
| 1 | 訪花者の種類、訪花頻度、花粉接触、訪花後結実率 | `pollinator_environment` と `bombus_frequency` を作る |
| 2 | 袋掛け結実率、自然結実率、人工自殖/他殖 | `selfing_ability`、自殖依存、繁殖保証を推定 |
| 3 | 自殖種子と他殖/自然種子の発芽率差 | `inbreeding_load` |
| 4 | 斑点面積率 | `nectar_guide` |
| 5 | 花サイズ、葯-柱頭距離、P/O比 | 自殖シンドローム確認 |
| 6 | SNP | `Fis`、`Fst`、移入・交雑履歴、遺伝的多様性 |

サンプル目安:

- 最小探索: 各地域 1 集団、各集団 30 個体、訪花観察 20 時間
- 仮説検証: 各地域 2-3 集団、各集団 40-60 個体、訪花観察 30-50 時間、人工自殖/他殖 20-30 母株
- ABMパラメータ推定まで狙う: 各地域 3 集団以上、各集団 60 個体前後、訪花観察 50 時間以上、SNP は各集団 30 個体以上

## 文献根拠

- Inoue, K. & Amano, M. 1986. Evolution of `Campanula punctata` Lam. in the Izu Islands: Changes of Pollinators and Evolution of Breeding Systems. Plant Species Biology. https://cir.nii.ac.jp/crid/1363388843410604032
- Inoue, K. 1989. Pattern of Breeding-System Change in the Izu Islands in `Campanula punctata`: Bumblebee-Absence Hypothesis. Plant Species Biology. https://zendy.io/title/10.1111/j.1442-1984.1988.tb00178.x
- Nagano, Y. et al. 2014. Changes in pollinator fauna affect altitudinal variation of floral size in a bumblebee-pollinated herb. Ecology and Evolution. https://pmc.ncbi.nlm.nih.gov/articles/PMC4228614/
- Leonard, A. S. & Papaj, D. R. 2011. "X" marks the spot: The possible benefits of nectar guides to bees and plants. Functional Ecology. https://doi.org/10.1111/j.1365-2435.2011.01885.x
- Lunau, K. et al. 2006. Visual targeting of components of floral colour patterns in flower-naive bumblebees. Naturwissenschaften. https://doi.org/10.1007/s00114-006-0105-2
- Sicard, A. & Lenhard, M. 2011. The selfing syndrome: a model for studying the genetic and evolutionary basis of morphological adaptation in plants. Annals of Botany. https://doi.org/10.1093/aob/mcr023
- Shimizu, K. K. & Tsuchimatsu, T. 2022. The selfing syndrome and beyond: diverse evolutionary consequences of mating system transitions in plants. https://pmc.ncbi.nlm.nih.gov/articles/PMC9149797/
- Wright, S. I. et al. 2013. Evolutionary consequences of self-fertilization in plants. Proceedings of the Royal Society B. https://pmc.ncbi.nlm.nih.gov/articles/PMC3652455/
- Baker's law / island reproductive assurance overview: https://www.nature.com/articles/s41598-024-62065-4
