# Conditional network allele-floor theorem

## Question

When does migration preserve a metapopulation-wide lower allele bound rather
than eroding a local refuge?

The answer depends on whether the lower bound is shared by every source patch.
This theorem treats that common-floor case exactly for the selection--migration
--sampling order used by the finite-bin simulator.

## Declared state region

Fix `J` patches and a finite horizon `T`. Suppose at the start of each step:

```text
p_j >= p_min              for every patch j,
q_j >= q_min              for every patch j,
N_j,next >= N_min         for every patch j.
```

The last two conditions are region premises. This theorem does not prove them.

Assume additionally:

```text
high_interaction_benefit >= 0
selection_strength >= 0.
```

These make the high-allele selection update monotone in `q`.

## Local selection

The simulator's high-allele update before migration is

```text
p_j^sel = p_j f_H(q_j) / [p_j f_H(q_j) + 1-p_j],
```

where

```text
f_H(q) = max(epsilon, 1 + selection_strength * [W(1;q)-viability_threshold]).
```

Under the declared conditions,

```text
p_j^sel >= s_min
```

with

```text
s_min = p_min f_H(q_min) / [p_min f_H(q_min) + 1-p_min].
```

## Migration lemma

The simulator then uses the census-weighted selected mean:

```text
p_bar^sel = sum_j N_j p_j^sel / sum_j N_j
p_j^mig   = (1-m) p_j^sel + m p_bar^sel.
```

Because every selected patch is at least `s_min`, so is their weighted mean.
Therefore exactly

```text
p_j^mig >= s_min
```

for every patch and every migration rate `m` in `[0,1]`.

Migration is neutral with respect to a **common** lower bound. It neither
reduces nor improves the theorem's common-floor envelope. This does not
contradict local rescue or local erosion: those occur when source and focal
lower bounds differ.

## Finite sampling

The simulator samples at least

```text
M_min = max(2, round_lower(2 effective_fraction N_min (1-skew_penalty)))
```

gene copies per patch. When `s_min > p_min`, Chernoff's lower-tail inequality
bounds the probability that one patch falls below the original floor:

```text
P(p_j,next < p_min)
<= exp[-M_min s_min (1-p_min/s_min)^2 / 2] = epsilon_p.
```

A union bound gives

```text
P(any patch breaks the common floor in one step) <= J epsilon_p,
P(all patches retain the floor through T) >= max(0, 1-T J epsilon_p).
```

## What this theorem establishes

Under its stated region premises, the theorem proves a high-probability,
finite-horizon common allele floor for a network with migration.

It does not establish:

- a lower bound on interaction or census size;
- realised high-trait occupancy;
- trait-bin persistence;
- a genetic lead ordering;
- a non-common local refuge under low-frequency sources;
- an infinite-horizon persistence result.

## Connection to H2 and H3

The theorem is a new intermediate layer:

```text
common q/N lower region
-> common allele-floor retention under selection + migration + sampling
-> candidate source-mean premise for a migration-aware refuge certificate.
```

It cleanly separates two mechanisms that phase diagrams can otherwise blur:

```text
connectivity as common-floor preservation
versus
connectivity as local rescue/erosion when floors differ.
```
