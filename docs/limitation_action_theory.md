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

be the candidates whose predictive outcome partitions are identified from the current state so that validated values

```text
V_A(Q)=I(S;Q|A)/K
```

are estimable.

For every `Q in E(A)`,

```text
V_A(Q) >= 0.
```

Budget state is kept separate from information state.

## 2. Proposition L1 — validated actionability dichotomy under complete candidate coverage

Assume:

1. the current mechanism-information state is estimable;
2. the declared design target remains unresolved, `T(A)=0`;
3. the candidate vocabulary is nonempty;
4. every declared candidate is estimable, `E(A)=C`.

Then exactly one of the following holds:

```text
max_{Q in C} V_A(Q) > 0
```

or

```text
max_{Q in C} V_A(Q) = 0.
```

Because every validated information value is non-negative, the second case is equivalent to

```text
V_A(Q)=0 for every Q in C.
```

Interpretation:

- `max V > 0`: the declared candidate vocabulary is **validated-actionable**; at least one available observation contains mechanism information.
- `max V = 0`: the declared candidate vocabulary is **information-limited** relative to the current mechanism target; collecting one of those same candidates cannot reduce mechanism entropy in expectation.

This is a dichotomy only for the **complete declared candidate vocabulary**. It is not a statement about every observation that could exist in nature.

## 3. Proposition L2 — incomplete predictive coverage blocks global actionability claims

Suppose

```text
empty != E(A) subsetneq C.
```

Then the values of candidates in `C \ E(A)` are not identified by the validated stored-region calculation. Consequently:

- a positive value among `E(A)` identifies only a **provisional best among estimable candidates**;
- zero values for every candidate in `E(A)` do **not** establish an information limit for `C`;
- `argmax_{Q in C} V_A(Q)` is not identified without valuing the remaining candidates or explicitly narrowing `C`.

This is why `partial_prediction_limited` is distinct from both `actionable` and `information_limited`.

## 4. Proposition L3 — no predictive coverage is prediction limitation, not zero information

If

```text
E(A)=empty
```

while `C` is nonempty, no publication-level candidate information value is identified from the current stored region. The correct status is **prediction-limited**.

A structural or heuristic fallback score may still be available operationally, but it is not a proof that candidate mutual information is zero or positive. Fallback availability therefore belongs to a separate reporting layer.

## 5. Proposition L4 — budget limitation is orthogonal to epistemic recommendation

Let the complete candidate vocabulary be estimable and suppose

```text
max_Q V_A(Q)>0.
```

The identity of a best candidate is defined whether or not current field budget remains. Therefore:

```text
budget exhausted
```

and

```text
validated best candidate identified
```

can hold simultaneously.

Budget exhaustion changes the feasible **action now**, not the epistemic ranking. A report may therefore state both:

```text
best next measurement: Q*
current action: unavailable because budget is exhausted.
```

This is more informative than converting the entire state into one `budget_limited` label.

## 6. Proposition L5 — declared target resolution is weaker than full mechanism resolution

A predeclared target predicate can satisfy

```text
T(A)=1
```

while

```text
H(S|A)>0.
```

For example, a selected confounding edge set can be resolved while unrelated switch combinations remain admissible. Therefore `declared target resolved` does not imply `full mechanism vector resolved` unless the target itself is defined as full mechanism resolution.

The reporting consequence is:

```text
stop the predeclared design sequence
AND
retain/report residual out-of-target mechanism ambiguity.
```

## 7. Proposition L6 — a non-estimable current state precedes observation design

If the current admissible-region representation does not yield an estimable mechanism distribution—for example an empty accepted region under the implementation—then `H(S|A)`, current resolvability and candidate conditional information are not licensed as ordinary finite-state summaries.

This is a **current-state estimation problem**, not a successful resolution result and not a candidate information limit. The next action is to repair, relax, resample or otherwise re-estimate the declared current state before claiming what follow-up observation is optimal.

## 8. Specification sensitivity

Let `Lambda` be a finite sensitivity set that holds the scientific mechanism target and candidate vocabulary fixed while varying a prior, tolerance, discrepancy or other defensible specification. For each `lambda`, compute the orthogonal axes above.

Only when every target-unresolved specification has complete candidate coverage and positive validated information is a cross-specification recommendation comparison fully defined. Then

```text
B_lambda = argmax_Q V_lambda(Q)
```

and

```text
B_common = intersection_{lambda in Lambda} B_lambda
```

can be reported as a recommendation-stability diagnostic.

If actionability itself differs across specifications, the correct result is `specification_sensitive_actionability`, not a forced common recommendation.

## 9. What these propositions do not establish

They do not show that:

- the declared mechanism family contains the true mechanism;
- an information-limited candidate vocabulary implies mechanism is unknowable in principle;
- a non-estimable candidate has zero information;
- a heuristic fallback is equivalent to validated mutual information;
- a common-best candidate is a new robust-design optimum;
- a narrower design target is the same as full mechanism resolution;
- budget and information can be compressed without loss into one scalar limitation severity.

The purpose is narrower: **make the logical status of `limitations -> next action` explicit using quantities MROD already computes.**
