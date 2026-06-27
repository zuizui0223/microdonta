# Post-eco-genetic program triage

## Decision

The H1--H3 eco-genetic theorem program is no longer developed in this repository. Its active home is `zuizui0223/eco-genetic-criticality`.

What remains in `microdonta` is not one project. It is three distinct categories:

1. an active generic RACH causal-identifiability program;
2. an empirical Campanula/Izu measurement-design program;
3. exploratory and teaching prototypes that must not be presented as active research claims.

This document is a scope boundary, not a claim that every retained module is a finished theory.

---

## A. Active future program: RACH causal identifiability

### Central question

Given a declared family of qualitative causal programs and a pattern of model outputs or observations, which causal motifs are shared by every **robustly admissible** program, and which additional observations or isolated interventions are sufficient to distinguish the remaining alternatives?

The intended conclusion is always vocabulary- and constraint-relative:

```text
Within the declared program grammar, constraints, observation set,
and robustness threshold, no robustly admissible explanation reproduces
the pattern without motif C.
```

It is not a claim that C is universally true in nature.

### Why this is a real next research program

The RACH design already distinguishes possible from robust explanations, separates structural program assumptions from endpoint outcomes, and records sensitivity/uncertainty of endpoint classifications. The next substantive task is to make the robust-admissibility program executable and benchmarked, rather than adding more unrelated ecological examples.

### Keep active in the future RACH repository

```text
causal_model/causal_admissibility.py
causal_model/causal_replaceability.py
causal_model/replaceability_theory.py
causal_model/rule_transition*.py
causal_model/structures.py
causal_model/simulator.py
causal_model/simulator_protocol.py
causal_model/generator_bridge.py
causal_model/parameter_constraints.py
causal_model/parameter_sampling.py
causal_model/ensemble.py
causal_model/identifiability.py
causal_model/minimal_explanations.py
causal_model/structure_discovery.py
causal_model/switch_inference.py
causal_model/known_truth_benchmark.py
causal_model/geometry_mechanism_discrimination.py
causal_model/endpoint_sensitivity_backends.py
causal_model/*metapopulation*.py
causal_model/ecological_rule_abm.py
examples/rule_transition_demo.py
examples/spatial_metapopulation_demo.py
examples/endpoint_sensitivity_report.py
docs/rach_*.md
docs/rule_transition*.md
docs/geometry_mechanism_discrimination.md
docs/latent_causal_generative_model.md
paper/odd_protocol_draft.md
```

### First publishable milestone

A ground-truth benchmark in which competing generative programs can reproduce the same pattern-oriented measurement (POM), followed by a minimal intervention/observation panel that distinguishes them with controlled false-invariant and false-exclusion rates.

The immediate theorem target is not a generic claim about ecology. It is a theorem or validated algorithmic guarantee about robust admissibility within a declared program grammar.

---

## B. Active empirical program: Campanula / Izu channel identification

### Central question

For a declared floral trait z, does a regime difference act through total local reproduction F(z), through establishment/reachability E(z), or remain non-identifiable without a direct factor or calibrated proxy?

```text
W(z) = F(z) E(z)
```

### Why this is a real next research program

The existing protocol makes an important negative result explicit: current published island patterns in flower size, selfing, and pollinator turnover do not by themselves identify F versus E. It also supplies the prospective measurement design needed to make the question theorem-ready.

### Keep active in the future Campanula repository

```text
causal_model/campanula_*.py
examples/campanula_izu/
docs/campanula_channel_protocol.md
docs/inoue_literature_values.md
paper/mee_manuscript_draft.md
```

### First publishable milestone

Pre-register a shared trait domain and census window; measure trait-specific W, direct F or a calibrated proxy, and the recruitment/reachability component needed to evaluate E. Pollinator-specific attribution is a separate treatment/component model and must not be inferred merely from visit counts.

---

## C. Incubator: attraction and mating-system model

`attraction_trait_model/` is not discarded. It has biologically specific state variables for nectar guides, flower size, delayed-selfing geometry, selfing ability, neutral diversity, and spatial location.

It is not yet an independent active theory program because it lacks a single declared question, a clearly delimited parameter/observation map, and a data-facing validation or discrimination target. It should remain frozen as an **incubator** until attached to the Campanula field-design program.

Promotion criterion:

```text
one explicit hypothesis
+ one declared life cycle
+ one measurable observation set
+ one falsification or discrimination target.
```

---

## D. Frozen trial-and-error / teaching prototypes

The following are not current research programs. They may be useful as regression fixtures, tutorials, or historical examples, but no new scientific claim should be built from them without an explicit promotion decision:

```text
causal_model/confound_demo.py
causal_model/synthetic_demo.py
causal_model/bergmann_worked_example.py
causal_model/nov_calibration.py
causal_model/phenomenological_model.py
causal_model/adaptation_plasticity.py
causal_model/abm_family*.py
causal_model/abm_robustness.py
causal_model/robust_abm_search.py
streamlit_app.py
```

Their matching tests and tutorial references are legacy validation materials, not evidence for a current theorem or empirical claim.

---

## E. Read-only duplicate: eco-genetic core

The eco-genetic files remaining here are historical mirrors. They are retained for source-history reproducibility only and must not receive new features, fixes, simulations, or documentation updates.

All future work on:

```text
interaction criticality
finite-bin closure
network/refuge persistence
genetic-lead certificates
moving allele corridors
H1--H3 phase diagrams
```

belongs in `zuizui0223/eco-genetic-criticality`.

---

## Separation rule

Until `rach-causal-theory` and `campanula-island-case-study` are created and their independent CI passes, no destructive file deletion occurs in `microdonta`.

From this commit onward:

- new RACH work may only target the RACH core in section A;
- new Campanula work may only target the empirical program in section B;
- section C is incubator-only;
- section D is frozen legacy material;
- section E is a read-only historical mirror.

This creates a complete **research-status separation** immediately, without losing reproducibility before physical repository transfers are validated.