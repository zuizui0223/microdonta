# Target-aware observation value — learning the mechanism versus resolving the target

MROD's validated publication-facing observation value remains

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

So an observation can be useless for mechanism resolution while completely resolving the declared target. The reverse configuration is also implemented below.

This is the computational counterpart of the existing TU-2 distinction:

```text
causal-learning value
!=
target-resolving value
!=
target licensing.
```

MROD still owns the causal-learning side; the target score is an explicit alternative task index, not a new universal utility.

## 4. Sequential target policy

The extension now includes

```text
target_sequential_observation_design(...)
```

which repeats the target-information calculation after every realised observation:

```text
A_0 = current admissible region
for t = 0,1,...:
    compute V_T,t(Q) for every remaining verified candidate
    choose the largest positive value
    only then reveal/materialise that selected candidate's outcome
    condition A_t to obtain A_{t+1}
    recompute the remaining target values
    stop when H(T|A_t)=0, no positive estimable value remains, or budget ends.
```

The ordering rule is fail-closed in the same sense as MROD's mechanism policy: outcomes of unselected candidates are not used when deciding what to measure next.

### Objective-reversal witness

A frozen finite witness uses four equally represented world types from

```text
A in {0,1}
T in {low,high}
```

with two verified candidates:

```text
Q_mech   exactly reveals A and is independent of T;
Q_target exactly reveals T and is independent of A.
```

Therefore

```text
I(A;Q_mech)=1 bit
I(T;Q_mech)=0

I(A;Q_target)=0
I(T;Q_target)=1 bit.
```

The mechanism objective ranks `Q_mech` first, while the target-oriented policy ranks `Q_target` first and resolves target entropy from 1 bit to 0 in one observation.

This is not a paradox. It is an explicit policy reversal caused by changing the scientific task.

## 5. Public API

The package-level API now exports both layers without renaming the original mechanism functions:

```text
mechanism task
--------------
observation_information_value
candidate_mutual_information_bits
sequential_observation_design

target task
-----------
target_entropy_bits
candidate_target_mutual_information_bits
target_observation_information_value
target_sequential_observation_design
```

The explicit result classes are also public so downstream code can preserve which task generated a score or sequence.

The anonymous reviewer package for the current MROD manuscript remains free to expose only the validated mechanism-facing publication core. Adding a prospective package utility does not retroactively change the paper's frozen primary estimand.

## 6. Files

- `causal_model/target_observation_value.py`
- `causal_model/target_sequential_design.py`
- `tests/test_target_observation_value.py`
- `tests/test_target_observation_public_api.py`
- `tests/test_target_sequential_design.py`

## 7. Claim boundary

The target score and target policy are conditional on the same declared admissible region, row weighting, candidate outcome map and target representation supplied to the calculation. A high `V_T`, or even `H(T)=0`, does not prove that the target itself is biologically sufficient, normatively licensed, or universally decision-relevant.

The extension answers only the declared conditional information and acquisition-order questions.
