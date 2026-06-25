# Multi-patch eco-genetic criticality simulation contract

## Role

This is a dynamic **simulation model**, not a proof engine. It is designed to
probe the three central hypotheses after the theorem layer:

```text
H_critical       discontinuous high-investment trait-mode transition
H_genetic_lag    genetic warning before trait-mode loss
H_fragmentation  fixed-total-area subdivision can prevent maintenance.
```

Every model-specific assumption is exposed below.

---

## State in patch j at generation t

```text
A_j       fixed patch area
N_j,t     census population size
q_j,t     interaction availability in [0,1]
p_j,t     frequency of a declared high-investment allele
N_e,j,t   effective reproductive size proxy
Omega_j,t viable trait set on a fixed continuous trait grid.
```

The high-investment trait region is the upper part of the grid. Its occupancy and
the number of viable components are recorded; neither is inferred from the allele
frequency alone.

---

## Declared model equations

### 1. Interaction update

```text
q_j,t+1 = sigma{kappa[(A_j/A_ref) D_j,t (alpha q_j,t + (1-alpha)p_j,t)-theta]},
```

where

```text
D_j,t = min(1, N_j,t / K_j),
K_j = density_capacity * A_j.
```

This assumes patch area, local density, current interaction state, and
high-investment composition jointly support interaction availability. It is not
the general theorem map, although it retains its positive-feedback character.

### 2. Trait-space fitness surface

For z in [0,1],

```text
W(z;q) = low_base - low_cost*z^2
       + [high_base + high_interaction_benefit*q]
         exp[-((z-1)/high_peak_width)^2].
```

```text
Omega_tau(q) = {z:W(z;q)>=tau}.
```

This deliberately permits a low-investment viable component near z=0 and a
separate high-investment component near z=1. The model records the high-component
presence and total connected-component count on the declared grid.

### 3. Trait-associated selection

The high allele has relative fitness

```text
w_H(q)=max(epsilon, 1 + selection_strength*[W(1;q)-tau]),
w_L=1.
```

and post-selection frequency is

```text
p*_j = p_j w_H / [p_j w_H + (1-p_j)w_L].
```

This is an explicit genotype-to-high-route assumption, not a universal genetic
architecture.

### 4. Demography and effective reproductive size

```text
N_j,t+1 = round{N_j,t exp[r0 + r_q q_j,t+1 + r_H p*_j - N_j,t/K_j]},
N_e,j,t = max(1, effective_fraction*N_j,t*(1-skew_penalty*q_j,t)).
```

The skew penalty is included because interaction can increase reproductive skew.
The sign of the interaction-to-N_e relation is therefore testable rather than
hard-wired as a general truth.

### 5. Migration and finite transmission

After selection, island-model migration gives

```text
p^mig_j=(1-m)p*_j + m p*_weighted_mean.
```

Transmission is diploid Wright--Fisher sampling for this **simulation instance**:

```text
2N_e,j,t p_j,t+1 ~ Binomial(2N_e,j,t,p^mig_j).
```

Mutation may be added later; the initial model uses an explicit zero-mutation
policy rather than silently assuming perpetual variation.

---

## Outputs

At each generation report separately:

```text
q_j,t
N_j,t
N_e,j,t
p_j,t
high-trait viable-component presence
number of viable trait-space components
H_alpha,t
H_gamma,t
F_ST,t.
```

Definitions:

```text
H_alpha = weighted mean_j 2p_j(1-p_j)
p_bar   = weighted mean_j p_j
H_gamma = 2p_bar(1-p_bar)
F_ST    = 1-H_alpha/H_gamma when H_gamma>0.
```

---

## Hypothesis tests and counterexamples

### H_critical

A run supports the model-specific version only if a parameter sweep reveals a
branch or sharply discontinuous high-component transition, and a nearby sweep
shows the threshold is not a grid artefact.

### H_genetic_lag

Predeclare

```text
tau_trait: first generation with no high-investment viable component
tau_H: first generation H_alpha crosses a warning threshold
tau_var: first generation allele-frequency spatial variance crosses threshold
tau_auto: first generation spatial autocorrelation crosses threshold.
```

A genetic lead means a predeclared inequality such as `tau_H<tau_trait`. It is
not declared from visually chosen trajectories.

### H_fragmentation

Compare equal total area across:

```text
one large patch
m isolated equal patches
m equal patches with controlled migration.
```

A result where H_alpha declines but H_gamma persists or F_ST rises is an expected
counterexample to any simplistic 'fragmentation lowers diversity' statement.
