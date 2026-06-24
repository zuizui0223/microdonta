# RACH: Causal Admissibility and Degeneracy Framework

[![CI](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml/badge.svg)](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml)

**RACH** means **Restricted Admissible Causal Hypotheses**. It keeps every causal
explanation that remains compatible with a declared model family, biological
constraints, and observed pattern, then states exactly what is still unresolved
and what observation would reduce that uncertainty.

```text
mathematical theorem
→ declared model-to-theorem projection
→ ABM robustness test under extra processes
→ POM admissibility / competing explanations
→ next-observation design
```

RACH is not a best-model selector and does not convert conditional simulation
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
replaceability, and observations expected to reduce that uncertainty.

## Mathematical identifiability boundary

The repository's theorem layer begins from a positive trait-specific
factorisation:

```text
W(z) = F(z) E(z)
```

where `F` is a local fecundity/survival channel and `E` is an
establishment/reachability channel.

### N1 — net-only observations are structurally non-identifying

For any positive trait-dependent multiplier `a(z)`, the two distinct changes

```text
(F, E) -> (aF, E)
(F, E) -> (F, aE)
```

produce the same net performance:

```text
W_after(z) = a(z) F(z) E(z).
```

Therefore **every observation that depends only on `W` is identical** between
those mechanisms: all thresholded viable sets, their lower and upper edges,
breadth, connectedness, and any other trait-space geometry. Geometry can be
informative inside a restricted simulator family, but it cannot generally recover
the changed vital-rate channel once channels have been collapsed into `W`.

### N2 — net performance plus one exact channel is sufficient

With positive factors, observing `W` and either one factor reconstructs the
other:

```text
E = W / F
F = W / E.
```

Hence before/after `W` plus before/after `F` (or `E`) identifies the two channel
change ratios. The implementation keeps `fecundity_only`, `establishment_only`,
`mixed_or_unidentified`, and `unchanged` as separate conclusions.

### N3/N4 — a proxy helps only under a calibration condition

For a proxy `X_i(z)=q_i(z)F_i(z)`:

```text
q_0(z) = q_1(z)
    -> X_1/X_0 = F_1/F_0; relative channel change is identified

q_0(z), q_1(z) unconstrained
    -> calibration drift restores non-identifiability
```

Thus a visit count, pollen-load index, or connectivity index is not
automatically a channel measurement. Its conversion to the mathematical factor
must be stable across the comparison, or separately calibrated.

These are algebraic theorems under the stated positive multiplicative model.
Randomised code checks are regression tests, not the proofs.

## Exact life-cycle bridge: colonization recruitment

The full colonization ABM reports a stochastic multi-step invasion growth rate
`lambda`; that quantity is not yet factorised. The repository now also exposes a
separate **exact one-step expected retained juvenile-recruitment submodel**:

```text
W_recruit(z) = F_local(z) E_settlement(z)

F_local = survival_probability * conception_probability
E_settlement = (1-extinction_rate)
               * [dispersal_probability * connectivity * expected_target_room
                  + (1-dispersal_probability) * local_room]
```

This matches the event order in the colonization life cycle: adult survival,
conception, mutually exclusive dispersal/local settlement branches, and the
end-of-step patch-extinction draw. In its strict positive interior, N1–N4 apply
exactly to `W_recruit`.

It does **not** follow that N1–N4 automatically apply to multistep `lambda`,
`Omega_inv`, population persistence, or endpoint trait-space geometry. Those are
the next ABM robustness questions.

## Projection ledger

The theorem-to-model boundary is explicit in
`causal_model.theorem_projection_ledger`:

| target | current status |
|---|---|
| abstract positive `W=FE` model | exact theorem target |
| colonization one-step recruitment | exact theorem target in its positive interior |
| spatial pollination ABM | requires a declared `W=FE` factorisation |
| colonization multistep `lambda` | requires a bridge from one-step factors to multistep dynamics |
| defense backend | requires a declared factorisation |
| published *Campanula microdonta* record | not yet a channel-identification observation class |

A model with biologically rich processes is not thereby theorem-exact. The
factorisation and observation map must be stated and checked.

## Repository structure

```text
causal_model/
  causal_admissibility.py               admissible causal regions and causal admissibility
  causal_replaceability.py              replaceability and causal degeneracy
  rach_seq.py                           next-observation value (NOV / EVSI)
  abm_family_adapter.py                 robust / fragile sweep classification
  rule_transition_invariants.py         conditional necessities across robust programs
  rule_transition_hardened.py           outcome provenance boundary
  rule_transition_protocol.py           isolated interventions and assumptions-only motifs
  rule_transition_diagnostics.py        endpoint sensitivity, Wilson intervals, benchmark reports
  endpoint_sensitivity_backends.py      defense endpoint sensitivity runner
  trait_space_theory.py                 restricted comparative statics for costly relationship-rewarded traits
  channel_identifiability_theory.py     N1/N2 net-performance and one-factor theorems
  proxy_calibration_theory.py           N3/N4 stable-proxy and calibration-drift theorems
  theorem_projection_ledger.py          theorem applicability boundary for each backend/data layer
  colonization_recruitment_factorization.py
                                        exact one-step juvenile-recruitment factorisation
  spatial_metapopulation_abm.py         fecundity-mediated individual / patch ABM
  defense_metapopulation_abm.py         survival-mediated defense ABM
  colonization_metapopulation_abm.py    establishment-mediated connectivity ABM
  campanula_real_data.py                published Campanula evidence and study design

examples/
  spatial_metapopulation_demo.py
  endpoint_sensitivity_report.py
  channel_identifiability_demo.py
  proxy_calibration_demo.py
```

## Campanula microdonta: empirical layer

The Campanula workflow intentionally separates **published observations** from
planned field data and theory-derived predictions. The present published targets
are the documented isolation gradients in selfing rate and flower size, together
with the documented pollinator transition.

Those published patterns do **not** currently provide:

```text
trait-specific total performance W
an explicit F/E factorisation
one direct channel, or a proxy with stable / calibrated conversion
```

They therefore cannot identify a fecundity/pollination channel versus an
establishment/reachability channel under N1–N4. Their correct role is to retain
competing explanations and specify the missing next observation.

The practical field-design target is not merely a flower-trait mean or a visit
count. It is a defensible mapping to:

```text
W(z)  trait-specific performance on a declared life-cycle scale
F(z)  local reproductive / pollination component, or a stable calibrated proxy
E(z)  establishment / reachability component inferred or directly measured
```

```bash
python -m causal_model.campanula_real_data
```

This remains a study-design result, not a claim that the published record has
already identified the causal mechanism.

## Rule-transition ABMs

The ABM layer asks a different, conditional question: after an ecological relation
changes, how does the set of trait values able to invade and persist change?

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

A non-stationary or extinct after resident is retained as a rejected endpoint; it
is not converted into an empty viable set. Complete corridor loss can remove
recolonisation and leave no defensible endpoint. That outcome is a counterexample
to over-generalisation, not missing data.

### Non-circular rule-transition inference

Program assumptions and simulated outcomes are kept separate.

```text
ProgramRun.motifs          structural assumptions only
ProgramRun.outcome_motifs  outcome labels derived from matching simulator metadata
```

`trait_space_contraction`, `trait_space_shift`, and related labels are never fixed
program assumptions. They are derived only from matching simulator metadata. Thus
a caller cannot obtain a contraction invariant merely by placing a contraction
label into a motif set.

The cross-system result may therefore be a broad
`trait_space_reconfiguration` rather than a geometry-specific contraction or
shift. All such claims remain conditional on the declared model family, sampled
regions, stationarity criterion, and acceptance rule.

### Isolated spatial interventions

The spatial public intervention factory changes exactly one biological channel at
a time:

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

A run is accepted only when its POM is within `epsilon` of its target and its
focal trait-space outcome satisfies the backend's declared criterion. Sweep
records are then classified as:

```text
robust        adequate recurrence across the declared sample
fragile       a rare or tuning-dependent match
rejected      insufficient matching support
insufficient  not enough replicates to judge
```

The `no_common_rule` result is intended: robust systems then have no shared
assumption, outcome, or supported minimal clause under the declared design.

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

## Running the repository

```bash
pip install -e ".[dev]"
pytest -q

# Mathematical theorem demonstrations
python -m examples.channel_identifiability_demo
python -m examples.proxy_calibration_demo

# Spatial individual / patch example
python -m examples.spatial_metapopulation_demo

# Generic rule-transition example and compact benchmark report
python -m examples.rule_transition_demo
```

## Documentation

- `docs/trait_space_contraction_theorem.md` — restricted comparative statics for the simplified viable-set model
- `docs/theory_corrections.md` — exact edge-retention threshold correction
- `docs/channel_identifiability_theorem.md` — N1/N2 structural non-identifiability and one-factor recovery
- `docs/proxy_calibration_theorem.md` — N3/N4 proxy calibration boundary
- `docs/colonization_recruitment_factorization.md` — exact one-step life-cycle bridge
- `docs/theorem_projection_ledger.md` — theorem applicability across models and data
- `docs/rule_transition_hardening.md` — provenance boundary, isolated channels, and uncertainty design
- `docs/post_intervention_reequilibration.md` — strict after-resident endpoint protocol
- `examples/campanula_izu/` — observation roles, candidate experiments, and Island Campanula workflow

## Interpretation boundary

The repository is designed to make limits visible rather than hide them. A result
should be reported at its actual layer:

> **Theorem layer:** under the stated factorisation and observation map, this
> identification or non-identification result follows algebraically.
>
> **ABM layer:** within a specified simulator family, intervention design,
> admissible parameter region, stationarity criterion, and pattern-acceptance rule,
> these causal programs remain compatible with the target pattern.
>
> **Empirical layer:** a channel claim requires field measurements that satisfy the
> declared mapping and calibration conditions; without them, the result is a
> next-observation design rather than empirical identification.
