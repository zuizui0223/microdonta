# RACH — Causal Admissibility and Degeneracy Framework: Formal Theory

> **Version**: 2.0 — complete restatement as independent causal framework
> **Worked example**: *Campanula punctata* along the Izu Islands isolation gradient

---

## Overview

RACH is a **causal admissibility and degeneracy framework** for ecological systems.

It does **not** select the best model from a pre-defined list.  
It does **not** test whether a hypothesis is true.

RACH asks:

> *Under the current biological constraints and independent observations, which latent causal mechanisms remain admissible? How degenerate is the causal explanation? How much does each observation contribute to causal resolution? What would most improve causal resolution?*

Japanese:

> 現在の生物学的制約と独立観測データのもとで、どの潜在因果メカニズムが許容されるか。因果説明はどれだけ縮退しているか。どの観測が因果識別性に寄与しているか。何を観測すれば因果識別性が最も向上するか。

**RACH is not ABC, ABM, or POM.**  
ABC, ABM, and POM are computational components used to approximate the admissible
causal region A_ε. The framework itself is defined by its inferential objects:
causal admissibility, causal degeneracy, causal resolvability, and next-observation value.

---

## 1. The RACH Object

A RACH analysis is formally specified as a tuple:

```
RACH = (X, Y, Θ, S, G, f, P_sim, P_obs, d, ε, A_ε, CA, D, R, OC, NOV)
```

### 1.1 Input spaces

| Symbol | Name | Description | Example (Campanula) |
|--------|------|-------------|---------------------|
| X | Fixed ecological context | x_obs fed into f; not part of ABC target | island distance, island area, observed Bombus presence |
| Y | Independent observation space | y_obs used for ABC acceptance | guide expression, selfing rate, herkogamy, flower size, Fis |
| Θ | Latent parameter space | Unknown ecological quantities inferred via ABC | guide_cost, selfing_benefit, Ne_isolation_slope, ... |
| S | Causal switch space | {0,1}^K — which mechanisms are active | S1: guide attracts Bombus; S2: selfing syndrome; S3: common cause; S5: small pollinator |

### 1.2 Constraint grammar G

G: Θ → {0, 1}

G(θ) = 1 if θ satisfies all biological feasibility constraints.  
G(θ) = 0 otherwise → θ is rejected before simulation.

G encodes **axioms** and **directional principles** (not data-dependent):

```
C1: selfing_benefit - inbreeding_depression ≥ -0.30  (net selfing fitness)
C2: NOT (background_pollinator_efficiency > 0.55 AND selfing_benefit > 0.55)
C3: NOT (guide_cost > 0.20 AND outcrossing_benefit < 0.05 AND guide_benefit > 0.80)
C4: background_pollinator_efficiency < 0.80  (guild functional distinction)
C5: Ne_isolation_slope > 0  (isolation reduces Ne: directional principle)
    migration_decay_rate > 0
    pollinator_loss_slope > 0
```

### 1.3 Generative dynamics f

f: X × Θ × S → Y_sim

f encodes the **ecological axioms** — dynamics that are unconditionally fixed:

```
Wright-Fisher / finite-population sampling
Mendelian / parental trait inheritance
Stochastic reproduction
Fitness-proportional selection
Pollination-to-reproduction rules
```

f uses x_obs as fixed input context and θ, s as latent arguments.

**Biological principles** encode direction into f's structure; magnitudes remain in θ:

```
Ne decreases with isolation     (direction: universal principle)
  Ne = 1 - Ne_isolation_slope × distance   (slope: θ, inferred via ABC)

Migration decays with isolation
  m = m_0 × exp(-migration_decay_rate × distance)   (rate: θ)

Bombus frequency declines with isolation
  Bombus = max(0, 0.80 - pollinator_loss_slope × distance)   (slope: θ)
```

### 1.4 Pattern maps and distance

```
P_sim:  Y_sim → pattern space
P_obs:  y_obs → pattern space

d(P_sim(y_sim), P_obs(y_obs)) = 1 - weighted_match_rate
```

A pattern is matched if the simulated direction (>, <, ~=) equals the observed direction.

### 1.5 The admissible causal region A_ε

```
A_ε(y_obs, x_obs) = { (θ, s) ∈ Θ × S :
                       G(θ) = 1,
                       d(P_sim(f(x_obs; θ, s)), P_obs(y_obs)) ≤ ε }
```

A_ε is the **core inferential object**.

- A_ε is a subset of parameter-mechanism space, not a probability distribution.
- ABC approximates A_ε by sampling (θ, s) from the prior and keeping draws with d ≤ ε.
- The approximation quality depends on sample size and prior coverage.
- y_obs must contain only **independent observations** (role = response_target).
  Hypothesis predictions and syndrome definitions are excluded to prevent circular inference.

---

## 2. The Five Core RACH Quantities

### 2.1 Causal admissibility CA_j

```
CA_j = P(s_j = 1 | (θ, s) ∈ A_ε)
```

CA_j is the **posterior probability that mechanism j is active**, given independent
observations and biological constraints.

| CA_j | Bayes factor | Interpretation |
|------|-------------|----------------|
| >> 0.5 | BF > 3 | Mechanism j is admissible — supported by data |
| ≈ 0.5 | BF ≈ 1 | Data non-informative about mechanism j |
| << 0.5 | BF < 1/3 | Mechanism j is inadmissible — opposed by data |

**Epistemic note**: CA_j is not a proof of causal truth. It is the proportion of
biologically feasible, observation-compatible parameter-mechanism space in which
mechanism j is active.

Code: `causal_model/causal_admissibility.py`, `causal_admissibility()`

### 2.2 Causal degeneracy D

```
D_RACH = H(S | A_ε) = -Σ_{v ∈ {0,1}^K} P(S=v | A_ε) log₂ P(S=v | A_ε)
```

D measures the **remaining uncertainty about mechanism combinations** after
conditioning on observations and constraints.

| D | Interpretation |
|---|----------------|
| D = 0 | Unique mechanism combination — zero causal ambiguity |
| D = K | All 2^K combinations equally present — maximum causal degeneracy |
| 0 < D < K | Partial resolution — some mechanisms identified, others not |

**Causal degeneracy is not a failure.** High D means the available observations
cannot distinguish competing mechanisms. This is an important scientific finding:
it tells the researcher which mechanisms are not yet separable given current data.

Code: `causal_model/causal_admissibility.py`, `causal_degeneracy()`

### 2.3 Causal resolvability R

```
R_RACH = 1 - H(S | A_ε) / H(S) = 1 - D / K
```

R normalizes causal degeneracy reduction to [0, 1]:

| R | Interpretation |
|---|----------------|
| R = 0 | No causal information from observations (D = K) |
| R = 1 | Complete causal resolution (D = 0) |
| R ∈ (0, 1) | Partial resolution |

R is the primary scalar summary of **how much the current observation set resolves competing mechanisms**.

Code: `causal_model/causal_admissibility.py`, `causal_resolvability()`

### 2.4 Observation contribution OC_k

```
OC_k = R_RACH(O) - R_RACH(O \ {k})
```

OC_k measures how much observation pattern k contributes to causal resolvability.
Estimated via leave-one-out (LOO) from the accepted sample.

| OC_k | Interpretation |
|------|----------------|
| OC_k > 0 | Pattern k increases causal resolution |
| OC_k ≈ 0 | Pattern k is redundant with other patterns |
| OC_k < 0 | Removing k would improve resolution (k confounds inference) |

Code: `causal_model/causal_admissibility.py`, `observation_contribution()`

### 2.5 Next-observation value NOV(q)

```
NOV(q) = E[ R_RACH(O ∪ q) - R_RACH(O) ]
```

NOV(q) estimates the expected increase in causal resolvability if candidate
observation q were added to y_obs.

The expectation is over possible outcomes of q (which we do not yet know).
The current implementation uses a heuristic approximation based on:

1. Current causal admissibility CA_j for the target switches of q
2. Remaining ambiguity: how far CA_j is from 0 or 1 (most ambiguous → most gain)
3. Number of target switches per candidate

This approximation gives a **prioritised list of recommended next observations**,
ranked by expected contribution to causal resolution.

Code: `causal_model/causal_admissibility.py`, `next_observation_value()`

---

## 3. Separation of epistemic roles

A central RACH requirement is strict separation between:

| Role | Used as | ABC acceptance | Code label |
|------|---------|---------------|------------|
| Axiom | Dynamics fixed in f | never | hardcoded in `simulation.py`, `inheritance.py` |
| Universal principle | Direction fixed in f / G; coefficient in θ | never | G constraint + θ prior |
| Fixed context | x_obs input to f | never | `input_context` |
| Independent observation | y_obs in d(·,·) | yes | `response_target` |
| Hypothesis prediction | Posterior predictive check only | NO | `hypothesis_prediction` |
| Diagnostic definition | Internal consistency only | NO | `diagnostic_only` |

**Why hypothesis_prediction must not be used as y_obs**:

Using predictions derived from the hypothesis to test the same hypothesis creates
circular inference. P(s | A_ε) would then reflect the researcher's prior assumption,
not independent data.

Example:
> "selfing increases along the isolation gradient"
> This is a **prediction** of S2/S3, not an independent field measurement.
> Including it in y_obs inflates P(S2=1 | A_ε) regardless of true mechanism.

**Current y_obs** (Campanula worked example, Inoue 1986):

```
nectar_guide_pairwise    Oshima > Hachijo   weight=1.0  field_derived
selfing_rate_pairwise    Oshima < Hachijo   weight=1.0  field_derived
herkogamy_pairwise       Oshima > Hachijo   weight=0.8  field_derived
flower_size_pairwise     Oshima > Hachijo   weight=0.8  field_derived
Fis_pairwise             Oshima < Hachijo   weight=1.0  genetic_derived
```

---

## 4. RACH vs existing methods

| Method | Target | RACH difference |
|--------|--------|----------------|
| AIC/BIC model comparison | Rank pre-enumerated models | RACH does not require model enumeration; posterior is over latent mechanisms |
| Standard ABC | Posterior over θ or models | RACH adds causal switch space S; primary output is CA_j, D, R, not θ posterior |
| Pattern-Oriented Modelling | Parameter sets reproducing patterns | RACH additionally quantifies causal degeneracy and observation value |
| SEM / DAG | Fit coefficients of pre-defined graph | RACH uses binary switches; no likelihood needed; mechanisms are latent binary variables |
| Causal discovery (PC, FCI) | Recover DAG from conditional independence | RACH is generative; uses simulation to test compatibility; works with small N |
| Bayesian model comparison | Bayes factors over specified models | RACH BFs are over binary switch states, not pre-specified full models |

**RACH is not a replacement for these methods.** It addresses a specific question:
*which mechanisms remain admissible given constraints and observations, and how degenerate is the causal explanation?*

---

## 5. Implementation correspondence

| RACH object | Python file | Function / class |
|-------------|-------------|-----------------|
| A_ε (admissible region) | `causal_model/switch_inference.py` | `run_switch_posterior_inference()` |
| G(θ) = 1 constraint | `causal_model/parameter_constraints.py` | `check_ecological_parameter_constraints()` |
| f(x_obs; θ, s) proxy | `examples/campanula_izu/campanula_phenomenological.py` | `simulate_campanula_isolation_gradient()` |
| f(x_obs; θ, s) ABM | `attraction_trait_model/simulation.py` | `simulate_population()` |
| P_sim / P_obs / d | `examples/campanula_izu/pattern_evaluator.py` | `evaluate_patterns()` |
| y_obs (response_target) | `examples/campanula_izu/data/observed_patterns.csv` | role=response_target rows |
| x_obs (input_context) | `examples/campanula_izu/data/observed_patterns.csv` | role=input_context rows |
| CA_j causal admissibility | `causal_model/causal_admissibility.py` | `causal_admissibility()` |
| D causal degeneracy | `causal_model/causal_admissibility.py` | `causal_degeneracy()` |
| R causal resolvability | `causal_model/causal_admissibility.py` | `causal_resolvability()` |
| OC_k observation contribution | `causal_model/causal_admissibility.py` | `observation_contribution()` |
| NOV(q) next-observation value | `causal_model/causal_admissibility.py` | `next_observation_value()` |
| θ prior (presets) | `causal_model/parameter_constraints.py` | `predefined_tradeoff_presets()` |
| θ sampling | `causal_model/parameter_sampling.py` | `sample_valid_parameter_sets()` |
| env slope θ extraction | `causal_model/parameter_sampling.py` | `env_slopes_from_param_set()` |
| Streamlit RACH UI | `streamlit_app.py` | "Causal Admissibility" tab |

---

## 6. General RACH vs Campanula worked example

**General RACH theory** (applies to any ecological system):

```
Admissible causal region A_ε(y_obs, x_obs)
Causal admissibility CA_j
Causal degeneracy D
Causal resolvability R
Observation contribution OC_k
Next-observation value NOV(q)
```

**Campanula Izu worked example** (system-specific):

```
Switches: S1 guide→Bombus, S2 selfing syndrome, S3 island common cause, S5 small pollinator
y_obs: Inoue 1986 Oshima/Hachijo pairwise comparisons
x_obs: island distance, Bombus frequency, island area
θ: guide_cost, selfing_benefit, Ne_isolation_slope, migration_decay_rate, ...
f: phenomenological model + stochastic ABM
```

RACH as a general method does not require Campanula-specific choices.
Any ecological system with:
1. A generative simulation model f
2. A biological constraint grammar G
3. Independent field observations y_obs
4. A fixed ecological context x_obs

can be analysed with RACH.

---

## 7. Suggested manuscript claim

English:

> We introduce RACH, a causal admissibility and degeneracy framework for ecological systems. Rather than selecting a single best model, RACH estimates the admissible causal region: the subset of latent parameter–mechanism space that satisfies biological constraints and reproduces independent observations under fixed ecological context. RACH quantifies causal admissibility (CA_j), causal degeneracy (D), causal resolvability (R), observation contribution (OC_k), and the expected value of additional observations (NOV). This framework distinguishes supported mechanisms from cases where the available observations lack sufficient causal resolution.

Japanese:

> 本研究では、生態学的因果メカニズムの許容性と縮退性を定量化するRACHを提案する。RACHは単一の最良モデルを選択するのではなく、生物学的制約を満たし、独立観測データを再現可能な潜在パラメータ・メカニズム空間の部分集合を許容因果領域として推定する。さらに、各因果メカニズムの許容性（CA_j）、因果縮退性（D）、因果識別可能性（R）、観測の寄与（OC_k）、および追加観測の価値（NOV）を定量化する。このフレームワークにより、支持されるメカニズムと、現在の観測集合では識別不能なメカニズム群を区別することができる。

---

## 8. Limitations

1. **ABC approximation**: A_ε is approximated by finite sampling. Posterior estimates stabilise with more draws (≥ 500 recommended for stable CA_j; ≥ 2000 for D).

2. **Switch independence prior**: S_j ~ Bernoulli(0.5) independently. If biological pathways are correlated in the prior, marginalise over the correlated prior instead.

3. **NOV approximation**: `next_observation_value()` uses a heuristic ambiguity-reduction approximation, not the true expectation over q's outcome distribution. Use as a priority guide, not a precise forecast.

4. **Proxy vs ABM**: The deterministic phenomenological model gives reproducible but deterministic A_ε estimates. The stochastic ABM is preferred for publication-quality inference because acceptance probability P(accept | θ, s) is continuous rather than binary.

5. **Causal identification vs admissibility**: High CA_j means mechanism j is present in many observation-compatible parameter regions. It does not guarantee causal identification in the interventionist sense (do-calculus). Confounding pathways can inflate CA_j; experimental manipulations are needed for stronger causal claims.

6. **y_obs completeness**: Causal degeneracy D is always relative to the current y_obs set. Adding more independent observations can only reduce D (or leave it unchanged); it cannot increase D.
