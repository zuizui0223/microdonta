# Latent Causal Generative Model

This document defines the causal layer above the Campanula generative simulator
and pattern-matching machinery.

## Core Problem

Observed pattern overlap is not sufficient evidence for causality. In the Izu
Islands *Campanula microdonta* example, pollinator assemblage, mating system,
flower size, and possible nectar-guide reduction may covary across islands.
That overlap does not by itself prove a direct pollinator-to-guide causal path.

RACH therefore asks which causal mechanisms remain admissible under biological
constraints and independent observations, not which fixed named model wins.

## General Model

```text
x_obs ecological context
+ latent parameters theta
+ causal switch state s in {0,1}^K
+ generative simulator f
+ independent y_obs distance
= admissible causal region A_epsilon
```

The primary output is:

```text
CA_j       mechanism-level causal admissibility
D_RACH     causal degeneracy
R_RACH     causal resolvability
OC_k       observation contribution
NOV        next-observation value
```

## Current Campanula Data Roles

Current source-confirmed `observed_target` rows:

```text
selfing_distance
flower_size_distance
```

Fixed context `x_obs` includes island distance, island area, population-size
proxy, and pollinator assemblage / Bombus availability.

Future or pending observations include nectar-guide area, herkogamy or
delayed-selfing geometry, Fis/He/Fst, bagging seed set, natural seed set,
pollinator visitation, guide-removal experiments, Qst-Fst comparison, and
molecular outcrossing rate `t_m`. These remain NOV/design candidates until
measured or independently source-confirmed.

## Causal Switches

RACH treats mechanisms as non-exclusive switches. For example:

```text
guide_attracts_bombus
selfing_syndrome_active
island_isolation_common_cause
small_pollinator_adaptation
```

Multiple switches can be ON simultaneously. A complex pathway is not a separate
model class unless the analysis chooses to report it as a named interpretation.

Drift is not an optional selection switch. Finite-population drift is part of the
background generative process; drift-dominated outcomes correspond to selection
switches being OFF or weak, plus latent drift parameters and ecological context.

## Supplementary M1-M5 Labels

Legacy M1-M5 labels can still help readers:

```text
M1  direct pollinator-to-guide interpretation
M2  selfing-mediated interpretation
M3  direct plus mediated interpretation
M4  common-island-cause interpretation
M0  null / all focal selection switches OFF
```

These labels are supplementary summaries of switch combinations. They are not
the primary inferential target and should not be described as fixed models being
selected.

## Why More Observations Are Needed

With only `selfing_distance` and `flower_size_distance`, many switch
combinations remain admissible. More observed targets should be added only when
they are measured and independently sourced. Adding theoretical herkogamy,
nectar-guide, Fis, seed-set, or visitation rows as current y_obs would sharpen
the apparent result while weakening the inference.

## Manuscript Sentence

Rather than interpreting the co-occurrence of pollinator change, mating-system
shift, and floral-size change as direct causal proof, RACH samples causal switch
combinations and latent parameters, keeps the region compatible with biological
constraints and source-confirmed observations, and reports which mechanisms
remain admissible and unresolved.
