# RACH: Mathematical Foundations

This document states the well-definedness conditions, metric bounds, and Monte Carlo
consistency properties of the RACH admissible causal region.

> **Important scope:** the theorem below proves admissibility well-posedness, not
> causal truth. RACH identifies mechanisms that remain admissible under specified
> model assumptions; it does not prove the true causal mechanism in nature.

---

## 1. Formal setup

Let:

```text
X       fixed ecological context space
Y       independent empirical observation space
Θ       latent ecological parameter space
S       finite causal switch space {0,1}^K
G       biological constraint grammar, G : Θ → {0,1}
f       generative simulator, f : X × Θ × S → Y_sim
P_sim   simulated-output pattern extractor, P_sim : Y_sim → P
P_obs   empirical-observation pattern extractor, P_obs : Y → P
d       pattern distance, d : P × P → R_{≥0}
ε       tolerance threshold, ε ≥ 0
π       probability measure on Θ × S
```

For fixed empirical context `x_obs ∈ X` and independent observations
`y_obs ∈ Y`, define the admissible causal region:

```text
A_ε(y_obs, x_obs)
=
{ (θ, s) ∈ Θ × S :
    G(θ) = 1
    and d(P_sim(f(x_obs; θ, s)), P_obs(y_obs)) ≤ ε }
```

This is the central inferential object of RACH.

**Worked-example instantiation (Campanula).** The abstract objects above are
realised, in the Izu Islands example, as follows. The pattern space `P` is the
product of **ordinal gradient directions** `{+, −, ~}` (one per observed variable),
where each direction is the sign of a trait's monotone trend along the
island-isolation axis (`x_obs = distance_from_mainland`) — **not** a pairwise
endpoint contrast. `P_obs(y_obs)` is the source-confirmed observed direction of
each gradient (current y_obs: selfing `+`, flower-size `−`); `P_sim` is the same
sign extracted from the simulated population gradient; and
`d(P_sim, P_obs) = 1 − weighted_match_rate` is the weight-normalised fraction of
gradient directions that disagree. The propositions below hold for this
instantiation because `P` is finite and `d ∈ [0, 1]`.

---

## 2. Proposition 1 — A_ε is well-defined

### Statement

If `G`, `f`, `P_sim`, `P_obs`, and `d` are defined as above, then for any
`x_obs ∈ X`, `y_obs ∈ Y`, and `ε ≥ 0`, the set `A_ε(y_obs, x_obs)` is a
well-defined subset of `Θ × S`.

### Proof

Take any `(θ,s) ∈ Θ × S`. Since `x_obs ∈ X`, `θ ∈ Θ`, and `s ∈ S`,
`f(x_obs; θ, s)` is defined. Since `P_sim` maps simulated outputs into the
pattern space, `P_sim(f(x_obs; θ, s))` is defined. Since `P_obs` maps empirical
observations into the same pattern space, `P_obs(y_obs)` is also defined.
Therefore `d(P_sim(f(x_obs;θ,s)), P_obs(y_obs))` is a non-negative real number.

The condition

```text
G(θ)=1 and d(P_sim(f(x_obs;θ,s)), P_obs(y_obs)) ≤ ε
```

therefore has a definite truth value for every `(θ,s) ∈ Θ×S`. The collection of
all points satisfying this condition is a subset of `Θ×S`. Thus `A_ε` is
well-defined. □

### Note on non-emptiness

This proposition does **not** claim that `A_ε` is nonempty or has positive prior
measure. Non-emptiness is an empirical/model-specific property. All conditional
RACH quantities below require:

```text
π(A_ε) > 0.
```

If `π(A_ε)=0`, the admissible region is empty under the specified prior,
simulator, constraints, distance function, tolerance, context, and observations.
In that case, causal admissibility and entropy summaries are not estimable under
that configuration.

---

## 3. Proposition 2 — Causal admissibility is a valid conditional probability

For switch `j`, define:

```text
B_j = {(θ,s) ∈ Θ×S : s_j = 1}
```

If `π(A_ε)>0`, define:

```text
CA_j = P(s_j=1 | A_ε)
     = π(B_j ∩ A_ε) / π(A_ε)
```

### Statement

If `π(A_ε)>0`, then `CA_j` is uniquely defined and satisfies:

```text
0 ≤ CA_j ≤ 1.
```

### Proof

Because `B_j ∩ A_ε ⊆ A_ε`, monotonicity of probability gives:

```text
0 ≤ π(B_j ∩ A_ε) ≤ π(A_ε).
```

Since `π(A_ε)>0`, division by `π(A_ε)` gives:

```text
0 ≤ π(B_j ∩ A_ε)/π(A_ε) ≤ 1.
```

Therefore `0 ≤ CA_j ≤ 1`. □

---

## 4. Proposition 3 — Causal degeneracy is bounded

Define causal degeneracy:

```text
D_RACH = H(S | A_ε)
       = -Σ_{s ∈ {0,1}^K} P(S=s | A_ε) log2 P(S=s | A_ε)
```

where terms with probability zero are treated as zero.

### Statement

If `S={0,1}^K` and `π(A_ε)>0`, then:

```text
0 ≤ D_RACH ≤ K.
```

### Proof

The switch vector has at most `|S| = 2^K` states. Conditional on `A_ε`, `S` is
still a finite discrete random variable on the same state space. Entropy of a
finite discrete variable with `n` possible states is bounded by `log2(n)`.
Therefore:

```text
0 ≤ H(S | A_ε) ≤ log2(2^K) = K.
```

Hence `0 ≤ D_RACH ≤ K`. □

---

## 5. Proposition 4 — Causal resolvability is bounded

Define causal resolvability by normalising by the maximum switch entropy:

```text
R_RACH = 1 - H(S | A_ε) / log2|S|
```

For `S={0,1}^K`, this is:

```text
R_RACH = 1 - H(S | A_ε) / K
       = 1 - D_RACH / K.
```

### Statement

If `K>0` and `π(A_ε)>0`, then:

```text
0 ≤ R_RACH ≤ 1.
```

### Proof

By Proposition 3, `0 ≤ D_RACH ≤ K`. Since `K>0`,

```text
0 ≤ D_RACH/K ≤ 1.
```

Subtracting from one gives:

```text
0 ≤ 1 - D_RACH/K ≤ 1.
```

Thus `0 ≤ R_RACH ≤ 1`. □

### Why the denominator is K, not H(S_prior)

For non-uniform priors, event conditioning can increase entropy relative to the
prior. Therefore `H(S|A_ε) ≤ H(S_prior)` is not guaranteed. Using the maximum
switch entropy `log2|S| = K` guarantees that `R_RACH` is bounded in `[0,1]`
regardless of prior choice.

---

## 6. Proposition 5 — Observation contribution is bounded

Let `O={o_1,...,o_M}` be the set of observation patterns. Let `O\{o_k}` denote
removing pattern `k`. If both corresponding admissible regions are nonempty,
define:

```text
OC_k = R_RACH(O) - R_RACH(O \ {o_k})
```

### Statement

If `A_ε(O)` and `A_ε(O\{o_k})` have positive prior measure, then:

```text
-1 ≤ OC_k ≤ 1.
```

### Proof

By Proposition 4, both `R_RACH(O)` and `R_RACH(O\{o_k})` lie in `[0,1]`. The
difference of two numbers in `[0,1]` lies in `[-1,1]`. Therefore
`-1 ≤ OC_k ≤ 1`. □

### Sign and non-monotonicity

`OC_k` **may be negative.** A negative `OC_k` means that *removing* pattern `k`
*increases* causal resolvability — which happens when `k` is noisy,
contradictory, or over-constraining relative to the other patterns. Equivalently,
observation contribution is **not monotone**: adding or removing an observation
does not guarantee a monotonic increase in `R_RACH`, because conditioning on the
extra pattern can make the retained switch distribution either more or less
entropic. Reporting only `|OC_k|` or assuming `OC_k ≥ 0` is therefore incorrect.

### Implementation requirement

`OC_k` must be computed from all evaluated draws, not only accepted draws. When
pattern `k` is removed, some previously rejected draws may become accepted. Using
only accepted rows underestimates or biases leave-one-out observation
contribution.

---

## 7. Proposition 6 — Exact NOV is well-defined under finite or integrable candidate outcomes

Let `q` be a candidate future observation with possible outcomes `Y_q`. If a
predictive distribution `P(y_q | A_ε)` is defined, exact next-observation value
is:

```text
NOV(q) = E_{y_q ~ P(y_q | A_ε)} [ R_RACH(O ∪ {q=y_q}) - R_RACH(O) ]
```

### Statement

If `Y_q` is finite, or if the integrand is measurable and bounded, then `NOV(q)`
exists as a finite expectation.

### Proof

By Proposition 4, for any candidate outcome `y_q`:

```text
0 ≤ R_RACH(O ∪ {q=y_q}) ≤ 1
0 ≤ R_RACH(O) ≤ 1
```

so the difference lies in `[-1,1]`. A bounded function is integrable under a
probability measure when it is measurable. If `Y_q` is finite, the expectation is
a finite weighted sum. Thus `NOV(q)` is well-defined under the stated
conditions. □

### Exact NOV versus heuristic NOV

The current app may report a heuristic NOV priority score. Exact NOV requires a
predictive distribution over possible outcomes of `q`. Without that outcome
model, NOV should be described as a heuristic causal-resolution priority score,
not exact EVSI. Proposition 6′ supplies the missing outcome model constructively
for quantitative observations.

### Proposition 6′ — Constructive admissible-region EVSI on resolvability

Let a quantitative candidate observation be a measurable function of the
admissible draw, `q = g(θ, s)` (the simulated value the measurement would take).
Take the predictive distribution `P(y_q | A_ε)` to be the **pushforward of the
restricted prior `π|A_ε` under `g`** — i.e. outcomes are weighted by the mass of
the admissible region that predicts them — and define the conditioned region at
measurement tolerance `τ`:

```text
A_ε | {q = v} = { (θ, s) ∈ A_ε : |g(θ, s) − v| ≤ τ }

EVSI(q) = Σ_v P(y_q = v | A_ε) · [ R_RACH(A_ε | {q=v}) − R_RACH(A_ε) ]
```

**Claim 1 (well-defined, bounded).** `EVSI(q)` exists and lies in `[-1, 1]`.
*Proof.* `g` is measurable and the outcome support is the (finite, when sampled)
image of `A_ε`; by Proposition 4 each bracket lies in `[-1,1]`, and a
probability-weighted average of values in `[-1,1]` lies in `[-1,1]`. It is a
special case of Proposition 6 with `P(y_q|A_ε)` the pushforward measure. □

**Claim 2 (exactness — no re-inference needed).** If the simulator `f` is
deterministic in `(θ, s)` given `x_obs`, then conditioning a *fresh* ABC run on
the augmented observation `q=v` accepts exactly the sub-region
`A_ε | {q=v}` obtained by *filtering the existing admissible region*. Hence the
EVSI computed from the stored admissible draws equals the EVSI obtained by
re-running inference with `q` added.
*Proof.* With deterministic `f`, acceptance of `(θ,s)` under the augmented target
`O ∪ {q=v}` holds iff `(θ,s)` was accepted under `O` (it satisfies the original
patterns) **and** `|g(θ,s) − v| ≤ τ` (it satisfies the added pattern). That is
exactly membership of `A_ε | {q=v}`. The resolvability of the two identical sets
is identical. □

**Claim 3 (unbiasedness).** `EVSI(q)` equals the predictive mean of the realised
resolvability gain: `EVSI(q) = E_{v ~ P(y_q|A_ε)}[ R_RACH(A_ε|{q=v}) − R_RACH(A_ε) ]`.
*Proof.* Immediate from the definition; the realised gain at an outcome `v` is the
bracket, and `EVSI(q)` is its `P(y_q|A_ε)`-weighted average. □

These three claims are verified empirically by `causal_model/nov_calibration.py`:
Claim 2 gives a perfect 1:1 match between the filter-based and re-inference gains,
and Claim 3 underlies the positive calibration of `EVSI(q)` against realised gains
across true states. Proposition 6′ therefore upgrades NOV from a heuristic priority
score to a **constructive, validated EVSI** for quantitative observations, while
ordinal-only candidates without an outcome model remain heuristic.

---

## 8. Proposition 7 — Monte Carlo estimators are consistent

Let `(θ_i,s_i) ~ π(θ,s)` be IID prior draws. Define:

```text
I_i = 1{(θ_i,s_i) ∈ A_ε}
S_ij = 1{s_ij = 1}
```

The empirical estimator of causal admissibility is:

```text
CA_hat_j = Σ_i I_i S_ij / Σ_i I_i.
```

### Statement

If `π(A_ε)>0`, then:

```text
CA_hat_j → CA_j
```

almost surely as the number of prior draws tends to infinity.

### Proof

By the strong law of large numbers:

```text
(1/n)Σ_i I_i S_ij → E[I_i S_ij] = π(A_ε ∩ B_j)
(1/n)Σ_i I_i     → E[I_i]       = π(A_ε)
```

almost surely. Since `π(A_ε)>0`, the denominator has a nonzero limit. The ratio
therefore converges almost surely to:

```text
π(A_ε ∩ B_j) / π(A_ε) = CA_j.
```

Thus `CA_hat_j` is strongly consistent. □

Because the switch space is finite, empirical frequencies of all switch
combinations also converge to `P(S=s | A_ε)`. Finite entropy is continuous on the
probability simplex, so empirical `D_RACH` and `R_RACH` also converge to their
population values.

---

## 9. Main theorem

### Theorem — RACH is a well-defined admissible causal inference framework

Assume:

1. `S={0,1}^K` with `K>0`.
2. `ε≥0`.
3. `π` is a probability measure on `Θ×S`.
4. `G`, `f`, `P_sim`, `P_obs`, and `d` are defined as above.
5. `π(A_ε)>0` for conditional quantities.

Then RACH defines a well-posed admissible causal inference problem. Specifically:

```text
A_ε       is a well-defined subset of Θ×S.
CA_j      is a conditional probability in [0,1].
D_RACH    is a finite entropy in [0,K].
R_RACH    is a normalised resolvability score in [0,1].
OC_k      is an observation contribution score in [-1,1].
NOV(q)    is a finite expected resolvability gain when candidate outcomes are finite or integrable.
```

Moreover, under IID prior sampling and `π(A_ε)>0`, Monte Carlo estimators of
`CA_j`, `D_RACH`, and `R_RACH` are consistent.

### Proof

The claims follow from Propositions 1–7. □

---

## 10. Limitations

- RACH proves admissibility well-posedness, not causal truth.
- Results depend on the prior `π`, constraint grammar `G`, simulator `f`, pattern
  extractors, distance function, tolerance `ε`, and independent observations.
- If `π(A_ε)=0`, conditional RACH quantities are not estimable under that
  configuration.
- Exact NOV requires a predictive distribution over future observation outcomes;
  Proposition 6′ supplies one constructively for *quantitative* observations (the
  admissible-region pushforward), validated in `nov_calibration.py`. Candidates
  without an outcome model remain heuristic priority scores.
- Empirical claims require prior sensitivity, ε sensitivity, pattern-weight
  sensitivity, known-truth recovery, and independent validation.

See [`docs/literature_comparison.md`](literature_comparison.md) for broader
methodological positioning and validity discussion.
