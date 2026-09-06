# Target-aware observation value — learning the mechanism versus resolving the target

MROD's publication-facing observation value remains

```text
V_S(Q) = I(S;Q | A_epsilon) / K,
```

where `S` is the residual mechanism vector. This is the correct quantity for the repository's primary question: which observation best reduces unresolved mechanism ambiguity?

A different scientific task can ask:

> Which observation best resolves a predeclared target `T`, even if mechanism identity remains ambiguous?

This extension keeps those utilities separate rather than replacing one with the other.

## 1. Target information value

For target columns `T` carried by the current admissible rows and a candidate observation `Q` with a verified outcome partition, compute

```text
H(T | A_epsilon)
```

and

```text
I(T;Q | A_epsilon).
```

The normalized prospective target score is

```text
V_T(Q)
= I(T;Q | A_epsilon) / H(T | A_epsilon)
```

when the current target entropy is positive.

If

```text
H(T | A_epsilon)=0,
```

then the target is already point-resolved in the stored admissible region and the additional normalized target value is defined as zero.

## 2. Same partition discipline as MROD

The extension reuses the existing verified predictive outcome partition. If a candidate's outcome maps do not form a mutually exclusive and exhaustive partition of the current admissible rows, `V_T` is reported as non-estimable.

A declared fallback outcome prior is not substituted and relabelled as target information.

## 3. Mechanism value and target value can diverge

The tests contain an explicit witness:

```text
candidate Q = high/low trait measurement
mechanism A = independent of high/low trait
target T = exactly high/low trait state
```

Then

```text
I(A;Q)=0
I(T;Q)=1 bit.
```

So an observation can be useless for mechanism resolution while completely resolving the declared target. The reverse configuration is also possible in principle.

This is the computational counterpart of the existing TU-2 distinction:

```text
causal-learning value
!=
target-licensing value.
```

MROD still owns the causal-learning side; the target score is an explicit alternative task index, not a new universal utility.

## 4. Files

- `causal_model/target_observation_value.py`
- `tests/test_target_observation_value.py`

Public functions in the new module:

```text
target_entropy_bits
candidate_target_mutual_information_bits
target_observation_information_value
```

## 5. Claim boundary

The target score is conditional on the same declared admissible region, row weighting, candidate outcome map and target representation supplied to the calculation. A high `V_T` does not prove that the target itself is biologically sufficient, normatively licensed, or universally decision-relevant.

It answers only the declared conditional information question.
