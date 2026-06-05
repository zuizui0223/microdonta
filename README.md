# シマホタルブクロ ネクターガイド進化 ABM

TenSnap で表示する Python ABM です。斑点面積率、訪花頻度、自殖能力、近交荷重、種子数、発芽率、SNP 指標に対応する説明変数を入れています。

## 実行

```powershell
cd abm
python -m pip install -r requirements.txt
python shimahotarubukuro_tensnap_abm.py
```

TenSnap renderer/client から `ws://localhost:8765` に接続してください。

## 仮説

通常状態、本土:

マルハナバチあり -> 他殖が成立 -> ネクターガイド維持 -> 遺伝的多様性維持

島状態、伊豆諸島:

マルハナバチ減少・不在 -> 他殖機会が不安定化 -> 繁殖保証として自殖が重要になる -> でも自殖は近交弱勢を生む -> 完全自殖には移行できない -> 他殖チャンスを残す個体ではネクターガイドが維持される -> 他殖チャンスがほぼない場所ではネクターガイドが退化する

## 先行文献による根拠

- Inoue & Amano (1986) は、本州・大島・その他の伊豆諸島で `Campanula punctata` の送粉者相と繁殖システムが異なることを示した。本州では主な送粉者が `Bombus diversus`、大島では `Bombus ardens` とコハナバチ類、神津島・八丈島などではコハナバチ類が優占し、八丈島個体は自家和合性・潜在的自動自殖性を示す。
- Inoue (1989) は、伊豆諸島でマルハナバチが大島を除いて存在せず、コハナバチ類が優占すること、そして本州・大島では多くが自家不和合、他の島ではほぼ自家和合であることを報告し、マルハナバチ不在による送粉効率低下が繁殖システム進化を促すという仮説を支持した。
- Nagano et al. (2014) は、`C. punctata var. hondoensis` で地域ごとのマルハナバチ相が花サイズに対応し、花と送粉者サイズの一致が雄性適応度に影響することを示した。これは送粉者による花形質選択の根拠になる。
- Leonard & Papaj (2011) および nectar guide 実験研究は、ネクターガイドがハナバチの探索・定位・花内での姿勢を変え、花粉移動効率や植物適応度に影響しうることを示す。
- 自殖は送粉者や交配相手が少ないとき繁殖保証として有利になりうるが、近交弱勢、ヘテロ接合度低下、集団間遺伝子流動低下を伴う。したがって、島では「完全自殖」ではなく、他殖機会と自殖保証の混合戦略が維持される可能性がある。

References:

- Inoue, K. & Amano, M. 1986. Evolution of `Campanula punctata` Lam. in the Izu Islands: Changes of Pollinators and Evolution of Breeding Systems. Plant Species Biology. https://cir.nii.ac.jp/crid/2051714791885953664
- Inoue, K. 1989. Pattern of Breeding-System Change in the Izu Islands in `Campanula punctata`: Bumblebee-Absence Hypothesis. Plant Species Biology. https://cir.nii.ac.jp/crid/2051714791885965312
- Nagano, Y. et al. 2014. Changes in pollinator fauna affect altitudinal variation of floral size in a bumblebee-pollinated herb. Ecology and Evolution. https://pmc.ncbi.nlm.nih.gov/articles/PMC4228614/
- Leonard, A. S. & Papaj, D. R. 2011. "X" marks the spot: The possible benefits of nectar guides to bees and plants. Functional Ecology. https://doi.org/10.1111/j.1365-2435.2011.01885.x
- Wright, S. I. et al. 2013. Evolutionary consequences of self-fertilization in plants. Proceedings of the Royal Society B. https://pmc.ncbi.nlm.nih.gov/articles/PMC3652455/
- Barrett, S. C. H. 1996. The reproductive biology and genetics of island plants. https://barrett.eeb.utoronto.ca/publications/files/2020/06/schb_134.pdf

## 野外データ対応

| ABM変数 | 野外データ | TenSnapでの扱い |
|---|---|---|
| `nectar_guide` | 斑点面積率 | Plant agent の色と chart |
| `bombus_frequency` | マルハナバチ訪花回数/時間 | slider |
| `small_bee_frequency` | 小型ハナバチ訪花回数/時間 | slider |
| `selfing_ability` | 袋掛け結実率 | slider |
| `inbreeding_load` | 自殖種子と自然種子の発芽率差 | slider |
| `seed_set_selfing` | 自殖時の種子数 | slider |
| `seed_set_outcrossing` | 他殖時の種子数 | slider |
| `germination_selfed` | 自殖種子の発芽率 | slider |
| `germination_outcrossed` | 自然/他殖種子の発芽率 | slider |
| `fitness` | 種子数・発芽率 | chart |
| `Fis` | SNP | chart |
| `Fst` | SNP | chart |
| `migration_rate` | 島間遺伝子流動の近似 | slider |

## TenSnap 表示

- Agents: `Plant`
  - `position`: 2D
  - `nectar_guide`: 0-1
  - `fitness`
  - `seed_output`
  - `germination`
  - `neutral_diversity`
  - `reproduction_mode`: `outcrossing` / `selfing` / `failed`
- Charts:
  - `mean_nectar_guide`
  - `guide_threshold_0_5`: threshold line at 0.5
  - `selfing_rate`
  - `outcrossing_rate`
  - `failed_rate`
  - `mean_fitness`
  - `seed_output`
  - `germination`
  - `mean_neutral_diversity`
  - `Fis`
  - `Fst`
- Presets:
  - `Mainland`
  - `Oshima`
  - `Kozu`
  - `Hachijo`
- CSV:
  - `Export CSV` action writes `shimahotarubukuro_results.csv`.

## Streamlit app

Streamlit アプリは `streamlit_app.py` です。実データが揃うまでは表の仮値を編集し、CSV upload/download で穴埋めできます。

ローカル実行:

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Streamlit Community Cloud では、このリポジトリを選び、main file path に `streamlit_app.py` を指定してください。
