# Attraction-trait evolution model design

Stage 1 design document for Issue #2:
**Roadmap: move from CAPOM workflow to a generative attraction-trait evolution model**.

## 1. Purpose

The current repository has two useful but distinct layers:

1. **CAPOM workflow / evaluation layer**
   - organizes observable field and literature patterns;
   - compares simulation outputs with those patterns;
   - ranks scenarios and filters plausible latent parameter ranges.

2. **Generative attraction-trait evolution model / model layer**
   - simulates how attraction traits are maintained, reduced, or lost;
   - treats individuals as evolving agents;
   - generates the outputs that CAPOM later evaluates.

This document specifies the second layer. It should guide a future
`attraction_trait_model/` module without replacing the existing
`constraint_abm/` CAPOM package.

The core biological question is:

```text
Under what combinations of pollinator loss, reproductive assurance through selfing,
inbreeding depression, genetic drift, small-pollinator replacement, and trait costs
is an attraction trait such as a nectar guide maintained, reduced, or lost?
```

## 2. Design principle

The model must not force nectar-guide loss by assumption.

It must allow at least four outcomes:

```text
nectar guide maintained
nectar guide reduced
nectar guide lost
intermediate stable state
```

These outcomes should emerge from the balance among:

- pollinator-mediated outcrossing benefit;
- reproductive assurance through selfing;
- inbreeding depression;
- nectar-guide maintenance cost;
- flower-size maintenance cost;
- replacement by small pollinators;
- drift and effective population size.

## 3. Separation from CAPOM

CAPOM remains the evaluation and inference workflow.

```text
observed field / literature patterns
-> compare with simulation outputs
-> rank scenarios
-> filter plausible latent parameter ranges
```

The attraction-trait model is the generator.

```text
individual traits + environment + latent trade-offs
-> outcrossing / selfing / failure
-> fitness
-> inheritance + mutation + drift
-> attraction-trait maintenance, reduction, or loss
```

Inoue-series literature patterns must be used as **external observed patterns**,
not as direct ABM inputs. They should evaluate model outputs, not determine them.

## 4. Proposed module structure

Future module:

```text
attraction_trait_model/
  __init__.py
  agents.py
  environment.py
  parameters.py
  reproduction.py
  fitness.py
  inheritance.py
  simulation.py
  diagnostics.py
  phase_diagram.py
  scenario_runner.py
```

`constraint_abm/` should remain the CAPOM layer. It can call this model, but the
new model should not depend on Streamlit or TenSnap.

## 5. Individual-level state variables

The future `PlantAgent` should carry evolving traits:

```python
nectar_guide: float       # G, attraction trait intensity, 0-1
flower_size: float        # F, floral display / corolla size, 0-1
herkogamy: float          # H, anther-stigma separation, 0-1
selfing_ability: float    # A, autonomous selfing capacity, 0-1
neutral_diversity: float  # D, neutral genetic diversity proxy, 0-1
```

Important shift from the current prototype:

```text
G, F, H, A, and D should all be individual-level states.
They should be inherited, mutate, and change across generations.
```

The current `constraint_abm.abm_core` evolves `nectar_guide` and neutral
diversity while treating `flower_size`, `herkogamy`, and `selfing_ability` as
population-level parameters. The new model should move these floral and mating
system traits into agents.

## 6. Environment-level variables

Each population / island should have an environment object:

```python
bombus_frequency: float
small_pollinator_frequency: float
pollinator_environment: float
migration_rate: float
effective_population_size: float
island_distance: float
```

These values can begin as ordinal or literature-derived proxies. Field data can
later replace them, but they should remain separate from latent trade-off
parameters.

Suggested interpretation:

- `bombus_frequency`: relative contribution of Bombus to effective pollination;
- `small_pollinator_frequency`: relative contribution of halictids and other
  smaller pollinators;
- `pollinator_environment`: overall opportunity for pollen-mediated outcrossing;
- `migration_rate`: gene-flow rescue among populations;
- `effective_population_size`: scale controlling drift;
- `island_distance`: ecological / spatial isolation proxy.

## 7. Latent parameters

Latent parameters are difficult to measure directly and should be explored by
CAPOM rather than treated as known truths.

```text
base_outcross_rate
bombus_efficiency
small_pollinator_efficiency
bombus_guide_use
small_pollinator_guide_use
inbreeding_depression
guide_cost
flower_size_cost
selfing_benefit
outcrossing_benefit
base_drift_strength
trait_correlation_strength
mutation_sd_guide
mutation_sd_flower_size
mutation_sd_herkogamy
mutation_sd_selfing_ability
```

These parameters define mechanisms. CAPOM later filters which ranges can
reproduce observable patterns.

## 8. Process rules

### 8.1 Outcrossing probability

Attraction traits should matter most when effective pollinators use them.

For individual `i`:

```text
P_outcross_i =
  base_outcross_rate
  + pollinator_environment * [
      bombus_frequency
      * bombus_efficiency
      * (1 + bombus_guide_use * G_i)
      +
      small_pollinator_frequency
      * small_pollinator_efficiency
      * small_pollinator_access(F_i)
      * (1 + small_pollinator_guide_use * G_i)
    ]
```

Where:

```text
G_i = nectar_guide
F_i = flower_size
```

Initial small-pollinator access function:

```python
small_pollinator_access = 1 - flower_size
```

This encodes the first-pass assumption that smaller pollinators may access or
effectively handle smaller flowers more easily. Later versions can replace this
with a fitted or flexible function.

Clamp `P_outcross_i` to `[0, 1]`.

### 8.2 Selfing probability

Selfing should occur only after outcrossing failure:

```text
P_self_i =
  (1 - P_outcross_i)
  * selfing_ability_i
  * (1 - herkogamy_i)
```

This explicitly links autonomous selfing to floral morphology.

Clamp `P_self_i` to `[0, 1]`.

### 8.3 Reproductive outcome

For each plant:

```text
draw outcrossing with probability P_outcross_i
if not outcrossing:
    draw selfing with probability P_self_i
if neither:
    reproduction failed
```

The model should record:

```text
outcrossing
selfing
failed
```

as individual-level reproduction modes each generation.

### 8.4 Fitness

Fitness should depend on reproductive output and trait-maintenance costs.

```text
if outcrossing:
    reproductive_output =
      seed_outcross
      * germination_outcross
      * (1 + outcrossing_benefit)

if selfing:
    reproductive_output =
      seed_self
      * germination_outcross
      * (1 - inbreeding_depression)
      * (1 + selfing_benefit)

if failed:
    reproductive_output = very_low
```

Trait costs:

```text
guide_cost_effect =
  guide_cost * nectar_guide * flower_size

flower_cost_effect =
  flower_size_cost * flower_size
```

Fitness:

```text
fitness =
  reproductive_output
  - guide_cost_effect
  - flower_cost_effect
```

Apply a small positive lower bound:

```python
fitness = max(fitness, 0.001)
```

Do **not** include `selfing_syndrome_score` or `island_syndrome_score` in
fitness. They are diagnostics only.

### 8.5 Inheritance and trait evolution

Children should inherit parental traits with mutation and drift:

```text
G_child = G_parent + mutation_G + drift_G
F_child = F_parent + mutation_F + drift_F
H_child = H_parent + mutation_H + drift_H
A_child = A_parent + mutation_A + drift_A
D_child = updated neutral diversity
```

Clamp all trait values to `[0, 1]`.

Mutation terms:

```text
mutation_G ~ Normal(0, mutation_sd_guide)
mutation_F ~ Normal(0, mutation_sd_flower_size)
mutation_H ~ Normal(0, mutation_sd_herkogamy)
mutation_A ~ Normal(0, mutation_sd_selfing_ability)
```

Drift terms should scale with effective population size.

### 8.6 Weak selfing-syndrome correlation

The model may include a weak, parameterized correlation among traits when
selfing is repeatedly favored:

```text
flower_size tends to decrease
herkogamy tends to decrease
nectar_guide tends to decrease
selfing_ability tends to increase
```

This must be controlled by `trait_correlation_strength` and should not make
nectar-guide loss inevitable.

Possible first implementation:

```text
syndrome_pressure =
  trait_correlation_strength
  * rolling_mean_selfing_advantage

G_child -= syndrome_pressure * small_coefficient_G
F_child -= syndrome_pressure * small_coefficient_F
H_child -= syndrome_pressure * small_coefficient_H
A_child += syndrome_pressure * small_coefficient_A
```

This pressure should be scenario-switchable so null and reduced models can turn
it off.

### 8.7 Drift from Ne

Drift strength should be linked to effective population size:

```text
drift_strength =
  base_drift_strength / sqrt(effective_population_size)
```

This allows island size and population size to affect random trait change and
neutral diversity.

## 9. Diagnostics

Each generation should output:

```text
generation
mean_nectar_guide
mean_flower_size
mean_herkogamy
mean_selfing_ability
selfing_rate
outcrossing_rate
failed_rate
mean_fitness
mean_neutral_diversity
Fis_proxy
Fst_proxy
selfing_syndrome_score
island_syndrome_score
guide_status
```

`guide_status` should be documented as provisional:

```text
maintained: mean_nectar_guide >= 0.60
reduced:    0.25 <= mean_nectar_guide < 0.60
lost:       mean_nectar_guide < 0.25
```

These thresholds are not biological conclusions. They are visualization and
phase-diagram labels that should be sensitivity-tested.

Diagnostic scores:

- `selfing_syndrome_score` summarizes whether selfing-related traits are moving
  together.
- `island_syndrome_score` summarizes island isolation, pollinator loss, drift,
  and diversity loss.

They are outputs for interpretation and CAPOM matching, not causal terms in
fitness.

## 10. Phase diagrams

A key goal is to produce condition boundaries.

First phase diagram:

```text
x = bombus_frequency
y = selfing_ability
output = final_mean_nectar_guide
```

Second phase diagram:

```text
x = guide_cost
y = inbreeding_depression
output = maintained_fraction
```

Expected table columns:

```text
x_value
y_value
mean_final_guide
sd_final_guide
maintained_fraction
mean_selfing_rate
mean_outcrossing_rate
```

The purpose is to identify:

```text
guide maintained region
guide reduced region
guide lost region
intermediate region
```

## 11. H1-H5 model scenarios

The model should support:

```text
H1_pollinator_loss_only
H2_pollinator_loss_plus_selfing
H3_pollinator_loss_plus_inbreeding_depression
H4_pollinator_loss_plus_drift
H5_compound_island_selfing_syndrome
```

Null models:

```text
drift_only
pollinator_loss_only
selfing_only
random_trait_loss
```

Scenario switches should control which mechanisms are active. They should not
be implemented by directly writing the observed output pattern into parameters.

## 12. Inoue literature comparison

Inoue-series literature patterns should be external validation targets:

```text
Bombus frequency:
Mainland > Oshima > Kozu/Niijima/Hachijo

Flower size:
Mainland > islands

Selfing ability:
Mainland < Oshima < Hachijo

Pollinator replacement:
Bombus-dominated mainland
-> mixed Oshima
-> halictid-dominated outer islands
```

Expected workflow:

```text
1. Define Mainland, Oshima, Kozu, Hachijo environments.
2. Define H1-H5 model scenarios.
3. Run the generative attraction-trait model.
4. Convert outputs to ordinal / categorical patterns.
5. Compare outputs with Inoue observed patterns using constraint_abm.matching.
6. Rank scenarios.
7. Save results to examples/campanula_izu/outputs/.
```

The current `examples/campanula_izu/run_inoue_pattern_comparison.py` performs
this comparison for the prototype ABM. A future
`run_inoue_model_comparison.py` should perform the same comparison using the
new `attraction_trait_model/` generator.

## 13. Implementation staging

### Stage 1: design documents

- This file: `docs/attraction_trait_model_design.md`.
- Keep Issue #2 as the roadmap.
- Define variables, process rules, diagnostics, scenarios, and phase diagrams.

### Stage 2: minimal model module

Create:

```text
attraction_trait_model/
  __init__.py
  agents.py
  environment.py
  parameters.py
  reproduction.py
  fitness.py
```

Add dataclasses only:

```text
PlantAgent
Environment
ModelParameters
```

Add pure functions:

```text
outcrossing_probability()
selfing_probability()
fitness()
```

### Stage 3: single-population simulation

- implement inheritance;
- implement mutation and drift;
- output generation-level diagnostics.

### Stage 4: phase diagrams

- implement two-axis sweeps;
- output maintained / reduced / lost regions.

### Stage 5: Inoue comparison

- run H1-H5 across Mainland, Oshima, Kozu, Hachijo;
- compare ordinal outputs to literature patterns.

### Stage 6: Streamlit integration

- only after model stabilizes, let `streamlit_app.py` call the new model;
- keep the current app working as the prototype.

## 14. Success criteria

This design succeeds when the repository clearly distinguishes:

```text
CAPOM = evaluation / pattern-matching workflow
Attraction-trait evolution model = generative biological model
```

and the model can answer:

```text
Under what conditions is the nectar guide maintained, reduced, or lost?
```

rather than only:

```text
Which current ABM scenario looks closest to the observed pattern?
```
