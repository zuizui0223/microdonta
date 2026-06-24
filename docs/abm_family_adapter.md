# ABM Family Adapter

`abm_family_adapter.py` connects parameter sweeps from ecological and evolutionary ABMs to Rule-Transition RACH.

## Principle

A single successful parameterisation is not treated as evidence for a general rule. Each `(scenario, program_id, motif set)` is evaluated over a declared admissible sweep.

- **robust**: the focal qualitative pattern occurs in at least `min_match_fraction` of at least `min_replicates` runs;
- **fragile**: the pattern occurs, but only rarely (`0 < fraction <= fragile_max_fraction`);
- **rejected**: the pattern is absent or too infrequent;
- **insufficient**: too few replicates were supplied.

The thresholds are a pre-registered policy, not a posterior probability. Claims remain conditional on the ABM family, its ecological constraints, and sweep design.

## Workflow

```python
from causal_model.abm_family_adapter import SweepRecord, RobustnessPolicy, program_runs_from_sweep
from causal_model.rule_transition_invariants import infer_rule_transition_invariants

runs = program_runs_from_sweep(sweep_records, RobustnessPolicy())
result = infer_rule_transition_invariants(runs)
```

`SweepRecord.motifs` should use the shared ecological vocabulary, for example:

- `interaction_loss`
- `reproductive_reconfiguration`
- `demographic_reconfiguration`
- `selection_reconfiguration`
- `trait_space_shift:low_investment`

The result is a conditional rule-transition invariant: no robust program in the specified family reproduces the qualitative pattern without the returned motif or clause.
