# From inferential limitations to explicit next actions

Status: **internal MROD prototype.** This note composes existing MROD outputs into an action/reporting layer. It is not part of the active MEE manuscript, does not define a new uncertainty score and does not change the frozen G2 policy.

## 1. Motivation

A conventional Discussion limitation often ends with a sentence such as

> alternative mechanisms cannot be excluded; future work is needed.

MROD can be more explicit because several distinct reasons for stopping or continuing are already observable from the current analysis. These reasons should not be collapsed into one generic `uncertainty` number.

The prototype therefore reports **orthogonal limitation axes** and an associated action.

## 2. First separate full mechanism resolution from the declared design target

Let

```text
D = H(S | A_current)
```

be current residual entropy in the full declared mechanism vector.

`D=0` means the current declared mechanism distribution is concentrated on one switch vector. That is a strong form of **full mechanism resolution** under the declared model family.

A sequential observation study can legitimately have a narrower predeclared target, however. For example, frozen G2 stops when the declared confounding-edge structure is resolved; other switch uncertainty may remain. Therefore:

```text
full mechanism resolution
    !=
declared design target resolution
```

The reporting layer records both. If the narrower target is resolved while `D>0`, the correct output is not `all mechanisms resolved`; it is

```text
declared target: resolved
full mechanism state: still ambiguous
```

and the residual ambiguity remains reportable.

If the current entropy itself is non-estimable—for example because no admissible rows survive—this is a separate `current_state_nonestimable` state. It must not be relabelled as either resolved or information-limited.

## 3. Validated candidate-information states

For a target that remains unresolved, let candidate observations have validated values

```text
V(Q) = I(S;Q | A_current)/K.
```

For one declared specification:

| State | Diagnostic | Meaning | Action |
|---|---|---|---|
| `not_required` | full mechanism or narrower declared target already resolved | the predeclared stopping target has been met | stop; if `D>0`, report remaining out-of-target ambiguity |
| `current_state_nonestimable` | current `D` is not estimable | no coherent current mechanism-information state exists | repair/re-estimate the admissible region before observation design |
| `actionable` | target unresolved, **all declared candidates estimable**, some `V(Q)>0` | ambiguity remains and the full declared candidate set can be ranked | measure a best current candidate |
| `information_limited` | target unresolved, **all declared candidates estimable**, all `V(Q)=0` | current candidate vocabulary contains no mechanism information | report information limit; redesign/expand observations |
| `prediction_limited` | candidates exist but none has an identified predictive partition | candidate values cannot yet be estimated | identify/model candidate outcome distributions first |
| `partial_prediction_limited` | some candidates estimable and some not | verified candidates can be described, but a global ranking over the declared set is not licensed | resolve non-estimable candidates or explicitly narrow the candidate set |
| `candidate_limited` | no candidate observations declared | no follow-up vocabulary exists | expand candidate vocabulary |
| `budget_limited` | informative candidates may exist but budget exhausted | ambiguity remains for a resource reason | report budget limit explicitly |

No information-limit claim is allowed while declared candidates remain non-estimable.

### 3.1 Validated actionability versus compatibility fallback

The current sequential compatibility backend can assign an explicitly labelled `normalized_edge_cut_fallback` to a candidate whose predictive partition is not identified. That fallback can be useful operationally, but it is **not** `I(S;Q|A_current)/K` and must not be used to convert a `prediction_limited` state into validated mechanism-information actionability.

This prototype therefore classifies only the **validated-information layer**. If a fallback is used in an application, report it on a separate axis such as

```text
validated candidate state: prediction_limited
compatibility fallback: available, normalized_edge_cut_fallback
```

rather than writing `actionable by mechanism information` when candidate MI is not estimable.

## 4. Specification axes

When several scientifically defensible priors, tolerances or other specifications are predeclared, compute the single-specification state separately for each one.

The prototype reports four stability axes. These are descriptive sensitivity labels, not robust-design objectives.

### Full-mechanism-resolution stability

```text
stable_mechanism_fully_resolved
stable_mechanism_ambiguous
stable_mechanism_nonestimable
specification_sensitive
```

This asks whether the complete declared mechanism vector has the same resolution status across specifications.

### Declared-target-resolution stability

```text
stable_target_resolved
stable_target_unresolved
stable_target_nonestimable
specification_sensitive
```

This is a different statement. A target can be stably resolved while full mechanism ambiguity remains.

### Validated actionability stability

```text
stable_actionable
stable_not_actionable
specification_sensitive
not_required
```

This asks whether every specification whose target remains unresolved agrees that the **complete declared candidate set is estimable and contains a positive-value candidate**.

### Recommendation stability

For fully actionable target-unresolved specifications let

```text
B_lambda = argmax_Q V_lambda(Q).
```

The intersection

```text
B_common = intersection B_lambda
```

gives:

```text
stable_common_best
specification_sensitive_ranking
specification_sensitive_actionability
not_available
```

This is the same sensitivity-reporting logic used in `docs/tolerance_and_specification_robustness.md`; it does not optimize a maximin, robust-EIG or other replacement objective.

## 5. Why keep the axes separate?

A single `limitation severity` score would destroy information needed for the next scientific action.

For example:

- declared confounding edges can be resolved while residual switch entropy remains positive;
- no admissible current region means re-estimate the state before ranking observations;
- `D>0, max V=0` **with every candidate estimable** means change what can be observed, not merely collect more replicates;
- non-estimable `V` means improve the predictive observation model, not reject the candidate as uninformative;
- a positive verified candidate does not justify a global `best next observation` claim while other declared candidates remain non-estimable;
- an available structural fallback does not turn non-estimable mechanism information into validated information;
- an empty common-best set means the recommendation depends on the analysis specification, not that every candidate has low value;
- exhausted budget means the observation may be known and useful but currently infeasible.

Preserving these distinctions is consistent with the wider project principle: do not manufacture certainty by coarsening unresolved structure.

## 6. Practical outputs

A target-resolved but fully ambiguous analysis could end with

```text
Declared design target: resolved
Full mechanism state: ambiguous, D=1.2 bits
Action: stop the predeclared design sequence and report residual out-of-target mechanism ambiguity
```

An actionable but specification-sensitive analysis could end with

```text
Declared design target: unresolved
Validated candidate-information state: actionable
Recommendation stability: specification-sensitive ranking
Best candidate under strict epsilon: pollen deposition
Best candidate under loose epsilon: common-garden phenotype
Common-best set: empty
Action: report recommendation sensitivity or declare an additional decision rule
```

An information-limited analysis could end with

```text
Declared design target: unresolved
Validated candidate-information state: information-limited
Verified candidate values: all zero
Non-estimable candidates: none
Action: current measurement vocabulary cannot resolve the remaining mechanism ambiguity
```

A partial-prediction analysis could end with

```text
Declared design target: unresolved
Validated candidate-information state: partial prediction limit
Best verified candidate: pollen deposition
Non-estimable candidate: reciprocal transplant
Compatibility fallback: available but non-information-theoretic
Action: do not call pollen deposition globally optimal until the remaining candidate can be valued or is explicitly removed from scope
```

This is more informative than a generic `future work is needed` statement.

## 7. Claim guard

Do not interpret the prototype as:

- a new scalar measure of scientific uncertainty;
- a claim that resolving a predeclared confounding target resolves the full mechanism vector;
- a proof that every limitation has an available remedy;
- a robust Bayesian design optimum;
- a replacement for cost/utility decisions;
- evidence that non-estimable candidates have zero information;
- permission to relabel a structural fallback as validated mechanism information;
- permission to call a verified candidate globally optimal while declared alternatives remain non-estimable;
- evidence that an undeclared mechanism has been ruled out.

The prototype only classifies **why the declared MROD validated-information workflow stops or continues and what kind of next action is licensed by its current outputs**. Compatibility fallbacks, when used, remain a separately labelled operational layer.

## 8. Implementation

```text
causal_model/limitation_action_report.py
tests/test_limitation_action_report.py
```

The module is intentionally not added to the publication-facing public API yet. Its role is to test whether the `limitations -> next action` framing can be made precise without changing the underlying inference or candidate-selection algorithm.
