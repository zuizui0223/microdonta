# From inferential limitations to explicit next actions

Status: **internal MROD prototype.** This note composes existing MROD outputs into an action/reporting layer. It is not part of the active MEE manuscript, does not define a new uncertainty score and does not change the frozen G2 policy.

## 1. Motivation

A conventional Discussion limitation often ends with

> alternative mechanisms cannot be excluded; future work is needed.

MROD can be more explicit because distinct reasons for stopping or continuing are already observable from the current analysis. Those reasons should not be collapsed into one generic uncertainty number.

The prototype therefore reports **orthogonal limitation axes** and derives actions from their combination.

## 2. Full mechanism resolution is not the same as the declared design target

Let

```text
D = H(S | A_current)
```

be residual entropy in the full declared mechanism vector.

`D=0` means the current declared mechanism distribution is concentrated on one switch vector: **full mechanism resolution** under the declared family. A sequential study can legitimately have a narrower predeclared target, however. Frozen G2, for example, stops when its declared confounding-edge structure is resolved; other switch uncertainty may remain.

Therefore:

```text
full mechanism resolution
    !=
declared design target resolution
```

If the narrower target is resolved while `D>0`, report both:

```text
declared target: resolved
full mechanism state: ambiguous
```

rather than writing `all mechanisms resolved`.

If the current entropy itself is non-estimable—for example because no admissible rows survive—that is a separate `current_state_nonestimable` state. It is neither resolution nor an information-limit result.

## 3. Orthogonal single-specification axes

For a target that remains unresolved, verified candidates have

```text
V(Q) = I(S;Q | A_current)/K.
```

The prototype keeps the following axes separate.

### 3.1 Current state

```text
estimable
nonestimable
```

A non-estimable current state must be repaired before candidate information is interpreted.

### 3.2 Full mechanism state

```text
fully_resolved
ambiguous
nonestimable
```

### 3.3 Declared design target

```text
resolved
unresolved
nonestimable
```

A resolved target can coexist with an ambiguous full mechanism state.

### 3.4 Budget

```text
available
exhausted
```

Budget is deliberately not a candidate-information label. A study can be budget-exhausted while the most informative future candidate is already known.

### 3.5 Candidate predictive coverage

```text
not_required       target already resolved
not_evaluable      current state not estimable
none_declared      no candidate vocabulary
none_estimable     candidate outcomes cannot be valued
partial            some candidates valued, others non-estimable
complete           every declared candidate valued
```

### 3.6 Validated candidate information

```text
not_required
not_evaluable
not_available
nonestimable
zero
positive
```

A global information-limit claim requires `candidate_coverage=complete` and `validated_information_status=zero`.

### 3.7 Recommendation status

```text
not_required
not_evaluable
unavailable
provisional_best_among_estimable
validated_best
```

A verified positive candidate under partial predictive coverage is only provisional among the estimable subset. It is not globally optimal over the declared candidate vocabulary.

## 4. Derived actions

The axes imply different actions without being collapsed into one severity score.

| Situation | Licensed action |
|---|---|
| current state non-estimable | repair/re-estimate the admissible region |
| full mechanism or declared target resolved | stop the predeclared sequence; report residual out-of-target ambiguity if present |
| no candidate vocabulary | expand candidate observations |
| no candidate predictive model | identify/model candidate outcome distributions |
| partial predictive coverage | resolve non-estimable candidates before a global ranking; optionally report a provisional best among estimable candidates |
| complete coverage, all `V=0` | report an information limit and redesign/expand the measurement vocabulary |
| complete coverage, positive `V`, budget available | measure a best current candidate |
| complete coverage, positive `V`, budget exhausted | report budget limitation **and retain the identified best candidate for future budget** |

The last case illustrates why budget and information should be separate axes.

### 4.1 Validated actionability versus compatibility fallback

The sequential compatibility backend can assign an explicitly labelled `normalized_edge_cut_fallback` when a predictive partition is unavailable. That may be operationally useful, but it is **not** `I(S;Q|A_current)/K`.

Thus a report may say

```text
validated candidate coverage: none_estimable
compatibility fallback: available, normalized_edge_cut_fallback
```

but must not translate that into

```text
actionable by validated mechanism information
```

The fallback remains a separately labelled heuristic layer.

## 5. Sensitivity axes across specifications

For a predeclared set of defensible priors, tolerances or other specifications, compute the single-specification axes separately and then report:

### Full-mechanism-resolution stability

```text
stable_mechanism_fully_resolved
stable_mechanism_ambiguous
stable_mechanism_nonestimable
specification_sensitive
```

### Declared-target-resolution stability

```text
stable_target_resolved
stable_target_unresolved
stable_target_nonestimable
specification_sensitive
```

### Validated actionability stability

```text
stable_actionable
stable_not_fully_actionable
specification_sensitive
not_required
```

`stable_actionable` requires complete candidate coverage and positive validated information under every target-unresolved specification.

### Recommendation stability

For fully actionable target-unresolved specifications,

```text
B_lambda = argmax_Q V_lambda(Q)
B_common = intersection_lambda B_lambda
```

and report

```text
stable_common_best
specification_sensitive_ranking
specification_sensitive_actionability
not_available
```

These are descriptive sensitivity labels, not a maximin, robust-EIG or other robust-design objective.

## 6. Why keep the axes separate?

A single `limitation severity` score would destroy information needed for the next scientific action.

Examples:

- declared confounding edges can be resolved while residual switch entropy remains positive;
- no admissible current region means re-estimate the state before ranking observations;
- `D>0, max V=0` with every candidate estimable means change **what can be observed**, not merely collect more replicates;
- non-estimable `V` means improve the predictive observation model, not reject the candidate as uninformative;
- a positive verified candidate does not justify a global `best next observation` claim while declared alternatives remain non-estimable;
- an available structural fallback does not turn non-estimable mechanism information into validated information;
- exhausted budget does not erase knowledge of which candidate would be best if resources become available;
- an empty common-best set means the recommendation depends on specification, not that every candidate has low value.

Preserving these distinctions follows the wider project rule: **do not manufacture certainty by coarsening unresolved structure.**

## 7. Example outputs

### Target resolved, full mechanism still ambiguous

```text
Current state: estimable
Full mechanism state: ambiguous, D=1.2 bits
Declared design target: resolved
Action: stop the predeclared sequence and report residual out-of-target ambiguity
```

### Actionable but recommendation-sensitive

```text
Current state: estimable
Declared design target: unresolved
Candidate coverage: complete
Validated information: positive
Budget: available
Recommendation stability: specification-sensitive ranking
Strict epsilon best: pollen deposition
Loose epsilon best: common-garden phenotype
Common-best set: empty
Action: report recommendation sensitivity or declare an additional decision rule
```

### Information-limited

```text
Declared design target: unresolved
Candidate coverage: complete
Validated information: zero
Non-estimable candidates: none
Action: current measurement vocabulary cannot resolve the remaining mechanism ambiguity
```

### Partial predictive coverage

```text
Declared design target: unresolved
Candidate coverage: partial
Validated information among estimable candidates: positive
Provisional best: pollen deposition
Non-estimable candidate: reciprocal transplant
Compatibility fallback: available but non-information-theoretic
Action: do not call pollen deposition globally optimal until the remaining candidate is valued or explicitly removed from scope
```

### Budget-limited but epistemically actionable

```text
Declared design target: unresolved
Candidate coverage: complete
Validated information: positive
Validated best: pollen deposition
Budget: exhausted
Action: report budget limitation; retain pollen deposition as the identified next measurement if budget becomes available
```

This is more informative than a generic `future work is needed` statement.

## 8. Claim guard

Do not interpret the prototype as:

- a new scalar measure of scientific uncertainty;
- a claim that resolving a predeclared confounding target resolves the full mechanism vector;
- a proof that every limitation has an available remedy;
- a robust Bayesian design optimum;
- a replacement for cost/utility decisions;
- evidence that non-estimable candidates have zero information;
- permission to relabel a structural fallback as validated mechanism information;
- permission to call a provisional verified candidate globally optimal while declared alternatives remain non-estimable;
- evidence that an undeclared mechanism has been ruled out.

The prototype classifies **why the declared validated-information workflow stops or continues and what kind of next action is licensed by its current outputs**. Compatibility fallbacks remain a separate operational layer.

## 9. Implementation

```text
causal_model/limitation_action_report.py
tests/test_limitation_action_report.py
```

The module is intentionally not added to the publication-facing API yet. Its role is to test whether the `limitations -> next action` framing can be made precise without changing the underlying inference or candidate-selection algorithm.
