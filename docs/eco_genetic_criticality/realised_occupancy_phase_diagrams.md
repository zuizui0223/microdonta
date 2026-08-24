# Realised occupancy phase-diagram experiments

This module is a **simulation/reporting** layer for the declared multi-patch
criticality model. It is not a theorem engine.

## Three distinct state layers

```text
potential trait viability:
Omega_tau^potential(q) = {z : W(z;q) >= tau}

realised trait occupancy:
n_{j,t}(z_k), with mu_{j,t}(z_k)=n_{j,t}(z_k)/sum_l n_{j,t}(z_l)

genetic persistence:
p_{j,t}, H_alpha, H_gamma, F_ST
```

Potential high-trait viability loss is not realised trait loss. Realised trait
loss is not allele loss. Allele persistence is not trait-mode recovery.

## Relation to the theorem layer

The canonical value `A_c = 4/kappa` belongs only to the canonical logistic
reduction. It is not automatically the threshold of this extended stochastic
model. Reports use terms such as:

```text
model-specific transition region
replicate transition probability
hysteretic regime under the declared update rule
```

No numerical transition here is a universal critical threshold.

## Occupancy and recruitment closures

The API keeps a small deterministic profile for fast tests, but the `standard`
and `full` profiles use the finite ecological-genetic closure:

```text
trait_occupancy_mode = finite_trait_bin_recruitment
genotype_trait_recruitment = two_kernel_recruitment
```

For finite occupancy, the next trait-bin cohort is sampled from a multinomial
recruitment distribution after viability weighting. This permits genuine bin
extinction:

```text
n_{j,t+1}(z_k) ~ Multinomial(N_{j,t+1}, pi_{j,t}(z_k)).
```

The two-kernel recruitment closure is explicitly model-specific:

```text
rho_{j,t}(z_k)
= (1-p_{j,t}) K_L(z_k) + p_{j,t} K_H(z_k)
```

and is mixed with resident trait composition by `inheritance_weight`. It is not
called Mendelian inheritance, mutation, or a polygenic architecture.

The interaction update may use declared weights on current interaction,
realised high-trait mass, and allele frequency. Trait-only, allele-proxy, and
coupled feedback are distinct parameter settings.

## Realised high-trait measures

For the declared high-trait region `Z_H`, reports keep both:

```text
N_H,j,t = sum_{z_k in Z_H} n_{j,t}(z_k)
x_H,j,t = N_H,j,t / N_j,t
```

A realised high trait is occupied only when `N_H,j,t` exceeds the predeclared
abundance threshold in finite mode. This is separate from its potential
viability under `W(z;q)`.

## First-passage events and censoring

Every replicate records `FirstPassageEvent` metadata:

```text
name
occurred
time
censored
threshold
aggregation_rule
```

The predeclared events are:

```text
tau_trait_potential
tau_trait_realised
tau_allele_loss
tau_H_alpha
tau_H_gamma
tau_FST
```

Trait and allele loss use the explicit `all_patch_loss` aggregation. Diversity
warnings use the declared metapopulation-weighted rule. Replicates where an
event does not occur remain censored; they are not silently converted to a
terminal-generation event or to no-lead.

The report separately estimates, among valid event pairs:

```text
Pr(tau_H_alpha < tau_trait_realised)
Pr(tau_H_gamma < tau_trait_realised)
Pr(tau_FST < tau_trait_realised)
Pr(tau_allele_loss < tau_trait_realised)
```

## Fragmentation comparisons

At fixed total habitat area, scenarios compare:

```text
one_large
equal_isolated
equal_migrating
```

For each scenario, retain patch-level `q`, census `N`, `N_e,next_breeder`, `p`,
and high-trait abundance. Aggregate reports separately retain potential trait
viability, realised occupancy, allele loss, `H_alpha`, `H_gamma`, and `F_ST`.
There is deliberately no single field named `diversity`.

## Uncertainty and profiles

Uncertainty uses empirical 2.5%, 50%, and 97.5% quantiles across replicates.

```text
quick     deterministic compatibility profile for tests/examples
standard  finite-bin, two-kernel, coupled-feedback local experiment
full      larger explicit opt-in finite-bin experiment; never CI
```

## Non-goals

This phase-diagram layer does not add mutation, recolonisation, seed banks,
polygenic inheritance, empirical calibration, universal genetic-warning claims,
or a claim that `A_genetic > A_ecological`.