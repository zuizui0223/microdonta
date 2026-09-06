# Limitation-to-action reporting: mathematical scope

Status: **internal theory note** for the MROD limitation-to-action prototype. This note does not change the active MEE manuscript or frozen G2 policy.

## 1. Setup

Let `A` be the current admissible mechanism region for one fixed scientific specification and let `S` be the declared mechanism vector. Let `T(A)` be a predeclared design-target predicate: `T(A)=1` means the narrower design objective has been resolved. Full mechanism resolution is stronger and is represented by

```text
H(S|A)=0.
```

Let `C` be the declared set of feasible candidate observations. Let

```text
E(A) subseteq C
```

be the candidates whose predictive outcome partitions are identified from the current state so that validated singleton values

```text
V_A(Q)=I(S;Q|A)/K
```

are estimable. For every `Q in E(A)`, `V_A(Q)>=0`.

When a coherent **joint** predictive distribution for the whole declared candidate vector is also identified, write

```text
Q_C = (Q : Q in C)
J_A(C) = I(S;Q_C|A)/K.
```

`J_A(C)` is a bundle-level diagnostic, not the current greedy MROD selection score. Budget state is kept separate from information state.

## 2. Proposition L1 — complete singleton coverage gives a one-step dichotomy

Assume:

1. the current mechanism-information state is estimable;
2. the declared design target remains unresolved, `T(A)=0`;
3. the candidate vocabulary is nonempty;
4. every declared singleton candidate is estimable, `E(A)=C`.

Then exactly one of the following holds:

```text
max_{Q in C} V_A(Q) > 0
```

or

```text
max_{Q in C} V_A(Q) = 0.
```

Because singleton information values are non-negative, the second case is equivalent to `V_A(Q)=0` for every `Q in C`.

Interpretation:

- `max V > 0`: the current positive-singleton greedy policy is **one-step actionable**;
- `max V = 0`: no declared **single** next observation has positive immediate mechanism information, so a positive-only greedy policy stops.

The second statement is only a **one-step information limit**. It does not imply that the joint candidate vector or a multi-observation sequence contains zero mechanism information.

## 3. Proposition L2 — incomplete predictive coverage blocks global singleton claims

Suppose

```text
empty != E(A) subsetneq C.
```

Then the values of candidates in `C \ E(A)` are not identified by the validated stored-region calculation. Consequently:

- a positive value among `E(A)` identifies only a **provisional best among estimable candidates**;
- zero values for every candidate in `E(A)` do not establish even a complete one-step zero result for `C`;
- `argmax_{Q in C} V_A(Q)` is not identified without valuing the remaining candidates or explicitly narrowing `C`.

Partial predictive coverage is therefore distinct from both one-step actionability and any information-limit statement.

## 4. Proposition L3 — no predictive coverage is prediction limitation, not zero information

If `E(A)=empty` while `C` is nonempty, no publication-level singleton candidate information value is identified from the current stored region. The correct status is **prediction-limited**.

A structural or heuristic fallback score may still be available operationally, but it is not a proof that candidate mutual information is zero or positive. Fallback availability therefore belongs to a separate reporting layer.

## 5. Proposition L4 — budget limitation is orthogonal to epistemic recommendation

Let the complete singleton candidate vocabulary be estimable and suppose `max_Q V_A(Q)>0`. The identity of a best singleton candidate is defined whether or not current field budget remains. Therefore

```text
budget exhausted
```

and

```text
validated best candidate identified
```

can hold simultaneously.

Budget exhaustion changes the feasible **action now**, not the epistemic ranking. A report may state both `best next measurement: Q*` and `current action: unavailable because budget is exhausted`.

## 6. Proposition L5 — declared target resolution is weaker than full mechanism resolution

A predeclared target predicate can satisfy `T(A)=1` while `H(S|A)>0`. For example, a selected confounding edge set can be resolved while unrelated switch combinations remain admissible. Therefore `declared target resolved` does not imply `full mechanism vector resolved` unless the target itself is defined as full mechanism resolution.

The reporting consequence is:

```text
stop the predeclared design sequence
AND
retain/report residual out-of-target mechanism ambiguity.
```

## 7. Proposition L6 — a non-estimable current state precedes observation design

If the current admissible-region representation does not yield an estimable mechanism distribution—for example an empty accepted region under the implementation—then `H(S|A)`, current resolvability and candidate conditional information are not licensed as ordinary finite-state summaries.

This is a **current-state estimation problem**, not a successful resolution result and not a candidate information limit. The next action is to repair, relax, resample or otherwise re-estimate the declared current state before claiming what follow-up observation is optimal.

## 8. Proposition L7 — zero singleton information does not imply zero sequence information

There exist finite mechanism/candidate systems for which

```text
I(S;Q1|A)=0,
I(S;Q2|A)=0,
```

but

```text
I(S;Q1,Q2|A)>0.
```

The executable XOR witness in `causal_model/zero_singleton_synergy_witness.py` has exactly

```text
I(S;Q1)=0 bit,
I(S;Q2)=0 bit,
I(S;Q1,Q2)=1 bit.
```

After observing either zero-valued first component, the second component has one conditional bit about `S`. The chain rule makes the logic explicit:

```text
I(S;Q1,Q2|A)
= I(S;Q1|A) + I(S;Q2|A,Q1).
```

The first term can be zero while the second is positive. Therefore a rule that refuses every zero-immediate-value first observation can stop even though a two-observation plan can resolve mechanism ambiguity.

This is not a new information-theory result. It is a claim ceiling on the interpretation of MROD's current positive-singleton greedy stopping rule.

## 9. Proposition L8 — joint zero information licenses a sequence-level information limit

Assume the coherent joint predictive vector `Q_C` is identified and

```text
J_A(C)=I(S;Q_C|A)/K=0.
```

Any transcript obtained by observing only candidates in `C`—in any fixed order, any subset, or any adaptive order whose realised transcript is a function of the joint candidate outcomes—cannot contain more information about `S` than `Q_C` itself. By the data-processing inequality,

```text
I(S; transcript | A) <= I(S;Q_C | A)=0.
```

Hence joint zero information is sufficient to call the declared candidate vocabulary **sequence-information-limited** relative to the current state.

Conversely, if `J_A(C)>0` while all singleton values are zero, the vocabulary contains resolving information in combinations, but the current greedy policy does not identify a positive first move. A non-myopic bundle/sequence objective or an additional decision rule is then required. `J_A(C)>0` does not by itself establish the best acquisition order, cost-optimal plan or global adaptive policy.

If a coherent joint predictive coupling among candidates is unavailable, sequence-level information status is itself non-audited; zero singleton values should not be promoted to a sequence-information-limit claim.

## 10. Specification sensitivity

Let `Lambda` be a finite sensitivity set that holds the scientific mechanism target and candidate vocabulary fixed while varying a prior, tolerance, discrepancy or other defensible specification. For each `lambda`, compute the orthogonal axes above.

Recommendation comparison is downstream of target status itself. If one specification resolves the declared target while another does not, or if the current target state is non-estimable under part of `Lambda`, the recommendation question is itself specification-sensitive and no common recommendation should be inferred from only the unresolved subset.

Only when every specification has the target unresolved, complete candidate coverage and positive singleton information is a full cross-specification **greedy next-candidate** comparison defined. Then

```text
B_lambda = argmax_Q V_lambda(Q)
B_common = intersection_{lambda in Lambda} B_lambda
```

can be reported as a recommendation-stability diagnostic.

A specification with zero singleton values but positive joint information is sequence-actionable in a different, non-myopic sense; it must not be forced into a singleton common-best comparison.

## 11. What these propositions do not establish

They do not show that:

- the declared mechanism family contains the true mechanism;
- zero singleton values imply sequence-level information impossibility;
- positive joint information supplies a unique or cost-optimal acquisition order;
- a sequence-information-limited declared vocabulary implies mechanism is unknowable in principle after expanding the vocabulary;
- a non-estimable candidate has zero information;
- a heuristic fallback is equivalent to validated mutual information;
- a common-best candidate is a new robust-design optimum;
- a narrower design target is the same as full mechanism resolution;
- budget and information can be compressed without loss into one scalar limitation severity.

The purpose is narrower: **make the logical status of `limitations -> next action` explicit using quantities MROD already computes, while separating myopic stopping from a genuine candidate-vocabulary information boundary.**
