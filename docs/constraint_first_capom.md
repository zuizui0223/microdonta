# Constraint-first CAPOM workflow

This project is no longer framed as a manual-slider ABM. The main model is a **constraint-first causal generative workflow**.

## One-sentence definition

**Constraint-first CAPOM first defines an ecologically plausible latent parameter space, then tests which causal structures can generate the observed patterns within that constrained space.**

Japanese:

> 生態学的制約先行型CAPOMは、まず生態学的に妥当な潜在パラメータ空間を定義し、その制約内でどの因果構造が観察パターンを生成できるかを検証する方法である。

---

## Why the order matters

The model should not work like this:

```text
manual parameter sliders
-> run a simulation
-> adjust until the desired pattern appears
```

That workflow is useful for intuition, but weak as research because it can look like hand-tuning.

Instead, the research workflow is:

```text
1. Define ecological trade-off presets
2. Apply parameter-to-parameter constraints
3. Randomly sample latent benefit/cost parameters inside the constrained space
4. Convert valid samples into model parameters
5. Run candidate causal structures M1-M5
6. Compare simulated patterns with observed patterns
7. Retain accepted scenario-parameter combinations
8. Report scenario ranking and accepted parameter ranges
```

In short:

```text
constrained parameter exploration
-> causal simulation
-> CAPOM pattern matching
-> accepted causal structures and latent parameter ranges
```

---

## Model target

The goal is not to predict one exact parameter value. The goal is to infer which combinations of hidden benefits, costs, and causal pathways are **compatible** with multiple observed patterns.

The inferential output is therefore:

- accepted causal structures
- rejected causal structures
- accepted latent parameter ranges
- trade-off classes of accepted parameter sets
- pattern mismatches that show what each causal scenario fails to explain

The output is not:

- one manually tuned parameter set
- one best-looking simulation run
- a slider-generated demonstration result

---

## Observable patterns

The Campanula / Izu Islands worked example currently uses ordinal observed patterns such as:

```text
nectar_guide:      Oshima > Hachijo
selfing_rate:      Oshima < Hachijo
herkogamy:         Oshima > Hachijo
flower_size:       Oshima > Hachijo
Fis:               Oshima < Hachijo
Bombus_frequency:  Oshima > Hachijo
```

These are not treated as input values to force the model. They are treated as **targets for CAPOM matching**.

---

## Latent benefit/cost parameters

The constrained parameter search focuses on latent or hard-to-measure quantities:

```text
guide_cost
outcrossing_benefit
selfing_benefit
inbreeding_depression
small_pollinator_efficiency
drift_strength
direct_pollinator_guide_benefit
cost_of_waiting_for_pollinators
```

These parameters are sampled from predefined ecological trade-off presets, not chosen manually.

---

## Ecological trade-off presets

The app currently supports five presets:

```text
broad_prior
reproductive_assurance
outcrossing_benefit
high_guide_cost
drift_dominated
```

Each preset defines a biologically motivated region of latent parameter space.

Examples:

- `reproductive_assurance`: selfing is potentially favored because pollinator service is unreliable.
- `outcrossing_benefit`: outcrossing and pollinator-mediated attraction remain valuable.
- `high_guide_cost`: nectar-guide maintenance is costly.
- `drift_dominated`: drift can affect guide state and acts as a null-like scenario.

---

## Parameter-to-parameter constraints

Parameters are not sampled independently without logic. The sampler rejects biologically inconsistent combinations.

Examples:

```text
selfing_benefit - inbreeding_depression >= -0.30
```

This avoids cases where selfing has a severe net cost but is still treated as strongly favorable.

```text
if small_pollinator_efficiency > 0.55 and selfing_benefit > 0.75: reject
```

This avoids assigning extreme selfing benefit when alternative small-pollinator outcrossing is already efficient.

```text
if guide_cost > 0.25 and outcrossing_benefit < 0.05 and direct_pollinator_guide_benefit > 0.80: reject
```

This avoids internally inconsistent cases where guide maintenance is extremely costly, outcrossing benefit is almost absent, but direct guide benefit is extreme.

---

## Candidate causal structures

The constrained parameter sets are used to evaluate alternative causal structures:

```text
M1_direct_pollinator_to_guide
M2_selfing_mediated
M3_direct_plus_mediated
M4_common_island_cause
M5_drift_null
```

These structures correspond to different explanations for the observed overlap among Bombus loss, selfing increase, and nectar-guide reduction.

---

## CAPOM acceptance rules

The Streamlit app currently supports two acceptance rules:

```text
strict_6_of_6:   all 6 observed relations must match
relaxed_5_of_6: at least 5 of 6 observed relations must match
```

The strict rule is useful for conservative filtering. The relaxed rule is useful for early-stage model exploration and debugging.

---

## App implementation

The main Streamlit entry point is now research-mode only:

```bash
streamlit run streamlit_app.py
```

This imports the Research Mode app from:

```text
streamlit_research_mode.py
```

The app performs:

```text
trade-off preset selection
-> constrained random sampling
-> M1-M5 causal simulation
-> observed pattern matching
-> scenario ranking
-> accepted parameter ranges
-> CSV download
```

Manual parameter sliders are intentionally removed from the main app.

---

## Manuscript framing

> We did not manually tune latent parameters to reproduce the observed island pattern. Instead, we first defined biologically motivated trade-off ranges and parameter-to-parameter constraints, sampled latent benefit/cost parameters from this constrained space, and then evaluated which causal structures could generate the observed ecological, reproductive, and genetic patterns.

Japanese:

> 本研究では、観察パターンに合うように潜在パラメータを手動調整するのではなく、まず生態学的に動機づけられたトレードオフ範囲とパラメータ間制約を定義し、その制約付き空間から利益・コストパラメータをサンプリングした。そのうえで、どの因果構造が観察された生態・繁殖・遺伝パターンを生成できるかを評価した。
