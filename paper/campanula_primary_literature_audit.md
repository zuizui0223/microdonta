# Primary-literature audit for the Izu Islands Campanula example

## Scope

This audit fixes the publication wording for the prospective Campanula example.
It does **not** add a new empirical validation dataset or change the frozen RACH
benchmarks. The purpose is to separate what the historical primary sources
directly report from later causal interpretation.

Audit level: publisher abstracts/metadata plus source text exposed through
CiNii/NDL were checked for the qualitative claims used in the main manuscript.
The main text does not use exact per-island numeric tables. Any future use of
exact historical per-island values still requires transcription from the primary
PDF/table with page/table provenance.

## Taxonomic caution

The nomenclature changes across the series. Inoue & Amano (1986) and Inoue
(1988) discuss Izu material under *Campanula punctata*. Inoue (1990a, 1990b)
treats the Izu-island populations as *C. microdonta* and compares them with
mainland Honshu *C. punctata*. Inoue & Kawahara (1990) retains *C. punctata* in
the title while its genetic results support a distinct island group. The
manuscript therefore describes a historical Izu-island Campanula system and
states the nomenclatural shift explicitly rather than silently treating all
papers as using the same taxon concept.

## Source-by-source claim audit

### Inoue & Amano 1986

**Reference**: Inoue, K. & Amano, M. 1986. Evolution of *Campanula punctata*
Lam. in the Izu Islands: Changes of Pollinators and Evolution of Breeding
Systems. *Plant Species Biology* 1: 89–97.
DOI: `10.1111/j.1442-1984.1986.tb00018.x`.

**Directly supported qualitative claims**

- Mainland Honshu: *Bombus diversus* was the predominant pollinator.
- Oshima: *Bombus ardens* and halictid bees were reported.
- Niijima, Kozushima and Hachijo: halictid bees were reported as predominant
  pollinators.
- Island flowers were reported smaller than mainland flowers.
- Mainland plants were mostly highly self-incompatible; Oshima included both
  self-compatible and highly self-incompatible plants; Hachijo plants were
  self-compatible and potentially autogamous.
- Breakdown of dichogamy was discussed together with self-compatibility in the
  development of self-fertilizing ability in Hachijo material.

**Do not overstate**

- The statement that smaller island flowers *might* reflect adaptation to smaller
  pollinators is an interpretation proposed by the authors, not a demonstrated
  causal effect.
- The abstract does not establish a monotonic per-island flower-size decline as a
  function of geographic distance.

### Inoue 1988

**Reference**: Inoue, K. 1988. Pattern of Breeding-System Change in the Izu
Islands in *Campanula punctata*: Bumblebee-Absence Hypothesis. *Plant Species
Biology* 3: 125–128. DOI: `10.1111/j.1442-1984.1988.tb00178.x`.

**Directly supported qualitative claims**

- Bagging experiments were conducted in natural populations on six Izu islands
  and mainland Honshu.
- Most plants on Honshu and Oshima were self-incompatible, whereas almost all
  plants on surveyed Izu islands other than Oshima were self-compatible.
- Bumblebees were absent from the surveyed Izu islands except Oshima; halictid
  bees were dominant Campanula pollinators on the other islands.

**Interpretive boundary**

- The paper supports the bumblebee-absence explanation as a hypothesis from the
  observed breeding-system and pollinator pattern. It does not directly identify
  a RACH fecundity or establishment channel.

### Inoue 1990a

**Reference**: Inoue, K. 1990a. Evolution of Mating Systems in Island
Populations of *Campanula microdonta*: Pollinator Availability Hypothesis.
*Plant Species Biology* 5: 57–64.
DOI: `10.1111/j.1442-1984.1990.tb00192.x`.

**Directly supported qualitative claims**

- Mainland Honshu *C. punctata* and Oshima island populations were described as
  self-incompatible and obligately outcrossing.
- Toshima and Niijima populations were self-compatible but largely outcrossing.
- Miyake and Hachijo populations were self-compatible and predominantly
  inbreeding.
- Pollinator availability and inbreeding depression were proposed as an
  evolutionary explanation for the observed mating-system pattern.

**Do not overstate**

- These categories support ordered differences among population groups, not by
  themselves a fitted continuous law of selfing versus geographic isolation.

### Inoue 1990b

**Reference**: Inoue, K. 1990b. Dichogamy, Sex Allocation, and Mating System of
*Campanula microdonta* and *C. punctata*. *Plant Species Biology* 5: 197–203.
DOI: `10.1111/j.1442-1984.1990.tb00179.x`.

**Directly supported qualitative claims**

- Staminate-phase duration differed among mating-system classes.
- Male reproductive effort decreased with increasing estimated selfing rate.
- Sex allocation and ovary allocation differed among mating-system classes.

**RACH role**

This is useful evidence about mating-system-associated floral biology. It is not
a direct trait-specific measurement of total performance `W`, local reproduction
`F`, or establishment/reachability `E`.

### Inoue & Kawahara 1990

**Reference**: Inoue, K. & Kawahara, T. 1990. Allozyme Differentiation and
Genetic Structure in Island and Mainland Japanese Populations of *Campanula
punctata* (Campanulaceae). *American Journal of Botany* 77: 1440–1448.
DOI: `10.1002/j.1537-2197.1990.tb12554.x`.

**Directly supported qualitative claims**

- Allozyme data separated mainland and island population groups.
- Outcrossing estimates were higher in self-incompatible mainland/Oshima groups,
  intermediate in northern self-compatible island groups, and lower in southern
  island groups described as predominantly inbreeding.
- Genetic diversity within island populations decreased with distance from the
  mainland.

**RACH role**

Population-genetic structure and mating-system estimates are independent context
or future observations. They are not interchangeable with trait-specific `W`,
`F` or `E` and therefore cannot by themselves identify the theorem channel.

## Safe main-text synthesis

The historical series safely supports the following synthesis:

> Mainland and Izu-island Campanula populations differ in pollinator assemblage,
> flower size, breeding/mating system and population-genetic structure. The
> historical studies propose pollinator availability as an evolutionary
> explanation, but the published record does not provide trait-specific total
> performance plus a resolved vital-rate channel or a demonstrated stable proxy.

The manuscript should **not** compress this into “selfing and flower size change
monotonically with isolation distance” unless a source-specific quantitative
analysis is added. Internal pattern names such as `selfing_distance` and
`flower_size_distance` are legacy implementation labels for ordered contrasts,
not evidence that the primary literature estimated a continuous distance slope.
