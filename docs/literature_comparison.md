# Literature comparison and novelty of RACH

**RACH = Restricted Admissible Causal Hypotheses**

This document compares RACH with related modelling and inference traditions and
clarifies what is genuinely new, what is inherited from previous methods, and
what claims should be avoided.

RACH should be described as a **causal admissibility and degeneracy framework**:

```text
RACH estimates which latent causal mechanisms remain admissible under
biological constraints and independent observations, and quantifies how much
causal uncertainty remains.
```

It should not be described as simply a combination of ABM, ABC, and POM.
Those methods are computational components. The RACH-specific contribution is
the definition and analysis of the admissible causal region and its information
structure.

---

## 1. Relation to Pattern-Oriented Modeling (POM)

Pattern-Oriented Modeling uses multiple empirical patterns to construct, reject,
and refine ecological or agent-based models. The central insight is that complex
systems cannot be fully matched in every detail, so carefully chosen patterns
provide stronger constraints on model structure than a single endpoint.

RACH inherits this logic but changes the inferential target.

| Aspect | POM | RACH |
|---|---|---|
| Main question | Which model reproduces multiple patterns? | Which causal mechanisms remain admissible in A_ε? |
| Model object | Agent-/individual-based model calibrated to patterns | Constrained parameter–switch region A_ε |
| Output | Pattern match, model plausibility | CA_j, D_RACH, R_RACH, OC_k, NOV(q) |
| Role of patterns | Calibration / validation targets | Independent observations y_obs with strict role labels |
| Treatment of ambiguity | Often model refinement | Quantified as causal degeneracy |

RACH therefore extends the POM idea in two ways:

1. It explicitly separates epistemic roles:

```text
observed_target
input_context
hypothesis_prediction
diagnostic_only
```

2. It treats remaining causal ambiguity as a measurable output, not just a
failure of model selection.

**Recommended wording**:

```text
RACH builds on the pattern-oriented modelling insight that multiple patterns can
constrain complex ecological models, but reframes the target from pattern-matched
model selection to causal mechanism admissibility and degeneracy.
```

---

## 2. Relation to Approximate Bayesian Computation (ABC)

Approximate Bayesian Computation approximates posterior inference for models with
intractable likelihoods by simulating from the prior and accepting draws whose
summary statistics are close to the observed summaries.

RACH uses ABC-style rejection to approximate A_ε, but the inferential target is
different.

| Aspect | ABC | RACH |
|---|---|---|
| Main target | Posterior over parameters or models | Admissible causal region A_ε and switch information |
| Acceptance | distance(summary_sim, summary_obs) ≤ ε | distance(P_sim(f(x_obs;θ,s)), P_obs(y_obs)) ≤ ε, plus G(θ)=1 |
| Output | posterior samples, posterior probabilities | CA_j, D_RACH, R_RACH, OC_k, NOV(q) |
| Interpretation | approximate Bayesian posterior | conditional causal admissibility under specified constraints |

RACH should acknowledge ABC as the computational approximation engine, but should
not reduce itself to ABC. The RACH object is:

```text
A_ε(y_obs, x_obs) = {(θ,s): G(θ)=1 and d(P_sim(f(x_obs;θ,s)), P_obs(y_obs)) ≤ ε}
```

ABC approximates this region by rejection sampling.

**Recommended wording**:

```text
RACH uses likelihood-free rejection as a numerical approximation to the
admissible causal region, but its reported quantities are mechanism-level
admissibility and causal degeneracy rather than ordinary parameter posteriors
alone.
```

---

## 3. Relation to ABC model choice and likelihood-free model selection

ABC model choice usually compares discrete candidate models and estimates model
posterior probabilities or Bayes factors. This can be problematic when summary
statistics are not sufficient for discriminating models.

RACH avoids framing the result as choosing a single true model. Instead, it
samples a vector of causal switches:

```text
s ∈ {0,1}^K
```

This allows mechanisms to be non-exclusive and co-active.

| Aspect | ABC model choice | RACH |
|---|---|---|
| Model space | Discrete alternatives M_1, ..., M_n | Switch space {0,1}^K |
| Main output | P(M_k | data) | P(s_j=1 | A_ε), H(S|A_ε) |
| Mechanisms | Often mutually exclusive | Can overlap / co-occur |
| Ambiguity | Often treated as poor discrimination | Explicitly quantified as D_RACH |

This distinction is central for ecology, where multiple mechanisms can generate
the same observed pattern and can operate simultaneously.

**Recommended wording**:

```text
RACH replaces exclusive model-choice language with mechanism-admissibility
language. It estimates support for each causal switch and the remaining entropy
over switch combinations, rather than forcing a single model label.
```

---

## 4. Relation to individual-based and agent-based models

Agent-based models and individual-based models generate system-level patterns
from rules operating at the level of individuals or agents. In ecology, these
models are often used to simulate trait inheritance, demographic stochasticity,
selection, dispersal, reproduction, and interaction networks.

RACH can use an ABM or IBM as its generative dynamics f:

```text
f(x_obs; θ, s)
```

But RACH is not identical to the ABM.

| Aspect | ABM / IBM | RACH |
|---|---|---|
| Main object | Generative simulator | Inference framework built around A_ε |
| Focus | Emergence from individual rules | Which mechanisms remain admissible under constraints |
| Output | Simulated trajectories / patterns | CA_j, D_RACH, R_RACH, OC_k, NOV(q) |
| Generality | System-specific simulator | General framework; ABM is one possible f |

In the Campanula example, the ABM implements stochastic reproduction,
inheritance, drift, and selection. That ABM is the worked example's f, not the
entire definition of RACH.

**Recommended wording**:

```text
The Campanula ABM is the generative component of the worked example. RACH itself
is the admissibility framework wrapped around any suitable generative ecological
model.
```

---

## 5. Relation to structural causal models, SEM, and potential outcomes

Structural causal models, structural equation models, and potential-outcome
frameworks formalise causal assumptions and causal effects. They are powerful
when interventions, treatment assignments, counterfactuals, or graph structures
are well specified.

RACH is related but does not claim to solve the same problem.

| Aspect | SCM / SEM / potential outcomes | RACH |
|---|---|---|
| Main causal object | Structural equations, DAGs, interventions, counterfactuals | Mechanism-switch admissibility under generative constraints |
| Data requirement | Often observational/experimental variables with effect identification assumptions | Independent ecological patterns plus generative simulator |
| Output | Causal effects / graph implications | Mechanisms compatible with f, G, π, d, ε, x_obs, y_obs |
| Claim strength | Can identify causal effects under assumptions | Identifies admissible mechanisms, not causal truth |

RACH should therefore avoid claiming that it proves true causality. Instead:

```text
RACH constrains the set of mechanisms that remain compatible with explicit
biological assumptions and independent observations.
```

This is most useful in ecological settings where direct intervention is limited,
mechanisms are non-exclusive, and multiple causal pathways can generate similar
macro-patterns.

---

## 6. Relation to Value of Information and Bayesian experimental design

Value of Information analysis and Bayesian experimental design ask how much
additional information is expected to improve a decision or posterior utility.

RACH's NOV(q) is related but narrower:

```text
NOV(q) = expected gain in causal resolvability if observation q is added.
```

| Aspect | VOI / Bayesian experimental design | RACH NOV |
|---|---|---|
| Objective | Expected utility gain | Expected or heuristic causal-resolvability gain |
| Utility | Decision utility, KL gain, information gain, cost-adjusted benefit | Increase in R_RACH |
| Output | Optimal design / value of sample information | Ranked next ecological observations |
| Current implementation | often full preposterior calculation | heuristic proxy unless P(y_q|A_ε) is specified |

The exact RACH NOV is:

```text
NOV(q) = E_{y_q ~ P(y_q | A_ε)}[R_RACH(O ∪ {q=y_q}) - R_RACH(O)]
```

The current implementation is a heuristic proxy because the full predictive
outcome distribution for q is not yet specified.

**Recommended wording**:

```text
RACH's NOV is inspired by value-of-information logic, but in the current
implementation it is a causal-resolution priority score rather than a full
EVSI calculation.
```

---

## 7. What is genuinely new in RACH

The individual components are not new by themselves:

```text
Pattern matching        -> related to POM
Simulation-based filtering -> related to ABC
Generative individuals  -> related to ABM/IBM
Causal assumptions      -> related to SCM/SEM
Future data value       -> related to VOI / Bayesian design
```

The novelty is the integration into a specific inferential object and metric
system:

### 7.1 Admissible causal region as the primary object

RACH centres inference on:

```text
A_ε(y_obs, x_obs)
```

not on a best model label.

### 7.2 Mechanism-level causal admissibility

RACH estimates:

```text
CA_j = P(s_j=1 | A_ε)
```

for each mechanism, allowing mechanisms to be non-exclusive and co-active.

### 7.3 Causal degeneracy and resolvability

RACH reports:

```text
D_RACH = H(S | A_ε)
R_RACH = 1 - H(S | A_ε)/K
```

thereby quantifying how much causal ambiguity remains.

### 7.4 Observation contribution and future-data guidance

RACH defines:

```text
OC_k = R_RACH(O) - R_RACH(O\{O_k})
NOV(q) = E[R_RACH(O∪q) - R_RACH(O)]
```

so that inference can guide future data collection.

### 7.5 Explicit epistemic role separation

RACH separates:

```text
observed_target       independent observations used for acceptance
input_context         fixed ecological context passed to f
hypothesis_prediction posterior prediction, excluded from acceptance
diagnostic_only       internal consistency, excluded from acceptance
```

This role separation directly addresses circular inference risk.

---

## 8. What RACH does not claim

RACH should not claim:

1. That it is unrelated to ABC, POM, or ABM.
2. That it proves true causality in nature.
3. That CA_j is an exact posterior truth probability independent of model assumptions.
4. That NOV(q) is exact EVSI unless a predictive outcome model and utility are defined.
5. That high causal degeneracy means failure.

Instead, RACH should claim:

```text
Given specified f, G, π, d, ε, x_obs, and independent y_obs,
RACH estimates which causal mechanisms remain admissible and how much
mechanism ambiguity remains.
```

---

## 9. Validity and rationality analysis

### 9.1 Internal mathematical rationality

RACH is internally coherent because:

- `A_ε` is a well-defined subset of `Θ × S`.
- `CA_j` is a conditional probability on `A_ε`.
- `D_RACH` is a finite entropy on the finite switch space.
- `R_RACH` is bounded in `[0,1]` when normalised by maximum switch entropy.
- `OC_k` is bounded in `[-1,1]`.
- exact `NOV(q)` is well-defined when candidate outcomes are finite or integrable.
- Monte Carlo estimators are consistent when samples are IID and `π(A_ε)>0`.

These proofs are in `docs/rach_mathematical_foundations.md`.

### 9.2 Biological rationality

RACH is biologically rational when:

- `f` contains defensible ecological dynamics such as inheritance, drift,
  reproduction, selection, and pollination-to-reproduction rules.
- `G(θ)` rejects biologically impossible or incoherent parameter combinations.
- `x_obs` contains fixed ecological context rather than response evidence.
- `y_obs` contains independent observations rather than hypothesis predictions.

### 9.3 Statistical validity concerns

RACH results depend on:

- prior ranges over θ and s
- the biological constraint grammar G
- the simulator f
- the distance function d
- the tolerance ε
- pattern weights
- the quality and independence of y_obs

Therefore, RACH analysis should include:

```text
prior sensitivity
epsilon sensitivity
pattern-weight sensitivity
known-truth recovery
posterior predictive checks
independent validation observations
```

### 9.4 Current limitations in this repository

For the current Campanula worked example:

- y_obs is mostly ordinal pairwise patterns rather than full numeric data with uncertainty.
- NOV is currently heuristic.
- The ABM is a stylised ecological generator, not a complete mechanistic model of all plant-pollinator processes.
- CA_j should be interpreted as admissibility under assumptions, not proof of mechanism truth.

---

## 10. Recommended manuscript wording

### Short version

```text
RACH is related to pattern-oriented modelling and approximate Bayesian
computation, but differs in its inferential target. Instead of selecting a
single best model or estimating only parameter posteriors, RACH defines the
admissible causal region A_ε and quantifies mechanism-level causal
admissibility, causal degeneracy, and causal resolvability. This reframing is
useful in ecological systems where multiple non-exclusive mechanisms can
generate the same observed patterns.
```

### Longer version

```text
We introduce RACH, a causal admissibility and degeneracy framework for ecological
systems. RACH builds on simulation-based inference and pattern-oriented
modelling, but its inferential target is not a single best model. Instead, RACH
constructs the admissible causal region: the subset of latent parameter and
causal-switch space that satisfies biological constraints and reproduces
independent observations. Within this region, RACH estimates causal
admissibility for each mechanism and quantifies remaining causal degeneracy via
switch-state entropy. Observation contribution and next-observation value then
identify which existing and future observations most improve causal
resolvability.
```

### Limitations wording

```text
RACH does not prove causal truth. It identifies mechanisms that remain admissible
under the specified biological constraints, priors, simulator, distance function,
tolerance, context variables, and independent observations. Therefore, RACH
results should be interpreted as constrained causal admissibility and evaluated
through prior sensitivity, epsilon sensitivity, known-truth recovery, and
independent validation data.
```

---

## 11. Reference anchors

The following literature families should be cited in a manuscript using RACH.

### Pattern-Oriented Modeling

- Grimm, V. et al. 2005. Pattern-oriented modeling of agent-based complex systems: lessons from ecology. *Science*.
- Grimm, V. and Railsback, S. F. 2005. *Individual-based Modeling and Ecology*. Princeton University Press.

### Approximate Bayesian Computation

- Beaumont, M. A. et al. 2002. Approximate Bayesian computation in population genetics.
- Sisson, S. A. et al. 2007. Sequential Monte Carlo without likelihoods. *PNAS*.
- Jabot, F. et al. EasyABC / ABC methods in ecology.

### ABC model choice cautions

- Robert, C. P. et al. 2011. Lack of confidence in ABC model choice. *PNAS* / arXiv.

### ABM / IBM

- Grimm, V. and Railsback, S. F. 2005. *Individual-based Modeling and Ecology*.
- Bonabeau, E. 2002. Agent-based modeling: methods and techniques for simulating human systems. *PNAS*.

### Causal inference

- Pearl, J. 2009. *Causality: Models, Reasoning, and Inference*.
- Rubin, D. B. 1974. Estimating causal effects of treatments in randomized and nonrandomized studies.

### Value of Information / Bayesian design

- Howard, R. A. 1966. Information value theory.
- Lindley, D. V. 1956. On a measure of information provided by an experiment.
- Schlaifer, R. and Raiffa, H. 1960s. Applied statistical decision theory.

---

## 12. Bottom line

RACH is not new because it uses simulation, pattern matching, or rejection
sampling. Those are established ideas.

RACH is new as a framework because it makes the following object and quantities
the primary inference target:

```text
A_ε, CA_j, D_RACH, R_RACH, OC_k, NOV(q)
```

This gives ecology a way to state:

```text
These mechanisms remain admissible.
These mechanisms are not resolved.
This is how much causal ambiguity remains.
This observation contributes most.
This next observation would most improve causal resolution.
```

That is the defensible novelty claim.
