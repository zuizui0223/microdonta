# Conditional network high-trait floor theorem

## Purpose

This theorem supplies the realised-trait side that is missing from the network
allele-floor result. It follows the exact life-cycle ordering of the finite-bin
simulator:

```text
current p_t and current resident trait abundance
-> two-kernel recruitment
-> viability selection across trait bins
-> finite multinomial trait recruitment
-> allele migration and finite allele sampling.
```

Therefore migration does not appear inside the same-generation trait-recruitment
bound. Its role is to help or harm the **next** generation's allele floor.

## Declared common region

For each patch `j`, suppose before trait recruitment:

```text
p_j,t >= p_min
r_H,j,t >= r_min
q_j,t >= q_min
N_j,t+1 >= N_min.
```

Here `r_H` is realised high-trait mass, not potential viability and not allele
frequency. The theorem does not prove that this region closes; it gives its
one-step conditional consequence.

The closure is restricted to:

```text
trait_occupancy_mode       = finite_trait_bin_recruitment
genotype_trait_recruitment = two_kernel_recruitment
low kernel centre          < high_trait_cutoff
high kernel centre         >= high_trait_cutoff
high_interaction_benefit   >= 0.
```

The simulator's kernel constructor makes the two kernels exactly disjoint across
the high-trait cutoff: the low kernel has zero high-trait mass and the high
kernel has unit high-trait mass.

## Recruit-mass lower bound

Let `w` be `inheritance_weight`. The pre-selection high-trait recruit mass is
bounded below exactly by

```text
r_pre,min = (1-w) p_min + w r_min.
```

This is a closure identity, not a heuristic association between allele frequency
and trait occupancy.

## Viability-selection lower bound

Define

```text
W_H,min = min_{z >= cutoff} max(floor, W(z; q_min))
W_max   = max_{z in grid} max(floor, W(z; 1)).
```

Then selected high-trait recruitment probability has lower bound

```text
pi_H,min >= r_pre,min W_H,min / W_max.
```

The `q_min` lower envelope is valid under non-negative high-interaction benefit.

## Finite realised-trait persistence

Given the update, the aggregate high-trait count is Binomial with cohort size
`N_j,t+1` and high-trait probability at least `pi_H,min`. If

```text
r_min < pi_H,min,
```

then a Chernoff lower-tail bound gives

```text
P(r_H,j,t+1 < r_min)
<= exp[-N_min pi_H,min (1-r_min/pi_H,min)^2 / 2]
= epsilon_H.
```

To ensure that the mass floor also implies the simulator's count-based
realised-occupancy definition, require

```text
r_min N_min >= realised_high_trait_abundance_threshold.
```

For `J` patches and a horizon `T`, the union bound yields

```text
P(all patches retain r_H >= r_min through T)
>= max(0, 1 - T J epsilon_H).
```

This strong all-patch statement is sufficient to prevent the simulator's
all-patch realised-high-trait-loss event. A future refuge-only version can use
an at-least-one-patch event and be less conservative.

## What it does not prove

- that the common region is invariant;
- that migration maintains `p_min` in the same generation;
- potential high-trait viability;
- a genetic lead ordering;
- infinite-horizon persistence;
- an empirical prediction.

## Role in the theorem chain

Together with the network allele-floor theorem, this supplies the key finite-bin
bridge:

```text
common p floor at time t
+ common r_H floor at time t
+ q/N lower region
-> high-probability r_H floor at time t+1.
```

The remaining H2 bottleneck is the expected H-alpha multiplier before sampling.
