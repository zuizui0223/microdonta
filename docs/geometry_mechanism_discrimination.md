# When does trait-space geometry distinguish mechanisms?

## Question

A common summary of ecological change records only a phenotype mean and whether
the population persists.  Those summaries can be compatible with several causal
programs.  This document defines a deliberately adversarial theory experiment:
we first retain all models that reproduce the same **coarse POM**, then ask what
happens when the geometry of viable trait support is added.

The implementation is `causal_model.geometry_mechanism_discrimination`.

## Coarse POM

The declared coarse target is intentionally small:

```text
realised mean trait decreases
viable population persists
```

It deliberately does **not** observe the lower or upper edge of the viable set,
its breadth, or whether it is connected.  Under this POM, five candidate programs
remain robust over their declared parameter regions:

| candidate program | causal idea | coarse outcome |
|---|---|---|
| `relationship_benefit_loss` | a costly high trait loses a relationship-gated benefit | mean decreases, persistence remains |
| `optimum_displacement` | a fitness optimum moves left | mean decreases, persistence remains |
| `connectivity_fragmentation` | patch reachability becomes discontinuous in trait space | mean decreases, persistence remains |
| `directional_connectivity_pruning` | high-trait suitable patches become unreachable | mean decreases, persistence remains |
| `compensated_frequency_reweighting` | support remains viable but realised frequencies move left | mean decreases, persistence remains |

This is not a claim that every system behaves this way.  It is an
**identifiability stress test**: a low-resolution POM cannot legitimately choose
among these mechanisms.

## Added observation: viable-trait geometry

For a before/after viable support, the experiment records

```text
lower edge
upper edge
breadth
number of connected components
```

and classifies the change as one of:

| geometry | condition | robust survivors in the current theory experiment |
|---|---|---|
| `upper_edge_contraction` | lower edge stable; upper edge and breadth decline | `relationship_benefit_loss`, `directional_connectivity_pruning` |
| `shift` | lower and upper edges move together; breadth stays constant | `optimum_displacement` |
| `fragmentation` | connected-component count increases | `connectivity_fragmentation` |
| `conserved` | edges, breadth, and connectedness are unchanged | `compensated_frequency_reweighting` |

The first row is deliberately **ambiguous**.  A directional spatial filter can
produce the same upper-edge contraction as loss of a relationship benefit.  Thus
an observed contraction is informative but is not, on its own, a unique signature
of mutualism or pollinator loss.

## Formal interpretation

Let `P_c` be the coarse POM and `G` the geometry observation.  For candidate
mechanism `m`, RACH retains

```text
A_epsilon(P_c, m)
```

when the coarse POM is reproduced robustly.  Geometry is useful only if it reduces
that candidate set:

```text
A_epsilon(P_c, G, m)  ⊂  A_epsilon(P_c, m).
```

For a geometry label `g`, the remaining candidates are

```text
M_g = { m : m robustly reproduces P_c and g }.
```

The result is reported as:

```text
unique       |M_g| = 1
ambiguous    |M_g| > 1
unsupported  |M_g| = 0
```

This prevents the method from calling every geometry a causal identification.

## What the experiment establishes

Within this explicit toy model family:

1. Mean-trait decline plus persistence is not an identifying POM.
2. Fragmentation, a whole-support shift, and conserved support can distinguish the
   corresponding candidate programs.
3. Upper-edge contraction alone does **not** distinguish relationship-benefit loss
   from directional trait-correlated connectivity loss.
4. Therefore, a useful empirical design needs geometry plus at least one further
   observation that separates these two contraction mechanisms.  Candidate
   observations include patch-specific trait suitability, realised dispersal,
   pollinator-mediated fitness, or a direct estimate of the lost benefit.

## Running the experiment

```bash
python -m examples.geometry_discrimination_demo
```

The resulting JSON records the target POM, every candidate's coarse classification,
all geometry-specific classifications, and the unresolved ambiguity for
upper-edge contraction.

## Scope

This module is a transparent mechanism-comparison construction, not an empirical
calibration or a claim of universal diagnosticity.  The next step is to attach the
same common POM/geometry adapter to the individual-based spatial, defense, and
colonization models, and then ask whether the discrimination survives their
independent demographic assumptions.
