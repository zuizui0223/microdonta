# Mechanism-Resolving Observation Design — theory contract

## 1. Scientific object

Mechanism-Resolving Observation Design is a set-valued workflow for ecological mechanism inference under residual ambiguity. It does not define success as selecting one modal mechanism. Its state is the **admissible mechanism region**

```text
A_epsilon(y_obs,x_obs)
= {(theta,s): G(theta)=1 and
   d(P_sim(f(x_obs;theta,s)),P_obs(y_obs)) <= epsilon}.
```

The region is conditional on the declared mechanism vocabulary, prior or sampling measure, biological constraints, simulator, observation map, discrepancy and tolerance. An omitted mechanism cannot be recovered by the method.

## 2. Evidence roles

Each empirical or synthetic quantity is assigned one role before inference:

- `observed_target`: may enter the acceptance discrepancy;
- `input_context`: may condition the simulator but is not independent acceptance evidence;
- `diagnostic_only`: evaluates behaviour after inference;
- `future_observation`: withheld as a candidate next measurement.

The same datum may not silently define context, enter the acceptance distance and then be reused as independent validation.

## 3. Residual mechanism ambiguity

For a binary mechanism vector `S in {0,1}^K`, marginal mechanism admissibility is

```text
CA_j = P(s_j=1 | A_epsilon).
```

The joint uncertainty object is

```text
D = H(S | A_epsilon),
R = 1 - D/K.
```

`D` is residual mechanism entropy and `R` is normalized resolvability. Mechanism-equivalence structure records which mechanism coordinates remain coupled in the retained region. Replaceability asks whether one mechanism can be removed while compatible alternatives remain.

High residual entropy is not a failed analysis. It is the reportable statement that the current observation set does not resolve the declared mechanism alternatives.

## 4. Observation information value

Let `Q` be a candidate future observation. When its possible outcomes form a verified mutually exclusive and exhaustive partition of current `A_epsilon`, define

```text
V(Q)
= E_Q[R(A_epsilon | Q)-R(A_epsilon)]
= I(S;Q | A_epsilon)/K.
```

The candidate is useful only to the extent that it carries information about the mechanism distinctions that remain unresolved. A scientifically interesting or precise measurement can therefore have `V(Q)=0` for the current ambiguity.

If the candidate outcome map does not identify a predictive partition of the current region, the validated information value is reported as non-estimable. An external outcome prior is not silently substituted and relabelled as the validated quantity.

## 5. Sequential closure

Observation value is state-dependent. After one realised observation, the admissible region changes and candidate rankings may change. The adaptive rule is

```text
A_0 = current admissible region
for t = 0,1,...:
    compute V_t(Q)=I(S;Q | A_t)/K for each estimable candidate
    select the largest positive current validated value
    reveal the selected outcome only after selection
    condition A_t on that outcome
    recompute all remaining values
```

Three stopping or continuation states must be kept distinct.

1. **Declared target resolved or budget exhausted.** The sequence can stop because its predeclared target has been met or because no further observation can currently be afforded. Neither statement implies that the full mechanism vector has entropy zero.
2. **Validated information limit.** If every declared remaining candidate has an estimable validated value and all satisfy `V_t(Q)=0`, then unresolved alternatives remain but the **complete declared candidate vocabulary** contains no expected information about those residual distinctions. This licenses an information-limited stop relative to that vocabulary.
3. **Prediction limit.** If any declared remaining candidate is non-estimable, zero values among the estimable subset do **not** establish an information limit for the full candidate vocabulary, and a positive value identifies only a provisional best among the estimable subset. The honest validated-information result is prediction limitation until the missing candidate outcome map is supplied or the candidate set is explicitly narrowed.

An explicitly labelled structural or edge-cut fallback may remain available for compatibility workflows, but fallback availability is not relabelled as validated `I(S;Q|A_t)/K` and does not by itself establish either zero or positive candidate mutual information.

## 6. Validation boundary

The primary validation is synthetic because hidden mechanism truth, candidate information structure and outcome timing must be controlled to test information leakage and selection behaviour. The frozen G2 benchmark compares an information-guided sequential policy with uniform random ordering on matched generated systems. Historical machine-readable protocol labels are retained unchanged for provenance but are not the active method name.

The method does not claim universal optimality, recovery under arbitrary simulator misspecification, or empirical discovery of a natural mechanism.

## 7. Public vocabulary

Publication-facing terms are:

```text
Mechanism-Resolving Observation Design
admissible mechanism region
mechanism entropy
mechanism resolvability
mechanism equivalence
mechanism replaceability
observation information value
sequential observation design
```

Retired project acronyms are not part of the active scientific vocabulary.
