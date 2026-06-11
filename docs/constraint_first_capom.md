# Constraint-First RACH Workflow

This project is no longer framed as manual-slider CAPOM or fixed M1-M5 model
choice. The main workflow is **constraint-first RACH**: define biologically
plausible latent parameter space, simulate causal switch combinations, and
quantify which switch states remain admissible under independent observations.

## One-Sentence Definition

RACH samples causal switch combinations `s in {0,1}^K` and latent parameters
`theta`, filters them through biological constraints and observation distance,
then reports causal admissibility, degeneracy, resolvability, observation
contribution, and next-observation value.

## Why The Order Matters

The model should not work like this:

```text
manual parameter sliders
-> run a simulation
-> adjust until the desired pattern appears
```

Instead, the research workflow is:

```text
1. Define ecological context x_obs.
2. Define biological feasibility constraints G(theta).
3. Sample latent parameters theta and causal switch states s.
4. Simulate f(x_obs; theta, s).
5. Compare simulated summaries with current independent y_obs.
6. Retain the admissible region A_epsilon.
7. Report CA_j, D_RACH, R_RACH, OC_k, and NOV.
```

## Epistemic Roles

The Campanula worked example separates roles explicitly:

```text
x_obs:
  island distance
  island area
  population size proxy
  primary pollinator frequency / Bombus availability
  ecological context

current y_obs:
  selfing_distance
  flower_size_distance

future_observation / NOV candidate:
  guide area spectrophotometry
  herkogamy / delayed-selfing geometry
  Fis / He / Fst
  bagging seed set
  natural seed set
  pollinator visitation rate
  guide removal experiment
  Qst-Fst comparison
  guide-to-visitation selection gradient
  molecular outcrossing rate t_m

diagnostic_only / hypothesis_prediction:
  selfing_herkogamy_corr
  selfing_flower_size_corr
  selfing_Fis_corr
  guide_outcross_corr
  theoretical nectar-guide gradients
  theoretical herkogamy gradients
```

Unmeasured guide, herkogamy, Fis/He, seed-set, and visitation rows must not be
promoted to `observed_target`.

## Current Acceptance Target

The current canonical y_obs has only two source-confirmed directional gradients:

```text
selfing_distance
flower_size_distance
```

Therefore A_epsilon is expected to be broad and causal resolution is expected to
be low. This is a preliminary worked example, not an empirical resolution of the
*Campanula microdonta* causal history.

## Acceptance Rules

Acceptance rules are pattern-count-independent. `strict_all` means all current
`observed_target` rows must pass. It no longer means a hard-coded "6 of 6".

Optional distance tools are available for later measured data:

```text
distance_mode:
  match_rate
  standardized
  hybrid

epsilon_mode:
  fixed
  adaptive_percentile

structure_prior_lambda:
  lambda = 0.0 gives the unweighted switch prior
  lambda > 0 applies P(s) proportional to exp(-lambda * |s|)
```

The structure prior is optional sensitivity analysis. It must not be presented
as evidence against biologically plausible multi-switch pathways.

## M1-M5 Role

M1-M5 named structures are retained only as a supplementary interpretation
layer. They are not the primary inferential object.

The primary RACH output is:

```text
switch vector s
CA_j
coactivation
D_RACH
R_RACH
OC_k
NOV
```

`nearest_structure` can be displayed as a diagnostic summary, but it should not
be treated as the main conclusion.

## Manuscript Framing

Recommended wording:

> We do not select among fixed M1-M5 causal structures. Instead, RACH samples
> causal switch combinations and latent parameters, retains the admissible region
> under biological constraints and source-confirmed observations, and quantifies
> how much the current observations resolve mechanism uncertainty.

Avoid:

```text
RACH resolves the Campanula causal history.
Six observed patterns are used.
Herkogamy is field-derived y_obs.
Fis is observed_target.
Primary pollinator frequency is y_obs.
```
