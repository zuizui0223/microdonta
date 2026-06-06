# ODD protocol draft

This document follows the ODD structure: Overview, Design concepts, and Details.

## 1. Overview

### 1.1 Purpose

The purpose of the model is to explore the ecological and evolutionary conditions under which a floral visual signal, the nectar guide, is maintained, reduced, or lost along an island isolation gradient.

More generally, the model demonstrates a constraint-aware pattern-oriented ABM framework for linking observable field patterns to latent ecological trade-offs.

The focal case study is *Campanula punctata* / shimahotarubukuro in the Izu Islands.

### 1.2 Entities, state variables, and scales

#### Entities

- Plant agents
- Island environment
- Pollinator environment

#### Plant state variables

- `nectar_guide`: strength or area ratio of internal floral guide pattern, scaled 0-1
- `neutral_diversity`: proxy for individual-level neutral genetic diversity, scaled 0-1
- `fitness`: reproductive contribution to the next generation
- `seed_output`: seed production component
- `germination`: germination component
- `reproduction_mode`: outcrossing, selfing, or failed

Future plant variables:

- `flower_size`
- `herkogamy`
- `pollen_ovule_ratio`
- family or maternal line ID for Qst-like extension

#### Environmental variables

- `pollinator_environment`
- `bombus_frequency`
- `bombus_pollination_efficiency`
- `other_pollinator_efficiency`
- `bombus_guide_dependence`
- `other_pollinator_guide_use`
- `selfing_ability`
- `inbreeding_load`
- `guide_cost`
- `seed_set_selfing`
- `seed_set_outcrossing`
- `germination_selfed`
- `germination_outcrossed`
- `migration_rate`

Future environmental variables:

- `island_distance`
- `isolation_index`
- `effective_population_size`
- `island_area`
- `drift_strength`

### 1.3 Process overview and scheduling

Each generation proceeds as follows:

1. Evaluate outcrossing probability for each plant.
2. Determine whether the plant reproduces by outcrossing, selfing, or fails.
3. Calculate seed output and germination.
4. Apply inbreeding depression to selfed offspring through reduced effective germination.
5. Subtract nectar-guide maintenance cost.
6. Use fitness-proportional sampling to select parents of the next generation.
7. Inherit nectar-guide value with mutation.
8. Update neutral diversity using reproduction mode, migration rescue, and drift.
9. Record observable and diagnostic outputs.

## 2. Design concepts

### 2.1 Basic principles

The model is based on three principles:

1. Field observations are visible patterns rather than direct measurements of mechanism.
2. Fitness, costs, future benefits, and trade-offs are often latent and uncertain.
3. Generative models can test which latent mechanisms reproduce multiple observable patterns simultaneously.

### 2.2 Emergence

Population-level nectar-guide decline, increased selfing rate, reduced genetic diversity, and syndrome-like diagnostic scores emerge from individual-level reproduction, inheritance, selection, and drift.

### 2.3 Adaptation

Plant agents do not make explicit decisions. Apparent adaptation emerges through fitness differences among individuals with different nectar-guide values under different pollinator and reproductive environments.

### 2.4 Objectives

The implicit objective of each plant is reproductive contribution to the next generation. Fitness is calculated from seed output, germination, inbreeding effects, and nectar-guide cost.

### 2.5 Learning

No learning is currently implemented.

### 2.6 Prediction

The model is not intended as a point-prediction model. It predicts qualitative and quantitative patterns under alternative ecological scenarios.

### 2.7 Sensing

Plants do not sense the environment explicitly. Environmental variables influence reproduction probabilities and fitness calculations.

### 2.8 Interaction

Plant agents interact indirectly through competition for representation in the next generation via fitness-proportional sampling.

Future versions may include explicit pollen transfer or spatial neighborhood mating.

### 2.9 Stochasticity

Stochasticity occurs in:

- outcrossing success
- selfing success
- parent sampling
- mutation of nectar-guide values
- genetic drift in neutral diversity

### 2.10 Collectives

No explicit collectives are implemented. Populations are interpreted as island or site-level populations.

### 2.11 Observation

The model records:

- mean nectar guide
- selfing rate
- outcrossing rate
- failed reproduction rate
- mean fitness
- seed output
- germination
- mean neutral diversity
- Fis proxy
- Fst proxy
- selfing syndrome score
- island syndrome score

## 3. Details

### 3.1 Initialization

The default model initializes a Mainland-like population.

Initial plant values:

- `nectar_guide`: beta-distributed values, scaled 0-1
- `neutral_diversity`: beta-distributed values biased toward high diversity

Default environment values are drawn from the Mainland preset.

### 3.2 Input data

The model can be run without empirical input using presets. Empirical input can later be supplied as observed patterns for pattern matching.

Potential field inputs:

- nectar-guide area ratio
- flower size
- herkogamy
- P/O ratio
- Bombus visit rate
- other pollinator visit rate
- bagged fruit set
- open fruit set
- seed set
- germination rate
- Fis
- Fst
- Pst
- Ne
- island distance

### 3.3 Submodels

#### 3.3.1 Outcrossing probability

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

#### 3.3.2 Selfing probability

Current version:

```text
selfing_probability = selfing_ability
```

Planned constraint-aware version:

```text
selfing_probability = selfing_ability * (1 - herkogamy)
```

#### 3.3.3 Fitness

```text
if outcrossing:
    seed_output = seed_set_outcrossing
    germination = germination_outcrossed
elif selfing:
    seed_output = seed_set_selfing
    germination = min(germination_selfed,
                      germination_outcrossed - inbreeding_load)
else:
    seed_output = low value
    germination = low value

fitness = seed_output * germination - guide_cost * nectar_guide
```

Planned constraint-aware cost:

```text
guide_penalty = guide_cost * nectar_guide * flower_size
```

#### 3.3.4 Inheritance and mutation

Offspring inherit nectar-guide value from sampled parents with Gaussian mutation.

#### 3.3.5 Neutral diversity

Neutral diversity increases slightly after outcrossing, decreases after selfing, and changes stochastically under drift. Migration rescue pulls low-diversity populations toward a higher reference value depending on `migration_rate`.

Planned Ne-aware drift:

```text
drift_strength = base_drift / sqrt(effective_population_size)
```

#### 3.3.6 Diagnostic scores

Selfing syndrome and island syndrome scores are diagnostics only. They are not used in the fitness function.

## 4. Planned extensions

- Add `effective_population_size`
- Add `island_distance` / `isolation_index`
- Make `flower_size` constrain guide cost and small-pollinator access
- Make `herkogamy` constrain selfing probability
- Add scenario comparison module
- Add sensitivity analysis module
- Add pattern-matching score
- Add ABC-like parameter filtering
- Add ODD export function
