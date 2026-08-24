# Stochastic refuge invariance for the finite-bin closure

## Scope

This theorem is an exact specialisation of the simulator to one designated
refuge patch with:

```text
trait_occupancy_mode = finite_trait_bin_recruitment
recruitment closure  = two_kernel_recruitment
migration_rate       = 0.
```

It is not yet a theorem for arbitrary multipatch migration. The refuge result
is useful because the simulator defines realised trait loss as all-patch loss:
if one refuge retains realised high-trait occupancy, all-patch loss has not yet
occurred.

## Region

Let the refuge state satisfy

```text
q_t >= q_min
p_t >= p_min
r_H,t >= r_min
N_min <= N_t <= N_max.
```

The certificate checks whether deterministic update envelopes return `q` and
`N` to the same rectangle. It separately bounds the two finite-sampling
failures which can break the lower allele and high-trait conditions.

## Deterministic envelopes

The interaction update is monotone in each state coordinate when all feedback
weights are nonnegative. Therefore the lower envelope is

```text
q_next_min = sigmoid[
  feedback * ((A/A_ref) min(1, N_min/K)
  * (alpha q_min + beta r_min + gamma p_min) - barrier)
].
```

The selected high-allele probability has lower envelope

```text
p_sel_min = p_min f_H(q_next_min)
            / [p_min f_H(q_next_min) + 1-p_min].
```

The density-dependent population equation gives a lower envelope from
`N_min`, `N_max`, `q_next_min`, and `p_sel_min`, and an upper envelope from the
opposite monotone bounds. The code uses safe lower/upper envelopes for Python
half-even rounding.

## Stochastic envelopes

Conditional on the declared region, the high-trait count is bounded below by a
Binomial recruitment variable with cohort lower bound `n_min` and selected
high-trait probability lower bound `pi_min`. Chernoff's inequality bounds the
chance of falling below `r_min`.

Likewise, with no migration, allele sampling is Binomial with selected allele
probability at least `p_sel_min` and a lower gene-copy bound from the lower
effective population size. Chernoff's inequality bounds the chance that the
sampled allele frequency falls below `p_min`.

If the deterministic rectangle closes and the two one-step failure bounds are
`eps_p` and `eps_r`, then

```text
P(refuge remains in the region for one step) >= 1 - eps_p - eps_r.
```

For a finite horizon `T`, conditional reapplication plus a union bound gives

```text
P(refuge remains in the region through T)
>= max(0, 1 - T(eps_p + eps_r)).
```

## Relation to H2 and L4

The certificate supplies a concrete, closure-derived high-probability trait
persistence event for one patch. Combining it with an independently established
expected H-alpha contraction bound gives a route to L4:

```text
P(tau_H <= t < tau_trait_realised)
```

can be bounded below without treating simulation output as a theorem premise.

## Limits

The theorem does not prove:

- invariant regions under nonzero migration;
- a universal genetic warning;
- a global metapopulation theorem;
- an empirical prediction for any named system.
