# Package roadmap

This repository currently provides a case-specific ABM for nectar-guide evolution in *Campanula*. The long-term goal is to develop it into a reusable package for constraint-aware pattern-oriented ecological ABMs.

## Package concept

The package should help researchers move from observable field patterns to plausible hidden mechanisms.

```text
observable patterns
+
latent parameters
+
ecological constraints
↓
generative ABM
↓
pattern matching
↓
ranked mechanisms
```

## Target package structure

```text
constraint_abm/
  __init__.py
  patterns.py
  latent.py
  constraints.py
  scenarios.py
  simulation.py
  matching.py
  sensitivity.py
  abc_filtering.py
  odd.py
  plotting.py

examples/
  campanula_izu/
    README.md
    observed_patterns_template.csv
    scenario_config.yaml
    run_case_study.py
    outputs/
    figures/

paper/
  manuscript_outline.md
  methods_workflow.md
  odd_protocol_draft.md
```

## Core API idea

```python
define_observable_patterns()
define_latent_parameters()
define_constraints()
run_abm_scenarios()
compare_patterns()
rank_mechanisms()
plot_thresholds()
export_odd_protocol()
```

## Minimum viable package

### 1. Pattern definition

Allow users to define observed patterns as numeric or ordinal targets.

Examples:

```text
numeric: nectar_guide = 0.42
ordinal: Mainland > Oshima > Kozu > Hachijo
```

### 2. Scenario definition

Allow users to define alternative mechanisms.

Examples:

```text
H1: pollinator_loss_only
H2: pollinator_loss_plus_selfing
H3: pollinator_loss_plus_inbreeding
H4: pollinator_loss_plus_drift
```

### 3. Simulation runner

Run each scenario with multiple random seeds and parameter sets.

### 4. Pattern matching

Calculate distance between simulated and observed patterns.

### 5. Sensitivity analysis

Rank which latent parameters most influence target patterns.

### 6. Output

Generate manuscript-ready tables and figures:

- scenario comparison table
- pattern matching scores
- threshold maps
- sensitivity plots
- ODD protocol draft

## Manuscript-readiness checklist

- [ ] Reproducible example dataset
- [ ] Script to regenerate all figures
- [ ] ODD protocol document
- [ ] Scenario comparison module
- [ ] Sensitivity analysis module
- [ ] Null model module
- [ ] Pattern matching scores
- [ ] Clear README usage
- [ ] Code citation / version tag

## Development order

1. Extract core simulation from Streamlit/TenSnap UI.
2. Implement pattern matching functions.
3. Add scenario configuration files.
4. Add sensitivity analysis.
5. Add null models.
6. Add ODD export.
7. Add example dataset for Campanula.
8. Prepare manuscript figures.

## Publication strategy

### Short-term

Use this repository to support a case-study manuscript on nectar-guide decline in *Campanula* along the Izu Islands gradient.

### Medium-term

Develop a methods manuscript introducing the constraint-aware pattern-oriented ABM framework, using *Campanula* as a worked example.

### Long-term

Release a reusable Python package for ecological systems in which observable patterns arise from hidden trade-offs and ecological constraints.
