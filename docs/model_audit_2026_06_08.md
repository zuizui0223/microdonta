# RACH model audit — 2026-06-08

This document audits the current `microdonta` repository from the viewpoint of:

1. simulation logic,
2. ecological plausibility,
3. circularity / tautology risk,
4. issue completion status,
5. next improvements needed for a publishable RACH model.

## Overall judgement

The repository has moved substantially beyond a manual-slider ABM. It now implements a recognizable **RACH** workflow:

```text
ecological constraint grammar
-> constrained latent parameter sampling
-> causal hypothesis simulation / switch inference
-> gradient-based POM / ABC-style pattern filtering
-> admissible causal hypotheses and compatible parameter regions
```

The strongest current contribution is not the M1-M5 ranking alone, but the newer **PathwaySwitch posterior inference**, which treats biological mechanisms as latent binary switches and estimates `P(switch ON | accepted)`.

However, the current model still has several logic issues that should be fixed before presenting it as a publishable method.

---

## What is already implemented well

### 1. RACH naming and conceptual framing

The README now defines RACH as:

```text
Restricted Admissible Causal Hypotheses
```

and frames the workflow as a constraint-first generative inference framework. This is a major improvement over the older CAPOM wording.

### 2. Empirical / literature observed pattern files

The repository includes:

```text
examples/campanula_izu/data/observed_patterns.csv
examples/campanula_izu/data/population_env.csv
examples/campanula_izu/observed_data.py
```

These implement the distinction between:

- simulation environment data, and
- POM / pattern-matching targets.

### 3. Gradient POM is implemented

`observed_patterns.csv` contains both pairwise and gradient patterns. The app currently uses gradient-only patterns as the main POM target.

Examples:

```text
nectar_guide decreases with distance_from_mainland
selfing_rate increases with distance_from_mainland
herkogamy decreases with distance_from_mainland
Fis increases with distance_from_mainland
rank_order for nectar_guide and selfing_rate
```

### 4. ABC-style distance is explicit

`causal_model/abc_distance.py` implements:

```text
pattern_distance = 1 - matches / total
weighted_distance = sum(w_i * mismatch_i) / sum(w_i)
accepted if distance <= epsilon
```

This resolves the earlier problem where pattern matching was only a count without formal tolerance.

### 5. Stochastic ABM layer exists

`attraction_trait_model/simulation.py` implements an individual-based stochastic simulation with:

- individual agents,
- reproduction mode assignment,
- fitness-proportional parent selection,
- inheritance,
- mutation,
- drift,
- generation-level summaries.

This is strong enough to support RACH as more than a proxy model.

### 6. PathwaySwitch posterior inference is a genuine model-level improvement

`causal_model/switch_inference.py` treats mechanisms as latent switches instead of forcing all inference through pre-defined M1-M5 structures. This is closer to an original algorithm than a simple ABM/POM/ABC combination.

---

## Main remaining problems

## Problem 1. Population CSV exists, but main simulation uses synthetic isolation-gradient populations

`population_env.csv` defines real worked-example populations:

```text
mainland
Oshima
Kozushima
Hachijo
```

with distance, pollinator, Ne, isolation, and migration values.

However, `streamlit_app.py` currently uses:

```text
simulate_campanula_isolation_gradient(..., n_points=8)
```

for proxy mode and internally creates synthetic populations such as:

```text
iso_0.000
iso_0.143
...
iso_1.000
```

Likewise, the stochastic ABM mode uses four synthetic isolation points:

```text
iso_0.000
iso_0.333
iso_0.667
iso_1.000
```

This is conceptually valid for a generalized island-gradient model, but it means that the current app is not directly simulating the empirical populations in `population_env.csv`.

### Why this matters

The documentation says the worked example is mainland → Oshima → Kozushima → Hachijo, but the actual main simulation is closer to a synthetic isolation-gradient generator.

This mismatch can confuse interpretation:

```text
Are results for real islands?
Or for an abstract isolation gradient?
```

### Fix

Add an explicit app mode:

```text
Gradient mode:
- empirical_populations
- synthetic_isolation_gradient
```

Behavior:

```text
empirical_populations:
  use population_env.csv exactly.
  simulate mainland, Oshima, Kozushima, Hachijo.

synthetic_isolation_gradient:
  generate iso_0.000 ... iso_1.000 from env_from_isolation().
  present as generalization / smooth gradient exploration.
```

The default for manuscript figures should be `empirical_populations`; synthetic gradient can be a sensitivity / generality check.

---

## Problem 2. Primary pollinator frequency is partly tautological when used as a POM target

`observed_patterns.csv` already marks the pairwise Bombus / primary-pollinator pattern as:

```text
NOT USED IN ABC — tautological: primary_pollinator_frequency is injected from env table not simulated
```

This is the right caution.

But the broader issue remains: primary pollinator frequency is currently an environmental input, not a simulated output. Therefore, using it as a matched output pattern can create circularity.

### Why this matters

If the model input says:

```text
primary_pollinator_frequency decreases with isolation
```

and the POM target also asks whether:

```text
primary_pollinator_frequency decreases with isolation
```

then that pattern is guaranteed by construction and should not count as evidence that a causal mechanism is supported.

### Fix

Classify POM targets into:

```text
input_environment_patterns
simulated_response_patterns
```

Only `simulated_response_patterns` should contribute to ABC/RACH acceptance.

Examples of input environment patterns:

```text
primary_pollinator_frequency decreases with isolation
community_pollinator_abundance decreases with isolation
migration_rate decreases with isolation
```

Examples of simulated response patterns:

```text
nectar_guide decreases with isolation
selfing_rate increases with isolation
herkogamy decreases with isolation
Fis increases with isolation
flower_size decreases with isolation
```

Implementation:

Add a column to `observed_patterns.csv`:

```text
role
```

with allowed values:

```text
input_context
response_target
```

Then `evaluate_patterns()` should exclude `role == input_context` from distance scoring unless the user explicitly chooses to include context checks.

---

## Problem 3. `Pattern of Moment` wording should be corrected to `Pattern-Oriented Model` / `pattern targets`

The README currently uses the heading:

```text
Pattern of Moment (POM)
```

This should be corrected. POM normally refers to:

```text
Pattern-Oriented Modeling
```

or, inside RACH, it may be better to avoid overusing POM and simply say:

```text
pattern targets
pattern-distance filtering
observable pattern constraints
```

### Fix

Replace:

```text
Pattern of Moment (POM)
```

with:

```text
Pattern-oriented targets
```

or:

```text
Gradient-based pattern targets
```

---

## Problem 4. The stochastic ABM uses uniparental reproduction and may not represent actual outcrossing genetics yet

The ABM assigns reproduction mode as:

```text
outcrossing / selfing / failed
```

but child production uses a selected parent and inheritance from that parent. This means that even when `reproduction_mode == outcrossing`, the child is still effectively produced from one parent rather than two parents.

### Why this matters

For trait evolution this may still work as a first approximation. But for selfing/outcrossing genetics, Fis, neutral diversity, and inbreeding depression, uniparental inheritance is a simplification.

### Fix

Add an explicit note in docs and output:

```text
Current ABM uses reproduction-mode-dependent fitness and trait shifts, but not explicit biparental genotype inheritance.
Fis is a proxy, not a genetic estimator.
```

Future implementation:

```text
if outcrossing:
    choose two parents or combine focal parent with pollen donor trait distribution.
if selfing:
    choose one parent and apply inbreeding effects.
```

This would make Fis and neutral diversity more mechanistic.

---

## Problem 5. M1-M5 and Switch Posterior currently coexist, but their roles need to be clearer

The app now has two inference modes:

```text
1. M1-M5 candidate hypothesis ranking
2. Switch Posterior Inference
```

This is good, but conceptually they should be framed as different levels:

```text
M1-M5 ranking:
  pedagogical / interpretable named scenarios

Switch Posterior:
  core RACH inference, because mechanisms are latent switches
```

### Fix

In the app and README, define:

```text
Primary output:
  switch posterior table and coactivation table

Secondary output:
  M1-M5 scenario ranking for interpretability
```

---

## Problem 6. Acceptance rules are labeled `strict_6_of_6`, but pattern count may change

`abc_distance.py` defines rules like:

```text
strict_6_of_6
relaxed_5_of_6
relaxed_4_of_6
```

but gradient patterns can now include 6, 7, or more rows depending on `observed_patterns.csv`.

The app partially handles thresholds through `GRADIENT_THRESH_MAP`, but the rule names can become misleading.

### Fix

Rename future-facing rules to proportion-based names:

```text
strict_all
relaxed_0_83
relaxed_0_67
weighted_strict
weighted_0_80
```

Keep old names as aliases for backward compatibility.

---

## Problem 7. Some parameter priors use literature citations, but several translations are still provisional

The constraint system is much stronger than before. However, several modelled ranges are still literature-inspired rather than directly measured in Campanula.

Examples:

- guide_cost,
- direct_pollinator_guide_benefit,
- background_pollinator_efficiency,
- cost_of_waiting_for_pollinators,
- drift_strength.

This is acceptable, but it must be reported as **sensitivity priors**, not true empirical estimates.

### Fix

In output and README:

```text
literature_grounded = literature-constrained prior, not posterior truth.
broad_prior = sensitivity analysis.
```

For manuscript:

```text
We used literature-constrained priors where direct Campanula measurements were unavailable and tested prior sensitivity using broad priors.
```

---

## Issue status audit

### Issue #1

Generalization of ABM into a constraint-aware pattern-oriented framework.

Status: mostly implemented and closed.

### Issue #2

Move from workflow to generative attraction-trait evolution model.

Status: partially implemented.

Implemented:

- `attraction_trait_model/`,
- individual agents,
- environment,
- parameters,
- fitness,
- reproduction,
- inheritance,
- simulation.

Remaining:

- explicit biparental outcrossing,
- more mechanistic Fis / genotype layer,
- phase diagrams,
- clearer guide maintained / reduced / lost regions.

### Issue #3

Generalize from attraction-trait ABM to latent causal generative model.

Status: substantially implemented.

Implemented:

- causal structures,
- switches,
- RACH framing,
- pattern-distance filtering,
- switch posterior inference.

Remaining:

- formal docs should be updated from old CAPOM wording to RACH.

### Issue #4

Turn causal framing into true generative model with pathway switches.

Status: mostly implemented.

Implemented:

- `causal_model/switches.py`,
- M1-M5 switch mappings,
- switch posterior inference.

Remaining:

- roles of M1-M5 vs switch posterior need clearer app/documentation framing.

### Issue #5

Ecology-principled parameter constraints.

Status: mostly implemented.

Implemented:

- `causal_model/parameter_constraints.py`,
- literature-grounded and broad priors,
- ecological hard constraints,
- rejected parameter set diagnosis.

Remaining:

- report prior sensitivity more explicitly.

### Issue #6

Upgrade to publishable constraint-first CAPOM model.

Status: mostly implemented but outdated.

Implemented:

- ABC distance,
- stochastic ABM backend,
- observed pattern CSV,
- population environment CSV,
- weighted distance,
- app output improvements.

Remaining:

- rename issue framing from CAPOM to RACH,
- close or supersede after the remaining audit issues are addressed.

---

## Recommended next issue

Create a follow-up issue:

```text
Audit fixes: remove circular pattern targets, separate empirical vs synthetic gradients, and clarify RACH inference levels
```

Required tasks:

1. Add `role=input_context|response_target` to `observed_patterns.csv`.
2. Exclude input-context patterns from acceptance distance by default.
3. Add `Gradient mode = empirical_populations | synthetic_isolation_gradient` to the app.
4. Use `population_env.csv` exactly for empirical mode.
5. Keep synthetic gradient as a generality/sensitivity mode.
6. Correct README wording from `Pattern of Moment` to gradient-based pattern targets.
7. Rename or alias acceptance rules from count-based names to proportion-based names.
8. Clarify that Fis is currently a proxy, not a genetic estimator.
9. Clarify that switch posterior inference is the primary RACH output, while M1-M5 ranking is a named-scenario interpretation layer.

---

## Bottom line

The current repository is no longer just a loose ABM/POM/ABC combination. It has a coherent RACH structure. The main risks now are not implementation absence, but **interpretation hygiene**:

- avoid circular use of input variables as output pattern targets,
- do not confuse synthetic isolation-gradient results with named island results,
- clearly state which quantities are simulated responses and which are environmental inputs,
- present Fis and genetic diversity as proxies until a genotype model is added.

If these are fixed, the project can credibly be presented as an original constraint-first causal generative inference framework.
