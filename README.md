# RACH: Causal Admissibility and Degeneracy Framework

[![CI](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml/badge.svg)](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml)

**RACH** means **Restricted Admissible Causal Hypotheses**. It is a framework for
keeping every causal explanation that is still compatible with a declared model
family, biological constraints, and observed pattern—then showing what remains
unresolved and which observation would discriminate among the survivors.

```text
Generative model or ABM
→ POM summary P_sim
→ admissible region A_epsilon
→ robust / fragile / rejected / insufficient program families
→ conditional rule-transition invariants
→ next-observation design
```

RACH is **not** a best-model selector and does not convert conditional simulation
results into empirical proof.

## Core object

```text
A_epsilon(y_obs, x_obs)
= { (theta, s) in Theta x S :
    G(theta) = 1
    and d(P_sim(f(x_obs; theta, s)), P_obs(y_obs)) <= epsilon
  }
```

| symbol | meaning |
|---|---|
| `x_obs` | fixed empirical context used as model input |
| `theta` | parameters sampled over biologically admissible ranges |
| `s` | causal program or switch state |
| `G(theta)` | physical, biological, and ecological constraints |
| `P_sim`, `P_obs` | simulated and observed pattern summaries |
| `d`, `epsilon` | discrepancy and predeclared acceptance tolerance |

The output is the set of surviving causal explanations, their equivalence or
replaceability, and the observations expected to reduce that uncertainty.

## Repository structure

```text
causal_model/
  causal_admissibility.py        admissible causal regions and causal admissibility
  causal_replaceability.py       replaceability and causal degeneracy
  rach_seq.py                    next-observation value (NOV / EVSI)
  abm_family_adapter.py          robust / fragile sweep classification
  rule_transition_invariants.py  conditional necessities across robust programs
  rule_transition_hardened.py    outcome provenance boundary
  rule_transition_protocol.py    isolated interventions and assumptions-only motifs
  rule_transition_diagnostics.py endpoint sensitivity, Wilson intervals, benchmark reports
  endpoint_sensitivity_backends.py
                                 defense endpoint sensitivity runner
  spatial_metapopulation_abm.py  fecundity-mediated individual / patch ABM
  defense_metapopulation_abm.py  survival-mediated defense ABM
  colonization_metapopulation_abm.py
                                 establishment-mediated connectivity ABM
  campanula_real_data.py         published Campanula evidence and study design

examples/
  spatial_metapopulation_demo.py
  endpoint_sensitivity_report.py
```

## Campanula microdonta: empirical layer

The Campanula workflow intentionally separates **published observations** from
planned field data and theory-derived predictions. The present published targets
are the documented isolation gradients in selfing rate and flower size, together
with the documented pollinator transition. The current honest result is that these
published patterns do **not** resolve the selfing-syndrome versus island-common-
cause explanation.

The practical output is a ranked field-design plan: candidate observations are
scored by their expected reduction in explanation-level uncertainty and then
combined with declared cost and feasibility estimates.

```bash
python -m causal_model.campanula_real_data
```

This is a study-design result, not a claim that the published record has already
identified the causal mechanism.

## Rule-transition ABMs

The ABM layer asks a different question: after an ecological relation changes, how
does the set of trait values able to invade and persist change?

```text
Omega_inv(Z*) = { z' : lambda(z' | Z*) > 0 }
```

`lambda` is the long-term growth rate of a rare, bred-true invader introduced into
a stationary resident community `Z*`. The resulting viable trait set may contract,
shift, fragment, expand, collapse, or remain conserved.

The three mechanistically distinct backends are:

| backend | focal trait reward | relation changed | endpoint status |
|---|---|---|---|
| spatial metapopulation | fecundity via mutualistic service | pollination loss | supported when both residents are stationary |
| defense metapopulation | survival via predator-dependent defense | predator loss | supported when both residents are stationary |
| colonization metapopulation | establishment via connectivity | corridor loss | excluded when complete loss leaves no stationary after-resident |

### Strict endpoint protocol

For defense and colonization, and for endpoint sensitivity in the spatial backend,
the comparison is:

```text
1. Equilibrate the before resident.
2. Estimate Omega_inv(before) against that resident.
3. Apply the intervention to the same community.
4. Re-equilibrate the after resident, including resources and trait composition.
5. Estimate Omega_inv(after) only if the after resident is stationary.
```

A non-stationary or extinct after resident is retained as a rejected endpoint; it is
not converted into an empty viable set. In particular, complete corridor loss in
the colonization backend can remove recolonisation and leave no defensible endpoint.
That outcome is a counterexample to over-generalisation, not missing data.

### Non-circular rule-transition inference

Program assumptions and simulated outcomes are kept separate.

```text
ProgramRun.motifs          structural assumptions only
ProgramRun.outcome_motifs  outcome labels derived from matching simulator metadata
```

`trait_space_contraction`, `trait_space_shift`, and related labels are never fixed
program assumptions. They are derived only from `trait_space_primary` or the POM
trait-space component of matching runs. Thus a caller cannot obtain a contraction
invariant merely by putting a contraction label into a motif set.

The cross-system result may therefore be a broad
`trait_space_reconfiguration` rather than a geometry-specific contraction or shift.
All such claims remain conditional on the declared model family, sampled regions,
stationarity criterion, and acceptance rule.

### Isolated spatial interventions

The spatial public intervention factory changes exactly one biological channel at a
time:

| intervention | changed channel | unchanged biological channels |
|---|---|---|
| `pollination_loss` | `interaction_scale` | predation, dispersal |
| `predation_loss` | `predation_scale` | interaction, dispersal |
| `dispersal_loss` | `dispersal_scale` | interaction, predation |

Alternative compensation is the separate `repro_baseline` parameter. It can be
zero for a pure intervention or varied independently in counterexample and
sensitivity analyses.

## Pattern-oriented modelling and classification

Each ABM run becomes a multivariate POM summary. For the spatial backend:

```text
P_sim = (
  interaction_network,
  patch_occupancy,
  persistence_ne,
  trait_moments,
  omega_inv_state
)
```

A run is accepted only when its POM is within `epsilon` of its target and its focal
trait-space outcome satisfies the backend's declared criterion. Sweep records are
then classified as:

```text
robust        adequate recurrence across the declared sample
fragile       a rare or tuning-dependent match
rejected      insufficient matching support
insufficient  not enough replicates to judge
```

The `no_common_rule` result is an intended result: it means robust systems have no
shared assumption, outcome, or supported minimal clause under the declared design.

## Endpoint sensitivity and uncertainty reports

`examples.endpoint_sensitivity_report` runs spatial-pollination and defense
endpoint sensitivity cells. It varies invasion-grid density, invasion duration,
replicate count, invasion threshold, and stationarity window. Every cell retains
region and stochastic-seed provenance and reports Wilson intervals.

```bash
pip install -e ".[dev]"

# Small local smoke report
python -m examples.endpoint_sensitivity_report \
  --profile quick \
  --output outputs/endpoint_sensitivity_quick.json

# Larger local analysis
python -m examples.endpoint_sensitivity_report \
  --profile standard \
  --backend all \
  --output outputs/endpoint_sensitivity_standard.json
```

A manual GitHub Actions workflow, **Endpoint sensitivity report**, can also run
`quick`, `standard`, or `full` profiles and uploads the resulting JSON as an
artifact. `full` is intentionally manual because it is a large factorial analysis.

Each report contains:

```text
reference assumptions and outcome provenance
reference-setting conditional necessity
counterexamples / unsupported cells
Wilson intervals overall, by region, and by seed
all declared endpoint sensitivity settings
unresolved limitations
```

## Running the repository

```bash
pip install -e ".[dev]"
pytest -q

# Spatial individual / patch example
python -m examples.spatial_metapopulation_demo

# Generic rule-transition example and compact benchmark report
python -m examples.rule_transition_demo
```

## Documentation

- `docs/rule_transition_hardening.md` — provenance boundary, isolated channels, and uncertainty design
- `docs/post_intervention_reequilibration.md` — strict after-resident endpoint protocol
- `docs/trait_space_contraction_theorem.md` — comparative-statics result for the simplified viable-set model
- `examples/campanula_izu/` — observation roles, candidate experiments, and Island Campanula workflow

## Interpretation boundary

The repository is designed to make limits visible rather than hide them. A model
result should be reported as:

> Within a specified simulator family, intervention design, admissible parameter
> region, stationarity criterion, and pattern-acceptance rule, these causal
> programs remain compatible with the target pattern; these conditions or
> reconfigurations are shared by the robust survivors.

It should not be reported as a general ecological law or as direct empirical proof
without independent field data and external validation.
