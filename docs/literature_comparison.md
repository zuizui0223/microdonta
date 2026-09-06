# Literature comparison and defensible novelty of MROD

Status: current conceptual comparison for **Mechanism-Resolving Observation Design (MROD)**. Historical RACH/NOV terminology is retained only in git history and frozen provenance files; it is not the active scientific vocabulary.

## 1. Inferential target

MROD starts from a declared model family in which several parameter–mechanism states remain compatible with the current evidence. Its primary state object is the admissible region

```text
A_epsilon = {(theta,s): declared constraints hold and observed targets are matched within tolerance}.
```

The scientific target is the projection of that region onto mechanism identity `S`, not a single modal model and not parameter uncertainty in general. Residual mechanism uncertainty is summarized by

```text
D = H(S | A_epsilon),
R = 1 - D/K.
```

For a verified candidate observation `Q`, publication-level observation information value is

```text
V(Q) = I(S;Q | A_epsilon)/K.
```

## 2. Pattern-oriented modelling and approximate Bayesian computation

Pattern-oriented modelling (POM) uses multiple patterns to constrain generative models. Approximate Bayesian computation (ABC) uses simulation and a discrepancy rule to approximate posterior restriction when likelihoods are unavailable. MROD borrows both ideas: multiple evidence roles constrain a simulator, and prior draws are retained or rejected under a declared tolerance.

The distinction is the inferential use of the retained region. MROD does not discard multiplicity after ranking a best model. The multiplicity of compatible mechanism programs is the object needed for mechanism entropy, equivalence structure and next-observation design.

This does not make MROD a replacement for ABC model choice or a general causal-discovery method. Its claims are conditional on the declared mechanism vocabulary, prior/parameter support, biological constraints, observation map, discrepancy and tolerance.

Key references: Beaumont et al. (2002, 2010); Grimm et al. (2005); Robert et al. (2011).

## 3. Value of information and Bayesian experimental design

Classical Bayesian experimental design asks which experiment maximizes an expected utility or information criterion. Value of Information (VoI) and Expected Value of Sample Information (EVSI) usually value information through improvement in a downstream decision. In applied ecology, Canessa et al. (2015) formulate VoI around explicit management actions, objectives and expected outcomes; Williams et al. (2020) likewise value sample information through management consequences.

MROD uses the same preposterior logic but a narrower internal target. It does not require a management action table or external reward function. The utility is mechanism resolution itself:

```text
expected gain in R
= I(S;Q | A_epsilon)/K.
```

Thus the defensible distinction is not that MROD invented EVSI or mutual information. It is that MROD defines a reproducible ecological **mechanism-resolution state**, preserves all compatible mechanism programs, and uses a verified candidate observation partition to value measurements specifically by how much they separate the residual mechanism vector.

Claim guard: do not say `more data is not a design` as if ecology lacks VoI or experimental-design theory. The stronger and more accurate claim is that generic calls for more data do not specify which *mechanism distinction* a measurement resolves, and management-oriented VoI optimizes a different downstream utility unless mechanism resolution itself is chosen as that utility.

Key references: Raiffa & Schlaifer (1961); Chaloner & Verdinelli (1995); Canessa et al. (2015); Williams et al. (2020).

## 4. Model discrimination and optimal experimental design

Designing experiments to discriminate between competing models is a classical statistical problem. Sequential and Bayesian model-discrimination designs therefore predate MROD.

MROD should not claim novelty for `choose an experiment that separates models`. Its narrower contribution is designed for ecological mechanism programs that can be non-exclusive and jointly active. The latent target is a mechanism vector rather than a single mutually exclusive model label, and the retained admissible set can contain many parameterizations of many switch combinations. Candidate value is calculated against that residual joint mechanism distribution.

The current controlled validation supports information-guided candidate screening within a frozen family of confounded systems. It does not establish global optimality or superiority to all Bayesian design or model-discrimination methods.

Key references: Atkinson & Cox (1974); Chaloner & Verdinelli (1995).

## 5. Structural identifiability and the Boundary interface

Structural identifiability asks whether distinct latent states can generate the same observations. The separate Boundary project develops this observation-map question for restricted ecological measurement classes. The interface to MROD is one-way and exact where applicable.

If a deterministic candidate is already determined by the current exact observation,

```text
Q = h(O),
```

then after conditioning on the current observation it is constant on the compatible fibre and

```text
I(S;Q | O) = 0.
```

In the exact positive log-linear class, a candidate row inside the current observation row span is therefore guaranteed to have zero new mechanism information.

The converse is false. A structurally new observation can partition only nuisance or continuous parameter variation while remaining independent of `S`. Boundary can therefore provide a **structural zero-value screen**; MROD still needs `I(S;Q|A_epsilon)` to determine whether a non-redundant observation is relevant to mechanism identity.

Claim guard: do not equate rank gain with positive MROD value.

Key references: Bellman & Åström (1970); Rothenberg (1971); Manski (2003).

## 6. Null testing, residual error and sampling precision

MROD is not a significance test. Rejecting a null can leave several non-null mechanisms admissible. It is not a residual diagnostic: two mechanism programs can fit the same target exactly. It is also not a claim that replication is useless: replication can reduce sampling error and distinguish mechanisms whose predictions are only approximately equal.

The structural statement is narrower:

> Increasing precision cannot repair an observation map that is exactly invariant along the mechanism distinction of interest.

When candidate predictions differ approximately rather than exactly, additional replication can be mechanism-informative and should be evaluated through the candidate predictive distribution.

## 7. Causal effects, mediation and mechanistic investigation

Causal-effect estimation, causal mediation and mechanistic investigation answer related but non-identical questions. Grace et al. (2025) explicitly distinguish causal-effect estimation from mechanistic investigation, while Correia et al. (2025) emphasize that mediation effects require their own causal assumptions. Siegel & Dee (2025) review causal-inference design in ecology.

MROD does not identify intervention counterfactuals from accepted-row filtering. A candidate observation may be experimental or observational, but its MROD value concerns information about the declared residual mechanism vector. If the scientific estimand is an intervention effect, the causal assumptions required for that estimand still apply.

Claim guard: `mechanism-resolving` does not mean `counterfactual causal effect identified`.

## 8. What the current paper can defensibly claim

1. **Set-valued mechanism reporting.** The compatible mechanism region is retained rather than hidden behind a modal explanation.
2. **A mechanism-specific uncertainty target.** `H(S|A_epsilon)` and normalized resolvability quantify ambiguity in the declared mechanism vector.
3. **Verified observation information value.** For a predictive outcome partition identified from the current region, `V(Q)=I(S;Q|A_epsilon)/K` exactly measures expected mechanism-resolvability gain.
4. **A structural zero-value condition.** A candidate already determined by the current exact observation map cannot add mechanism information; structural novelty alone is not sufficient.
5. **Sequential recomputation with a precise two-step condition.** Adaptive recomputation is weakly better than the best precommitted second measurement and strictly better exactly when positive-probability branches disagree on every common optimal remaining candidate.
6. **Controlled selection validation.** The frozen G2 benchmark shows strong information-guided screening against random ordering, while the stronger static-information diagnostic limits the empirical claim for adaptation itself.
7. **Evidence-role discipline.** Observed targets, simulator context, diagnostics and future observations are preassigned distinct inferential roles to reduce circular evidence use.

## 9. Claims to avoid

- MROD proves a natural-system causal mechanism.
- MROD replaces causal inference or mediation analysis.
- Mutual information, EVSI, model discrimination or structural identifiability are new inventions of MROD.
- More data never help.
- Any biologically proximal measurement is more mechanistic or more resolving than a field observation.
- Any structurally new measurement has positive mechanism information.
- Adaptive recomputation always outperforms a static information ordering.
- The frozen synthetic benchmark establishes universal optimality.

## 10. Current manuscript framing

The cleanest paper-level sequence is

```text
current ecological evidence
-> retain compatible mechanism programs
-> diagnose residual mechanism ambiguity
-> exclude provably redundant observations where an exact structural screen exists
-> verify candidate predictive partitions
-> value candidates by mechanism information
-> observe the highest-value candidate
-> condition and recompute
-> stop when resolved, budget-limited or information-limited.
```

The practical rhetorical translation is:

> Do not leave alternative mechanisms only as a limitation statement. State which distinctions remain unresolved and, when the predictive candidate vocabulary permits it, which observation would reduce that ambiguity most. If no available observation carries mechanism information, report that information limit rather than recommending unspecified additional data.

## References

- Atkinson, A.C. & Cox, D.R. (1974). Planning experiments for discriminating between models. *Journal of the Royal Statistical Society: Series B* 36: 321–334.
- Beaumont, M.A., Zhang, W. & Balding, D.J. (2002). Approximate Bayesian computation in population genetics. *Genetics* 162: 2025–2035.
- Beaumont, M.A. (2010). Approximate Bayesian computation in evolution and ecology. *Annual Review of Ecology, Evolution, and Systematics* 41: 379–406.
- Bellman, R. & Åström, K.J. (1970). On structural identifiability. *Mathematical Biosciences* 7: 329–339.
- Canessa, S. et al. (2015). When do we need more data? A primer on calculating the value of information for applied ecologists. *Methods in Ecology and Evolution* 6: 1219–1228.
- Chaloner, K. & Verdinelli, I. (1995). Bayesian experimental design: a review. *Statistical Science* 10: 273–304.
- Correia, H.E., Dee, L.E. & Ferraro, P.J. (2025). Designing causal mediation analyses to quantify intermediary processes in ecology. *Biological Reviews* 100: 1512–1533.
- Grace, J.B. et al. (2025). Causal effects versus causal mechanisms: two traditions with different requirements and contributions towards causal understanding. *Ecology Letters* 28: e70029.
- Grimm, V. et al. (2005). Pattern-oriented modeling of agent-based complex systems: lessons from ecology. *Science* 310: 987–991.
- Manski, C.F. (2003). *Partial Identification of Probability Distributions*. Springer.
- Raiffa, H. & Schlaifer, H. (1961). *Applied Statistical Decision Theory*. Harvard University Press.
- Robert, C.P. et al. (2011). Lack of confidence in approximate Bayesian computation model choice. *PNAS* 108: 15112–15117.
- Rothenberg, T.J. (1971). Identification in parametric models. *Econometrica* 39: 577–591.
- Siegel, K. & Dee, L.E. (2025). Foundations and future directions for causal inference in ecological research. *Ecology Letters* 28: e70053.
- Williams, B.K. et al. (2020). Scenarios for valuing sample information in natural resources. *Methods in Ecology and Evolution* 11.
