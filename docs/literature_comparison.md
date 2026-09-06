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

## 3. Multiple working hypotheses and pre-data hypothesis vetting

Multiple-hypothesis reasoning is established ecological methodology, not an MROD invention. Betini et al. (2017) documented that explicit testing of multiple competing hypotheses remained uncommon despite the long-standing multiple-working-hypotheses and strong-inference traditions. Yanco et al. (2020) went further and supplied a formal **pre-data** workflow: candidate hypotheses are made explicit as models, their sampling distributions are simulated, overlap is inspected for degeneracy or noisiness, and the hypothesis set or study design is revised before data collection when the candidates are not distinguishable.

This prior art overlaps directly with the motivation for mechanism-resolving observation design. MROD must therefore acknowledge that ecology already has procedures for asking whether hypotheses are distinguishable and for changing design when they are not.

The narrower difference is the point in the inferential cycle and the object carried forward. Yanco et al. vet candidate hypotheses before new data are collected. MROD begins after a current evidence set has already restricted a declared model family to a **post-data admissible region**, potentially containing non-exclusive mechanism combinations. It then:

```text
current A_epsilon
-> retain the joint mechanism projection
-> quantify residual H(S | A_epsilon)
-> derive/verify candidate outcome partitions on that same current region
-> score I(S;Q | A_epsilon)/K
-> observe Q
-> condition A_epsilon on the realised outcome
-> recompute the remaining candidate values.
```

Thus the defensible contribution is not `use multiple working hypotheses`, `simulate competing hypotheses`, or `revise study design when hypotheses overlap`. It is the closed-loop connection from a **current set-valued, non-exclusive mechanism inference** to mechanism-targeted follow-up observation value and sequential conditioning.

Claim guard: do not write that MROD turns ambiguity into design as though that general idea were absent from ecology. Write that it operationalizes a specific post-current-data mechanism-resolution loop over an admissible joint mechanism region.

Key references: Betini et al. (2017); Yanco et al. (2020).

## 4. Value of information and Bayesian experimental design

Classical Bayesian experimental design asks which experiment maximizes an expected utility or information criterion. Value of Information (VoI) and Expected Value of Sample Information (EVSI) usually value information through improvement in a downstream decision. In applied ecology, Canessa et al. (2015) formulate VoI around explicit management actions, objectives and expected outcomes; Williams et al. (2020) likewise value sample information through management consequences.

MROD uses the same preposterior logic but a narrower internal target. It does not require a management action table or external reward function. The utility is mechanism resolution itself:

```text
expected gain in R
= I(S;Q | A_epsilon)/K.
```

Thus the defensible distinction is not that MROD invented EVSI or mutual information. It is that MROD defines a reproducible ecological **mechanism-resolution state**, preserves all compatible mechanism programs, and uses a verified candidate observation partition to value measurements specifically by how much they separate the residual mechanism vector.

Claim guard: do not say `more data is not a design` as if ecology lacks VoI or experimental-design theory. The stronger and more accurate claim is that generic calls for more data do not specify which *mechanism distinction* a measurement resolves, and management-oriented VoI optimizes a different downstream utility unless mechanism resolution itself is chosen as that utility.

Key references: Raiffa & Schlaifer (1961); Chaloner & Verdinelli (1995); Canessa et al. (2015); Williams et al. (2020).

## 5. Model discrimination and optimal experimental design

Designing experiments to discriminate between competing models is a classical statistical problem. Sequential and Bayesian model-discrimination designs therefore predate MROD.

MROD should not claim novelty for `choose an experiment that separates models`. Its narrower contribution is designed for ecological mechanism programs that can be non-exclusive and jointly active. The latent target is a mechanism vector rather than a single mutually exclusive model label, and the retained admissible set can contain many parameterizations of many switch combinations. Candidate value is calculated against that residual joint mechanism distribution.

The current controlled validation supports information-guided candidate screening within a frozen family of confounded systems. It does not establish global optimality or superiority to all Bayesian design or model-discrimination methods.

Key references: Atkinson & Cox (1974); Chaloner & Verdinelli (1995).

## 6. Structural identifiability and the Boundary interface

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

## 7. Null testing, residual error and sampling precision

MROD is not a significance test. Rejecting a null can leave several non-null mechanisms admissible. It is not a residual diagnostic: two mechanism programs can fit the same target exactly. It is also not a claim that replication is useless: replication can reduce sampling error and distinguish mechanisms whose predictions are only approximately equal.

The structural statement is narrower:

> Increasing precision cannot repair an observation map that is exactly invariant along the mechanism distinction of interest.

When candidate predictions differ approximately rather than exactly, additional replication can be mechanism-informative and should be evaluated through the candidate predictive distribution.

## 8. Causal effects, mediation and mechanistic investigation

Causal-effect estimation, causal mediation and mechanistic investigation answer related but non-identical questions. Grace et al. (2025) explicitly distinguish causal-effect estimation from mechanistic investigation, while Correia et al. (2025) emphasize that mediation effects require their own causal assumptions. Siegel & Dee (2025) review causal-inference design in ecology.

MROD does not identify intervention counterfactuals from accepted-row filtering. A candidate observation may be experimental or observational, but its MROD value concerns information about the declared residual mechanism vector. If the scientific estimand is an intervention effect, the causal assumptions required for that estimand still apply.

Claim guard: `mechanism-resolving` does not mean `counterfactual causal effect identified`.

## 9. Singleton screening, synergistic information and non-myopic design

The active MROD selection rule evaluates immediate singleton observations by

```text
V(Q_j)=I(S;Q_j|A_epsilon)/K.
```

This is an auditable one-step information criterion, but a zero value for every singleton does not imply that the full declared candidate vector is uninformative. Complementary observations can exhibit synergistic information. The controlled XOR witness gives

```text
I(S;Q_1|A_epsilon)=0,
I(S;Q_2|A_epsilon)=0,
I(S;Q_1,Q_2|A_epsilon)=1 bit.
```

Accordingly, complete singleton coverage with all `V(Q_j)=0` licenses only a **validated one-step information stop** for the current positive-singleton greedy policy. A stronger **sequence-information limit** requires a coherent joint predictive vector `Q_C` and zero joint information

```text
I(S;Q_C|A_epsilon)=0.
```

If joint information is positive while all singleton values are zero, the limitation is in the myopic acquisition rule, not in the declared measurement vocabulary itself. A non-myopic or bundle-level objective is then needed.

This is a claim ceiling, not a novelty claim. Synergistic information, batch information acquisition, non-myopic Bayesian experimental design and adaptive-submodular design all have established literatures. MROD does not claim to invent them, and positive joint information alone does not determine a unique acquisition order or a cost-optimal adaptive policy.

A further guard concerns interventions and destructive measurements. A joint candidate vector is licensed only when the candidate outcomes have a coherent joint predictive model. If measuring or intervening on one candidate changes the distribution of another, an order-specific transition or potential-outcome model is required; singleton predictions cannot simply be stacked into a valid `Q_C`.

## 10. What the current paper can defensibly claim

1. **Post-data set-valued mechanism reporting.** The compatible, potentially non-exclusive mechanism region is retained rather than hidden behind a modal explanation.
2. **A mechanism-specific uncertainty target.** `H(S|A_epsilon)` and normalized resolvability quantify ambiguity in the declared joint mechanism vector after current evidence has been applied.
3. **Verified singleton observation information value from the same current region.** For a predictive outcome partition identified from `A_epsilon`, `V(Q)=I(S;Q|A_epsilon)/K` exactly measures expected immediate mechanism-resolvability gain.
4. **A structural zero-value condition.** A candidate already determined by the current exact observation map cannot add mechanism information; structural novelty alone is not sufficient.
5. **A closed sequential conditioning loop.** The selected outcome conditions the same admissible region and all remaining singleton candidate values are recomputed.
6. **A precise two-step condition for adaptive recomputation after a fixed first observation.** Adaptive recomputation is weakly better than the best precommitted second measurement and strictly better exactly when positive-probability branches share no common optimal remaining candidate.
7. **Controlled selection validation and a negative stronger-comparator result.** Frozen G2 supports information-guided singleton screening against random ordering, while static initial-information essentially matches adaptive recomputation on that family and narrows the empirical adaptive claim.
8. **Evidence-role discipline.** Observed targets, simulator context, diagnostics and future observations are preassigned distinct inferential roles to reduce circular evidence use.
9. **A stopping-depth claim ceiling.** Prediction limitation, zero-singleton one-step stopping and coherent-joint sequence-information limits are not interchangeable.

## 11. Claims to avoid

- MROD invented multiple working hypotheses, strong inference, pre-data hypothesis vetting or design revision under hypothesis degeneracy.
- MROD proves a natural-system causal mechanism.
- MROD replaces causal inference or mediation analysis.
- Mutual information, EVSI, model discrimination, structural identifiability, synergistic information or non-myopic Bayesian design are new inventions of MROD.
- More data never help.
- Any biologically proximal measurement is more mechanistic or more resolving than a field observation.
- Any structurally new measurement has positive mechanism information.
- Adaptive recomputation always outperforms a static information ordering.
- All singleton values equal to zero implies that the candidate vocabulary is sequence-information-limited.
- A joint candidate distribution can be created by stacking order-dependent or mutually incompatible interventions without an additional transition model.
- Positive joint information identifies the unique best acquisition order.
- The frozen synthetic benchmark establishes universal optimality.

## 12. Current manuscript framing

The cleanest paper-level sequence is

```text
current ecological evidence
-> retain compatible non-exclusive mechanism programs
-> diagnose residual joint mechanism ambiguity
-> exclude provably redundant observations where an exact structural screen exists
-> verify singleton candidate predictive partitions on the same current region
-> value immediate candidates by mechanism information
-> if a positive singleton exists, observe a highest-current-value candidate
-> condition the region on the realised outcome and recompute
-> if candidate predictions are missing, report prediction limitation
-> if every estimable singleton is zero, report a validated one-step stop rather than sequence impossibility
-> claim a sequence-information limit only after a licensed coherent joint candidate vector has zero joint mechanism information.
```

The practical rhetorical translation is:

> Multiple working hypotheses and pre-data discriminability checks already tell ecologists not to trust a single unvetted explanation. MROD addresses the later problem: after current evidence has already left a set of mechanism programs admissible, report that set and use it to quantify which feasible follow-up observation would reduce the remaining joint mechanism ambiguity. If no immediate singleton carries mechanism information, report that one-step stopping state honestly; do not call the candidate vocabulary information-limited unless a coherent joint-information audit supports the stronger statement.

## References

- Atkinson, A.C. & Cox, D.R. (1974). Planning experiments for discriminating between models. *Journal of the Royal Statistical Society: Series B* 36: 321–334.
- Beaumont, M.A., Zhang, W. & Balding, D.J. (2002). Approximate Bayesian computation in population genetics. *Genetics* 162: 2025–2035.
- Beaumont, M.A. (2010). Approximate Bayesian computation in evolution and ecology. *Annual Review of Ecology, Evolution, and Systematics* 41: 379–406.
- Bellman, R. & Åström, K.J. (1970). On structural identifiability. *Mathematical Biosciences* 7: 329–339.
- Betini, G.S., Avgar, T. & Fryxell, J.M. (2017). Why are we not evaluating multiple competing hypotheses in ecology and evolution? *Royal Society Open Science* 4: 160756.
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
- Yanco, S.W., McDevitt, A., Trueman, C.N., Hartley, L. & Wunder, M.B. (2020). A modern method of multiple working hypotheses to improve inference in ecology. *Royal Society Open Science* 7: 200231.
