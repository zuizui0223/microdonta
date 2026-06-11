# RACH — Causal Admissibility and Degeneracy Framework: Formal Theory

> **Version**: 2.0 — complete restatement as independent causal framework
> **Worked example**: Izu Islands *Campanula microdonta* system. Older literature may refer to the broader *C. punctata* complex.

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
| Y | Independent observation space | y_obs used for ABC acceptance | flower size, selfing/outcrossing rate, genetic endpoints when independently measured |
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
- y_obs must contain only **independent observations** (`role = observed_target`; legacy `response_target` is accepted for backward compatibility).
- Hypothesis predictions and syndrome definitions are excluded to prevent circular inference.

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
It is estimated by leave-one-out **re-acceptance over all evaluated rows**, not from
accepted rows alone. This distinction matters because removing pattern k can allow
previously rejected simulations to enter A_ε.

**OC_k is pattern-level, not switch-specific.** R_RACH is the *joint* resolvability
of the whole switch vector s ∈ {0,1}^K (derived from the joint entropy H(S | A_ε), a
single scalar over all K switches). OC_k therefore quantifies how pattern k changes
the resolvability of the *entire* mechanism combination; there is exactly one OC_k per
pattern and it does not decompose into a per-switch quantity. `observation_contribution()`
returns one `ObservationContribution` per pattern, with `level="pattern"` and `n_switches=K`
recorded for provenance.

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
| Independent observation | y_obs in d(·,·) | yes | `observed_target` |
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

**Current y_obs** (Campanula microdonta worked example; Inoue-series endpoint patterns):

```
selfing_rate_pairwise    Oshima < Hachijo   weight=1.0  field_derived / Inoue1990
flower_size_pairwise     Oshima > Hachijo   weight=0.8  field_derived / Inoue1986
```

Nectar-guide intensity is planned own-field data, not an Inoue-series per-population
measurement. Herkogamy is treated as a theoretical/diagnostic selfing-syndrome trait
or pending field-validation target, not as an Inoue1986 observed_target. Fis remains
excluded until an independent genetic estimate is source-confirmed; the current
simulator's Fis proxy is partly generated from selfing rate, so using it as y_obs
would double-count selfing evidence.

---

## 4. Validation strategy

RACH requires at least three validation layers:

1. **Known-truth recovery**: generate synthetic y_obs from a known switch state, then test whether CA_j is high for the true ON switches.
2. **Sensitivity analysis**: vary priors, ε, and pattern weights; robust conclusions should not flip under small perturbations.
3. **Observation contribution and NOV**: if D_RACH remains high, identify which new observations would most improve R_RACH.

---

## 5. Manuscript framing

English:

> We introduce RACH, a causal admissibility and degeneracy framework for ecological systems. Rather than selecting a single best model, RACH estimates the admissible causal region: the subset of latent parameter–mechanism space that satisfies biological constraints and reproduces independent observations. It then quantifies causal admissibility, causal degeneracy, causal resolvability, and the expected value of additional observations.

Japanese:

> 本研究では、生態学的因果メカニズムの許容性と縮退性を定量化するRACHを提案する。RACHは単一の最良モデルを選択するのではなく、生物学的制約を満たし、独立観測データを再現可能な潜在パラメータ・メカニズム空間の部分集合を許容因果領域として推定する。さらに、各因果メカニズムの許容性、因果縮退性、因果識別可能性、および追加観測の価値を定量化する。
