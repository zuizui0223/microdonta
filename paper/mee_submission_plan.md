# MEE submission plan

Target journal: **Methods in Ecology and Evolution**

## Why MEE?

The project should be framed not as a species-specific ABM, but as a reusable methodological workflow for linking observable field patterns to latent ecological mechanisms.

The Campanula / Izu Islands system is the worked example, not the whole contribution.

## Required shift in framing

### Not enough for MEE

```text
We built an ABM for nectar-guide decline in Campanula.
```

### MEE-level framing

```text
We introduce a constraint-aware pattern-oriented ABM workflow that uses observable field patterns to constrain hidden ecological trade-offs, and demonstrate it with Campanula nectar-guide decline along an island isolation gradient.
```

## Distinction from ordinary ABM

Ordinary ABM:

```text
individual rules → population patterns
```

This framework:

```text
observable field patterns
+ latent trade-offs
+ ecological constraints
→ generative ABM
→ scenario comparison
→ sensitivity analysis
→ pattern matching
→ plausible mechanism ranking
```

The key novelty is not only generating patterns, but using patterns to constrain hidden costs, benefits, and trade-offs.

## Distinction from ordinary POM

Pattern-oriented modeling usually asks whether a model can reproduce multiple observed patterns.

This framework asks additionally:

```text
Which hidden parameter regions are required to reproduce the observed patterns?
Which latent trade-offs are identifiable from observable pattern combinations?
Which ecological constraints make some mechanisms implausible?
```

## MEE contribution checklist

To be suitable for MEE, the repository should provide:

- [ ] A reusable package-like API
- [ ] Clear documentation and tutorial
- [ ] A worked example dataset
- [ ] Reproducible scripts for all figures
- [ ] ODD protocol export or model description
- [ ] Scenario comparison module
- [ ] Sensitivity analysis module
- [ ] Pattern matching / scoring module
- [ ] Null models / negative controls
- [ ] Demonstration that the method is general beyond pollination
- [ ] Clear statement of limitations and when not to use the method

## Minimum viable MEE manuscript package

```text
constraint_abm/
  patterns.py
  latent.py
  constraints.py
  scenarios.py
  simulation.py
  matching.py
  sensitivity.py
  null_models.py
  odd.py
  plotting.py

examples/campanula_izu/
  observed_patterns_template.csv
  scenario_config.yaml
  run_case_study.py
  README.md

paper/
  manuscript_outline.md
  methods_workflow.md
  odd_protocol_draft.md
  mee_submission_plan.md
```

## Manuscript figures needed

1. Conceptual framework diagram
   - Observable patterns
   - Latent trade-offs
   - Constraints
   - Generative ABM
   - Pattern matching

2. Workflow diagram
   - define patterns
   - define latent parameters
   - run scenarios
   - compare patterns
   - filter plausible mechanisms

3. Campanula case-study system
   - Mainland → Oshima → Kozu/Niijima → Hachijo
   - expected gradients

4. Scenario comparison
   - H1-H5 output trajectories

5. Sensitivity / threshold map
   - guide_cost × inbreeding_depression × Bombus frequency

6. Pattern matching score
   - scenario ranking

7. Null model comparison
   - drift only / pollinator loss only / selfing only / random loss

## Manuscript sections for MEE

### Abstract

State the general problem first: ecological mechanisms often involve hidden costs and trade-offs that are difficult to measure directly.

Then present the method: constraint-aware pattern-oriented ABM.

Then present the worked example: Campanula nectar-guide decline along the Izu Islands gradient.

End with the package/reuse claim.

### Introduction

- Field data as overlapping observable patterns
- Hidden mechanisms: fitness, costs, future benefits, inbreeding, drift
- Limits of correlation-only field analysis
- ABM and POM background
- Gap: lack of reusable workflow to constrain latent trade-offs from observable pattern combinations
- Aim: introduce reusable framework and demonstrate it

### Methods

- Framework definition
- Package / API
- ODD protocol
- Scenario design
- Pattern matching
- Sensitivity analysis
- Null models
- Campanula worked example

### Results

MEE methods papers can include demonstration results rather than full biological inference.

Show:

- the tool reproduces expected known patterns
- different scenarios are distinguishable
- hidden parameters can be constrained by pattern combinations
- null models fail or succeed in informative ways

### Discussion

- How this differs from ordinary ABM/POM
- When the method is useful
- When it is not useful
- How to extend to other systems
- Limitations of pattern matching and identifiability

## Strongest novelty sentence

```text
We do not use ABM merely to reproduce ecological patterns; we use observable patterns to constrain hidden ecological trade-offs.
```

## What must be implemented next

Priority 1:

- [ ] Extract core ABM from UI into reusable functions/classes
- [ ] Add `compare_patterns()`
- [ ] Add scenario configuration
- [ ] Add `run_scenarios()`
- [ ] Add null models

Priority 2:

- [ ] Add sensitivity analysis
- [ ] Add threshold maps
- [ ] Add ABC-like parameter filtering
- [ ] Add example observed pattern template

Priority 3:

- [ ] Add ODD exporter
- [ ] Add documentation site or tutorial notebook
- [ ] Add tests
- [ ] Add package metadata

## MEE risk points

Potential reviewer criticism:

1. This is just another ABM.
   - Response: emphasize reusable workflow, pattern matching, latent parameter filtering, null models, and general API.

2. POM already exists.
   - Response: frame this as a constraint-aware extension focusing on latent trade-offs and field-measurable pattern combinations.

3. Campanula example is too specific.
   - Response: keep Campanula as worked example and include at least one generic toy example or cross-system demonstration.

4. No real empirical data yet.
   - Response: provide observed-pattern template and use literature-derived/field-ready patterns as demonstration; plan to update with empirical data.

5. Method cannot prove causality.
   - Response: explicitly state that it ranks plausible mechanisms and identifies parameter regions, not definitive causality.

## Target claim for submission

This package provides a practical workflow for ecologists facing systems where important mechanisms are hidden but their consequences are visible as overlapping patterns. The framework turns those visible patterns into constraints on latent ecological trade-offs.
