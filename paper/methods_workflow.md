# Methods workflow for publication

## Overview

This workflow describes how to use the repository as a manuscript-ready example of a constraint-aware pattern-oriented ABM.

The aim is to infer plausible ecological mechanisms from overlapping field patterns when key drivers such as fitness, costs, and trade-offs are not directly observable.

## Step 1. Define the observable patterns

Create a table of empirical patterns for each population or island.

Required columns for the Campanula example:

```text
population
island_distance
nectar_guide
flower_size
bombus_frequency
other_pollinator_frequency
selfing_ability
open_fruit_set
bagged_fruit_set
seed_set
germination_rate
Fis
Fst
Pst_nectar_guide
Ne
```

The first validation can use ordinal patterns rather than exact values.

Example target:

```text
nectar_guide: Mainland > Oshima > Kozu/Niijima > Hachijo
bombus_frequency: Mainland > Oshima > Kozu/Niijima ≈ Hachijo
selfing_ability: Mainland < Oshima < Kozu/Niijima < Hachijo
flower_size: Mainland > Oshima > Kozu/Niijima > Hachijo
```

## Step 2. Define latent parameters

Latent parameters are parameters that are difficult to measure directly in the field.

Examples:

```text
guide_cost
outcrossing_benefit
inbreeding_depression
drift_strength
small_pollinator_efficiency
bombus_guide_dependence
future_reproductive_benefit
```

These are not fixed at a single value in the first analysis. They are explored across broad biologically plausible ranges.

## Step 3. Define ecological constraints

Constraints determine how latent mechanisms can operate.

Examples:

```text
flower_size → guide_cost and small-pollinator access
herkogamy → autonomous selfing probability
island_distance → migration_rate and Bombus frequency
effective_population_size → drift strength
genetic diversity → response to selection
```

## Step 4. Run hypothesis scenarios

Run multiple scenarios rather than one model.

Recommended scenarios:

```text
H1: Pollinator loss only
H2: Pollinator loss + reproductive assurance through selfing
H3: Pollinator loss + inbreeding depression
H4: Pollinator loss + Ne decline / drift
H5: Pollinator loss + small-pollinator adaptation + selfing syndrome
```

Each scenario should be run with multiple random seeds.

## Step 5. Match simulated patterns to observed patterns

### 5.1 Ordinal matching

Evaluate whether the simulated pattern has the same direction as the observed island gradient.

Example:

```text
observed: Mainland > Oshima > Kozu > Hachijo
simulated: Mainland > Oshima > Kozu > Hachijo
score = match
```

### 5.2 Numeric matching

When empirical values become available, calculate a distance metric.

```python
error = sum((observed - simulated) ** 2)
```

Multiple patterns can be combined with weights.

```python
total_error = (
    w1 * error_nectar_guide
    + w2 * error_selfing
    + w3 * error_flower_size
    + w4 * error_genetic_diversity
)
```

## Step 6. Sensitivity analysis

Explore how results change when latent parameters are varied.

Important parameters:

```text
guide_cost
inbreeding_depression
pollinator_efficiency
small_pollinator_efficiency
drift_strength
selfing_ability
migration_rate
```

Outputs:

- threshold maps
- response surfaces
- tornado plots or ranked sensitivity scores
- parameter regions that maintain or lose nectar guides

## Step 7. ABC-like parameter filtering

Use simulation-based filtering when enough empirical patterns are available.

Workflow:

```text
sample parameter set
run ABM
calculate distance to observed patterns
retain if distance < tolerance
summarize retained parameter distributions
```

This allows estimation of plausible ranges for hidden parameters such as `guide_cost`, `inbreeding_depression`, and `drift_strength`.

## Step 8. Null and negative-control models

Run null models to test whether the observed pattern can appear without the proposed mechanism.

Null models:

```text
N1: drift only
N2: pollinator loss only
N3: selfing only
N4: random trait loss
```

If null models reproduce the target pattern, the focal mechanism is not strongly supported. If only compound scenarios reproduce the target pattern, this supports a multi-process explanation.

## Step 9. Report model outputs

Minimum outputs for manuscript figures:

1. Conceptual five-layer framework diagram
2. Island gradient diagram
3. Scenario comparison of nectar-guide trajectories
4. Threshold map for nectar-guide maintenance
5. Sensitivity analysis summary
6. Pattern matching scores across scenarios
7. Null model comparison

## Step 10. Generalization beyond Campanula

After the Campanula case study, the same workflow can be applied to:

- urban ecological systems with hidden mortality and movement costs
- alpine plants with phenological mismatch and frost risk
- biological invasions with hidden establishment costs
- island systems with dispersal costs and reproductive assurance
- animal behaviour systems with predation-risk and foraging-benefit trade-offs

The general method is not specific to pollination. It is designed for any system in which observable patterns are produced by hidden trade-offs and ecological constraints.
