# RACH: Causal Admissibility and Degeneracy Framework

**RACH** stands for **Restricted Admissible Causal Hypotheses**.

RACH is a **causal admissibility and degeneracy framework** for ecological systems. It estimates which latent causal mechanisms remain admissible under biological constraints and independent observations, and quantifies whether the available observations are sufficient to resolve competing mechanisms.

English:

> RACH defines the admissible causal region and quantifies causal admissibility, causal degeneracy, and causal resolvability under biological constraints. It does not select the best model. It estimates which mechanisms remain admissible and how degenerate the causal explanation is.

Japanese:

> RACHは、生物学的制約と独立観測データのもとで、どの潜在因果メカニズムが許容されるか、また現在の観測集合がどの程度それらを識別できるかを定量化する、生態学的因果許容性・因果縮退性解析フレームワークである。RACHは単一モデルを選ぶのではなく、許容因果領域を推定し因果縮退性を定量化する。

**RACH is not a combination of ABM, ABC, and POM.** ABM, ABC, and POM are computational components used to approximate the admissible causal region A_ε. The framework is defined by its inferential objects: causal admissibility (CA_j), causal degeneracy (D_RACH), causal resolvability (R_RACH), observation contribution (OC_k), and next-observation value (NOV).

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
θ      = latent ecological parameters to infer or marginalise over
s      = causal switch state, s ∈ {0,1}^K
G(θ)   = ecological constraint grammar
f      = generative ecological dynamics
P_sim  = pattern extractor for simulated output
P_obs  = pattern extractor for empirical observations
y_obs  = independent empirical observations used for ABC/RACH acceptance
d      = distance between simulated and observed pattern spaces
ε      = tolerance threshold
```

The key inference is not a best-model label, but the admissible region and its information structure.

---

## Core workflow

```text
1. Define biological axioms and ecological constraint grammar
2. Define fixed empirical context x_obs
3. Sample latent parameters θ within biologically admissible ranges
4. Sample causal switch states s ∈ {0,1}^K
5. Run generative simulation f(x_obs; θ, s)
6. Extract comparable patterns P_sim and P_obs
7. Accept samples whose distance to independent y_obs is ≤ ε
8. Estimate CA_j, D_RACH, R_RACH, OC_k, and NOV(q)
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
| **Hypothesis prediction** | Model prediction or future test | no | no | no | selfing increases with isolation, guide decreases along isolation if not independently measured |
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

Risky if fixed inside `f`:

```text
effective_population_size = 1.00 - 0.765 × isolation
primary_pollinator_frequency = 0.80 - 0.94 × isolation
community_pollinator_abundance = 0.88 - 0.635 × isolation
```

Those coefficients should be latent parameters unless independently fixed by data and uncertainty is deliberately ignored.

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

Pollinator presence/frequency can be empirical, but if it is used as fixed input context, it should be classified as `input_context`, not an ABC target.

---

## What must not be used as y_obs?

Hypothesis-derived expectations must not be used as independent observations.

Examples:

```text
selfing increases along isolation
nectar guide decreases along isolation
neutral diversity decreases along isolation, if not yet measured
```

These should be classified as:

```text
hypothesis_prediction
posterior_predictive_check
future_observation_target
```

and excluded from default ABC/RACH acceptance.

---

## Data-role labels

RACH data files should use explicit roles:

```text
input_context
observed_target
hypothesis_prediction
diagnostic_only
```

The safest default for ABC is:

```text
use only role == observed_target
```

Current backward-compatible labels may include `response_target`, but strict RACH inference should use `observed_target` for independent empirical y_obs.

---

## Causal admissibility and switch support

RACH samples a binary causal switch vector:

```text
s ∈ {0,1}^K
```

and estimates support within the admissible region:

```text
CA_j = P(s_j = 1 | (θ, s) ∈ A_ε)
```

`CA_j` is **causal admissibility**: the probability that mechanism j remains admissible under the current biological constraints and independent observations.

For the Campanula worked example, current switches are:

| Switch | Interpretation |
|---|---|
| `guide_attracts_bombus` | nectar guide causally increases Bombus-mediated outcrossing |
| `selfing_syndrome_active` | reproductive assurance activates selfing-syndrome evolution |
| `island_isolation_common_cause` | isolation acts as a common cause affecting multiple traits |
| `small_pollinator_substitution` | smaller pollinators compensate for Bombus absence |

Drift itself is not a switch: finite-population drift is part of the generative axiom. A drift-related switch should mean something more specific, such as `guide_loss_drift_dominant` or `guide_selection_near_neutral`.

---

## RACH-specific computation algorithm

The RACH-specific calculations use sampled prior rows, evaluated rows, and the accepted subset A_ε.

```text
prior rows:      all sampled (θ_i, s_i), before ABC acceptance
evaluated rows:  all rows for which f(x_obs; θ_i, s_i) was evaluated and pattern matches were recorded
accepted rows:   A_ε = rows passing d(P_sim(f(x_obs;θ,s)), P_obs(y_obs)) ≤ ε
```

The key implementation rule is:

```text
Observation contribution and leave-one-out metrics require all_evaluated_rows,
not accepted_rows alone.
```

Reason: when one pattern is removed, some samples that were previously rejected may become accepted. Using only `accepted_rows` would underestimate the contribution of patterns and distort causal resolvability.

### 1. Causal admissibility

```text
CA_j = P(s_j = 1 | A_ε)
```

Algorithm:

```python
CA_j = mean(row[switch_j] for row in accepted_rows)
```

### 2. Causal degeneracy

```text
D_RACH = H(S | A_ε)
```

Algorithm:

```python
state_counts = count tuples (s1, s2, ..., sK) in accepted_rows
p_state = state_counts / n_accepted
D_RACH = -sum(p_state * log2(p_state))
```

### 3. Causal resolvability

```text
R_RACH = 1 - H(S | A_ε) / H(S)
```

If the switch prior is independent Bernoulli(0.5), then:

```text
H(S) = K bits
R_RACH = 1 - D_RACH / K
```

### 4. Mechanism identifiability

```text
I_j = H(S_j prior) - H(S_j | A_ε)
```

For Bernoulli(0.5) prior:

```text
H(S_j prior) = 1 bit
H(S_j | A_ε) = -p_j log2(p_j) - (1-p_j)log2(1-p_j)
I_j = 1 - H(S_j | A_ε)
```

### 5. Observation contribution

```text
OC_k = R_RACH(O) - R_RACH(O \ {O_k})
```

Algorithm:

```python
R_all = causal_resolvability(accepted_all)

for each pattern k:
    accepted_without_k = recompute_acceptance(
        all_evaluated_rows,
        drop_pattern=k,
        threshold=ε
    )
    R_without_k = causal_resolvability(accepted_without_k)
    OC_k = R_all - R_without_k
```

Implementation requirement:

```text
Each evaluated row must store per_pattern_matched:
  {pattern_id: (matched: bool, weight: float)}
```

Acceptance without pattern k is recomputed from the remaining pattern weights:

```python
weighted_match_rate_without_k = matched_weight_without_k / total_weight_without_k
accepted_without_k = weighted_match_rate_without_k >= threshold
```

### 6. Next-observation value

The strict theoretical definition is:

```text
NOV(q) = E[ R_RACH(O ∪ q) - R_RACH(O) ]
```

where q is a candidate future observation.

A practical first implementation can use a heuristic approximation:

```python
uncertainty_j = H(S_j | A_ε)
NOV(q) = feasibility(q) * sum(uncertainty_j for j in target_switches(q))
```

Candidate observation table:

```text
candidate_observation,target_switches,feasibility,rationale
guide_outcrossing_response,guide_attracts_bombus,0.7,Tests whether guide expression increases outcrossing
bagging_seed_set,selfing_syndrome_active,0.9,Tests autonomous selfing and reproductive assurance
neutral_diversity,island_isolation_common_cause,0.6,Separates demographic drift from adaptive floral change
background_pollinator_visitation,small_pollinator_substitution,0.8,Tests whether small pollinators compensate for Bombus absence
```

---

## Theory metrics

RACH quantifies not only which mechanisms are supported, but also whether the observation set can identify mechanisms at all.

```text
CA_j = P(s_j = 1 | A_ε)
D_RACH = H(S | A_ε)
R_RACH = 1 - H(S | A_ε) / H(S)
I_j = H(S_j prior) - H(S_j | A_ε)
OC_k = R_RACH(O) - R_RACH(O \ {O_k})
NOV(q) = E[ R_RACH(O ∪ q) - R_RACH(O) ]
```

High causal degeneracy means that many different switch combinations remain admissible. This is not a failure; it indicates that the current observation set is insufficient to distinguish mechanisms.

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

Implementation status:

```text
✓ observed_target / hypothesis_prediction / diagnostic_only / input_context role taxonomy
✓ hypothesis_prediction gradient patterns excluded from ABC (circular inference prevented)
✓ independent_observations.csv created as future numeric y_obs table
✓ Ne_isolation_slope / migration_decay_rate / pollinator_loss_slope promoted to θ
✓ env_slopes_from_param_set() extracts slope θ from each sampled parameter set
✓ C5 constraint enforces direction principle: all slopes must be > 0
```

Remaining implementation steps:

```text
1. Store all_evaluated_rows in SwitchPosteriorResult, not only accepted_rows.
2. Recompute leave-one-out acceptance from all_evaluated_rows for OC_k.
3. Implement causal_admissibility.py with CA, D_RACH, R_RACH, OC, and NOV.
4. Add numeric ABC distance using independent_observations.csv once values and uncertainty are filled.
```

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

> We introduce RACH, a causal admissibility and degeneracy framework for ecological systems. Rather than selecting a single best model, RACH estimates the admissible causal region: the subset of latent parameter–mechanism space that satisfies biological constraints and reproduces independent observations. It then quantifies causal admissibility, causal degeneracy, causal resolvability, and the expected value of additional observations.

Japanese:

> 本研究では、生態学的因果メカニズムの許容性と縮退性を定量化するRACHを提案する。RACHは単一の最良モデルを選択するのではなく、生物学的制約を満たし、独立観測データを再現可能な潜在パラメータ・メカニズム空間の部分集合を許容因果領域として推定する。さらに、各因果メカニズムの許容性、因果縮退性、因果識別可能性、および追加観測の価値を定量化する。
