# Manuscript outline

## Working title

**When hidden costs shape visible traits: a constraint-aware pattern-oriented ABM framework for ecological evolution**

Case-study title option:

**Inferring the conditions for floral signal loss from island gradients: a constraint-aware ABM of Campanula nectar guides**

## Core message

Field data usually provide observable patterns rather than direct measurements of the causal mechanisms that generated them. Trait values, interaction frequencies, reproductive success, germination, and genetic structure are visible outcomes of multiple overlapping ecological and evolutionary processes. In contrast, fitness components, trait-maintenance costs, future reproductive benefits, inbreeding depression, dispersal costs, and drift contributions are often difficult to measure directly in the field.

This study proposes a **constraint-aware pattern-oriented ABM framework** that treats such hidden quantities as uncertain latent parameters. The model explores which combinations of latent parameters and ecological constraints can reproduce multiple observable field patterns simultaneously.

## Conceptual contribution

The framework extends pattern-oriented modeling by explicitly separating five layers:

1. **Observable pattern layer**
   - measurable field patterns such as trait values, interaction frequencies, reproductive success, germination, genetic diversity, Fis, Fst, Pst, Ne, and spatial gradients.

2. **Latent trade-off layer**
   - hidden or difficult-to-measure quantities such as fitness, trait-maintenance cost, future reproductive benefit, inbreeding depression, drift contribution, mortality risk, dispersal cost, and interaction efficiency.

3. **Constraint layer**
   - ecological, morphological, spatial, demographic, and genetic constraints that restrict how latent mechanisms can operate.

4. **Generative ABM layer**
   - individual agents, ecological interactions, reproduction, inheritance, mutation, selection, and drift.

5. **Pattern-matching layer**
   - comparison between simulated outputs and observed field patterns to rank plausible mechanisms.

## Case study

The first worked example is the Izu Islands system of *Campanula punctata* / shimahotarubukuro.

The focal empirical question is:

```text
Under what ecological and evolutionary conditions does the nectar guide decline or disappear along an island isolation gradient?
```

The expected island gradient is:

```text
Mainland
↓
Oshima
↓
Kozu / Niijima
↓
Hachijo
```

Potentially overlapping field patterns:

```text
island isolation ↑
migration_rate ↓
effective population size ↓
drift strength ↑
Bombus frequency ↓
small pollinator relative importance ↑
selfing ability ↑
flower size ↓
nectar guide ↓
```

## Research gap

Previous studies on *Campanula punctata* in the Izu Islands have shown changes in pollinator fauna, breeding system, floral size, self-compatibility, and autonomous selfing. However, the evolution of an internal floral visual signal, the nectar guide, has not been explicitly framed as a response to overlapping island syndrome, selfing syndrome, pollinator loss, genetic drift, and hidden fitness trade-offs.

The key gap is not merely whether nectar guides differ among islands, but **under which conditions nectar guides should be maintained, reduced, or lost**.

## Methods overview

### Step 1: Define observable patterns

Observable patterns are field-measurable quantities:

- nectar-guide area ratio
- flower size
- Bombus visit rate
- other pollinator visit rate
- bagged fruit set
- open-pollinated fruit set
- seed set
- germination rate
- Fis
- Fst
- Pst
- Ne
- island distance / isolation index

### Step 2: Define latent parameters

Latent parameters are hard to estimate directly from a single field season:

- nectar-guide maintenance cost
- outcrossing benefit
- future reproductive benefit
- inbreeding depression
- drift strength
- small-pollinator efficiency
- Bombus guide dependence
- cost of waiting for pollinators

### Step 3: Define ecological constraints

Constraints limit how mechanisms operate:

- flower size constrains pollinator access and guide cost
- herkogamy constrains autonomous selfing
- island distance constrains migration rate
- effective population size constrains drift strength
- genetic diversity constrains response to selection

### Step 4: Run scenario-based ABM

Hypothesis scenarios:

```text
H1: Pollinator loss only
H2: Pollinator loss + reproductive assurance through selfing
H3: Pollinator loss + inbreeding depression
H4: Pollinator loss + Ne decline / drift
H5: Pollinator loss + small-pollinator adaptation + selfing syndrome
```

### Step 5: Match simulated and observed patterns

Initial matching can be ordinal:

```text
nectar_guide: Mainland > Oshima > Kozu/Niijima > Hachijo
Bombus_frequency: Mainland > Oshima > Kozu/Niijima ≈ Hachijo
selfing_ability: Mainland < Oshima < Kozu/Niijima < Hachijo
flower_size: Mainland > Oshima > Kozu/Niijima > Hachijo
```

Later matching can use numeric distances:

```python
error = sum((observed_pattern - simulated_pattern) ** 2)
```

### Step 6: Sensitivity analysis

Vary latent parameters across broad ranges:

- guide_cost
- inbreeding_depression
- pollinator_efficiency
- small_pollinator_efficiency
- drift_strength
- selfing_ability
- migration_rate

### Step 7: ABC-like parameter filtering

Sample parameter sets, run the ABM, calculate distance to observed patterns, and retain parameter sets that reproduce the observations.

```text
sample parameters
→ run ABM
→ calculate pattern distance
→ retain good-fitting parameter sets
→ infer plausible parameter regions
```

### Step 8: Null and negative-control models

Run minimal or null scenarios:

```text
null 1: drift only
null 2: pollinator loss only
null 3: selfing only
null 4: random trait loss
```

If null models reproduce the same pattern, selection-based explanations are weak. If only compound scenarios reproduce the observed island gradient, this supports a multi-process mechanism.

## Expected outputs

- threshold maps for nectar-guide maintenance
- scenario comparison plots
- sensitivity analysis summaries
- ranked mechanisms by pattern-matching score
- inferred plausible ranges for hidden parameters
- ODD protocol model description
- reproducible case-study example for the Izu Islands

## Manuscript structure

1. Introduction
   - Field data as overlapping patterns
   - Difficulty of directly measuring fitness, cost, and trade-offs
   - Need for generative modeling
   - Pattern-oriented modeling and ABM background
   - Proposed framework

2. Framework
   - Five-layer structure
   - Observable patterns vs latent mechanisms
   - Constraints and pattern matching

3. Case study system
   - *Campanula punctata* in the Izu Islands
   - Pollinator changes, selfing, floral size, and nectar-guide question

4. Model description
   - ODD protocol
   - Agents, state variables, submodels, scheduling

5. Simulation experiments
   - Hypothesis scenarios
   - Sensitivity analysis
   - Null models

6. Pattern matching and validation
   - Observed island gradient
   - Ordinal matching
   - Numeric distances
   - ABC-like parameter filtering

7. Discussion
   - Conditions for nectar-guide loss
   - Island syndrome and selfing syndrome as overlapping processes
   - Generality beyond pollination
   - Limitations and future data needs

8. Package / reproducibility
   - Code availability
   - Example dataset
   - Reusable functions
   - ODD export

## Candidate journals

- Ecological Modelling
- Journal of Theoretical Biology
- Methods in Ecology and Evolution, if the package and validation are strong enough
- Ecology and Evolution, if framed as case-study plus modeling framework

## Main claim for abstract

Field observations often reveal visible patterns but not the hidden trade-offs that generated them. We propose a constraint-aware pattern-oriented ABM framework that combines observable ecological, trait, reproductive, and genetic patterns with uncertain latent parameters such as fitness, maintenance cost, inbreeding depression, and drift contribution. Using *Campanula* nectar guides along an island isolation gradient as a worked example, we show how the framework can identify conditions under which floral signals are maintained, reduced, or lost.
