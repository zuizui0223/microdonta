# Inoue-series literature values and next-observation (NOV) result

This note records the empirical facts from the Inoue series that are safe to cite
for the Campanula worked example, and separates them from values that still need
primary-PDF transcription. The worked example is the Izu Islands *Campanula
microdonta* system; older papers may refer to the broader *C. punctata* complex
or compare island *C. microdonta* with mainland *C. punctata*.

Exact per-island numeric tables are not reproduced here. Empty numeric cells in
the CSV files mean "source-known but not yet transcribed", not zero and not
absence of evidence.

## Primary sources

- Inoue, K. & Amano, M. 1986. Evolution of *Campanula punctata* Lam. in the Izu
  Islands: changes of pollinators and evolution of breeding systems. *Plant
  Species Biology* 1(1): 89-97. doi:10.1111/j.1442-1984.1986.tb00018.x
- Inoue, K. 1988. Pattern of breeding-system change in the Izu Islands in
  *Campanula punctata*: bumblebee-absence hypothesis. *Plant Species Biology*
  3(2): 125-128. doi:10.1111/j.1442-1984.1988.tb00178.x
- Inoue, K. 1990a. Evolution of mating systems in island populations of
  *Campanula microdonta*: pollinator availability hypothesis. *Plant Species
  Biology* 5(1): 57-64. doi:10.1111/j.1442-1984.1990.tb00192.x
- Inoue, K. 1990b. Dichogamy, sex allocation, and mating system of *Campanula
  microdonta* and *C. punctata*. *Plant Species Biology* 5(2): 197-203.
  doi:10.1111/j.1442-1984.1990.tb00179.x
- Inoue, K. & Kawahara, T. 1990. Allozyme differentiation and genetic structure
  in island and mainland Japanese populations of *Campanula punctata*
  (Campanulaceae). *American Journal of Botany* 77: 1440-1448. Genetic
  endpoint values require separate source confirmation before use as y_obs.

## Source-confirmed empirical structure

These facts justify the current directional gradients. They are not a complete
numeric dataset.

| Quantity | Source-confirmed statement | RACH role |
|---|---|---|
| Taxon/provenance | Izu island system is treated here as *C. microdonta*; older literature may use the broader *C. punctata* complex, and mainland Honshu *C. punctata* is a comparison context. | provenance |
| Pollinator assemblage | Honshu: *Bombus diversus*; Oshima: *Bombus ardens* plus halictid bees; Niijima, Kozushima, and Hachijo: halictid bees. Bumblebees are absent from the Izu Islands except Oshima. | x_obs / input_context |
| Flower size | Island flowers were reported smaller than mainland flowers; adaptation to smaller pollinators was proposed as a possible explanation, not demonstrated. Exact per-island corolla values require PDF transcription. | supports an island-vs-mainland flower-size contrast; not a source-confirmed monotonic distance slope |
| Breeding system, 1986/1988 | Honshu mostly highly self-incompatible; Oshima mixed but mostly self-incompatible in later summary; Izu islands except Oshima largely self-compatible. | supports selfing/outcrossing gradient |
| Mating system, 1990a | Honshu and Oshima are self-incompatible and obligately outcrossing; Toshima and Niijima are self-compatible and largely outcrossing; Miyake and Hachijo are self-compatible and predominantly inbreeding. | current y_obs as directional selfing/outcrossing gradient |
| Dichogamy, 1990b | Staminate-phase duration differs among mating-system classes; male reproductive effort decreases with estimated selfing rate. This is dichogamy/sex-phase timing evidence, not a measured static herkogamy endpoint. | hypothesis_prediction / future observation, not y_obs |
| Allozyme/outcrossing, 1990 | Mainland and island populations form differentiated genetic groups; outcrossing estimates are higher in mainland/Oshima groups, intermediate in northern self-compatible islands, and lower in southern predominantly inbreeding islands. Genetic diversity within island populations decreases with distance from the mainland. | independent population-genetic context; not trait-specific W/F/E |

## Current y_obs consequence

The current ABC acceptance target deliberately remains narrow. The historical
pattern names ending in `_distance` are **legacy implementation labels**, not a
claim that the cited primary papers estimated a continuous linear response to
geographic distance.

- `selfing_distance`: interpret as an ordered mating-system contrast across the
  declared mainland/island comparison: mainland/Oshima are predominantly
  self-incompatible/outcrossing, northern self-compatible islands remain largely
  outcrossing, and southern self-compatible islands are predominantly inbreeding.
  Source: Inoue 1990a/1990b and Inoue & Kawahara 1990, with 1986/1988
  breeding-system corroboration. Do not describe this as a source-fitted
  monotonic distance law.
- `flower_size_distance`: interpret only as the source-confirmed island-versus-
  mainland smaller-flower contrast from Inoue & Amano 1986. The source summary
  does not establish a monotonic per-island flower-size decline with distance.

Pollinator assemblage is observed context (`x_obs`), not an output target.
Herkogamy, nectar-guide intensity, Fis/He, bagging seed set, and modern
visitation rates remain future/NOV candidates until directly measured or
independently source-confirmed.

## Next-observation value (NOV)

The current admissible region is broad because y_obs has only two source-confirmed
directional gradients. NOV candidates should therefore target independent
observations that can split mechanisms rather than adding unmeasured rows to
`observed_target`.

| Priority | Candidate | Why it matters |
|---|---|---|
| 1 | Dichogamy / delayed-selfing geometry across intermediate islands | Tests the selfing-syndrome mechanism without pretending that static herkogamy is already measured. |
| 2 | Nectar-guide quantification | Direct planned own-field observation for the guide-attracts-Bombus switch. |
| 3 | Independent genetic structure (Fis/He/Fst) | Separates selfing-generated proxy signals from independent drift/structure evidence. |
| 4 | Bagging/autonomous selfing and seed set | Tests reproductive assurance; should enter only after measured values and uncertainty are recorded. |
| 5 | Modern pollinator visitation | Updates x_obs or becomes a separate target only under a clearly specified measurement question. |

This is a resolvability statement, not a claim of causal truth. Adding unsupported
observed targets would make A_epsilon look sharper while reducing epistemic
validity.
