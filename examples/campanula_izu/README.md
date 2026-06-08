# Campanula Izu Islands worked example

This directory will contain the first worked example for the constraint-aware pattern-oriented ABM framework.

## Biological question

Under what conditions does the nectar guide decline or disappear in island populations of *Campanula punctata* / shimahotarubukuro?

## Study gradient

The case study uses the Izu Islands as an isolation gradient.

```text
Mainland
↓
Oshima
↓
Kozu / Niijima
↓
Hachijo
```

## Observable patterns

The empirical data should be organized as observable patterns rather than as direct causal mechanisms.

Core patterns:

```text
nectar_guide
flower_size
Bombus frequency
other pollinator frequency
selfing ability
open fruit set
bagged fruit set
seed set
germination
Fis
Fst
Pst
Ne
island distance
```

## Latent mechanisms

Latent mechanisms are not directly measured. They are explored as uncertain model parameters.

```text
nectar-guide maintenance cost
outcrossing benefit
inbreeding depression
drift strength
small-pollinator efficiency
future reproductive benefit
cost of waiting for pollinators
```

## Hypothesis scenarios

```text
H1: Pollinator loss only
H2: Pollinator loss + reproductive assurance through selfing
H3: Pollinator loss + inbreeding depression
H4: Pollinator loss + Ne decline / drift
H5: Pollinator loss + small-pollinator adaptation + selfing syndrome
```

## First validation target

The first goal is not exact numerical prediction. It is ordinal pattern reproduction.

```text
nectar_guide: Mainland > Oshima > Kozu/Niijima > Hachijo
Bombus_frequency: Mainland > Oshima > Kozu/Niijima ≈ Hachijo
selfing_ability: Mainland < Oshima < Kozu/Niijima < Hachijo
flower_size: Mainland > Oshima > Kozu/Niijima > Hachijo
```

## Future files

Planned files:

```text
observed_patterns_template.csv
run_case_study.py
run_causal_structure_comparison.py
causal_structures_config.json
run_inoue_pattern_comparison.py
scenario_config.yaml
figures/
outputs/
```

`run_causal_structure_comparison.py` ranks the Issue #3 latent causal
structures M1-M5 against observable Campanula pattern targets. It uses a
deterministic proxy generator connected to `attraction_trait_model`
reproduction-probability functions, then converts simulated Oshima/Hachijo
values into pattern relations for scoring.

`causal_structures_config.json` records the Issue #4 pathway switches for each
M1-M5 causal structure. The same switch names are exposed by
`causal_model.switches.PathwaySwitches`.

`run_inoue_pattern_comparison.py` treats the Inoue-series literature information
as observed CAPOM patterns, runs H1-H5 ABM scenarios, and ranks scenarios by how
well their simulated outputs match Bombus frequency, flower size, selfing
ability, and pollinator-fauna patterns.

## Manuscript use

This example is designed to be used as the main case study for a methods-oriented manuscript. The broader framework should be presented as general, while this example demonstrates how the method works in a real ecological system.
