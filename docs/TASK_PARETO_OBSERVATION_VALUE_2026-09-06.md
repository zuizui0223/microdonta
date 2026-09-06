# Task-Pareto observation value

MROD now exposes two explicitly distinct prospective utilities:

```text
V_S(Q) = I(S;Q | A_epsilon) / K
```

for residual mechanism resolution, and

```text
V_T(Q) = I(T;Q | A_epsilon) / H(T | A_epsilon)
```

for a predeclared target.

There is no scientifically privileged scalar weight that turns these two tasks
into one universal score.  The default cross-task comparison therefore reports
the two-dimensional value pair and its Pareto status.

Implementation:

```text
causal_model/task_pareto.py
tests/test_task_pareto.py
```

## Finite policy witness

The registered 2 x 2 x 2 admissible region contains an independent mechanism
bit `S`, target bit `T`, and nuisance/noise bit.  Three candidate observations
then have values

```text
measure_mechanism -> (V_S,V_T)=(1,0)
measure_target    -> (V_S,V_T)=(0,1)
measure_noise     -> (V_S,V_T)=(0,0).
```

The first two candidates form a two-point Pareto front.  Neither dominates the
other.  The noise candidate is dominated by both.

Thus

```text
no unique best next observation
```

can be inferred without declaring which task matters, even when every candidate
has an exact verified outcome partition.

## Non-estimable dimensions are not zero

If either task value is unavailable because the candidate lacks a verified
predictive partition, the missing coordinate remains non-estimable.  It is not
silently converted to zero and allowed to enter the Pareto comparison.

## Relation to sequential policies

The existing mechanism-oriented and target-oriented sequential policies remain
separate.  The Pareto front is a decision surface for choosing between task
objectives; it is not a third hidden scalar policy.

This is the executable counterpart of the broader distinction

```text
causal-learning utility
!=
target-resolving utility.
```

## Claim boundary

Pareto non-dominance does not imply equal scientific importance.  It says only
that, under the declared admissible region and task definitions, no other
jointly estimable candidate is at least as informative on both axes and strictly
better on one.  Costs, ethics, feasibility, and report licensing remain separate
constraints.
