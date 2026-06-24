# When does trait-space geometry distinguish mechanisms?

## Status of this experiment

This document describes a deliberately adversarial **finite toy-family
experiment**, implemented in `causal_model.geometry_mechanism_discrimination`.
It is not a general theorem that geometry identifies causal channels.

The general mathematical boundary is now stated first in
`docs/channel_identifiability_theorem.md`:

> When two vital-rate channels enter only through the same net-performance
> product, every observation derived only from that product -- including all
> trait-space geometries -- is structurally unable to identify which channel
> changed.

The experiment below asks a narrower, useful question: once a simulator family
adds explicit structure beyond a net-performance-only observation, can geometry
reduce the candidate set **within that declared family**?

## Coarse POM

The declared coarse target is intentionally small:

```text
realised mean trait decreases
viable population persists
```

It deliberately does **not** observe the lower or upper edge of the viable set,
its breadth, or whether it is connected. Under this POM, five candidate programs
remain robust over their declared parameter regions:

| candidate program | causal idea | coarse outcome |
|---|---|---|
| `relationship_benefit_loss` | a costly high trait loses a relationship-gated benefit | mean decreases, persistence remains |
| `optimum_displacement` | a fitness optimum moves left | mean decreases, persistence remains |
| `connectivity_fragmentation` | patch reachability becomes discontinuous in trait space | mean decreases, persistence remains |
| `directional_connectivity_pruning` | high-trait suitable patches become unreachable | mean decreases, persistence remains |
| `compensated_frequency_reweighting` | support remains viable but realised frequencies move left | mean decreases, persistence remains |

This is an **identifiability stress test**: a low-resolution POM cannot
legitimately choose among these mechanisms.

## Added observation: viable-trait geometry

For a before/after viable support, the experiment records

```text
lower edge
upper edge
breadth
number of connected components
```

and classifies the change as one of:

| geometry | condition | robust survivors in this toy family |
|---|---|---|
| `upper_edge_contraction` | lower edge stable; upper edge and breadth decline | `relationship_benefit_loss`, `directional_connectivity_pruning` |
| `shift` | lower and upper edges move together; breadth stays constant | `optimum_displacement` |
| `fragmentation` | connected-component count increases | `connectivity_fragmentation` |
| `conserved` | edges, breadth, and connectedness are unchanged | `compensated_frequency_reweighting` |

The first row remains deliberately **ambiguous**. A directional spatial filter
can produce the same upper-edge contraction as loss of a relationship benefit.
Thus an observed contraction is informative under extra simulator assumptions,
but is not on its own a unique signature of mutualism or pollinator loss.

## Formal interpretation in RACH

Let `P_c` be the coarse POM and `G` a geometry observation. For candidate
mechanism `m`, RACH retains

```text
A_epsilon(P_c, m)
```

when the coarse POM is reproduced robustly. Geometry is useful in this simulator
family only when it reduces that candidate set:

```text
A_epsilon(P_c, G, m)  subset  A_epsilon(P_c, m).
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

This is a model-family result. If observations collapse all vital rates into
`W(z)=F(z)E(z)`, theorem N1 says even full geometry cannot resolve the channel.

## What the experiment establishes

Within this explicit toy family:

1. Mean-trait decline plus persistence is not an identifying POM.
2. Added geometry can distinguish some candidate programs.
3. Upper-edge contraction alone does **not** distinguish relationship-benefit
   loss from directional trait-correlated connectivity loss.
4. A useful design needs either direct channel-resolved observations or a clearly
   stated structural assumption that rules out one of the observationally
   equivalent channels.

The experiment is therefore retained as a transparent illustration of how RACH
can reduce degeneracy **after** the structural non-identifiability boundary is
made explicit.

## Running the experiment

```bash
python -m examples.geometry_discrimination_demo
```

The resulting JSON records the target POM, every candidate's coarse
classification, all geometry-specific classifications, and the unresolved
ambiguity for upper-edge contraction.

## Scope

This module is a mechanism-comparison construction, not an empirical calibration
or a claim of universal diagnosticity. The next simulation task is to attach
channel-resolved observation operators to the independent spatial, defense, and
colonization ABMs, then test whether the mathematical boundary survives their
additional demographic assumptions.
