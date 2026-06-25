# Realised occupancy phase-diagram experiments

This document describes a simulation/reporting layer for the declared
multi-patch criticality model. These experiments are model-specific stochastic
experiments, not theorems.

## Layer separation

The experiment layer keeps three quantities separate:

```text
potential trait viability:
Omega_tau^potential(q) = {z : W(z; q) >= tau}

realised trait occupancy:
mu_{j,t}(z_k), the resident trait-bin distribution in patch j

genetic persistence:
p_{j,t}, H_alpha, H_gamma, and F_ST
```

The outputs must not infer any one of these directly from another. Potential
high-trait viability loss is not realised trait extinction. Realised high-trait
loss is not allele loss. Allele persistence is not trait-mode recovery.

## Relation to theorem layer

The theorem layer remains separate. The canonical value `A_c = 4/kappa` belongs
only to the canonical logistic reduction where a regression test establishes
that the simulator has reduced to that map. It is not automatically the
threshold of the extended stochastic simulator.

For the extended simulator, reports should use language such as:

```text
model-specific transition region
replicate transition probability
hysteretic regime under the declared update rule
```

Numerical transitions in this experiment layer must not be called universal
critical thresholds.

## Declared realised occupancy closure

Realised trait occupancy depends on the declared recruitment closure:

```text
mu_{j,t+1}(z_k) proportional to
mu_{j,t}(z_k) * max(epsilon, W(z_k; q_{j,t}))
```

This is the named `viability_selection_local_recruitment` closure. It introduces
no mutation, trait-bin dispersal, recolonisation, or genotype-to-trait
architecture. Those are future model extensions.

## Warning times

The experiment layer predeclares warning and first-passage times:

```text
tau_trait_potential
tau_trait_realised
tau_H_alpha
tau_H_gamma
tau_FST
```

Replicates where an event never occurs remain censored for that event. They are
not silently coded as a lead, no-lead, or terminal-generation event.

Genetic lead probabilities are estimated separately:

```text
Pr(tau_H_alpha < tau_trait_realised)
Pr(tau_H_gamma < tau_trait_realised)
Pr(tau_FST < tau_trait_realised)
```

Each probability is computed only among replicate pairs where both events are
observed; the valid-pair count and censored count are reported.

## Fragmentation comparisons

At fixed total habitat area, the scenario constructors compare:

```text
one_large
equal_isolated
equal_migrating
```

For each scenario the experiment output preserves separate patch-level
distributions for:

```text
q
census N
N_e,next_breeder proxy
p
```

The aggregate report also keeps separate:

```text
potential high-trait viability
realised high-trait occupancy
H_alpha
H_gamma
F_ST
first-passage metrics
```

There is deliberately no single field named `diversity`. `H_alpha`, `H_gamma`,
and `F_ST` have distinct meanings and can move in different directions.

## Uncertainty convention

The default uncertainty convention is empirical quantiles across stochastic
replicates: 2.5%, 50%, and 97.5%, plus the replicate mean where meaningful.
This is a reporting convention for finite ensembles, not an asymptotic theorem.

## Profiles

The API provides three profiles:

```text
quick     tiny grid, low replicate count, intended for tests and examples
standard  moderate grid for practical local runs
full      explicit opt-in profile; never run automatically in CI
```

Default tests use only the quick profile.

## Non-goals

This PR does not add mutation, recolonisation, polygenic architecture, trait-bin
mutation, empirical species calibration, universal genetic early-warning claims,
or a claim that `A_genetic > A_ecological`.
