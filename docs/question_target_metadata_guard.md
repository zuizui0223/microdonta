# Question-target definition guard

Status: internal companion note to `question_relative_mechanism_target.md`.

For a question-relative mechanism target, the target is a single predeclared map

```text
T = tau(S)
```

shared by every candidate being compared.

`CandidateObservation.target_switches` does **not** define this target. That field is candidate-level rationale metadata describing switches a measurement is expected to inform. If the scientific target were allowed to change candidate by candidate, information values would no longer answer one common question and candidate ranking would be circular.

The existing target-aware calculation therefore uses one fixed `target_columns` declaration for the entire candidate set. In the deterministic-coarsening special case audited here, those target columns must encode the same `tau(S)` for every candidate.

Do not infer or optimize `tau` from candidate outcomes. Changing the target partition is a change in the scientific question/model, not a tuning step in observation selection.
