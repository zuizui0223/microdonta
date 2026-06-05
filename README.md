# シマホタルブクロ ネクターガイド進化 ABM

TenSnap/Python ABM と Streamlit ダッシュボードです。斑点面積率、訪花頻度、自殖能力、近交荷重、種子数、発芽率、SNP 指標に対応する説明変数を入れています。

## Streamlit app

Streamlit アプリは `streamlit_app.py` です。実データが揃うまでは表の仮値を編集し、CSV upload/download で穴埋めできます。
`Fieldwork plan` タブには、野外で取るデータの目安と、調査項目チェックリストがあります。
`Threshold sweep` タブでは、`selfing_ability` と `pollinator_environment` をグリッド探索し、ネクターガイド維持に必要な他殖可能環境と、その境界での自殖率/他殖率を確認できます。ネクターガイドへの選択だけは、`bombus_present` と `bombus_guide_dependence` でマルハナバチ依存性を分けています。

ローカル実行:

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Streamlit Community Cloud では、このリポジトリを選び、main file path に `streamlit_app.py` を指定してください。

## TenSnap ABM

```powershell
cd abm
python -m pip install -r requirements.txt
python shimahotarubukuro_tensnap_abm.py
```

TenSnap renderer/client から `ws://localhost:8765` に接続してください。

## 仮説

通常状態、本土:

マルハナバチあり -> 他殖が成立 -> ネクターガイド維持 -> 遺伝的多様性維持

島状態、大島:

`Bombus ardens` とコハナバチ類あり -> 他殖機会は本土とは違うがゼロではない -> ネクターガイド維持の余地が残る

島状態、大島以外:

マルハナバチ不在・コハナバチ類優占 -> 他殖機会が不安定化 -> 繁殖保証として自殖が重要になる -> でも自殖は近交弱勢を生む -> 完全自殖には移行できない -> 他殖チャンスを残す個体ではネクターガイドが維持される -> 他殖チャンスがほぼない場所ではネクターガイドが退化する

## 先行文献による根拠

- Inoue & Amano (1986) は、本州・大島・その他の伊豆諸島で `Campanula punctata` の送粉者相と繁殖システムが異なることを示した。本州では主な送粉者が `Bombus diversus`、大島では `Bombus ardens` とコハナバチ類、神津島・八丈島などではコハナバチ類が優占する。つまり、伊豆諸島すべてでマルハナバチがいないわけではなく、大島は例外である。
- Inoue (1989) は、伊豆諸島でマルハナバチが大島を除いて存在せず、コハナバチ類が優占すること、そして本州・大島では多くが自家不和合、他の島ではほぼ自家和合であることを報告し、マルハナバチ不在による送粉効率低下が繁殖システム進化を促すという仮説を支持した。
- Nagano et al. (2014) は、`C. punctata var. hondoensis` で地域ごとのマルハナバチ相が花サイズに対応し、花と送粉者サイズの一致が雄性適応度に影響することを示した。これは送粉者による花形質選択の根拠になる。
- Leonard & Papaj (2011)、Lunau et al. (2006) および nectar guide 実験研究は、ネクターガイドがハナバチ、とくに Bombus の探索・定位・花内での姿勢を変え、花粉移動効率や植物適応度に影響しうることを示す。
- 自殖は送粉者や交配相手が少ないとき繁殖保証として有利になりうるが、近交弱勢、ヘテロ接合度低下、集団間遺伝子流動低下を伴う。したがって、島では「完全自殖」ではなく、他殖機会と自殖保証の混合戦略が維持される可能性がある。

References:

- Inoue, K. & Amano, M. 1986. Evolution of `Campanula punctata` Lam. in the Izu Islands: Changes of Pollinators and Evolution of Breeding Systems. Plant Species Biology. https://cir.nii.ac.jp/crid/2051714791885953664
- Inoue, K. 1989. Pattern of Breeding-System Change in the Izu Islands in `Campanula punctata`: Bumblebee-Absence Hypothesis. Plant Species Biology. https://cir.nii.ac.jp/crid/2051714791885965312
- Nagano, Y. et al. 2014. Changes in pollinator fauna affect altitudinal variation of floral size in a bumblebee-pollinated herb. Ecology and Evolution. https://pmc.ncbi.nlm.nih.gov/articles/PMC4228614/
- Leonard, A. S. & Papaj, D. R. 2011. "X" marks the spot: The possible benefits of nectar guides to bees and plants. Functional Ecology. https://doi.org/10.1111/j.1365-2435.2011.01885.x
- Lunau, K. et al. 2006. Visual targeting of components of floral colour patterns in flower-naive bumblebees. Naturwissenschaften. https://doi.org/10.1007/s00114-006-0105-2
- Wright, S. I. et al. 2013. Evolutionary consequences of self-fertilization in plants. Proceedings of the Royal Society B. https://pmc.ncbi.nlm.nih.gov/articles/PMC3652455/
- Barrett, S. C. H. 1996. The reproductive biology and genetics of island plants. https://barrett.eeb.utoronto.ca/publications/files/2020/06/schb_134.pdf

## 野外で取るデータ

最低限ほしいデータ:

| データ | 目的 | 最低サンプル感 |
|---|---|---|
| 斑点面積率 `nectar_guide` | 目的形質。個体ごとのネクターガイド退化/維持を見る | 各集団 30-50 個体、各個体 3-5 花 |
| 訪花者の種類・訪花回数・花粉接触 | `pollinator_environment`, `bombus_present`, `bombus_guide_dependence` を作る | 各集団 20-30 時間以上、時間帯を分散 |
| 訪花後の結実率・種子数 | 他殖機会が fitness に効くかを見る | 各集団 30-50 花以上 |
| 袋掛け結実率 | `selfing_ability`。送粉者なしで自殖できるか | 各集団 30-50 花以上 |
| 人工自殖・人工他殖の種子数と発芽率 | `inbreeding_load` と fitness 成分 | 各集団 20-30 母株、各処理 1-3 花 |
| 自然条件の発芽率 | 自然繁殖の fitness baseline | 各集団 20-30 母株 |
| SNP/ゲノムデータ | `Fis`, `Fst`, 遺伝的多様性、集団分化 | 各集団 20-30 個体以上 |

強く推奨:

- 本土・大島・神津島・八丈島を同じ年に調査する。
- 開花期の前半・中盤・後半を分ける。
- 訪花観察は晴天/曇天、午前/午後を偏らせない。
- 同じ個体で「斑点面積率」「自然結実」「袋掛け」「人工交配」「SNP」をできるだけ結びつける。

どれほどデータがほしいか:

- 最小セット: 各地域 1 集団、各集団 30 個体、訪花観察 20 時間。仮説の方向を見るだけ。
- まともに検定するセット: 各地域 2-3 集団、各集団 40-60 個体、訪花観察 30-50 時間、交配実験 30 母株程度。
- ABM のパラメータ推定まで狙うセット: 各地域 3 集団以上、各集団 60 個体前後、訪花観察 50 時間以上、人工自殖/他殖/袋掛け/自然結実を同一個体群で揃え、SNP は各集団 30 個体以上。

優先順位は、1. 訪花者組成、2. 袋掛け結実率、3. 自殖/他殖の発芽率差、4. 斑点面積率、5. SNP です。SNP は強いですが、最初からなくても ABM の主要仮説は動かせます。

## 野外データ対応

| ABM変数 | 野外データ | アプリでの扱い |
|---|---|---|
| `nectar_guide` | 斑点面積率 | 個体形質、chart |
| `pollinator_environment` | 訪花者組成・訪花頻度・花粉接触から作る他殖可能環境 | slider / CSV |
| `bombus_present` | マルハナバチ在/不在 | slider / CSV |
| `bombus_guide_dependence` | マルハナバチがネクターガイドを利用する強さ | slider / CSV |
| `other_pollinator_guide_use` | コハナバチ類などがネクターガイドを利用する強さ | slider / CSV |
| `selfing_ability` | 袋掛け結実率 | slider / CSV |
| `inbreeding_load` | 自殖種子と自然/他殖種子の発芽率差 | slider / CSV |
| `seed_set_selfing` | 自殖時の種子数 | CSV |
| `seed_set_outcrossing` | 他殖時の種子数 | CSV |
| `germination_selfed` | 自殖種子の発芽率 | CSV |
| `germination_outcrossed` | 自然/他殖種子の発芽率 | CSV |
| `fitness` | 種子数・発芽率 | chart |
| `Fis` | SNP | chart |
| `Fst` | SNP | chart |
| `migration_rate` | 島間遺伝子流動の近似 | slider / CSV |
| `Pst_nectar_guide` | 集団間/集団内の斑点面積率分散 | 診断 |
| `Pst_flower_size` | 集団間/集団内の花サイズ分散 | 診断 |
| `admixture_index` | SNP などからの交雑・混合度 | 診断 |
| `colonization_history` | 移入経緯・植栽・創始者効果のメモ | 診断 |

## 送粉者環境とネクターガイド選択

ABM では、送粉者を `bombus_frequency` と `small_bee_frequency` のように横並びで直接使うのではなく、まず `pollinator_environment` として「他殖できる環境」を表します。これは訪花者の種類、訪花頻度、花粉接触、滞在時間、結実率などから作る合成変数です。

一方で、ネクターガイドへの選択はマルハナバチに強く関係すると仮定します。そのため、`bombus_present` と `bombus_guide_dependence` を別に置きます。

```text
outcross_probability
  = base_outcross
  + pollinator_environment
    * (pollinator_environment_outcross_effect
       + guide_alignment * nectar_guide)

guide_alignment
  = bombus_present * bombus_guide_dependence
    + (1 - bombus_present) * other_pollinator_guide_use
```

つまり、自殖率・繁殖保証・実際の近交度は送粉者不足全体に関係し、ネクターガイドの維持/退化はその中でも Bombus がいるか、Bombus がどれだけ guide を利用するかに強く関係する、という整理です。

## Threshold の考え方

`mean_nectar_guide = 0.5` は、可視化上の形質値の目安です。本当に見たい threshold は、どの `selfing_ability`、どの送粉者頻度、どの `inbreeding_load` の組み合わせでネクターガイドが維持から退化へ切り替わるかです。

Streamlit の `Threshold sweep` では、各 `selfing_ability` について `pollinator_environment` を 0-1 で動かし、最終世代の `mean_nectar_guide` が指定した `guide criterion` 以上になる最小値を出します。これを「維持境界」として見ます。確率シミュレーションなので、`replicates` を増やして平均した境界を見るのが基本です。

注意: 神津島・八丈島では `bombus_present = 0` が生態学的前提です。したがって、これらの島で `bombus_guide_dependence` を sweep するのは「もしマルハナバチがいたら」という反実仮想です。現実的な threshold は、`pollinator_environment`、実測 `outcrossing_rate`、または両者をまとめた effective outcrossing opportunity として読むべきです。

近交弱勢は入っています。ただし、`inbreeding_load` は自殖種子の発芽率低下として fitness に一回だけ反映します。自殖時の fitness は概念的には次の形です。

```text
selfing_fitness = seed_set_selfing * effective_germination_selfed - guide_cost * nectar_guide
effective_germination_selfed = min(germination_selfed, germination_outcrossed - inbreeding_load)
```

以前の実装では `germination_selfed` を低くしたうえでさらに `(1 - inbreeding_load)` を掛けており、近交弱勢が二重に効く可能性があったため修正しました。

## Pst / Fst-Qst と移入・交雑履歴

`Fst-Qst` は、形質分化が中立的な集団分化だけで説明できるか、それとも選択を考えるべきかを見るために重要です。ただし Qst には遺伝分散成分が必要なので、まずは表現型分散から `Pst` として始めます。

このアプリでは、`Pst/Fst diagnostics` タブで `Pst` と `Fst` を比べます。これは ABM の fitness ルールには直接入れません。役割は、ABM の結果を解釈するときの診断です。

- `Pst > Fst`: ネクターガイドや花サイズに分化選択がかかった可能性。
- `Pst ≈ Fst`: 漂流、創始者効果、移入経緯、集団構造だけでも説明できる可能性。
- `Pst < Fst`: 安定化選択、制約、強い遺伝子流動などの可能性。

移入経緯と交雑履歴はかなり重要です。島ごとのネクターガイド差が、現在の送粉者環境への適応ではなく、過去の移入元、創始者効果、園芸由来、近縁分類群との交雑で生じた可能性があるからです。したがって、`colonization_history` と `admixture_index` を野外データ表に入れています。

Qst に進むなら、common garden、reciprocal transplant、母株/家系構造を持つ種子採集が必要です。まず Pst で探索し、強いシグナルが出た形質に絞って Qst へ進むのが現実的です。
