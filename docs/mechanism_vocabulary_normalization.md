# Mechanism vocabulary, raw information and K-normalization

Status: mathematical scope note and executable audit for Mechanism-Resolving Observation Design (MROD).

## 1. Why this matters

MROD declares a binary mechanism vector

```text
S in {0,1}^K
```

and reports

```text
D = H(S | A_epsilon),
R = 1 - D/K,
V(Q) = I(S;Q | A_epsilon)/K.
```

The mechanism vocabulary is a scientific modelling choice. A reviewer can therefore ask whether splitting, duplicating or recoding mechanism coordinates changes the reported quantities.

The answer has two layers:

1. **raw information quantities and within-vocabulary candidate ranking have exact invariances;**
2. **the K-normalized 0–1 magnitudes are vocabulary-internal scales and are not generally invariant across differently encoded vocabularies.**

The distinction should be reported rather than hidden.

## 2. Proposition V1 — bijective recoding invariance

Let `T=f(S)` be a bijective recoding of the mechanism state on the relevant support. Because a bijection preserves state probabilities,

```text
H(T | A) = H(S | A).
```

For any candidate observation `Q`, mutual information is invariant to an invertible transformation of either variable, so

```text
I(T;Q | A) = I(S;Q | A).
```

Thus raw mechanism entropy and raw candidate mechanism information do not depend on labels or one-to-one recodings of the same mechanism states.

## 3. Proposition V2 — deterministic redundant-coordinate invariance

Let a vocabulary be augmented by a coordinate

```text
U = g(S)
```

that is a deterministic function of the existing mechanism vector. Then

```text
H(S,U | A)
= H(S | A) + H(U | S,A)
= H(S | A),
```

because `H(U|S,A)=0`.

Likewise, by the chain rule for mutual information,

```text
I((S,U);Q | A)
= I(S;Q | A) + I(U;Q | S,A)
= I(S;Q | A).
```

The second term is zero because `U` is already determined by `S`.

Therefore a deterministic redundant mechanism coordinate creates no raw mechanism entropy and no raw mechanism–observation information.

## 4. Corollary V2a — K-normalized magnitudes are not invariant

Suppose the original vocabulary has `K` binary coordinates and the augmented vocabulary contains `m` extra deterministic redundant coordinates. Let

```text
D = H(S|A),
I_Q = I(S;Q|A).
```

Raw quantities remain `D` and `I_Q`, but the normalized reports become

```text
R_K     = 1 - D/K,
R_K+m   = 1 - D/(K+m),

V_K(Q)   = I_Q/K,
V_K+m(Q) = I_Q/(K+m).
```

Unless `D=0`, adding redundant coordinates makes the reported normalized resolvability larger. Unless `I_Q=0`, it makes the normalized candidate value smaller.

This does **not** mean the evidence became more resolving or the observation became less informative. It means the denominator changed.

## 5. Corollary V2b — candidate selection is preserved

Within one declared vocabulary, every candidate is divided by the same positive constant `K`. Therefore

```text
argmax_Q V(Q) = argmax_Q I(S;Q|A).
```

Under deterministic redundant augmentation the raw `I(S;Q|A)` values are unchanged, and the new denominator `K+m` is again common to every candidate. Hence:

```text
candidate ranking is unchanged,
zero-value candidates remain zero,
positive-value candidates remain positive.
```

The observation-selection decision is therefore invariant to deterministic redundant coordinates even though the displayed normalized magnitudes are not.

## 6. Executable witness

`causal_model/vocabulary_normalization_witness.py` uses balanced mechanisms `(A,B)` and appends `A_copy=A`.

The original vocabulary has `K=2`; the redundant vocabulary has `K=3`. The four mechanism states remain equally represented.

Two candidate observations are evaluated:

- `observe_A`: one bit of raw mechanism information;
- `observe_A_and_B`: `H2(1/4)=0.811278` bit.

The exact expected audit is:

| Quantity | Original `(A,B)` | Redundant `(A,B,A_copy)` |
|---|---:|---:|
| raw entropy `H(S)` | 2.0000 bit | 2.0000 bit |
| normalized `R` | 0.0000 | 0.3333 |
| raw MI `observe_A` | 1.000000 bit | 1.000000 bit |
| normalized `V(observe_A)` | 0.5000 | 0.3333 |
| raw MI `observe_A_and_B` | 0.811278 bit | 0.811278 bit |
| normalized `V(observe_A_and_B)` | 0.4056 | 0.2704 |
| candidate ranking | A > A∧B | A > A∧B |

This is a representation audit, not an ecological performance benchmark.

## 7. What is and is not a harmless vocabulary change

A deterministic redundant coordinate is not a new scientific mechanism. A bijective recoding is also not a new target. The invariances above should hold for such representation-only changes.

By contrast, splitting one broad mechanism into genuinely uncertain submechanisms, adding a mechanism not determined by the old state, or changing which causal/process distinctions count as `S` changes the scientific target. In those cases `H(S|A)`, `I(S;Q|A)` and candidate ranking may legitimately change. No representation-invariance claim applies.

## 8. Reporting rule

For a fixed declared vocabulary, normalized `R` and `V` provide convenient bounded scales and do not alter candidate ranking relative to raw mutual information.

For transparency:

1. report residual mechanism entropy `D=H(S|A)` in **bits** together with `K`;
2. report candidate mutual information `I(S;Q|A)` in **bits** together with normalized `V(Q)`;
3. do not compare absolute `R` or `V` values across differently encoded mechanism vocabularies without a vocabulary-sensitivity argument;
4. use raw bits to audit bijective recodings and deterministic redundant refinements;
5. predeclare the biological mechanism vocabulary rather than changing it to improve normalized scores.

The public observation-information result already exposes `mutual_information_bits`, so this reporting rule does not require a change to the candidate-selection algorithm or to the frozen G2 policy.

## 9. Claim guard

Do not claim that:

- `R` or normalized `V` is a universal scale across arbitrary mechanism vocabularies;
- adding a redundant switch genuinely increases mechanistic resolution;
- deterministic vocabulary augmentation changes MROD's candidate ranking;
- raw entropy or raw mutual information is invariant when the scientific mechanism target itself changes.

The correct statement is:

> **Raw mechanism information is invariant to one-to-one recoding and deterministic redundant coordinates; K-normalized magnitudes are conditional on the declared vocabulary, while within-vocabulary observation ranking is preserved.**

## 10. Reproduce

```bash
python -m causal_model.vocabulary_normalization_witness
pytest -q tests/test_vocabulary_normalization_witness.py
```
