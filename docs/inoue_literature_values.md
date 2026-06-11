# Inoue-series literature values and next-observation (NOV) result

This note records (a) the *defensible* empirical values from the Inoue series that
can be cited for the Campanula worked example, and (b) the RACH next-observation
ranking computed on the current admissible region. It is provenance scaffolding
for the manuscript — **exact per-island numeric tables live in paywalled PDFs and
must be transcribed from the primary sources; they are NOT reproduced here, and no
per-island decimals have been invented.**

## Primary sources

- Amano, M. & Inoue, K. 1986. Evolution of *Campanula punctata* in the Izu
  Islands: changes of pollinators and evolution of breeding systems.
  *Plant Species Biology* 1: 89–97.
- Inoue, K. 1988. Patterns of breeding-system change in the Izu Islands in
  *Campanula punctata*: bumblebee-absence hypothesis.
  *Plant Species Biology* 3: 125–128.
- Inoue, K. 1990. Evolution of mating systems in island populations of
  *Campanula microdonta*: pollinator availability hypothesis.
  *Plant Species Biology* 5: 57–64.
- Inoue, K. 1990. Dichogamy, sex allocation and mating system of
  *Campanula microdonta* and *C. punctata*. *Plant Species Biology* 5 (page range
  to confirm from the primary PDF).
- Inoue, K. & Kawahara, T. 1990. Allozyme differentiation and genetic structure
  in island and mainland Japanese populations of *Campanula punctata*
  (Campanulaceae). *American Journal of Botany* 77: 1440–1448.

## Values that are defensible from the literature (multi-source corroborated)

These are the values used to justify the **direction** of the y_obs gradients.
Treat ranges as breeding-system-class summaries, not per-island measurements.

| Quantity | Value / direction | Notes |
|---|---|---|
| Outcrossing rate t — SI mainland & Oshima | **t ≈ 0.62–0.79** | obligately outcrossing (self-incompatible) |
| Outcrossing rate t — SC northern islands (Toshima, Niijima) | **t ≈ 0.37–0.57** | self-compatible, mixed mating |
| Outcrossing rate t — SC southern islands (Miyake, Hachijo) | **predominantly selfing** (low t, potentially autogamous) | self-compatible, inbreeding |
| Breeding system gradient | SI/outcross (Honshu, Oshima) → SC/largely-outcross (north) → SC/inbreeding (south) | — |
| Pollinator fauna | *Bombus diversus* (Honshu) → *B. ardens* + halictids (Oshima) → halictids only (Niijima, Kozushima, Hachijo) | this is **x_obs** (context) |
| Flower / corolla size | islands **<** mainland; smaller on more isolated islands | adaptation to smaller pollinators (Amano & Inoue 1986) |
| Dichogamy | protandrous; male phase precedes female (~2 days); secondary pollen presentation; stigma lobes recurve | the operative "herkogamy" is female-phase delayed-selfing geometry |

**Consequence for the worked example.** These confirm the two y_obs gradient
directions already in `observed_patterns.csv`:

- `selfing_distance`: selfing **increases** with isolation (t falls
  0.62–0.79 → 0.37–0.57 → predominantly selfing). Source: Inoue 1990.
- `flower_size_distance`: corolla size **decreases** with isolation.
  Source: Amano & Inoue 1986.

The exact per-island `observed_value` cells in
`data/independent_observations.csv` remain empty pending transcription from the
primary PDFs (Inoue 1990 PSB 5:57–64 for t; Inoue & Kawahara 1990 AJB
77:1440–1448 for per-island Fis; Amano & Inoue 1986 PSB 1:89–97 for corolla size).

## Next-observation value (NOV) — what to measure next

Computed on the current admissible region (proxy backend; baseline R_RACH ≈ 0.13,
D_RACH ≈ 3.5 of 4 — i.e. heavily degenerate, all four switches **unresolved**).
With only two correlated gradient observations the data cannot yet separate
H1–H4, so RACH flags every switch as a NOV target.

**Simulation NOV** (integrates over candidate outcomes — the trustworthy ranking;
expected ΔR = E[R(O∪q)] − R(O)):

| Rank | Candidate | ΔR | Target switch(es) |
|---|---|---|---|
| 1 | herkogamy / dichogamy gradient (intermediate islands) | **+0.14** | selfing_syndrome_active (S2) |
| 2 | nectar-guide quantification (guide-area spectrophotometry) | **+0.06** | guide_attracts_bombus (S1), S2 |
| 3 | Fis gradient (intermediate islands) | +0.02 | S2, island_isolation_common_cause (S3) |
| — | pollinator visitation, bagging, He, falsification candidates | ≤ 0 | (ambiguous outcomes — no expected gain) |

**Heuristic NOV** (ranks by current ambiguity only — less reliable) instead puts
pollinator-visitation and bagging on top; the discrepancy is itself informative:
the simulation shows those measurements do **not** resolve the switches they
target because both possible outcomes leave the admissible region similarly
degenerate.

### Reading

- The single most informative next observation is the **dichogamy / female-phase
  delayed-selfing gradient across intermediate islands** (resolves S2), followed
  by the **nectar-guide measurement** (the planned own-field data, resolving S1).
- Many candidates have NOV ≤ 0: adding them could keep or even worsen degeneracy
  because their outcomes are not discriminating under the current model. This is a
  genuine RACH result, not a defect — it tells you which fieldwork is worth the
  cost and which is not.
- This is a *resolvability* statement, not a claim of causal truth. Direct
  separation of H3 (direct selection) from H2 (selfing-mediated) still needs the
  manipulative / selection-gradient observations listed in
  `data/future_observations.csv`.
