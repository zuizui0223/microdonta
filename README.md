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
