# ABM-family workflow for Rule-Transition RACH

## Purpose

A single ABM run is never treated as evidence for a general ecological rule.
This adapter converts a family of stochastic runs into qualitative program
records that can be analysed by `rule_transition_invariants`.

## Required input

Each `ABMTrial` needs:

- `scenario`: ecological system/scenario label;
- `program_id`: causal program or ABM-family member;
- `region_id`: predeclared coarse parameter/initial-state region;
- `output`: simulator output.

The analyst supplies two functions:

1. `pattern_matches(output) -> bool`, defining the focal qualitative pattern;
2. `motifs_for_program(scenario, program_id)`, returning the ecological
   rule-transition motifs encoded by that program.

## Robustness policy

A program is robust only when:

- the focal pattern occurs in at least `min_regions` independent declared
  regions; and
- the mean within-region success rate exceeds `min_success_rate`.

A program that succeeds at least once but fails this rule is retained as a
fragile explanation. A program that never succeeds is not an admissible
explanation and is omitted.

`region_id` must not be a random seed. Multiple seeds within one region improve
estimation but cannot, by themselves, demonstrate robustness.

## Workflow

```python
runs, audits = classify_abm_family(
    trials=abm_trials,
    pattern_matches=matches_focal_pattern,
    motifs_for_program=motifs_for_program,
    policy=RobustnessPolicy(min_success_rate=0.6, min_regions=3),
)

result = infer_rule_transition_invariants(runs)
```

The resulting invariant has the conditional interpretation:

> No robust admissible program in the declared ABM family reproduces the focal
> qualitative pattern without the returned motif or disjunctive clause.

It does not assert that the motif is universally true in nature.
