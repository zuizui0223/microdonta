# Repository scope audit and migration decision

## Decision

`microdonta` should stop being the active home for unrelated research programs.
The recommended architecture is:

```text
1. New active repository: eco-genetic-criticality
   - current theorem-first H1--H3 program
   - finite-bin coupled closure and its tests
   - only documentation needed to reproduce and interpret that program

2. This repository: microdonta-legacy (archive after migration)
   - preserve full git history and reproducibility
   - no destructive deletion before destination CI is green

3. Separate repositories or archived snapshots for independent programs
   - rach-causal-theory
   - campanula-island-case-study
   - optional attraction-trait-model
```

The names are recommendations; the scientific split matters more than names.

## Scope rule

A file belongs in `eco-genetic-criticality` only if removing it would prevent a
reader from understanding, proving, testing, simulating, or reproducing one of
these current claims:

```text
H1: interaction criticality and potential high-trait viability
H2: conditional/probabilistic genetic warning before realised high-trait loss
H3: fixed-total-area fragmentation under isolation, migration rescue, or erosion
```

A generic causal-methods file, an empirical Campanula case study, or a separate
agent-based model does not remain solely because it once motivated the program.

## Keep and migrate to the new active eco-genetic repository

### A. Theorem core

Keep all theorem modules and corresponding tests/docs/examples whose subjects
are interaction criticality, finite population genetics, trait occupancy, or
finite-horizon persistence. This includes the following families:

```text
causal_model/eco_genetic_*.py
causal_model/multipatch_criticality_*.py
causal_model/patch_genetic_drift_theory.py
causal_model/finite_bin_closure_bounds.py
causal_model/stochastic_refuge_invariance.py
causal_model/migration_safe_refuge.py
causal_model/network_allele_floor_theory.py
causal_model/network_high_trait_floor_theory.py
causal_model/restricted_h_alpha_multiplier_theory.py
causal_model/probabilistic_h_alpha_lead_theory.py
causal_model/colonization_recruitment_factorization.py
```

Include matching `tests/`, `docs/`, and `examples/` files. The colonization
one-step factorization remains because it is an explicit projection example for
channel identifiability and finite recruitment, but it should be kept in a
clearly labelled `projections/` or `worked_examples/` directory, not presented
as the main H1--H3 model.

### B. Simulation and reproducibility core

Keep only simulation code that directly implements or diagnoses the finite-bin
criticality program:

```text
causal_model/multipatch_criticality_dynamics.py
causal_model/multipatch_criticality_ensemble.py
examples/multipatch_phase_diagram_pilot.py
examples/eco_genetic_lag_demo.py
examples/restricted_h_alpha_multiplier_demo.py
```

Retain the phase-diagram documentation as simulation evidence, explicitly below
the theorem layer.

### C. Conceptual governance required by the active program

Keep:

```text
causal_model/theorem_projection_ledger.py
docs/theorem_projection_ledger.md
causal_model/eco_genetic_constitutive_theory.py
docs/eco_genetic_constitutive_theory.md
docs/three_hypotheses_status.md
```

These files are not optional prose: they prevent theorem, conditional theorem,
simulation result, and empirical projection from being conflated.

## Move to `rach-causal-theory` or archive as a versioned snapshot

These files form a coherent generic causal / RACH program, but are not required
to advance H1--H3. Move them together rather than deleting individual pieces.

```text
causal_model/abm_family*.py
causal_model/abm_robustness.py
causal_model/robust_abm_search.py
causal_model/ecological_rule_abm.py
causal_model/spatial_metapopulation_abm.py
causal_model/colonization_metapopulation_abm.py
causal_model/defense_metapopulation_abm.py
causal_model/rule_transition*.py
causal_model/generator_bridge.py
causal_model/simulator.py
causal_model/simulator_protocol.py
causal_model/rach_seq.py
causal_model/switch_inference.py
causal_model/known_truth_benchmark.py
causal_model/phenomenological_model.py
causal_model/structure_discovery.py
causal_model/identifiability.py
causal_model/causal_admissibility.py
causal_model/minimal_explanations.py
causal_model/parameter_sampling.py
causal_model/parameter_constraints.py
causal_model/ensemble.py
causal_model/geometry_mechanism_discrimination.py
causal_model/adaptation_plasticity.py
causal_model/confound_demo.py
causal_model/synthetic_demo.py
causal_model/nov_calibration.py
causal_model/bergmann_worked_example.py
```

Move their linked materials as a unit:

```text
docs/abm_*.md
docs/rach_*.md
docs/rule_transition*.md
docs/geometry_mechanism_discrimination.md
docs/latent_causal_generative_model.md
docs/tutorial.md
examples/rule_transition_demo.py
examples/spatial_metapopulation_demo.py
examples/endpoint_sensitivity_report.py
paper/odd_protocol_draft.md
```

### Why move rather than delete

This group contains a reusable methodological program and may support a future
methods paper. It is unrelated to the current eco-genetic manuscript's central
claims, but it is not disposable.

## Move to `campanula-island-case-study`

The Campanula / Izu files are an empirical case study and field-protocol
program. They should not be nested inside a generic theorem repository.

```text
causal_model/campanula_*.py
examples/campanula_izu/
docs/campanula_channel_protocol.md
docs/inoue_literature_values.md
paper/mee_manuscript_draft.md
streamlit_app.py
attraction_trait_model/
```

The exact destination can be a single field-case repository or two repositories
if the attraction model becomes its own paper. Default recommendation: keep the
Campanula case study and `attraction_trait_model` together initially, because
they share trait attraction/pollination motivation; split them only once their
dependencies and manuscript targets diverge.

## Delete only after migration and import checks

Do not delete research code directly from `microdonta` now. Use this sequence:

1. Create destination repositories.
2. Copy the chosen file families with their tests, docs, examples, requirements,
   and CI workflow.
3. Make imports work without reaching back into `microdonta`.
4. Run destination CI on Python 3.10, 3.11, and 3.12.
5. Tag this repository at the final pre-split commit, e.g. `microdonta-legacy-v1`.
6. Replace moved files here with a short archival README or remove them in one
   reviewed PR after all destination checks are green.

Deletion is appropriate only for files that satisfy all three conditions:

```text
- no active manuscript or field protocol uses them;
- no retained module imports them;
- their scientific question is fully superseded by a migrated program.
```

At this stage, no identified group meets all three conditions with confidence.

## Proposed destination layout

```text
eco-genetic-criticality/
  causal_model/
    theory/
    closure/
    certificates/
    simulation/
    projections/
  tests/
  docs/
    theorem/
    simulation/
    governance/
  examples/
  paper/

rach-causal-theory/
  causal_model/
  tests/
  docs/
  examples/
  paper/

campanula-island-case-study/
  src/
  data/
  docs/
  notebooks_or_apps/
  paper/
```

## Immediate next action

Create `eco-genetic-criticality` first. Move the theorem core and finite-bin
simulation core before touching the other two groups. The active theoretical
work then has a clean README, a small dependency surface, and CI whose failures
refer only to the current scientific program.
