# ABM robustness backend

`causal_model.abm_robustness` converts parameter-sweep output into the
`ProgramRun` objects used by Rule-Transition RACH.

## Required record fields

Each ABM evaluation must provide:

```text
scenario         independent ecological system / scenario
program_id       causal program or ABM family identifier
parameter_cell   one distinct parameter + update-rule + initial-state draw
replicate_id     stochastic replicate within that cell
motifs           ecological rule-transition motifs active in that run
matches_pattern  whether the declared qualitative target pattern occurred
fragile_flags    optional: exact_cancellation, boundary_only,
                 exact_initial_alignment, measure_zero_tuning
```

## Operational robustness rule

A parameter cell is successful when at least 50% of its stochastic replicates
match the focal qualitative pattern. A program is robust by default when:

1. it was evaluated in at least three distinct parameter cells;
2. at least 60% of those cells are successful;
3. no successful record carries a disqualifying fragility flag.

These are explicit, adjustable operating thresholds, not a theorem about
nature. They should be recorded with every RACH result.

## Pipeline

```python
from causal_model.abm_robustness import program_runs_from_sweep
from causal_model.rule_transition_invariants import infer_rule_transition_invariants

program_runs = program_runs_from_sweep(sweep_records)
result = infer_rule_transition_invariants(program_runs)
```

The resulting invariant states only that no robust admissible program in the
specified ABM family reproduces the declared qualitative pattern without the
returned motif or clause.
