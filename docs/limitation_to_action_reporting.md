# From inferential limitations to explicit next actions

Status: **internal MROD prototype.** This note composes existing MROD outputs into an action/reporting layer. It is not part of the active MEE manuscript, does not define a new uncertainty score and does not change the frozen G2 policy.

## 1. Motivation

A conventional Discussion limitation often ends with a sentence such as

> alternative mechanisms cannot be excluded; future work is needed.

MROD can be more explicit because several distinct reasons for stopping or continuing are already observable from the current analysis. These reasons should not be collapsed into one generic `uncertainty` number.

The prototype therefore reports **orthogonal limitation axes** and an associated action.

## 2. Single-specification states

Let

```text
D = H(S | A_current)
```

be current residual mechanism entropy and let candidate observations have validated values

```text
V(Q) = I(S;Q | A_current)/K.
```

For one declared specification:

| State | Diagnostic | Meaning | Action |
|---|---|---|---|
| `resolved` | `D=0` under the declared resolution rule | no residual mechanism distinction remains | stop as resolved |
| `actionable` | `D>0`, **all declared candidates are estimable**, and some `V(Q)>0` | ambiguity remains and the full declared candidate set can be ranked | measure a best current candidate |
| `information_limited` | `D>0`, **all declared candidates are estimable**, and all `V(Q)=0` | current candidate vocabulary contains no mechanism information | report information limit; redesign/expand observations |
| `prediction_limited` | `D>0`, candidates exist but none has an identified predictive partition | candidate values cannot yet be estimated | identify/model candidate outcome distributions first |
| `partial_prediction_limited` | `D>0`, some candidates are estimable and some are not | verified candidates can be described, but a global ranking over the declared candidate set is not licensed | resolve non-estimable candidates or explicitly narrow the candidate set before ranking |
| `candidate_limited` | `D>0`, no candidate observations declared | no follow-up vocabulary exists | expand candidate vocabulary |
| `budget_limited` | `D>0`, informative candidates may exist but budget is exhausted | scientific ambiguity remains for a resource reason | report budget limit explicitly |

These states answer different questions. In particular, `information_limited` is not the same as `budget_limited`, and no information-limit claim is allowed while declared candidates remain non-estimable.

## 3. Specification axes

When several scientifically defensible priors, tolerances or other specifications are predeclared, compute the single-specification state separately for each one.

The prototype then reports three additional axes. These are **stability labels**, not robust-design objectives.

### Resolution stability

```text
stable_resolved
stable_unresolved
specification_sensitive
```

A mix of resolved and unresolved specifications means that even the claim `mechanism resolved` is specification-sensitive.

### Actionability stability

```text
stable_actionable
stable_not_actionable
specification_sensitive
not_required
```

This asks whether every unresolved specification agrees that the **complete declared candidate set is estimable and contains a positive-value candidate**.

### Recommendation stability

For fully actionable specifications let

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

## 4. Why keep the axes separate?

A single `limitation severity` score would destroy information needed for the next scientific action.

For example:

- `D>0, max V=0` **with every candidate estimable** means change what can be observed, not merely collect more replicates;
- non-estimable `V` means improve the predictive observation model, not reject the candidate as uninformative;
- a positive verified candidate does not justify a global `best next observation` claim while other declared candidates remain non-estimable;
- an empty common-best set means the recommendation depends on the analysis specification, not that every candidate has low value;
- exhausted budget means the observation may be known and useful but currently infeasible.

Preserving these distinctions is consistent with the wider project principle: do not manufacture certainty by coarsening unresolved structure.

## 5. Practical output

A paper, report or software interface could end the mechanism-resolution analysis with a block such as

```text
Current mechanism state: unresolved
Candidate-information state: actionable
Recommendation stability: specification-sensitive ranking
Best candidate under strict epsilon: pollen deposition
Best candidate under loose epsilon: common-garden phenotype
Common-best set: empty
Action: report recommendation sensitivity or declare an additional decision rule
```

or

```text
Current mechanism state: unresolved
Candidate-information state: information-limited
Verified candidate values: all zero
Non-estimable candidates: none
Action: current measurement vocabulary cannot resolve the remaining mechanism ambiguity
```

or

```text
Current mechanism state: unresolved
Candidate-information state: partial prediction limit
Best verified candidate: pollen deposition
Non-estimable candidate: reciprocal transplant
Action: do not call pollen deposition globally optimal until the remaining candidate can be valued or is explicitly removed from scope
```

This is more informative than a generic `future work is needed` statement.

## 6. Claim guard

Do not interpret the prototype as:

- a new scalar measure of scientific uncertainty;
- a proof that every limitation has an available remedy;
- a robust Bayesian design optimum;
- a replacement for cost/utility decisions;
- evidence that non-estimable candidates have zero information;
- permission to call a verified candidate globally optimal while declared alternatives remain non-estimable;
- evidence that an undeclared mechanism has been ruled out.

The prototype only classifies **why the declared MROD workflow stops or continues and what kind of next action is licensed by its current outputs**.

## 7. Implementation

```text
causal_model/limitation_action_report.py
tests/test_limitation_action_report.py
```

The module is intentionally not added to the publication-facing public API yet. Its role is to test whether the `limitations -> next action` framing can be made precise without changing the underlying inference or candidate-selection algorithm.
