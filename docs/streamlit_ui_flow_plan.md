# Streamlit UI flow redesign plan

## Current problem

The current Streamlit app already exposes the RACH workflow, but the user flow is
hard to follow because primary and supplementary analyses are mixed in the same
page flow.

Observed issues:

1. The primary RACH inference controls are in the sidebar, but the conceptual
   explanation and results are spread across the main page.
2. The supplementary M1-M5 structure comparison appears before the primary RACH
   results in the main-page code flow.
3. If no M1-M5 comparison has been run, the app can still display a generic
   "Configure settings and click Run RACH inference" message even when the user
   is mainly looking for RACH results.
4. RACH results have many tabs, but the recommended reading order is not clear.
5. Downloads are correct but buried at the end.
6. The app lacks a simple "Start here → Run → Interpret → Download" flow.

## Design goal

Make the app read like a guided RACH workflow rather than a dashboard of many
independent tools.

The user should immediately understand:

```text
1. What data are being used?
2. Which analysis should I run first?
3. What does RACH conclude?
4. Why is causal degeneracy important?
5. What should I measure next?
6. How do I download the full reproducible output?
```

## Proposed main-page structure

### Section 0 — Start here

At the top of the page, add a compact guide:

```text
RACH workflow for Campanula / Izu Islands

1. Check y_obs and x_obs
2. Choose prior + ε in the sidebar
3. Click Run RACH inference
4. Read results in this order:
   Summary → CA_j → D/R → OC_k → NOV → A_ε → Downloads
5. Use supplementary M1-M5 comparison only after primary RACH inference
```

Use `st.info()` or `st.container(border=True)`.

### Section 1 — Data roles

Move / keep the existing y_obs and x_obs panel near the top, but label it clearly:

```text
Step 1. Data roles: what is fixed context and what is independent evidence?
```

Keep:

- y_obs response_target patterns
- x_obs fixed empirical context

### Section 2 — Primary RACH run

Move the primary run explanation into a visible main-page panel, while keeping
actual parameter controls in the sidebar.

Add text:

```text
Step 2. Run primary RACH inference
Use the sidebar to choose prior, ε, random seed, draw number, and ABM settings.
Then click Run RACH inference.
```

The sidebar button can stay, but main page should clearly point to it.

### Section 3 — Primary RACH results

When `sp_result` exists, show a summary tab first.

Recommended tab order:

```text
1. Summary
2. CA_j
3. D/R
4. OC_k
5. NOV
6. A_ε parameter space
7. Downloads
8. Sensitivity
```

Currently there is no explicit Summary tab. Add one before CA_j.

Summary tab should show:

```text
|A_ε| accepted
Total draws
Acceptance rate
D_RACH
R_RACH
Most admissible switch
Most informative next observation
Interpretation sentence
```

Example interpretation:

```text
The current y_obs reproduces the island trait syndrome, but R_RACH is low, so
causal mechanisms remain highly degenerate. Additional independent observations
are needed to distinguish mechanisms.
```

### Section 4 — Supplementary M1-M5 comparison

Move M1-M5 comparison into a clearly labelled expander below primary RACH results:

```text
Supplementary / optional: M1-M5 structure comparison
```

Make clear:

```text
This is not the primary RACH output. It is only a conventional structure-label
view for comparison.
```

Do not show M1-M5 results above RACH results.

### Section 5 — Downloads

Keep downloads in the RACH results tabs, but add a small note near the Summary:

```text
For reproducibility, download the ZIP after every run. The ZIP includes
accepted_rows, evaluated_rows, posterior_table, OC_k, NOV, and RACH summary.
```

## Sidebar structure

Use headings with numbers:

```text
1. Prior and ε
2. Simulation effort
3. Run primary RACH
4. Optional: M1-M5 comparison
```

Suggested labels:

- `θ prior preset` → `1. Prior preset for θ`
- `ε (ABC acceptance rule)` → `2. Acceptance rule ε`
- `Joint prior draws (θ, s)` → `3. Number of joint draws (θ, s)`
- `Run RACH inference` → `Run primary RACH inference`

## Small logic fix

Current message:

```python
else:
    st.markdown("Configure settings in the sidebar and click Run RACH inference...")
```

is tied to the absence of `research_result`, not necessarily absence of
`sp_result`. Replace with:

```python
if "sp_result" not in st.session_state and "research_result" not in st.session_state:
    st.markdown(...)
```

or show separate messages for primary and supplementary analyses.

## Acceptance criteria

- App opens with a clear "Start here" guide.
- The user can understand the intended sequence without reading source code.
- Primary RACH inference is visually separated from supplementary M1-M5 comparison.
- RACH results begin with a Summary tab.
- Downloads are still available and include all reproducibility tables.
- No generic run prompt appears after RACH results are already available.
- Existing RACH calculations are not changed; this is a UI/flow refactor.
