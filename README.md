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
local interaction = trait match × distance decay × density modulation
reproduction      = interaction success + mate availability + resources − trait cost
offspring         = inheritance + mutation
dispersal         = patch connectivity and distance
population change = births, deaths, movement, local extinction
```

Trait evolution is therefore an emergent outcome of individual interactions, local demography, patch structure, and physical or allocation trade-offs.

---

## Pattern-oriented modelling (POM)

Every ABM run is converted to a multi-component summary statistic before acceptance. For the spatial backend:

```text
P_sim = (
  interaction_connectivity,
  patch_persistence,
  inbreeding_proxy,
  trait_investment,
  trait_space_state
)
```

These components represent changes in interaction structure, occupied patches, within-patch diversity, mean focal investment, and the qualitative state of occupied trait space.

The same acceptance rule is used throughout RACH:

```text
d(P_sim, P_obs) ≤ ε
```

This matters because RACH does not accept a model merely because one hand-picked trait changed in the desired direction. A program must reproduce the specified multivariate ecological pattern.

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

The spatial backend currently reports an occupied trait-space proxy through trait variance and persistence. A future extension can estimate an invasion-based viable trait set:

```text
Ω_inv(Z*) = { z' : λ(z' | Z*) > 0 }
```

where `λ` is the long-term growth rate of a rare introduced phenotype in a resident ecological state `Z*`.

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
