# Tolerance sensitivity and specification-robust next observations

Status: mathematical scope note and controlled audit for Mechanism-Resolving Observation Design (MROD).

## 1. Why this matters

MROD evaluates a candidate observation on the **current admissible mechanism region**,

```text
V_epsilon(Q) = I(S;Q | A_epsilon) / K.
```

The acceptance tolerance `epsilon` is therefore part of the conditioning state. If more than one tolerance is scientifically plausible, the relevant question is not only whether `R` or marginal mechanism support changes, but whether the **recommended next observation itself** changes.

The same issue applies more generally to a declared sensitivity set of priors, tolerances, discrepancies or other predeclared specifications.

## 2. Proposition T1 — nested admissible regions do not imply monotone mechanism information

For `epsilon_1 < epsilon_2`, standard threshold acceptance gives nested regions

```text
A_{epsilon_1} subseteq A_{epsilon_2}.
```

Set inclusion alone does not imply that

```text
H(S | A_epsilon)
```

or

```text
I(S;Q | A_epsilon)
```

must increase or decrease monotonically with `epsilon`. Enlarging the accepted region changes the conditional distribution of mechanism states, and that change can either concentrate or disperse different mechanism coordinates.

Consequently, there is no general invariance guarantee for

```text
argmax_Q V_epsilon(Q).
```

A candidate that is optimal under one defensible tolerance need not remain optimal under another.

## 3. Controlled ranking-reversal witness

`causal_model/tolerance_sensitivity_witness.py` uses one fixed evaluated pool with a row-level discrepancy score. The strict region at `epsilon=0.10` contains 10 rows and is nested inside the loose region at `epsilon=0.20`, which contains 18 rows.

The declared mechanism vector is `S=(A,B)`. Candidate `observe_A` reads `A` exactly and candidate `observe_B` reads `B` exactly.

### Strict tolerance

Within the strict region, `A` is balanced and `B` is concentrated:

```text
I(S;observe_A | A_0.10) = H(A | A_0.10) = 1.000000 bit,
I(S;observe_B | A_0.10) = H(B | A_0.10) = 0.721928 bit.
```

For `K=2`,

```text
V_0.10(observe_A) = 0.5000,
V_0.10(observe_B) = 0.3610.
```

Thus `observe_A` is preferred.

### Loose tolerance

The additional rows admitted at `epsilon=0.20` make `A` more concentrated but `B` nearly balanced:

```text
I(S;observe_A | A_0.20) = 0.852405 bit,
I(S;observe_B | A_0.20) = 0.991076 bit.
```

Hence

```text
V_0.20(observe_A) = 0.4262,
V_0.20(observe_B) = 0.4955,
```

and the ranking reverses to `observe_B`.

The data-generating pool and candidate observations are unchanged; only the acceptance tolerance changes.

## 4. Specification-robust optimality diagnostic

Let `Lambda` be a finite, predeclared sensitivity set of scientifically defensible specifications. A specification can encode a prior, tolerance, discrepancy rule or another modelling choice that changes the current admissible mechanism distribution.

For each `lambda in Lambda`, define the set of current best candidates

```text
B_lambda = argmax_Q V_lambda(Q).
```

Then define the **common-best set**

```text
B_common = intersection_{lambda in Lambda} B_lambda.
```

This is a diagnostic, not a new decision-theory optimum.

- If `B_common` is nonempty, every candidate in it is optimal under every specification in the declared sensitivity set. The next-observation recommendation is specification-robust over that set.
- If `B_common` is empty, no available candidate is uniformly best over the declared specifications. The scientifically correct output is that the next-observation recommendation is specification-sensitive, unless an additional decision rule is declared.

The tolerance witness has

```text
B_0.10 = {observe_A},
B_0.20 = {observe_B},
B_common = empty.
```

## 5. What this diagnostic does not do

An empty common-best set does not imply that observation design is impossible. It says that a unique recommendation requires an additional choice about specification uncertainty. Possible downstream rules include model averaging, minimax or regret criteria, but those introduce extra decision assumptions and are not silently added to the current MROD publication claim.

Likewise, a nonempty common-best set establishes robustness only over the declared sensitivity set; it does not prove robustness to undeclared model misspecification.

## 6. Reporting rule

When prior, tolerance or another specification is not scientifically fixed:

1. predeclare a plausible sensitivity set;
2. report current mechanism ambiguity under each specification;
3. recompute raw candidate mutual information and normalized `V(Q)` under each specification;
4. report whether the common-best set is nonempty;
5. if it is empty, label the next-observation recommendation as specification-sensitive rather than presenting one candidate as uniquely warranted.

This turns specification uncertainty into an auditable limitation of the **observation recommendation itself**.

## 7. Claim guard

Do not claim that:

- candidate information is monotone in the acceptance tolerance;
- a next observation selected under one tolerance is automatically robust to another;
- a nonempty common-best set proves robustness to specifications outside the declared sensitivity set;
- MROD supplies a universal rule for resolving specification disagreement.

The demonstrated result is narrower:

> **Nested admissible regions can reverse the information ranking of candidate observations; robustness of the next-observation recommendation should therefore be assessed over a predeclared sensitivity set when the specification is uncertain.**

## 8. Reproduce

```bash
python -m causal_model.tolerance_sensitivity_witness
pytest -q tests/test_tolerance_sensitivity_witness.py
```
