# Question-relative mechanism resolution as a coarsening of the full mechanism world

Status: **internal theory / claim-ceiling audit**. The active MEE manuscript continues to use the full declared mechanism vector `S` as its primary information target. This note specializes the repository's existing target-aware utilities to an ecological question target that is itself a deterministic partition of mechanism space.

## 1. Why this is different from a generic target variable

The repository already supports a separately declared target `T` through

```text
target_observation_information_value
target_sequential_observation_design
task_pareto_values
```

and therefore already distinguishes mechanism-learning value from generic target-resolving value.

For a **question-relative mechanism target**, impose the stronger relation

```text
T = tau(S),
```

where `S` is the full declared mechanism world and `tau` maps microscopic or lower-level mechanism states into the ecological mechanism classes named by the scientific question.

Examples of the intended logic are:

```text
full S:
    pollinator pathway subtype
    floral physiological subtype
    abiotic pathway subtype
    historical submechanism

question T=tau(S):
    pollinator-mediated explanation
    versus
    abiotic-mediated explanation
```

The target map is part of the scientific question. It must be declared; it is not discovered by maximizing information.

## 2. Entropy coarsening theorem

Because `T=tau(S)` is deterministic,

```text
H(T|S,A)=0.
```

The entropy chain rule gives

```text
H(S|A)
= H(T|A) + H(S|T,A).
```

Therefore

```text
H(T|A) <= H(S|A).
```

Full mechanism resolution implies target resolution:

```text
H(S|A)=0  =>  H(T|A)=0.
```

The converse is false whenever multiple full mechanism states remain inside one target class:

```text
H(T|A)=0
but
H(S|A)=H(S|T,A)>0.
```

This is the formal version of **question-relative mechanistic sufficiency**. A study can have resolved the mechanism distinction it actually asked about while lower-level mechanism ambiguity remains.

## 3. Target-information data-processing theorem

For any candidate observation `Q`, deterministic coarsening also gives

```text
I(S;Q|A)
= I(T;Q|A) + I(S;Q|T,A).
```

Hence

```text
I(T;Q|A) <= I(S;Q|A).
```

So a candidate cannot contain more raw information about a deterministic question-class target than it contains about the full mechanism world. But this does **not** preserve candidate ranking: the extra term

```text
I(S;Q|T,A)
```

can differ sharply among candidates.

A deep assay can therefore be highly informative about variation *within* target classes while carrying little or no information about the class contrast named by the question.

## 4. Executable ranking-reversal witness

`causal_model/question_relative_mechanism_target_witness.py` uses eight equally weighted worlds

```text
S = (T,U1,U2)
in {0,1}^3,
```

with `T` independent of the two within-class submechanism bits `U1,U2`. The row column `question_class` is a deterministic function of `T`, so it is a valid `tau(S)` target.

Two verified observations are compared:

```text
deep_submechanism
    reveals (U1,U2)

question_class
    reveals T
```

For the full mechanism objective,

```text
I(S; deep_submechanism) = 2 bits
I(S; question_class)    = 1 bit
```

so full-state MROD prefers the deeper submechanism assay.

For the question-relative target,

```text
I(T; deep_submechanism) = 0 bits
I(T; question_class)    = 1 bit
```

so the target-aware policy reverses the ranking.

The same witness then fixes `T` while retaining all four `(U1,U2)` states:

```text
H(T)=0
H(S)=2 bits.
```

Thus target resolution does not require complete lower-level mechanism resolution.

## 5. Mechanistic depth is not question-relevant identifying power

The witness formalizes the distinction

```text
mechanistic depth
!=
information about the full declared mechanism vector
!=
information about the mechanism partition named by the question.
```

The scientifically appropriate objective depends on what the study claims to resolve.

- If the claim is about the full declared mechanism vector, use `I(S;Q|A)`.
- If the claim is about a predeclared mechanism class `T=tau(S)`, use `I(T;Q|A)`.
- If both matter, keep them as separate task-indexed utilities or report a Pareto front; do not silently collapse them into one weighted score.

This is especially relevant to proximate/ultimate or molecular/ecological hierarchies. A molecular assay is not automatically the strongest observation for an ecological mechanism contrast, and a field-level observation is not automatically superficial if it sharply separates the relevant target classes.

## 6. Normalization caution

The current publication mechanism score uses

```text
V_S(Q)=I(S;Q|A)/K,
```

where `K` is the declared number of binary mechanism coordinates.

The existing target-aware utility uses

```text
V_T(Q)=I(T;Q|A)/H(T|A)
```

when current target entropy is positive. These are **different within-task normalizations**. Their absolute normalized magnitudes should not be interpreted as a common utility scale.

Raw information bits provide the clean theorem-level comparison:

```text
I(T;Q|A) <= I(S;Q|A).
```

Candidate rankings should be compared separately within each declared task, or through the existing Pareto representation when both tasks are relevant.

## 7. Target validity is not supplied by information theory

Declaring `T=tau(S)` does not prove that the partition is biologically correct, causally sufficient, normatively important or exhaustive of nature. A target can be perfectly resolved and still be the wrong target.

Therefore a question-relative target must be:

1. specified before candidate outcomes are inspected;
2. biologically interpretable as the distinction the paper intends to claim;
3. kept separate from undeclared deeper mechanisms that are irrelevant to that claim;
4. revised only as a scientific-model change, not because a different partition gives a more convenient result.

This is a target-definition contract, not a data-driven clustering step.

## 8. Scope

This note does **not** change the active MEE paper's primary estimand, frozen G2 policy or figures. It does not claim novelty for data processing, sufficient statistics, hierarchical latent variables or task-specific information gain.

Its contribution to the repository is narrower: it identifies the exact special case of the existing target-aware layer that formalizes the project's biological principle

> **the right mechanistic observation is not necessarily the deepest observation; it is the observation that best resolves the mechanism distinction actually named by the scientific question.**
