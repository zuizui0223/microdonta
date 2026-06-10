# Ensemble-first Streamlit workflow for RACH

## Rationale

The primary RACH workflow should not be a single manual run first. Because RACH
quantities depend on prior settings and ε, the app should first scan the
configuration space, identify robust inferences, then use the best-supported
configuration for main reporting.

Recommended analysis order:

```text
1. Ensemble scan
2. Robust conclusion check
3. Best-setting main RACH result
4. NOV for unresolved / sensitive switches
5. Downloads
6. Supplementary M1-M5 comparison
```

## Step 1 — Ensemble scan

Run all combinations of:

```text
preset × acceptance_rule
```

For each configuration, compute:

```text
n_accepted
acceptance_rate
CA_j
D_RACH
R_RACH
```

Select the best setting using:

```text
n_accepted >= 20
maximise R_RACH
```

If no setting has `n_accepted >= 20`, show a warning and select the setting with
largest `n_accepted`, but flag it as unstable.

## Step 2 — Robust conclusion check

For each switch, compute sensitivity across ensemble configurations:

```text
sensitivity_range_j = max(CA_j across configs) - min(CA_j across configs)
```

Classify:

```text
robust      if sensitivity_range_j < 0.2
sensitive   if sensitivity_range_j >= 0.2
```

Only robust switches should be treated as reliable inference targets. Sensitive
switches should be labelled:

```text
prior/epsilon sensitive — requires additional observations
```

## Step 3 — Main RACH result from best setting

The main CA_j / D / R report should come from the ensemble-selected best setting,
not from an arbitrary manual single run.

The Summary should show:

```text
selected preset
selected acceptance_rule
n_accepted
D_RACH
R_RACH
robust switches
sensitive switches
```

Recommended interpretation sentence:

```text
This main result is reported from the ensemble-selected setting that maximises
R_RACH among stable configurations. Switches with high sensitivity_range are not
interpreted as robust; they are treated as targets for additional observations.
```

## Step 4 — NOV after sensitivity analysis

NOV should target unresolved/sensitive switches. The question is:

```text
Which new observation would reduce uncertainty in the switches that are not robust?
```

Therefore NOV belongs after ensemble sensitivity analysis.

NOV table should include:

```text
candidate
target_switches
target_switch_is_sensitive
expected_resolvability_gain
current_R
priority
rationale
```

## Step 5 — Downloads

The reproducible ZIP should include:

```text
ensemble_results.csv
robustness_table.csv
best_setting_summary.csv
accepted_rows.csv
evaluated_rows.csv
posterior_table.csv
observation_contribution.csv
nov_table.csv
rach_summary.csv
```

## Step 6 — Supplementary M1-M5 comparison

M1-M5 structure comparison should be clearly labelled as optional and
supplementary.

Text:

```text
This is not the primary RACH output. It maps switch-level inference back to
conventional structure labels for comparison only.
```

## Implementation suggestions

Add helper functions where practical:

```python
select_best_ensemble_setting(results, min_accepted=20)
classify_switch_robustness(ensemble_table, threshold=0.2)
```

Keep the existing single-run RACH mode as an advanced/manual option, not the
primary default workflow.

## Acceptance criteria

- App opens with an ensemble-first workflow guide.
- First primary action is ensemble scan.
- Best setting is automatically selected from ensemble results.
- Robust and sensitive switches are visually separated.
- Main CA_j/D/R result comes from best setting.
- NOV is framed as resolving sensitive switches.
- Downloads include ensemble and best-setting outputs.
- M1-M5 comparison is supplementary.
