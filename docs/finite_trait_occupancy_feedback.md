# Finite trait occupancy and feedback closure

This document describes a simulation closure, not a theorem. It makes realised
trait occupancy, allele persistence, and interaction feedback causally connected
enough for later phase-diagram experiments, while keeping all assumptions named.

## Deterministic composition versus finite abundance

The backward-compatible mode is:

```text
trait_occupancy_mode = deterministic_viability_selection
```

It updates only the realised composition:

```text
mu_{j,t+1}(z_k) proportional to mu_{j,t}(z_k) max(epsilon, W(z_k; q_{j,t})).
```

Because every initially positive bin remains positive when `epsilon > 0`,
component counts in this deterministic mode are composition summaries, not true
finite-bin extinction events.

The finite mode is:

```text
trait_occupancy_mode = finite_trait_bin_recruitment
```

It tracks abundance:

```text
n_{j,t}(z_k)
mu_{j,t}(z_k) = n_{j,t}(z_k) / sum_l n_{j,t}(z_l)
```

Trait-bin recruitment uses a multinomial draw, so a bin can truly disappear in a
finite replicate.

## Potential viability versus realised occupancy

Potential viability is still:

```text
Omega_tau^potential(q) = {z : W(z; q) >= tau}.
```

Realised high-trait occupancy in finite mode is abundance-based:

```text
N_H,j,t = sum_{z_k in Z_H} n_{j,t}(z_k)
x_H,j,t = N_H,j,t / N_j,t
realised high-trait occupied iff
N_H,j,t >= realised_high_trait_abundance_threshold.
```

Potential high-trait viability and realised high-trait occupancy are not
substitutes for one another.

## Realised occupancy versus allele persistence

The high allele frequency `p_{j,t}` remains a separate state variable. Allele
persistence does not imply realised high-trait occupancy, and realised
high-trait occupancy does not imply allele persistence. The simulator reports
`tau_allele_loss`, `tau_trait_realised`, `H_alpha`, `H_gamma`, and `F_ST`
separately.

## Two-kernel genotype-to-trait recruitment closure

The optional closure is:

```text
genotype_trait_recruitment = two_kernel_recruitment
```

with declared kernels:

```text
K_L(z_k)  low-trait recruitment kernel
K_H(z_k)  high-trait recruitment kernel
rho_{j,t}(z_k) =
  (1 - p_{j,t}) K_L(z_k) + p_{j,t} K_H(z_k).
```

The recruit distribution is:

```text
pi_{j,t}(z_k) proportional to
[
  (1 - inheritance_weight) rho_{j,t}(z_k)
  + inheritance_weight mu_{j,t}(z_k)
]
W(z_k; q_{j,t}).
```

This is a declared genotype-to-trait recruitment closure. It is not called
Mendelian inheritance. The first implementation uses low and high kernels with
separate low/high trait regions, so no mutation or across-bin trait dispersal is
introduced by default.

## Realised-trait feedback versus allele-proxy feedback

The old feedback path is preserved unless the explicit feedback parameters are
used. The new explicit form is:

```text
q_{j,t+1} =
sigma(
  kappa[
    (A_j/A_ref) D_j,t
    (alpha_q q_{j,t}
     + beta_trait x_H,j,t
     + gamma_allele p_{j,t})
    - theta
  ]
)
```

Supported modes include:

```text
trait-only feedback:
beta_trait > 0, gamma_allele = 0

allele-proxy feedback:
beta_trait = 0, gamma_allele > 0

coupled feedback:
beta_trait > 0, gamma_allele > 0

canonical reduction:
beta_trait = 0, gamma_allele = 0, density = 1, alpha_q = 1
```

The canonical reduction is a regression-tested simulator mode. The regression
test is not a mathematical proof.

## First-passage recording

Detailed first-passage records retain:

```text
event occurred boolean
event time or None
censored status
threshold used
aggregation rule
```

The default loss events use `all_patch_loss`. Genetic diversity summaries use
`metapopulation_weighted_loss`.

## Limitations

This PR does not add mutation, recolonisation, seed banks, multiple loci,
polygenic trait models, empirical calibration, phase diagrams, universal genetic
early-warning claims, or a claim that `A_genetic` is always larger than
`A_ecological`.

All findings remain model-specific simulation results under the declared
closures.
