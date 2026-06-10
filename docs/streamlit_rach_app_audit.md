# Streamlit RACH app audit

This note audits the Streamlit implementation against the current RACH theory and
implementation state.

## Overall verdict

The Streamlit app is substantially aligned with the current RACH implementation.
It exposes the primary RACH workflow and displays the core quantities:

- `CA_j` causal admissibility
- `D_RACH` causal degeneracy
- `R_RACH` causal resolvability
- `OC_k` observation contribution
- `NOV(q)` next-observation value
- accepted parameter space `A_ε`

The app is therefore not merely showing a generic ABC/ABM result. It has a
RACH-specific interface.

## Confirmed implementation points

### 1. Primary RACH workflow exists

The sidebar has a primary section named:

```text
RACH inference — A_ε & core quantities
```

It runs joint prior draws `(θ, s)`, calls the stochastic ABM backend, and stores
the resulting `SwitchPosteriorResult` in session state.

### 2. RACH result tabs exist

The app creates tabs for:

```text
CA_j — causal admissibility
D · R — degeneracy & resolvability
OC_k — observation contribution
NOV — next-observation value
Parameter space A_ε
Downloads
```

This matches the current RACH framing.

### 3. OC_k uses evaluated_rows

The app computes observation contribution using:

```python
_oc_source = getattr(sp, "evaluated_rows", None) or sp.accepted_rows
_oc_results = _oc_fn(_oc_source, CAMPANULA_SWITCHES, threshold=_thresh_display)
```

This is correct. It prioritises all evaluated rows, which is required because
removing one pattern may cause previously rejected rows to become accepted in the
leave-one-out admissible region.

### 4. RACH modules are imported lazily

The RACH-specific functions are imported inside the result block. This prevents
initial app load from failing due to a downstream optional computation before any
run has been performed.

## Minor issues / recommended fixes

### Issue A — `causal_admissibility.py` top-level docstring still says R uses `H(S)`

Current top-level docstring text says:

```text
R      Causal resolvability    1 - H(S | A_ε) / H(S)
```

But the mathematical-foundations document correctly defines the robust version as:

```text
R_RACH = 1 - H(S | A_ε) / log2|S| = 1 - H(S | A_ε)/K
```

The actual code uses `_max_entropy(K)`, so the implementation is fine. The
docstring should be updated to avoid theoretical ambiguity.

### Issue B — public API docstring says `observation_contribution(accepted_rows, ...)`

The top-level docstring currently says:

```text
observation_contribution(accepted_rows, switches, threshold)
```

but the function now correctly takes:

```text
observation_contribution(evaluated_rows, switches, threshold)
```

This is documentation drift, not a functional bug.

### Issue C — Downloads should include evaluated_rows and OC/NOV tables

The Streamlit downloads currently expose accepted rows and posterior table. For
reproducibility of RACH inference, it would be better to also export:

```text
evaluated_rows.csv
observation_contribution.csv
nov_table.csv
rach_summary.csv
```

The evaluated rows are especially important because OC_k cannot be reproduced
from accepted rows alone.

### Issue D — Runtime smoke test should be added

A lightweight smoke test should verify that `streamlit_app.py` imports without
raising errors and that the RACH module imports used in the app are available.
This can be a simple Python test; full Streamlit browser testing is not required.

## Conclusion

The Streamlit implementation is conceptually correct and already exposes the core
RACH workflow. The remaining work is polishing and reproducibility:

1. update stale docstrings;
2. export evaluated rows and RACH metric tables;
3. add a simple app-import smoke test.

These are not blockers for the mathematical model itself, but they should be
fixed before using the app as a public demo or manuscript supplement.
