# RACH: Causal Admissibility and Degeneracy Framework

[![CI](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml/badge.svg)](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml)

**RACH** means **Restricted Admissible Causal Hypotheses**.

RACH is not a best-model selector. It is a simulator-agnostic inference framework for asking:

```text
Which causal explanations remain compatible with biological constraints and observed patterns?
Which explanations are still indistinguishable?
Which additional observation would separate them?
```

The repository now has two connected layers:

```text
individual / patch ABM
→ POM pattern extraction
→ admissible causal region A_ε
→ robust vs fragile causal-program families
→ rule-transition invariants
```

The Campanula system is a worked example, not the definition of RACH.

---

## Core RACH object

The lower-level object is the admissible causal region:

```text
A_ε(y_obs, x_obs)
=
{(θ, s) ∈ Θ × S :
  G(θ) = 1,
  d(P_sim(f(x_obs; θ, s)), P_obs(y_obs)) ≤ ε }
```

where:

```text
x_obs  fixed empirical context used as simulator input
θ      latent parameters sampled over biologically admissible ranges
s      causal program or switch state
G(θ)   ecological, physical, and biological constraints
f      generative simulator or ABM
P_sim  pattern summary extracted from a simulation
P_obs  corresponding empirical or synthetic target pattern
d      distance between pattern summaries
ε      acceptance tolerance
```

A run enters `A_ε` only when it is both biologically admissible and sufficiently close to the target pattern. The output is a set of surviving explanations, not a single winner.

---

## What is distinctive in RACH

RACH turns the accepted region into causal objects:

```text
CA_j       causal admissibility of mechanism j
D_RACH     causal degeneracy: how many explanations remain
R_RACH     causal resolvability: uncertainty removed by observations
OC_k       contribution of observation k
NOV(q)     expected value of the next observation q
```

It also represents mechanism equivalence explicitly: substitution, disjunction, exclusion, and unresolved paths can remain visible instead of being hidden behind a MAP model.

The sequential layer (`RACH-SEQ`) uses NOV to choose observations that reduce unresolved causal equivalence classes.

---

## Spatial metapopulation ABM backend

`causal_model.spatial_metapopulation_abm` is the individual-based, patch-based backend for rule-transition RACH.

Each individual has:

```text
trait investment
heritable genotype
age
patch identity
within-patch location
```

Each patch has:

```text
area
carrying capacity
resource state
connectivity to other patches
```

The simulator does **not** prescribe whether the focal trait should increase or decrease. It specifies only constraints and local processes:

```text
relationship service = (own trait investment) × local availability, gated by the relationship
mate success         = trait match × distance decay (a compatible, nearby partner)
reproduction         = fecundity floor + relationship service + mate + resources − trait cost,
                       then logistic in local density (finite resources)
survival             = age- and density-dependent, reduced by a survival trade-off
offspring            = inheritance + mutation
dispersal            = patch connectivity and distance
population change     = births, deaths, movement, local extinction
```

Because the relationship *service* rewards the trait investment and is gated by the
relationship being intact, losing the relationship removes the support for the
costly trait — so trait space can contract. Trait evolution is an emergent outcome
of individual interactions, local demography, patch structure, and trade-offs; no
trait direction is ever supplied.

---

## Relationship-change interventions and the viable trait set `Ω_inv`

The spatial backend studies trait space through a controlled **intervention**, not a
single run. An intervention is a paired *before*/*after* `Regime` run from the
**same** resident community and the same RNG structure, so the only difference is
the relationship change. Three are provided:

```text
pollination_loss   the mutualistic service that rewards the trait collapses
predation_loss     the trait-supporting relationship is lost and top-down control relaxes
dispersal_loss     the trait-supporting relationship is lost and dispersal pathways are cut
```

Trait space is summarised not by a mean but by the **viable trait set**

```text
Ω_inv(Z*) = { z' : λ(z' | Z*) > 0 }
```

where `λ` is the long-term invasion growth rate of a rare, bred-true mutant `z'`
introduced into the quasi-stationary resident community `Z*` (measured in the full
spatial dynamics with mutation off). The change in `Ω_inv` before vs after the
intervention is classified as **contraction / fragmentation / shift / collapse**.
Resident communities are first screened for **stationarity** (stationary /
not_converged / extinct / oscillating); non-stationary residents are bucketed
separately and never accepted.

## Pattern-oriented modelling (POM)

Every ABM run is converted to a multi-component summary statistic before acceptance. For the spatial backend:

```text
P_sim = (
  interaction_network,     realised relationship service (gated by the relationship)
  patch_occupancy,         fraction of patches occupied / local extinction
  persistence_ne,          census × diversity (Ne / persistence proxy)
  trait_moments,           trait variance + |cov(trait, genotype)|
  omega_inv_state          qualitative Ω_inv verdict (contracted / fragmented / …)
)
```

The same acceptance rule is used throughout RACH:

```text
d(P_sim, P_obs) ≤ ε   and   the viable set actually contracted
```

This matters because RACH does not accept a model merely because one hand-picked trait changed in the desired direction. A program must reproduce the specified multivariate ecological pattern, and the focal claim (trait-space contraction) must hold.

A **random ecosystem ensemble** randomises interaction strength, patch
size/connectivity, resources, trade-offs, mutation, and dispersal — always
honouring finite resources, positive trait cost, finite patches, local
interaction, and bounded traits (the trait *direction* is never an input). Under
this regime trait-space contraction follows the relationship loss **robustly**;
a **compensated counterexample** ensemble (low trait cost, ample dispersal, large
connected patches, *sufficient* compensation) does **not** contract, so the
pipeline correctly reports non-contraction and `no_common_rule` where they hold.

Run the worked demonstration:

```bash
python -m examples.spatial_metapopulation_demo   # spatial IBM → robust/fragile → invariants
```

Tests: `pytest tests/test_spatial_metapopulation_abm.py -q`.

### Key findings and causal-isolation controls

The diagnostics in `causal_model.spatial_metapopulation_analysis` answer the obvious
reviewer questions and turn the demo into falsifiable claims.

* **Channel decomposition (causal isolation).** Each intervention removes the
  trait-supporting interaction *and* a secondary channel. Decomposing them
  (`decompose_channels`) shows the contraction is driven by losing the
  **trait-supporting relationship**, not the secondary toggle:

  | scenario | interaction-only loss | secondary-only loss |
  |---|---|---|
  | pollination_loss | ~0.83 contracts | 0.00 (no secondary channel) |
  | predation_loss | ~0.83 contracts | ~0.08 — **predator removal alone does not contract** |
  | dispersal_loss | ~0.83 contracts | ~0.45–0.67 — **a separate spatial route to contraction** |

  So "any relationship loss contracts trait space" is **false**: predator removal is
  a clean dissociation, dispersal loss is an independent route, and the weak full
  predation result (~0.4–0.5) is explained by the secondary channel *cancelling*
  part of the interaction-loss contraction.

* **Threshold robustness.** `threshold_sensitivity` re-classifies one collected
  sweep across an `ε × contraction-tolerance` grid; the constrained-vs-compensated
  separation holds at every threshold (it is not a tuned-threshold artefact).

* **Monte-Carlo characterisation.** `replicate_convergence` and `seed_spread` report
  how the invasion-fitness estimate behaves with more replicates and across
  independent seeds (e.g. pollination contraction ≈ 0.73 over seeds, range
  ~0.64–0.91; predation a stable-moderate ≈ 0.45), so the conclusion is not
  seed-dependent.

Tests: `pytest tests/test_spatial_metapopulation_analysis.py -q`.

### Theorem: why relationship loss contracts trait space

The simulation result is underwritten by a comparative-statics theorem on invasion
fitness — see [`docs/trait_space_contraction_theorem.md`](docs/trait_space_contraction_theorem.md).
With a viable set `Ω(I,R) = { z : I·B(z) − C(z) + K + R ≥ 0 }` (relationship benefit
`B↑`, trait cost `C↑`, baseline `K ≥ 0`, compensation `R`), the proven results are:

* **T1** pure relationship loss contracts the viable set (`Ω(0,0) ⊆ Ω(1,0)`);
* **T2** incomplete compensation still contracts it;
* **T3** an exact **compensation threshold** `R* = B(z_max)`: trait loss occurs *iff*
  the alternative route returns less than the lost benefit at the trait it supported;
* **T4** under diminishing benefit / accelerating cost the loss only **recedes the
  upper edge** (contraction/shift) — **fragmentation** is the signature of the
  separate spatial-isolation route (Proposition S1).

All four are machine-verified over thousands of random monotone benefit/cost models
(`causal_model/trait_space_theory.py`, `pytest tests/test_trait_space_theory.py -q`),
and the spatial-ABM rare-invader fitness reduces to the theorem's structure (its
viable upper edge recedes under loss in ~94% of random ecosystems; the secondary
mate-matching term is the documented exception).

### Persistence after re-equilibration, and the conditions for contraction

The contraction is **not** a transient invasibility artefact. `run_reequilibration_experiment`
lets the resident *re-evolve* under the post-loss regime to a new quasi-stationary
state and compares the realised occupied trait set at that eco-evolutionary endpoint.
`verify_persistent_contraction` reports the outcome honestly:

* under **incomplete** compensation, relationship loss is **destabilising** — a
  substantial fraction of populations go extinct or fail to re-converge — and
  *among those that re-stabilise*, the contracted trait set **persists** (conditional
  contraction ≈ 0.6–0.9 across seeds);
* under **sufficient** compensation the system stays stable (≈ 0 destabilisation)
  and does **not** contract (conditional ≈ 0.2).

The framework therefore returns **conditions**, not a universal law
(`contraction_conditions_report`): contraction follows relationship loss *when* the
relationship is load-bearing and compensation is incomplete, and **not** under
sufficient compensation, ample dispersal, large connected patches, or low trait cost.
A benefit-form sweep (`benefit_form_sweep`) further shows the result is **not an
artefact of a linear benefit** — it holds for saturating (Holling-II) benefit too,
because loss gates off the whole benefit term — while the genuine boundary is the
relationship's *magnitude* (contraction vanishes once the benefit is too small to be
load-bearing).

This is the methodological point: rather than reporting one ABM's contraction as a
general rule, the pipeline subjects it to **re-equilibration, randomised ensembles,
explicit counterexamples, channel decomposition, and threshold/seed sensitivity**,
and returns only the rule transitions that survive — together with the conditions and
the regimes where they fail.

---

## Rule-transition RACH

The upper layer compares **families of admissible programs**, not one tuned parameterisation.

```text
ABM run
→ POM pattern
→ A_ε acceptance
→ recurrence across parameter regions and random seeds
→ robust / fragile / rejected / insufficient classification
→ invariant extraction across robust programs
```

A program is robust only when it repeatedly enters `A_ε` across declared parameter regions and seeds. Runs that work only through cancellation, boundary values, one seed, or one small parameter region are retained as fragile, but are not promoted as robust explanations.

For every robust program `g`, let `M(g)` be its set of rule-transition motifs. RACH reports:

```text
necessary motifs
minimal OR clauses
cross-system invariants
no_common_rule when no shared motif exists
```

The central output is conditional:

> Within the specified model family, constraints, and observed pattern, no robust admissible program reproduces the pattern without the reported rule transition.

This is not a claim that the same rule is automatically true in nature.

---

## Ecological interpretation

The intended ecological question is not only whether a mean trait rises or falls. It is whether a change in relationships restructures the set of traits that can persist.

```text
relationship change
→ individual interaction network
→ patch demography and connectivity
→ mating, dispersal, drift, and selection
→ occupied or viable trait space
```

The spatial backend reports the invasion-based **viable trait set**

```text
Ω_inv(Z*) = { z' : λ(z' | Z*) > 0 }
```

where `λ` is the long-term growth rate of a rare introduced phenotype in the
resident ecological state `Z*`, and tracks whether `Ω_inv` **contracts, fragments,
or shifts** across a relationship change.

---

## Installation

```bash
pip install -e ".[dev]"
pytest -q
```

---

## Main modules

```text
causal_model/abc_distance.py
    Common pattern-distance and A_ε acceptance utilities.

causal_model/simulator.py
    Simulator protocol and evidence-tier policy.

causal_model/spatial_metapopulation_abm.py
    Individual- and patch-based spatial metapopulation backend.

causal_model/ecological_rule_abm.py
    Lightweight abstract rule-transition backend for fast demonstrations.

causal_model/abm_family_adapter.py
    Converts parameter sweeps into robust / fragile / rejected / insufficient families.

causal_model/rule_transition_invariants.py
    Extracts necessary motifs, OR clauses, and cross-system invariants.

causal_model/mechanism_equivalence.py
    Represents unresolved substitution, disjunction, exclusion, and equivalence structure.
```

---

## Scope and limits

- RACH can establish admissibility, degeneracy, and conditional necessity within a specified model family.
- It does not establish causal truth from simulation alone.
- Synthetic recovery benchmarks test pipeline behavior under specified simulators; they are not empirical proof.
- Empirical use requires independently measured `P_obs` and explicit ecological constraints.
- The broadest ecological claim must be tested against alternative ABM families and counterexamples, not inferred from a single simulator.

For mathematical foundations, see `docs/rach_mathematical_foundations.md`.
For literature positioning, see `docs/literature_comparison.md`.
