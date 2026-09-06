# Observation information value — mathematical foundations

This note states the mathematical claims used by Mechanism-Resolving Observation Design. They concern conditional ambiguity and observation value inside a declared mechanism family; they do not establish causal truth in nature.

## Setup

Let `S in {0,1}^K` be the finite mechanism vector and let `A` denote a nonempty admissible mechanism region. All probabilities below are conditional on `A` unless otherwise stated.

Define

```text
D = H(S | A),
R = 1 - D/K,
```

for `K>0`.

For a candidate observation `Q` whose outcomes form a verified partition of `A`, define

```text
V(Q) = E_Q[R(A | Q)-R(A)].
```

## Proposition 1 — entropy and resolvability bounds

Because `S` has at most `2^K` states,

```text
0 <= H(S | A) <= K.
```

Hence

```text
0 <= D <= K,
0 <= R <= 1.
```

The denominator `K` is the maximum switch entropy, not the realised prior entropy. This keeps the scale bounded even when conditioning increases entropy relative to a non-uniform prior. The resulting normalized scale is conditional on the declared mechanism vocabulary; Proposition 8 below states the relevant representation sensitivity.

## Proposition 2 — information identity

For a verified candidate partition,

```text
V(Q)
= E_Q[R(A | Q)-R(A)]
= {H(S|A)-H(S|A,Q)}/K
= I(S;Q | A)/K.
```

Thus the expected resolvability gain and normalized mechanism-observation mutual information are the same quantity.

## Proposition 3 — information-value bounds

Conditional mutual information is non-negative and cannot exceed the current entropy of `S`, so

```text
0 <= V(Q) <= H(S|A)/K = 1-R(A) <= 1.
```

The upper bound is attained when `Q` removes all residual mechanism entropy.

## Proposition 4 — zero-value condition

For a verified candidate,

```text
V(Q)=0
```

if and only if

```text
I(S;Q | A)=0,
```

which is equivalent to conditional independence of `S` and `Q` under the current admissible-region distribution. A zero value therefore means that the candidate cannot discriminate the residual mechanism states represented in the current region.

## Proposition 5 — realised and expected changes differ

`V(Q)` is preposterior. An individual realised outcome can increase conditional entropy relative to the current state, even though the expectation over coherent predictive outcomes is non-negative. Observation value therefore evaluates expected design quality, not guaranteed gain for every realised outcome.

## Proposition 6 — predictive-partition requirement

The stored-region identity requires the candidate outcome maps to be mutually exclusive and exhaustive over the current admissible rows. If the outcome maps overlap, fail to cover the region, or depend on unrepresented simulator outputs, the stored-region predictive distribution is not identified by those rows. In that case the validated `V(Q)` is non-estimable until an additional predictive model or observation map is supplied.

## Proposition 7 — sequential recomputation

After observing `Q_t=q_t`, the next design state is the conditioned region

```text
A_{t+1} = A_t | Q_t=q_t.
```

Because both `P(S|A_t)` and the predictive candidate distributions can change after conditioning, candidate values must be recomputed at every step. A ranking computed only at `A_0` is not generally invariant through the sequence.

## Proposition 8 — vocabulary recoding, redundant coordinates and K-normalization

The mechanism vocabulary is part of the declared scientific target. Representation-only changes have exact raw-information invariances.

### 8a. Bijective recoding

If `T=f(S)` is a bijection on the relevant mechanism support, then

```text
H(T|A)=H(S|A),
I(T;Q|A)=I(S;Q|A).
```

Thus labels or one-to-one recodings do not change raw residual mechanism entropy or raw candidate mutual information.

### 8b. Deterministic redundant augmentation

Let `U=g(S)` be a deterministic function of the existing mechanism vector. Then

```text
H(S,U|A)
= H(S|A) + H(U|S,A)
= H(S|A),
```

and by the mutual-information chain rule,

```text
I((S,U);Q|A)
= I(S;Q|A) + I(U;Q|S,A)
= I(S;Q|A).
```

A deterministic redundant coordinate therefore creates neither raw mechanism entropy nor raw mechanism-observation information.

### 8c. Normalized magnitudes are vocabulary-internal

If `m` deterministic redundant binary coordinates are appended, the raw quantities remain

```text
D = H(S|A),
I_Q = I(S;Q|A),
```

but the normalized reports change from

```text
R_K = 1-D/K,
V_K(Q)=I_Q/K
```

to

```text
R_{K+m}=1-D/(K+m),
V_{K+m}(Q)=I_Q/(K+m).
```

Therefore the absolute values of `R` and normalized `V` are not invariant to arbitrary changes in the declared coordinate count. They are bounded within-vocabulary scales, not universal cross-vocabulary metrics.

### 8d. Candidate selection is preserved under deterministic redundancy

For a fixed vocabulary, dividing every candidate's raw mutual information by the same positive `K` does not change its ranking:

```text
argmax_Q V(Q) = argmax_Q I(S;Q|A).
```

After deterministic redundant augmentation, raw candidate mutual information is unchanged and the new denominator `K+m` is again common to every candidate. Candidate ranking, zero-value status and positive-value status are therefore preserved.

This invariance does not apply when the scientific target itself changes—for example, when a broad mechanism is split into genuinely uncertain submechanisms or a new mechanism not determined by the old state is introduced.

## Reporting consequence of Proposition 8

For transparency, report:

```text
D = H(S|A) in bits, together with K,
I(S;Q|A) in bits, together with normalized V(Q).
```

Do not compare absolute `R` or normalized `V` values across differently encoded mechanism vocabularies without a vocabulary-sensitivity argument. The public observation-information result already exposes `mutual_information_bits`, so this rule does not alter the selection algorithm or the frozen G2 policy.

## Monte Carlo implementation

The implementation represents `A` by accepted samples. Entropies, predictive outcome frequencies and mutual information are empirical finite-sample quantities on that retained sample. Numerical convergence of those estimates depends on Monte Carlo coverage; the algebraic identities above are properties of the declared conditional distribution, not guarantees about finite-sample approximation quality.
