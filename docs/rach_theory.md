# RACH — Restricted Admissible Causal Hypotheses: Formal Theory

> **Version**: Issue #8 initial formalisation  
> **Status**: working document — mathematical definitions subject to revision  
> **Worked example**: *Campanula punctata* along the Izu Islands isolation gradient

---

## 1. Motivation

Classical model-comparison methods (AIC, Bayes factor over pre-defined structures,
structural equation modelling) require the analyst to enumerate candidate models
before seeing data.  In ecology, the true causal mechanism is rarely known in advance,
and the space of plausible mechanisms is too large to enumerate exhaustively.

RACH takes a different route: instead of defining models, it defines **biological
constraints** and **observable gradient pattern targets**, then asks which
mechanism combinations produce parameter-space regions compatible with those targets.
The result is a *posterior over latent mechanisms*, not a ranked list of pre-specified models.

---

## 2. Formal definitions

### 2.1  Latent parameter space Θ

Let **θ ∈ Θ ⊂ ℝ^d** denote a vector of latent ecological trade-off parameters.
In the Campanula example, Θ is the 8-dimensional space of benefit/cost parameters:

```
θ = (guide_cost, outcrossing_benefit, selfing_benefit,
     inbreeding_depression, background_pollinator_efficiency,
     drift_strength, direct_pollinator_guide_benefit,
     cost_of_waiting_for_pollinators)
```

The prior distribution π(θ) is specified by ecology-principled trade-off presets
(see `causal_model/parameter_sampling.py`, `predefined_tradeoff_presets()`).

---

### 2.2  Mechanism (switch) space {0,1}^K

Let **s ∈ {0,1}^K** be a binary vector of *biological switch states*, where K is
the number of mechanistic pathways under consideration.

**Definition 1 (Biological switch).** A biological switch S_j is a binary variable
representing whether pathway j is active in the data-generating process:

```
S_j = 1  ⟺  pathway j is causally active
S_j = 0  ⟺  pathway j is causally inactive
```

The Campanula example has K = 5 switches:

| Symbol | Name                        | Pathway question                                              |
|--------|-----------------------------|---------------------------------------------------------------|
| S1     | guide_attracts_bombus       | Does guide phenotype directly attract Bombus (primary poll.)? |
| S2     | selfing_syndrome_active     | Is selfing syndrome expressed as a breeding system response?  |
| S3     | island_isolation_common_cause | Does island isolation drive both guide loss and poll. loss?  |
| S4     | drift_drives_guide_loss     | Does genetic drift drive guide loss independently?           |
| S5     | small_pollinator_substitution | Are small pollinators substituting for absent Bombus?       |

Prior: S_j ~ Bernoulli(0.5) independently (uninformative over mechanism combinations).

---

### 2.3  Simulation model

**Definition 2 (Simulation model).** A function

```
simulate : Θ × {0,1}^K → Y
```

mapping a parameter vector θ and switch state s to a simulated output y = simulate(θ, s).

In the Campanula example, Y is the space of ecological gradient outputs (per-population
trait values along the isolation axis):

```
y = { (pop_i, nectar_guide_i, selfing_rate_i, herkogamy_i, ...) : i = 1..n_points }
```

Two backends are available:

- **Proxy simulation** (`proxy_simulation.simulate_campanula_isolation_gradient`):
  deterministic, fast (< 1 ms per draw)
- **Stochastic ABM** (`attraction_trait_model.simulation.simulate_population`):
  individual-based, stochastic (~ 300 ms per draw per population)

---

### 2.4  Gradient pattern targets Y_obs

**Definition 3 (Gradient pattern target).** A pattern target is a qualitative or
semi-quantitative assertion about the simulated output that can be evaluated as
*matched* or *unmatched*:

```
pattern k : Y → {0,1}    (or a soft weight ∈ [0,1])
```

Pattern targets have a *role* attribute:

- `response_target`: used as ABC acceptance criterion
- `input_context`: environmental predictor variable — **excluded** from ABC

The Campanula observed pattern targets are in:
`examples/campanula_izu/data/observed_patterns.csv`

The set of response_target patterns is accessed via:
```python
from examples.campanula_izu.observed_data import response_target_patterns
```

Evaluation is performed by `examples/campanula_izu/pattern_evaluator.py`:
```python
evaluate_patterns(outputs_list, pattern_targets, synth_env) → EvaluationResult
```

---

### 2.5  Ecological constraint grammar C

**Definition 4 (Constraint grammar).** A set of hard constraints C over Θ:

```
C = { C1, C2, C3, C4 }
```

| Constraint | Description                                      | Code                          |
|------------|--------------------------------------------------|-------------------------------|
| C1         | Outcrossing benefit ≥ guide cost (guide utility) | `parameter_constraints.py`    |
| C2         | Selfing benefit ≤ 1 − inbreeding depression      | `parameter_constraints.py`    |
| C3         | Background pollinator efficiency < primary       | `parameter_constraints.py`    |
| C4         | Trade-off class consistency                      | `parameter_constraints.py`    |

Parameters violating C are rejected at the sampling stage (before simulation).
This implements prior knowledge about biological feasibility.

---

### 2.6  Admissible causal region A_ε

**Definition 5 (Admissible causal region).** The admissible causal region is:

```
A_ε = { (θ, s) ∈ Θ × {0,1}^K :
          θ satisfies C,
          d(simulate(θ, s), y_obs) ≤ ε }
```

where d(·, ·) is the pattern-distance metric:

```
d(y, y_obs) = 1 − weighted_match_rate(y, y_obs)
            = 1 − (Σ_k w_k · 1[pattern k matched]) / (Σ_k w_k)
```

and ε = 1 − threshold (e.g., ε = 0 for strict_all_match, ε = 0.2 for relaxed_0.83).

The ABC sample {(θ_i, s_i)}_i is an empirical approximation of the uniform
distribution over A_ε.

---

### 2.7  Posterior over switches

**Definition 6 (Switch posterior).** Given the ABC sample from A_ε:

```
P(S_j = 1 | A_ε) ≈ (1/|A_ε|) Σ_i  1[s_i(j) = 1]
```

This is the fraction of accepted samples with switch j ON.

The **Bayes factor** for switch j is:

```
BF_j = P(S_j=1 | A_ε) / P(S_j=0 | A_ε)
     = p̂_j / (1 − p̂_j)
```

Interpretation: BF > 3 → supported; BF > 10 → strongly supported; BF < 1/3 → opposed.

Code: `causal_model/switch_inference.py`, `run_switch_posterior_inference()`

---

## 3. Information-theoretic metrics (Phase 2)

### 3.1  Mechanism identifiability I_j

**Definition 7 (Mechanism identifiability).** The identifiability of switch j is
the reduction in Shannon entropy achieved by conditioning on A_ε:

```
I_j = H(S_j | prior) − H(S_j | A_ε)
    = H(0.5) − H(p̂_j)
    = 1 − (−p̂_j log₂ p̂_j − (1−p̂_j) log₂(1−p̂_j))
```

where H(·) is binary entropy in bits.

Properties:
- `I_j = 0`: prior and posterior coincide — A_ε provides no information about S_j
- `I_j = 1`: posterior is 0 or 1 — S_j is fully determined by A_ε
- `I_j ∈ (0, 1)`: partial identifiability

| I_j range | Interpretation         |
|-----------|------------------------|
| ≥ 0.75    | highly identifiable    |
| ≥ 0.40    | moderately identifiable|
| ≥ 0.10    | weakly identifiable    |
| < 0.10    | not identifiable       |

Code: `causal_model/identifiability.py`, `SwitchIdentifiability.I_j`

---

### 3.2  Causal degeneracy D

**Definition 8 (Causal degeneracy).** The causal degeneracy is the joint entropy
of the switch vector over the accepted sample:

```
D = H(S | A_ε) = −Σ_{v ∈ {0,1}^K} P(S=v | A_ε) log₂ P(S=v | A_ε)
```

Properties:
- `D = 0`: every accepted sample has the same switch vector — A_ε identifies a unique mechanism combination
- `D = K`: all 2^K switch vectors are equally represented — A_ε provides no information about mechanism combinations
- In general `D ≤ K` (by the data-processing inequality)

The **degeneracy reduction** R = K − D measures how much A_ε constrains the mechanism space.

Note that `Σ_j I_j ≥ D` (sum of marginal identifiabilities upper-bounds degeneracy
reduction) only when switches are independent in A_ε; in general the two measures
are not directly comparable.

Code: `causal_model/identifiability.py`, `RACHTheoryMetrics.causal_degeneracy`

---

### 3.3  Pattern contribution C_k(j)

**Definition 9 (Pattern contribution).** The contribution of pattern target k to
the identifiability of switch j is estimated via leave-one-out (LOO):

```
C_k(j) = I_j(all patterns) − I_j(A_ε \ {k})
```

where `A_ε \ {k}` is the hypothetical admissible region obtained by removing
pattern k from the acceptance criterion.

In practice, `A_ε \ {k}` is approximated from the stored per-pattern match data:
for each accepted row, the weighted_match_rate is recomputed without pattern k's
contribution, and the row is retained in the LOO subset if this recomputed rate
still meets the threshold.

Interpretation:
- `C_k(j) > 0`: pattern k increases identifiability of switch j (informative about j)
- `C_k(j) < 0`: removing k would *increase* identifiability (k confounds inference about j)
- `C_k(j) ≈ 0`: pattern k is irrelevant to switch j's identifiability

Code: `causal_model/identifiability.py`, `pattern_contribution_table()`

---

## 4. Known-truth validation

The `test_known_truth.py` file implements known-truth validation:

1. Set the true switch state `s* = {S1=ON, S2=ON}` (guide_attracts_bombus + selfing_syndrome)
2. Simulate gradient outputs from `s*`
3. Derive synthetic pattern targets from those outputs
4. Run RACH inference against those targets
5. Verify that:
   - P(S1=ON | A_ε) > 0.5
   - P(S2=ON | A_ε) > 0.5
   - P(S4=ON | A_ε) < P(S1) and P(S2)  (drift null is not supported)
   - I_j(S1) > I_j(S4) and I_j(S2) > I_j(S4)
   - H(S|A_ε) < K (acceptance criterion provides information)

This provides a mathematical guarantee that RACH correctly recovers the true
mechanisms when the data are generated by a known process.

Run:
```
python examples/campanula_izu/test_known_truth.py
```

---

## 5. Code correspondence table

| Mathematical object        | Python location                                    | Function / class                         |
|----------------------------|----------------------------------------------------|------------------------------------------|
| Θ (parameter space)        | `causal_model/parameter_sampling.py`               | `predefined_tradeoff_presets()`          |
| π(θ) (prior)               | `causal_model/parameter_sampling.py`               | `sample_valid_parameter_sets()`          |
| {0,1}^K (switch space)     | `causal_model/switches.py`                         | `PathwaySwitches`                        |
| S_j prior                  | `causal_model/switch_inference.py`                 | `BiologicalSwitch.prior_on_prob`         |
| simulate(θ, s)             | `examples/campanula_izu/proxy_simulation.py`       | `simulate_campanula_isolation_gradient()`|
| simulate(θ, s) ABM         | `attraction_trait_model/simulation.py`             | `simulate_population()`                  |
| y_obs pattern targets      | `examples/campanula_izu/data/observed_patterns.csv`| role=response_target rows               |
| input_context predictors   | `examples/campanula_izu/data/ecological_context.csv`| role=input_context rows                |
| d(y, y_obs)                | `examples/campanula_izu/pattern_evaluator.py`      | `weighted_pattern_distance()`            |
| evaluate patterns          | `examples/campanula_izu/pattern_evaluator.py`      | `evaluate_patterns()`                    |
| Constraint grammar C       | `causal_model/parameter_constraints.py`            | `sample_all_sets_with_rejection_log()`   |
| Admissible region A_ε      | `causal_model/switch_inference.py`                 | `run_switch_posterior_inference()`       |
| P(S_j=1 \| A_ε)            | `causal_model/switch_inference.py`                 | `SwitchPosteriorResult.posterior_table`  |
| Bayes factor BF_j          | `causal_model/switch_inference.py`                 | `posterior_table[*]["Bayes_factor"]`     |
| Identifiability I_j        | `causal_model/identifiability.py`                  | `SwitchIdentifiability.I_j`              |
| Causal degeneracy D        | `causal_model/identifiability.py`                  | `RACHTheoryMetrics.causal_degeneracy`    |
| Degeneracy reduction R     | `causal_model/identifiability.py`                  | `RACHTheoryMetrics.degeneracy_reduction` |
| Pattern contribution C_k(j)| `causal_model/identifiability.py`                  | `pattern_contribution_table()`           |
| Constraint posterior shift | `causal_model/identifiability.py`                  | `constraint_posterior_shift()`           |
| Theory UI                  | `streamlit_app.py`                                 | sp_tab3 "RACH Theory Metrics"            |
| Known-truth validation     | `examples/campanula_izu/test_known_truth.py`       | `test_posterior_favours_true_switches_s1_s2()` etc. |

---

## 6. Relationship to existing causal inference methods

| Method | Mechanism | RACH difference |
|---|---|---|
| AIC/BIC model comparison | Ranks pre-enumerated models by fit + complexity | RACH does not require pre-enumeration; posterior is over latent mechanisms, not structures |
| Structural equation modelling (SEM) | Fits coefficients of pre-defined DAG | RACH uses binary switches and ABC; no likelihood function needed |
| Approximate Bayesian Computation (ABC) | Matches summary statistics | RACH uses ecological constraint grammar C to pre-filter parameter space; pattern targets are qualitative (direction/rank), not numeric summaries |
| Causal discovery (PC, FCI) | Recovers DAG skeleton from conditional independence tests | RACH is generative; mechanism states are latent variables inferred from simulation-compatible parameter regions |
| Random forest / regression | Predicts outcome from features | RACH infers latent causal states, not predictive relationships |

---

## 7. Limitations and future work

1. **ABC approximation**: A_ε is an empirical approximation; posterior estimates improve with more draws.
2. **Switch independence prior**: S_j ~ Bernoulli(0.5) independently may not hold if pathways are biologically correlated.
3. **Proxy vs ABM**: Proxy simulation is deterministic; stochastic ABM is preferred for Bayes factor computation.
4. **Pattern completeness**: Gradient pattern targets must be chosen carefully to avoid confounding C_k(j) estimates.
5. **Identifiability guarantee**: I_j > 0 is a necessary but not sufficient condition for causal identification; confounding pathways may inflate I_j.
