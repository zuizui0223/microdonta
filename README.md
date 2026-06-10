# RACH: Restricted Admissible Causal Hypotheses

**RACH** stands for **Restricted Admissible Causal Hypotheses**.

RACH is a general framework for simulation-based ecological causal inference. It asks:

> **Which latent causal mechanisms are admissible, given fixed ecological context, biological axioms, latent parameters, and independent observations?**

Japanese:

> **RACHは、固定された生態学的文脈・生物学的公理・潜在パラメータ・独立観測データのもとで、どの潜在因果メカニズムが許容されるかを推定する汎用フレームワークである。**

This repository implements a worked example using the Izu Islands population system of *Campanula punctata* / シマホタルブクロ. The Campanula model is an example, not the definition of RACH.

---

## Formal definition

The core RACH object is the **admissible causal region**:

```text
A_ε(y_obs, x_obs)
=
{(θ, s) ∈ Θ × S :
  G(θ)=1,
  d(P_sim(f(x_obs; θ, s)), P_obs(y_obs)) ≤ ε }
```

where:

```text
x_obs  = fixed empirical context used as simulator input
         e.g. island distance, island area, observed pollinator presence/frequency

θ      = latent ecological parameters to infer or marginalise over
         e.g. costs, benefits, inbreeding depression, drift scale,
              pollinator-loss slope, Ne-isolation slope, migration-decay rate

s      = causal switch state, s ∈ {0,1}^K
         e.g. guide-mediated attraction, selfing-syndrome evolution,
              isolation common cause, small-pollinator substitution

G(θ)   = ecological constraint grammar
         e.g. biological feasibility constraints on θ

f      = generative ecological dynamics
         e.g. Wright-Fisher drift, selection, reproduction, inheritance,
              pollination and mating rules

P_sim  = pattern extractor for simulated output
P_obs  = pattern extractor for empirical observations

y_obs  = independent empirical observations used for ABC/RACH acceptance

d      = distance between simulated and observed pattern spaces
ε      = tolerance threshold
```

The main inferential quantity is the switch posterior within the admissible region:

```text
π_j = P(s_j = 1 | (θ, s) ∈ A_ε)
```

This is an ABC-approximated posterior support for each latent mechanism.

---

## Core workflow

```text
1. Define biological axioms and ecological constraint grammar
       ↓
2. Define fixed empirical context x_obs
       ↓
3. Sample latent parameters θ within biologically admissible ranges
       ↓
4. Sample causal switch states s ∈ {0,1}^K
       ↓
5. Run generative simulation f(x_obs; θ, s)
       ↓
6. Extract comparable patterns P_sim and P_obs
       ↓
7. Accept samples whose distance to independent y_obs is ≤ ε
       ↓
8. Estimate switch posterior, identifiability, and causal degeneracy
```

RACH is **not** manual parameter tuning. The goal is to identify the subset of latent parameter–mechanism space that is both biologically coherent and compatible with independent observations.

---

## Required separation of roles

A central RACH requirement is that biological assumptions, fixed inputs, latent parameters, independent observations, hypothesis-derived predictions, and diagnostic definitions are not mixed.

| Class | Role in RACH | Used in `f`? | Part of `θ`? | Used as `y_obs` in ABC? | Example |
|---|---|---:|---:|---:|---|
| **Axiom** | Fixed model dynamics | yes | no | no | Wright-Fisher sampling, stochastic inheritance, fitness-proportional selection |
| **Universal / directional principle** | Directional biological constraint; coefficients remain uncertain | yes / G | partly | no | low Ne increases drift; drift ∝ 1/√Ne; reproductive assurance can favour selfing |
| **Latent parameter** | Unknown quantity to sample or infer | yes | yes | no | guide cost, inbreeding depression, Ne-isolation slope, migration-decay rate |
| **Fixed empirical context** | Observed input context `x_obs` | yes | no | no | island distance, island area, observed Bombus presence/frequency |
| **Empirical observation** | Independent response data `y_obs` | no | no | yes | measured guide value, selfing rate, herkogamy, flower size, seed set, genetic Fis/He if measured |
| **Hypothesis prediction** | Model prediction or future test | no | no | no | “selfing increases with isolation”, “guide decreases along isolation” if not independently measured |
| **Diagnostic-only pattern** | Internal consistency / syndrome definition | no | no | no by default | selfing-herkogamy correlation as a definition of selfing syndrome |

Japanese summary:

```text
公理: f の力学に固定
普遍的原理: 方向だけ f/G に固定し、係数は θ
観測文脈: x_obs として f に渡すがABCから除外
独立観測: y_obs としてABCに使用
仮説予測: ABCから除外し、posterior predictive check / future prediction に使う
診断定義: ABCから除外し、diagnostic_only として扱う
```

---

## What belongs in `f`?

`f` should contain biological or stochastic dynamics that define the generative process:

```text
Wright-Fisher / finite-population sampling
Mendelian or parent-offspring trait inheritance
mutation or perturbation processes
fitness-proportional selection
selfing / outcrossing probability rules
pollination-to-reproduction rules
```

`f` may use fixed empirical context `x_obs`, but it should not hard-code uncertain empirical slopes as if they were laws.

Good:

```text
Drift increases as Ne decreases.
```

Risky if fixed inside `f`:

```text
effective_population_size = 1.00 - 0.765 × isolation
primary_pollinator_frequency = 0.80 - 0.94 × isolation
community_pollinator_abundance = 0.88 - 0.635 × isolation
```

Those coefficients should be latent parameters unless independently fixed by data and uncertainty is ignored deliberately.

---

## What belongs in θ?

θ contains unknown or partially known ecological quantities:

```text
guide_cost
outcrossing_benefit
selfing_benefit
inbreeding_depression
background_pollinator_efficiency
drift_effect_scale
guide_selection_strength
primary_pollinator_guide_response
cost_of_waiting_for_pollinators
pollinator_loss_slope
Ne_isolation_slope
community_abundance_isolation_slope
background_pollinator_slope
migration_decay_rate
```

For general RACH applications, environmental-gradient coefficients should normally be sampled as θ, not hard-coded into the simulator.

Example:

```text
Ne(isolation) = Ne0 × exp(-α_Ne × isolation)
α_Ne ∈ θ, α_Ne ≥ 0
```

The directional principle “isolation tends to reduce migration / Ne” can be part of the constraint grammar, while the magnitude remains latent.

---

## What belongs in y_obs?

`y_obs` should contain **independent empirical observations** only.

For the Campanula worked example, valid `y_obs` candidates include field- or literature-derived response measurements such as:

```text
nectar-guide expression or area
selfing rate or autonomous selfing proxy
herkogamy
flower size
seed set under bagging / natural pollination
visitation response if experimentally measured
Fis / He / neutral diversity if measured genetically
```

Important: pollinator presence/frequency can be empirical, but if it is used as fixed input context, it should be classified as `input_context`, not an ABC target.

Example:

```text
Bombus presence on Oshima vs absence on Hachijo
→ fixed empirical context x_obs / input_context
→ excluded from ABC acceptance
```

---

## What must not be used as y_obs?

Hypothesis-derived expectations must not be used as independent observations.

Examples:

```text
selfing increases along isolation
nectar guide decreases along isolation
neutral diversity decreases along isolation, if not yet measured
```

These are useful, but they are not independent data. They should be classified as:

```text
hypothesis_prediction
posterior_predictive_check
future_observation_target
```

and excluded from default ABC/RACH acceptance.

Otherwise the model risks reproducing predictions generated by its own hypotheses.

---

## Data-role labels

RACH data files should use explicit roles. Recommended roles are:

```text
input_context
observed_target
hypothesis_prediction
diagnostic_only
```

Current backward-compatible labels may include `response_target`; in strict RACH theory, this should be interpreted carefully:

```text
observed_target:
  independent empirical observation used in ABC/RACH acceptance

hypothesis_prediction:
  theoretical expectation or posterior predictive check; excluded from ABC by default

input_context:
  fixed observed predictor/context used by f(x_obs; θ, s); excluded from ABC

diagnostic_only:
  syndrome definition or internal consistency check; excluded from ABC by default
```

The safest default for ABC is:

```text
use only role == observed_target
```

During exploratory model development, `hypothesis_prediction` patterns can be displayed and used for sanity checks, but they should not be treated as independent evidence.

---

## Switch Posterior Inference

RACH does not primarily select among pre-defined models M1–M5. Instead, it samples a binary causal switch vector:

```text
s ∈ {0,1}^K
```

and estimates:

```text
P(s_j = 1 | accepted)
```

For the Campanula worked example, current switches are:

| Switch | Interpretation |
|---|---|
| `guide_attracts_bombus` | nectar guide causally increases Bombus-mediated outcrossing |
| `selfing_syndrome_active` | reproductive assurance activates selfing-syndrome evolution |
| `island_isolation_common_cause` | isolation acts as a common cause affecting multiple traits |
| `small_pollinator_substitution` | smaller pollinators compensate for Bombus absence |

Drift requires special care. Drift itself is not a switch: finite-population drift is part of the generative axiom. A drift-related switch should mean something more specific, for example:

```text
guide_loss_drift_dominant
```

or

```text
guide_selection_near_neutral
```

That is, the hypothesis is not “drift exists”, but whether guide loss is dominated by near-neutral drift rather than selection.

---

## Theory metrics

RACH quantifies not only which mechanisms are supported, but also whether the observation set can identify mechanisms at all.

```text
H(S | A_ε)
```

is the causal degeneracy: the remaining entropy of switch states after ABC/RACH filtering.

```text
K - H(S | A_ε)
```

is degeneracy reduction.

```text
I_j = H(S_j prior) - H(S_j | A_ε)
```

is mechanism identifiability for switch j.

High causal degeneracy means that many different switch combinations remain admissible. This is not a failure; it indicates that the current observation set is insufficient to distinguish mechanisms.

Pattern contribution can be estimated by leave-one-out:

```text
C_k(j) = I_j(all patterns) - I_j(without pattern k)
```

This helps decide which additional empirical observations would most improve causal resolution.

---

## Campanula / Izu Islands worked example

This repository currently uses *Campanula punctata* / シマホタルブクロ as a worked example involving:

```text
pollinator loss
nectar-guide maintenance or loss
selfing syndrome
inbreeding proxy
finite-population drift
small-pollinator substitution
```

However, the worked example should not be confused with the general RACH theory.

For manuscript-level use, empirical targets should be split into at least:

```text
field_derived observed_target:
  guide expression, selfing proxy, herkogamy, flower size, seed set if measured

genetic_derived observed_target:
  Fis, He, neutral diversity, Fst if measured genetically

input_context:
  island distance, island area, Bombus presence/frequency, background pollinator context

hypothesis_prediction:
  isolation-gradient expectations not independently measured

diagnostic_only:
  syndrome-definition correlations such as selfing-herkogamy correlation
```

---

## Current implementation status

The current implementation already includes:

```text
causal switch posterior inference
ecological constraint grammar
proxy and stochastic ABM backends
role-based exclusion of input_context rows
RACH theory metrics: identifiability and causal degeneracy
known-truth validation prototype
```

Important caution:

```text
Some current gradient patterns are conceptual or hypothesis-derived.
They are useful for exploratory model diagnostics, but strict RACH inference should use only independent empirical observed_target rows for ABC acceptance.
```

A future implementation step is to move fixed isolation-gradient coefficients into θ and to create an `independent_observations.csv` table for observed response values and uncertainty.

---

## Relation to existing methodology

RACH connects to POM, ABC, ABM/IBM, simulation-based inference, and causal modelling, but differs in its inferential target.

| Method | Typical target | RACH difference |
|---|---|---|
| Pattern-Oriented Modeling | model outputs that reproduce patterns | RACH estimates admissible causal switch regions |
| ABC | approximate posterior over parameters or models | RACH targets switch posterior under ecological constraints |
| ABM/IBM | emergent dynamics from individual rules | RACH uses ABM as a generator inside admissible-region inference |
| SEM / DAG | coefficients or graph structure | RACH tests latent mechanisms by generative compatibility with observations |
| Model selection | best pre-defined model | RACH estimates which mechanism switches remain admissible |

---

## Suggested manuscript claim

English:

> We introduce RACH, a constraint-first generative framework that defines the admissible causal region: the subset of latent parameter–mechanism space that satisfies biological constraints and reproduces independent empirical observations under fixed ecological context. RACH estimates posterior support for causal mechanism switches and quantifies causal degeneracy, thereby distinguishing supported mechanisms from cases where the available observations lack sufficient causal resolution.

Japanese:

> 本研究では、生物学的制約を満たし、固定された生態学的文脈のもとで独立観測データを再現できる潜在パラメータ・メカニズム空間の部分集合を「許容因果領域」として定義するRACHを提案する。RACHは、この許容領域内で因果メカニズムスイッチの事後支持を推定し、因果縮退性を定量化することで、支持されるメカニズムと、観測データだけでは識別不能なメカニズム群を区別する。
