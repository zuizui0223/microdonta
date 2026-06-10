# Mathematical foundations of RACH

**Well-definedness, bounds, and Monte Carlo consistency**

This document proves that RACH is a mathematically well-defined framework for
admissible causal inference under biological constraints. The goal is not to
prove that RACH recovers the true causal mechanism in nature. The goal is to
prove that the objects used by RACH — the admissible causal region and its
information-theoretic summaries — are valid mathematical objects under explicit
assumptions.

---

## 1. Formal setup

A RACH analysis is specified by

```text
RACH = (X, Y, Θ, S, G, f, P_sim, P_obs, d, ε, π)
```

where:

```text
X       fixed ecological context space
Y       independent observation space
Θ       latent parameter space
S       finite causal switch space {0,1}^K
G       biological constraint grammar, G: Θ -> {0,1}
f       generative ecological dynamics, f: X × Θ × S -> Y_sim
P_sim   simulated output to pattern-space map, P_sim: Y_sim -> Z
P_obs   empirical observation to pattern-space map, P_obs: Y -> Z
d       pattern distance, d: Z × Z -> R_{≥0}
ε       admissibility tolerance, ε ≥ 0
π       prior probability measure on Θ × S
```

Let `x_obs ∈ X` be fixed empirical context and `y_obs ∈ Y` be independent
observations. The central object of RACH is the admissible causal region:

```text
A_ε(y_obs, x_obs)
=
{(θ,s) ∈ Θ×S :
  G(θ)=1,
  d(P_sim(f(x_obs;θ,s)), P_obs(y_obs)) ≤ ε}
```

Intuitively, `A_ε` is the subset of latent parameter–mechanism space that is
biologically admissible and can reproduce the independent observations within
tolerance.

Throughout this document, probabilities are with respect to the prior measure
`π` on `Θ × S`, unless stated otherwise.

---

## 2. Proposition 1 — `A_ε` is well-defined

### Statement

Assume that `G`, `f`, `P_sim`, `P_obs`, and `d` are defined as above. Then for
any `x_obs ∈ X`, `y_obs ∈ Y`, and `ε ≥ 0`, the set

```text
A_ε(y_obs, x_obs)
```

is a well-defined subset of `Θ × S`.

### Proof

Take any `(θ,s) ∈ Θ × S`. Since `x_obs ∈ X`, `θ ∈ Θ`, and `s ∈ S`, the
composition

```text
f(x_obs; θ, s)
```

is defined by the domain of `f`. Since `P_sim: Y_sim -> Z`,

```text
P_sim(f(x_obs; θ, s)) ∈ Z
```

is defined. Since `P_obs: Y -> Z`,

```text
P_obs(y_obs) ∈ Z
```

is also defined. Therefore, because `d: Z × Z -> R_{≥0}`,

```text
d(P_sim(f(x_obs; θ, s)), P_obs(y_obs))
```

is a non-negative real number. Finally, since `G: Θ -> {0,1}`, the condition
`G(θ)=1` is a Boolean statement.

Thus, for each `(θ,s) ∈ Θ×S`, the condition

```text
G(θ)=1 and d(P_sim(f(x_obs;θ,s)), P_obs(y_obs)) ≤ ε
```

has a definite truth value. The collection of all `(θ,s)` satisfying that
condition is therefore a subset of `Θ×S`.

Hence `A_ε(y_obs, x_obs)` is well-defined. □

---

## 3. Proposition 2 — Causal admissibility is a valid conditional probability

### Definition

For switch `j`, define the event

```text
B_j = {(θ,s) ∈ Θ×S : s_j = 1}
```

where `s_j` is the `j`th causal switch. If `π(A_ε)>0`, define causal
admissibility as

```text
CA_j = P(s_j=1 | A_ε)
     = π(B_j ∩ A_ε) / π(A_ε)
```

### Statement

If `π(A_ε)>0`, then `CA_j` is uniquely defined and satisfies

```text
0 ≤ CA_j ≤ 1.
```

### Proof

Since `B_j ∩ A_ε ⊆ A_ε`, monotonicity of probability measures gives

```text
0 ≤ π(B_j ∩ A_ε) ≤ π(A_ε).
```

By assumption, `π(A_ε)>0`, so division by `π(A_ε)` is valid. Therefore,

```text
0 ≤ π(B_j ∩ A_ε) / π(A_ε) ≤ 1.
```

Hence

```text
0 ≤ CA_j ≤ 1.
```

The value is unique by the definition of conditional probability on a positive
probability event. □

### Note on empty admissible regions

If `π(A_ε)=0`, then `CA_j` is not mathematically defined. In finite simulation,
this corresponds to zero accepted samples or an approximation to a zero-measure
admissible region. The correct output in this case is not a causal probability,
but "not estimable under the current ε, prior, simulator, and observations."

---

## 4. Proposition 3 — Causal degeneracy is bounded

### Definition

Let

```text
D_RACH = H(S | A_ε)
```

where `H` is Shannon entropy in bits and `S` is the causal switch vector.

### Statement

If `S = {0,1}^K` and `π(A_ε)>0`, then

```text
0 ≤ D_RACH ≤ K.
```

### Proof

The switch vector `S` has at most

```text
|S| = 2^K
```

possible states. Conditional on `A_ε`, `S` is still a discrete random variable
on the same finite state space. For any finite discrete random variable taking
values in a set of size `n`, Shannon entropy satisfies

```text
0 ≤ H ≤ log2(n).
```

Here, `n = 2^K`. Therefore,

```text
0 ≤ H(S | A_ε) ≤ log2(2^K) = K.
```

Thus,

```text
0 ≤ D_RACH ≤ K.
```

□

---

## 5. Proposition 4 — Causal resolvability is bounded

### Definition

Define causal resolvability by normalising causal degeneracy by the maximum
switch entropy:

```text
R_RACH = 1 - H(S | A_ε) / log2|S|.
```

For `S = {0,1}^K`, this becomes

```text
R_RACH = 1 - H(S | A_ε) / K
       = 1 - D_RACH / K.
```

### Statement

If `K>0` and `π(A_ε)>0`, then

```text
0 ≤ R_RACH ≤ 1.
```

### Proof

By Proposition 3,

```text
0 ≤ D_RACH ≤ K.
```

Since `K>0`, division by `K` gives

```text
0 ≤ D_RACH / K ≤ 1.
```

Subtracting from 1 gives

```text
0 ≤ 1 - D_RACH / K ≤ 1.
```

Therefore,

```text
0 ≤ R_RACH ≤ 1.
```

□

### Why max entropy is the safe denominator

It may be tempting to define

```text
R = 1 - H(S | A_ε) / H(S prior).
```

This is not generally safe for non-uniform priors. Conditioning on an event can
increase entropy relative to a strongly biased prior by making the conditional
distribution more uniform. Therefore `H(S | A_ε) ≤ H(S prior)` is not guaranteed.

By using the maximum possible entropy `log2|S| = K`, RACH guarantees that
`R_RACH ∈ [0,1]` regardless of the switch prior.

---

## 6. Proposition 5 — Observation contribution is bounded

### Definition

Let

```text
O = {O_1, ..., O_m}
```

be the set of observation patterns used as `y_obs`. Let `O \ {O_k}` denote the
observation set with pattern `k` removed. If the corresponding admissible
regions are nonempty, define observation contribution as

```text
OC_k = R_RACH(O) - R_RACH(O \ {O_k}).
```

### Statement

If `A_ε(O)` and `A_ε(O \ {O_k})` are nonempty, then

```text
-1 ≤ OC_k ≤ 1.
```

### Proof

By Proposition 4,

```text
0 ≤ R_RACH(O) ≤ 1
```

and

```text
0 ≤ R_RACH(O \ {O_k}) ≤ 1.
```

For any two numbers `a,b ∈ [0,1]`, their difference satisfies

```text
-1 ≤ a - b ≤ 1.
```

Setting

```text
a = R_RACH(O)
b = R_RACH(O \ {O_k})
```

therefore gives

```text
-1 ≤ OC_k ≤ 1.
```

□

### Interpretation

`OC_k` is not required to be positive.

```text
OC_k > 0   pattern k increases causal resolvability
OC_k ≈ 0   pattern k is redundant
OC_k < 0   removing pattern k increases causal resolvability
```

A negative `OC_k` can occur when a pattern is noisy, contradictory, or
over-constraining. Thus, negative contribution is not a mathematical failure;
it is an interpretable diagnostic.

---

## 7. Proposition 6 — Exact NOV is well-defined under finite or integrable candidate outcomes

### Definition

Let `q` be a candidate future observation. Let `Y_q` be the possible outcome
space of `q`. Suppose a predictive distribution

```text
P(y_q | A_ε)
```

is defined over `Y_q`. The exact next-observation value is

```text
NOV(q)
=
E_{y_q ~ P(y_q | A_ε)}
[
  R_RACH(O ∪ {q=y_q}) - R_RACH(O)
].
```

### Statement

If `Y_q` is finite, or if the integrand is measurable and bounded, then
`NOV(q)` is a finite, well-defined expectation.

### Proof

For any possible outcome `y_q ∈ Y_q`, Proposition 4 gives

```text
0 ≤ R_RACH(O ∪ {q=y_q}) ≤ 1
```

and

```text
0 ≤ R_RACH(O) ≤ 1.
```

Therefore,

```text
-1 ≤ R_RACH(O ∪ {q=y_q}) - R_RACH(O) ≤ 1.
```

The integrand is bounded in `[-1,1]`. If `Y_q` is finite, the expectation is a
finite weighted sum and is therefore well-defined. If `Y_q` is not finite but
the integrand is measurable, it is a bounded measurable function and hence
integrable under any probability distribution on `Y_q`.

Thus, `NOV(q)` is well-defined under the stated conditions. □

### Exact NOV versus implemented NOV

The repository currently implements a heuristic proxy for NOV. Exact NOV requires
a predictive distribution over future outcomes `P(y_q | A_ε)`. Without such a
predictive outcome model, the implemented NOV should be interpreted as a
priority score for future data collection, not as exact expected value of
information.

---

## 8. Proposition 7 — Monte Carlo estimators are consistent

### Setup

Let

```text
(θ_i, s_i) ~ π(θ,s),   i = 1,...,n
```

be IID samples from the prior. Define the acceptance indicator

```text
I_i = 1{(θ_i,s_i) ∈ A_ε}
```

and the switch-ON indicator

```text
S_{ij} = 1{s_{ij}=1}.
```

The empirical estimator of `CA_j` is

```text
CA_hat_j = Σ_i I_i S_{ij} / Σ_i I_i.
```

### Statement

If `π(A_ε)>0`, then

```text
CA_hat_j -> CA_j
```

almost surely as `n -> ∞`.

### Proof

By the strong law of large numbers,

```text
(1/n) Σ_i I_i S_{ij} -> E[I_i S_{ij}]
```

almost surely. Since `I_i S_{ij}=1` exactly when `(θ_i,s_i) ∈ A_ε` and
`s_{ij}=1`,

```text
E[I_i S_{ij}] = π(A_ε ∩ B_j).
```

Similarly,

```text
(1/n) Σ_i I_i -> E[I_i] = π(A_ε)
```

almost surely. By assumption `π(A_ε)>0`, the denominator has a nonzero limit.
Therefore, by the continuous mapping theorem,

```text
CA_hat_j
= Σ_i I_i S_{ij} / Σ_i I_i
-> π(A_ε ∩ B_j) / π(A_ε)
= CA_j.
```

Thus, `CA_hat_j` is a strongly consistent estimator of `CA_j`. □

### Consistency of `D_RACH` and `R_RACH`

Because `S={0,1}^K` is finite, the empirical frequencies of all switch states
among accepted samples converge almost surely to the conditional distribution
`P(S=v | A_ε)` for each `v ∈ S`. Shannon entropy on a finite probability simplex
is continuous, so

```text
D_hat_RACH -> D_RACH.
```

Since

```text
R_hat_RACH = 1 - D_hat_RACH / K,
```

it follows immediately that

```text
R_hat_RACH -> R_RACH.
```

□

---

## 9. Main theorem

### Theorem — RACH is a well-defined admissible causal inference framework

Assume:

1. `S = {0,1}^K` with `K>0`.
2. `ε ≥ 0`.
3. `π` is a probability measure on `Θ × S`.
4. `G`, `f`, `P_sim`, `P_obs`, and `d` are defined as in Section 1.
5. `π(A_ε)>0`.

Then RACH defines a well-posed admissible causal inference problem. In particular:

```text
A_ε       is a well-defined subset of Θ×S.
CA_j      is a conditional probability in [0,1].
D_RACH    is a finite entropy in [0,K].
R_RACH    is a normalised resolvability score in [0,1].
OC_k      is an observation contribution score in [-1,1].
NOV(q)    is a finite expected resolvability gain when candidate outcomes are finite or integrable.
```

Furthermore, under IID sampling from `π`, the Monte Carlo estimators of `CA_j`,
`D_RACH`, and `R_RACH` are consistent as the number of prior draws tends to
infinity.

### Proof

The claims follow directly from Propositions 1–7. □

---

## 10. What this theorem does and does not prove

This theorem proves mathematical well-posedness:

```text
RACH defines valid sets, probabilities, entropies, bounded scores, and consistent Monte Carlo estimators under explicit assumptions.
```

It does **not** prove causal truth in nature.

RACH identifies which mechanisms remain admissible under a specified simulator,
constraint grammar, prior, distance function, tolerance, fixed context, and
independent observations:

```text
RACH proves admissibility, not causal truth.
```

Therefore, empirical claims from RACH must be evaluated through:

```text
prior sensitivity
epsilon sensitivity
pattern-weight sensitivity
known-truth recovery
independent validation observations
manipulative experiments where possible
```

High causal degeneracy is not a failure. It means the current observation set is
insufficient to distinguish competing mechanisms. In this sense, RACH also
quantifies the limits of inference and helps identify which additional
observations would most improve causal resolution.

---

## 11. Implementation correspondence

The mathematical quantities above correspond to repository functions as follows:

| Mathematical object | Repository implementation |
|---|---|
| `A_ε` | accepted rows from `run_switch_posterior_inference*` |
| `π` sampling | `parameter_sampling.py` and switch-state sampling |
| `G(θ)` | `parameter_constraints.py` |
| `f(x_obs;θ,s)` | `campanula_phenomenological.py` or ABM `simulate_population()` |
| `P_sim`, `P_obs`, `d` | `pattern_evaluator.py`, `abc_distance.py` |
| `CA_j` | `causal_admissibility()` / posterior table |
| `D_RACH` | `causal_degeneracy()` |
| `R_RACH` | `causal_resolvability()` |
| `OC_k` | `observation_contribution(evaluated_rows, ...)` |
| `NOV(q)` | `next_observation_value()` heuristic proxy |

The implemented `observation_contribution()` correctly uses `evaluated_rows`,
not only `accepted_rows`, so that removing one observation pattern can allow
previously rejected samples to enter the leave-one-out admissible region.
