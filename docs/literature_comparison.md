# Literature comparison and novelty of RACH

This document compares RACH to related frameworks, states defensible novelty claims, and lists known validity limitations.

---

## 1. Relation to Pattern-Oriented Modeling (POM)

**Key POM references:** Grimm et al. (2005) *Science*; Grimm & Railsback (2012) *Agent-Based and Individual-Based Modeling*.

POM uses multiple qualitative and quantitative patterns observed in ecological systems to constrain, calibrate, and reject agent-based models. A model that reproduces a wide set of patterns is considered better calibrated than one that reproduces only a few.

| | POM | RACH |
|---|---|---|
| **Inferential target** | Which model structure reproduces the patterns? | Which latent causal mechanisms remain admissible in A_ε, and how degenerate is the causal explanation? |
| **Primary output** | Pattern match scores; model ranking | CA_j, D_RACH, R_RACH, OC_k, NOV(q) |
| **Pattern roles** | Patterns used uniformly for calibration | Separated into `observed_target`, `input_context`, `hypothesis_prediction`, `diagnostic_only` to prevent circular inference |
| **Degeneracy** | Not quantified; multiple good models treated as a problem | Explicitly quantified as D_RACH = H(S\|A_ε); high degeneracy is scientific information |
| **Observational guidance** | No formal metric for which new data to collect | OC_k and NOV(q) guide future data collection |

**What RACH borrows from POM:** the idea that multiple independent patterns jointly constrain the model space.

**What RACH adds:** the admissible causal region A_ε as a formal inferential object; causal-switch inference over s ∈ {0,1}^K; mechanism-level admissibility CA_j; and the information-theoretic quantities D_RACH, R_RACH, OC_k, NOV(q).

---

## 2. Relation to Approximate Bayesian Computation (ABC)

**Key ABC references:** Beaumont et al. (2002) *Genetics*; Tavaré et al. (1997) *Genetics*; Sisson, Fan & Beaumont (2018) *Handbook of ABC*.

ABC approximates posterior distributions over parameters when likelihoods are intractable, by simulating data and accepting parameter draws whose summary statistics are within tolerance ε of observed summaries.

| | ABC | RACH |
|---|---|---|
| **Inferential target** | Posterior p(θ\|y_obs) | Admissible causal region A_ε; CA_j = P(s_j = 1 \| A_ε) |
| **Primary output** | Parameter posterior samples | Mechanism admissibility, degeneracy, resolvability |
| **Switch states** | Not part of the model | s ∈ {0,1}^K sampled jointly with θ |
| **Degeneracy** | Diffuse posterior not separately diagnosed | D_RACH explicitly quantifies causal ambiguity |
| **Model comparison** | Bayes factor / marginal likelihood approximation | Not model comparison; all admissible (θ, s) pairs are retained |

**What RACH borrows from ABC:** rejection sampling from a prior using a distance-based acceptance criterion; the use of simulation when likelihoods are intractable.

**What RACH adds:** a causal switch layer s on top of θ; the distinction between parameter uncertainty and mechanism uncertainty; explicit treatment of high degeneracy as a result rather than a problem.

**Pitfall RACH avoids:** ABC-based Bayes factors and model probabilities can be unstable and sensitive to summary statistics and ε (Robert et al. 2011 *PNAS*). RACH does not compute Bayes factors across models. It estimates CA_j as an empirical frequency inside A_ε and reports degeneracy directly.

---

## 3. Relation to ABC model choice / likelihood-free model choice

**Key references:** Pudlo et al. (2016) *Bioinformatics* (ABC-RF); Marin et al. (2012) *Statistics and Computing*.

ABC model choice samples a set of discrete candidate models M_1, ..., M_K and estimates posterior model probabilities P(M_k \| y_obs) using ABC rejection or random forest classifiers.

| | ABC model choice | RACH |
|---|---|---|
| **Model space** | Discrete mutually exclusive models | Non-exclusive binary switches; 2^K switch combinations |
| **Output** | P(M_k \| y_obs) | CA_j = P(s_j = 1 \| A_ε) per mechanism independently |
| **Mechanism overlap** | Not supported; each model is exclusive | Multiple mechanisms can be simultaneously ON |
| **Degeneracy** | Not computed | D_RACH and R_RACH quantify unresolved degeneracy |

RACH should be positioned as **mechanism-admissibility analysis**, not classifier-style model selection. It is especially appropriate when competing mechanisms are not mutually exclusive — a common situation in ecology.

---

## 4. Relation to individual-based / agent-based models (ABM/IBM)

**Key references:** Grimm et al. (2005, 2012); Railsback & Grimm (2019) *Agent-Based and Individual-Based Modeling* (2nd ed.); ODD protocol (Grimm et al. 2010 *Ecological Modelling*).

ABMs generate emergent ecological dynamics from individual-level rules. They serve both as explanatory tools and as forward simulators for ABC or POM.

| | ABM | RACH |
|---|---|---|
| **Role** | Generative simulator of ecological dynamics | Not an ABM; uses an ABM as f(x_obs; θ, s) |
| **Output** | Population-level emergent patterns | Pattern-space match under specified (θ, s) |
| **Causal inference** | Emergent behavior explained verbally | Formal CA_j, D_RACH, R_RACH, OC_k |

**Important:** The Campanula ABM in this repository is the worked example used to implement f. It is not the definition of RACH. RACH can be applied with any generative simulator — phenomenological, stochastic, ABM, ODE, or other — as long as f maps (x_obs, θ, s) to a comparable pattern space.

---

## 5. Relation to structural causal models / causal graphs / SEM

**Key references:** Pearl (2009) *Causality*; Spirtes, Glymour & Scheines (2001) *Causation, Prediction, and Search*; Peters et al. (2014) *JMLR*.

Structural causal models (SCMs) and structural equation models (SEMs) encode causal assumptions as directed graphs and estimate causal effects or test causal graph structure.

| | SCM / SEM | RACH |
|---|---|---|
| **Causal assumptions** | Encoded as DAG edges and structural equations | Encoded as biological axioms in f and constraint grammar G(θ) |
| **Inference** | Estimate causal effects or test interventional distributions | Estimate which causal switch combinations remain admissible |
| **Data requirement** | Often requires interventional or longitudinal data | Accepts observational patterns under biological constraints |
| **Output** | Causal effect estimates or graph skeleton | A_ε; CA_j; D_RACH; R_RACH |

**Clarification:** RACH does not prove causal truth. It identifies mechanisms that remain admissible under specified biological constraints, priors, simulator, distance function, and observations. This is constraint-based causal admissibility, not effect estimation. RACH results are strengthened by manipulative experiments or independent longitudinal observations.

---

## 6. Relation to Value of Information / optimal experimental design

**Key references:** Raiffa & Schlaifer (1961) *Applied Statistical Decision Theory*; Chaloner & Verdinelli (1995) *Statistical Science*; Myung & Pitt (2009) *Psychological Review*.

Value of Information (VOI) and Expected Value of Sample Information (EVSI) quantify how much a future observation is expected to improve a decision or reduce posterior uncertainty.

| | VOI / EVSI | RACH NOV(q) |
|---|---|---|
| **What is valued** | Expected utility gain from information | Expected causal-resolvability gain E[ΔR_RACH] |
| **Requires** | Utility function and decision model | Only R_RACH and the candidate observation's prior outcome distribution |
| **Exactness** | Full EVSI is exact if prior and likelihood are specified | Constructive resolvability-EVSI for quantitative observations (Prop 6′), exact from the admissible region under a deterministic simulator; heuristic for ordinal candidates |

**Status:** For **quantitative** observations RACH now computes a *constructive preposterior EVSI on causal resolvability* (Proposition 6′ in `rach_mathematical_foundations.md`): the outcome distribution is the admissible-region pushforward of the measured value, the utility is internal (resolvability, so no external decision model is needed), and the computation is exact from the stored admissible region under a deterministic simulator — validated 1:1 against fresh re-inference and positively calibrated against realised gains in `nov_calibration.py`. The remaining heuristic case is ordinal/qualitative candidates that lack an outcome model; these are reported as priority scores, not EVSI.

---

## 7. What is genuinely new in RACH

The following claims are defensible:

1. **A_ε as primary inferential object.** RACH defines the admissible causal region A_ε explicitly and treats it as the target of inference, not merely as a by-product of ABC calibration.

2. **Mechanism-level causal admissibility CA_j.** RACH estimates the conditional probability that each individual causal mechanism is active within A_ε, supporting non-exclusive mechanisms and partial support.

3. **Causal degeneracy D_RACH and resolvability R_RACH.** These information-theoretic quantities measure whether the current observation set resolves mechanism uncertainty. High degeneracy is treated as a scientific finding (the data are insufficient to distinguish mechanisms), not as a failure.

4. **OC_k — observation contribution.** A leave-one-out metric OC_k = R_RACH(O) − R_RACH(O∖{k}) quantifies how much each observed pattern contributes to mechanism resolution. Critically, OC_k must be computed from all evaluated draws (not only accepted draws) to avoid downward bias when LOO re-acceptance occurs.

5. **NOV(q) — next-observation value as a constructive resolvability-EVSI.** A forward-looking preposterior expectation of the gain in causal resolvability from a future observation. For quantitative observations it is a genuine EVSI with an internal (resolvability) utility and the admissible-region pushforward as the outcome model (Proposition 6′), computable exactly from the stored admissible region without re-inference under a deterministic simulator. This targets ecological mechanism resolution without requiring an external decision/utility model.

6. **Epistemic role separation.** RACH explicitly labels each observation row as `observed_target`, `input_context`, `hypothesis_prediction`, or `diagnostic_only`, preventing circular inference and tautological calibration.

---

## 8. Validity and limitations

### Internal mathematical rationality

- A_ε is a well-defined rejection region in Θ × S space under a distance function d and tolerance ε.
- CA_j is a coherent empirical posterior frequency inside A_ε.
- D_RACH and R_RACH are coherent entropy summaries of switch-state uncertainty.
- OC_k is coherent only when computed from `evaluated_rows` (all draws, not only accepted draws), because LOO re-acceptance can recover previously-rejected draws.

### Biological rationality

- f contains biological axioms: drift, inheritance, stochastic reproduction, natural selection, and pollination-to-reproduction coupling.
- G(θ) restricts biologically implausible parameter combinations before inference, independently of the observed data.
- The separation of x_obs (fixed ecological context, e.g. island distance, Bombus frequency) and y_obs (independent observations, e.g. pairwise floral trait comparisons) prevents treating ecological input predictors as response evidence.

### Statistical validity concerns

- **Prior sensitivity.** CA_j, D_RACH, and R_RACH depend on the prior ranges for θ and on the prior probabilities over switch states. Prior sensitivity analysis is required before manuscript-level claims.
- **ε sensitivity.** Results depend on the acceptance threshold ε (or the ABC acceptance rule and pattern weights). The Streamlit app provides an ε-sensitivity panel; this should be reported in any publication.
- **Pattern quality.** Current y_obs consists of two source-confirmed directional gradients from the Inoue series: selfing/outcrossing shifts with isolation and flower size declines in the island/small-pollinator context. Numeric observations with measurement uncertainty would yield stronger, more discriminating inference, but unmeasured guide, herkogamy, Fis/He, seed-set, and visitation rows are deliberately kept out of observed_target.
- **Heuristic NOV.** The current heuristic NOV prioritises candidates by current CA_j ambiguity. The simulation-based NOV integrates over discrete outcomes but is not a full EVSI. Neither should be interpreted as exact expected information gain without further validation.
- **Known-truth recovery.** Before manuscript-level causal claims, RACH should demonstrate recovery of known switch states when data are generated from a known (θ, s). The `test_known_truth.py` tests provide a starting point.

### Claims to avoid

| Claim | Why to avoid |
|---|---|
| "RACH proves causal truth" | A_ε is an admissibility region, not a proof of causation |
| "NOV is exact EVSI for all candidates" | NOV is a constructive resolvability-EVSI for *quantitative* observations (Prop 6′); ordinal candidates without an outcome model remain heuristic priority scores |
| "High CA_j means the mechanism is true" | CA_j = P(s_j = 1 \| A_ε) is a conditional empirical frequency, not proof |
| "RACH is unrelated to ABC / POM / ABM" | RACH borrows key ideas from all three |
| "Bayes factors from CA_j are reliable" | BF = CA_j / (1 − CA_j) × prior ratio; reliable only if prior is carefully justified |

---

## 9. Recommended manuscript wording

### Framing paragraph

> RACH (Restricted Admissible Causal Hypotheses) is a causal admissibility and degeneracy framework for ecological systems. It is related to pattern-oriented modelling (POM; Grimm et al. 2005) and approximate Bayesian computation (ABC; Beaumont et al. 2002), but differs in its inferential target. Rather than selecting a single best model or estimating only parameter posteriors, RACH defines the admissible causal region A_ε and quantifies mechanism-level causal admissibility (CA_j), degeneracy (D_RACH), and resolvability (R_RACH). This reframing is useful in ecological systems where multiple non-exclusive mechanisms can generate the same observed patterns.

### Limitations paragraph

> RACH does not prove causal truth. It identifies causal mechanisms that remain admissible under the specified biological constraints, prior parameter ranges, generative simulator, distance function, and independent observations. Results depend on prior sensitivity, the acceptance threshold ε, and the quality of observed patterns. Heuristic NOV(q) provides a priority ranking for future data collection but is not an exact expected value of sample information. Manuscript-level causal claims require prior sensitivity analysis, ε sensitivity analysis, and known-truth recovery tests.

---

## References

- Beaumont, M.A., Zhang, W., & Balding, D.J. (2002). Approximate Bayesian computation in population genetics. *Genetics*, 162, 2025–2035.
- Chaloner, K., & Verdinelli, I. (1995). Bayesian experimental design: A review. *Statistical Science*, 10(3), 273–304.
- Grimm, V., Berger, U., Bastiansen, F., Eliassen, S., Ginot, V., Giske, J., et al. (2006). A standard protocol for describing individual-based and agent-based models. *Ecological Modelling*, 198, 115–126.
- Grimm, V., Revilla, E., Berger, U., Jeltsch, F., Mooij, W.M., Railsback, S.F., et al. (2005). Pattern-oriented modeling of agent-based complex systems: lessons from ecology. *Science*, 310, 987–991.
- Grimm, V., & Railsback, S.F. (2012). *Agent-Based and Individual-Based Modeling: A Practical Introduction* (2nd ed.). Princeton University Press.
- Marin, J.-M., Pudlo, P., Robert, C.P., & Ryder, R.J. (2012). Approximate Bayesian computational methods. *Statistics and Computing*, 22, 1167–1180.
- Myung, J.I., & Pitt, M.A. (2009). Optimal experimental design for model discrimination. *Psychological Review*, 116(3), 499–518.
- Pearl, J. (2009). *Causality: Models, Reasoning, and Inference* (2nd ed.). Cambridge University Press.
- Peters, J., Mooij, J.M., Janzing, D., & Schölkopf, B. (2014). Causal discovery with continuous additive noise models. *Journal of Machine Learning Research*, 15, 2009–2053.
- Pudlo, P., Marin, J.-M., Estoup, A., Cornuet, J.-M., Gautier, M., & Robert, C.P. (2016). Reliable ABC model choice via random forests. *Bioinformatics*, 32, 859–866.
- Raiffa, H., & Schlaifer, R. (1961). *Applied Statistical Decision Theory*. Harvard University Press.
- Railsback, S.F., & Grimm, V. (2019). *Agent-Based and Individual-Based Modeling: A Practical Introduction* (2nd ed.). Princeton University Press.
- Robert, C.P., Cornuet, J.-M., Marin, J.-M., & Pillai, N.S. (2011). Lack of confidence in approximate Bayesian computation model choice. *PNAS*, 108, 15112–15117.
- Sisson, S.A., Fan, Y., & Beaumont, M.A. (eds.) (2018). *Handbook of Approximate Bayesian Computation*. CRC Press.
- Spirtes, P., Glymour, C., & Scheines, R. (2001). *Causation, Prediction, and Search* (2nd ed.). MIT Press.
- Tavaré, S., Balding, D.J., Griffiths, R.C., & Donnelly, P. (1997). Inferring coalescence times from DNA sequence data. *Genetics*, 145, 505–518.
