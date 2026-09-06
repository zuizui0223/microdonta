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
| `actionable` | `D>0` and some verified `V(Q)>0` | ambiguity remains and available observations can reduce it | measure a best current candidate |
| `information_limited` | `D>0`, verified candidates exist, all `V(Q)=0` | current candidate vocabulary contains no mechanism information | report information limit; redesign/expand observations |
| `prediction_limited` | `D>0`, candidates exist but none has an identified predictive partition | the candidate outcomes cannot yet be valued | identify/model candidate outcome distributions first |
| `candidate_limited` | `D>0`, no candidate observations declared | no follow-up vocabulary exists | expand candidate vocabulary |
| `budget_limited` | `D>0`, informative candidates may exist but budget is exhausted | scientific ambiguity remains for a resource reason | report budget limit explicitly |

These states answer different questions. In particular, `information_limited` is not the same as `budget_limited`, and `prediction_limited` is not evidence that all candidate measurements are useless.

## 3. Specification axes

When several scientifically defensible priors, tolerances or other specifications are predeclared, compute the single-specification state separately for each one.

The prototype then reports three additional axes.

### Resolution stability

```text
robust_resolved
robust_unresolved
specification_sensitive
```

A mix of resolved and unresolved specifications means that even the claim `mechanism resolved` is specification-sensitive.

### Actionability stability

```text
robust_actionable
robust_not_actionable
specification_sensitive
not_required
```

This asks whether every unresolved specification agrees that some current candidate contains positive mechanism information.

### Recommendation stability

For actionable specifications let

```text
B_lambda = argmax_Q V_lambda(Q).
```

The intersection

```text
B_common = intersection B_lambda
```

gives:

```text
robust
specification_sensitive_ranking
specification_sensitive_actionability
not_available
```

This is the same sensitivity-reporting logic used in `docs/tolerance_and_specification_robustness.md`; it is not a new robust-design objective.

## 4. Why keep the axes separate?

A single `limitation severity` score would destroy information needed for the next scientific action.

For example:

- `D>0, max V=0` means **change what can be observed**, not merely collect more replicates;
- non-estimable `V` means **improve the predictive observation model**, not reject the candidate as uninformative;
- an empty common-best set means **the recommendation depends on the analysis specification**, not that every candidate has low value;
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
Action: report recommendation sensitivity or declare an additional robust decision rule
```

or

```text
Current mechanism state: unresolved
Candidate-information state: information-limited
Verified candidate values: all zero
Action: current measurement vocabulary cannot resolve the remaining mechanism ambiguity
```

This is more informative than a generic `future work is needed` statement.

## 6. Claim guard

Do not interpret the prototype as:

- a new scalar measure of scientific uncertainty;
- a proof that every limitation has an available remedy;
- a robust Bayesian design optimum;
- a replacement for cost/utility decisions;
- evidence that non-estimable candidates have zero information;
- evidence that an undeclared mechanism has been ruled out.

The prototype only classifies **why the declared MROD workflow stops or continues and what kind of next action is licensed by its current outputs**.

## 7. Implementation

```text
causal_model/limitation_action_report.py
tests/test_limitation_action_report.py
```

The module is intentionally not added to the publication-facing public API yet. Its role is to test whether the `limitations -> next action` framing can be made precise without changing the underlying inference or candidate-selection algorithm.
