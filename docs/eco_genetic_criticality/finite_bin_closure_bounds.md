# Finite-bin closure bounds for L4

## Purpose

L4 gives a high-probability lower bound for

```text
P(tau_H <= t < tau_trait_realised).
```

It needs three quantities:

```text
lambda_bar  : expected H-alpha multiplier upper bound
n_min       : recruitment cohort lower bound
pi_min      : high-trait recruit probability lower bound.
```

This document identifies which of these are algebraic consequences of the
finite-bin simulator and which remain invariant-region premises.

## Declared refuge-patch region

Choose one patch which is sufficient to prevent the simulator's all-patch
realised-trait-loss event. Assume it stays in the declared region:

```text
q_t >= q_min
p_t >= p_min
r_H,t >= r_min
N_min <= N_t <= N_max
q_(t+1) >= q_next_min
p_selected,t >= p_selected_min.
```

This is an assumption ledger, not a trajectory estimate. Establishing that the
region is invariant is a separate theorem problem.

## High-trait recruitment probability

The finite-bin closure uses two truncated kernels. The low kernel has support
below `high_trait_cutoff` and the high kernel has support at or above it. Let
`w` be `inheritance_weight`. Before viability selection, high-trait recruit mass
is bounded below by

```text
r_pre,min = (1-w) p_min + w r_min.
```

The selected distribution is proportional to recruit mass times

```text
max(trait_selection_floor, W(z; q_t)).
```

Define

```text
W_H,min = min_{z >= cutoff} max(floor, W(z; q_min))
W_max   = max_{z in grid} max(floor, W(z; 1)).
```

Then the selected high-trait recruit probability satisfies

```text
pi_min >= r_pre,min W_H,min / W_max.
```

This is implemented in `finite_bin_trait_recruitment_bound`.

## Cohort-size bound

The simulator update is

```text
N_(t+1) = max(1, round[N_t exp(b + g_q q_(t+1) + g_p p_selected,t - N_t/K)]).
```

where `K = density_capacity * patch_area`. The declared region yields the safe
lower exponent

```text
eta_min = b + g_q q_next_min + g_p p_selected_min - N_max/K.
```

Therefore

```text
N_(t+1) >= max(1, ceil[N_min exp(eta_min) - 1/2]).
```

The `ceil(x-1/2)` form is safe for Python's banker rounding.

## H-alpha multiplier: what can and cannot be derived

Conditional on the pre-sampling allele frequency, the simulator samples

```text
M = max(2, round(2 N_e))
```

copies. Wright--Fisher sampling gives the exact conditional relation

```text
E[H_after_sampling | H_before_sampling] = (1 - 1/M) H_before_sampling.
```

With a region upper bound on census size, one gets a finite upper bound
`M_max`, hence a sampling multiplier at most

```text
1 - 1/M_max.
```

But selection and migration act before sampling and can increase H-alpha.
Consequently the full expected multiplier requires a separately proved premise

```text
E[H_before_sampling | H_t] <= rho H_t.
```

The closure-derived result is only

```text
lambda_bar <= rho (1 - 1/M_max).
```

The theorem machinery refuses to claim L4 readiness unless this quantity is
strictly below one.

## Scope

This layer derives L4 ingredients from a declared invariant region. It does
not prove the region is invariant, estimate its bounds from simulations, or
project the result to an empirical system.
