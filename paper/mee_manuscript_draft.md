# RACH: information-theoretic next-observation selection for causally degenerate ecological models

> **Submission-track draft for Methods in Ecology and Evolution.** This manuscript reports RACH, validated NOV, RACH-SEQ and the frozen G2 observation-selection benchmark. Channel-identifiability theorems, bounded proxy-drift intervals and their ecological design rules are developed separately and are not primary contributions of this paper.

---

## Abstract

1. Ecological mechanism inference often ends with several explanations that reproduce the same observed pattern. Selecting the highest-ranked explanation conceals this causal degeneracy, while collecting every conceivable measurement is rarely feasible. We introduce Restricted Admissible Causal Hypotheses (RACH), a workflow that retains all mechanism programs compatible with a predeclared model family, biological constraint grammar and observation set, then reports residual uncertainty rather than forcing a winner.

2. RACH quantifies causal admissibility, joint mechanism entropy and resolvability. For a candidate measurement whose outcomes form a verified predictive partition of the current admissible region, its next-observation value is `NOV(Q)=I(S;Q|A_ε)/K`: normalised mutual information between the measurement and residual mechanism identity. RACH-SEQ selects the candidate with maximum current NOV, conditions the admissible region on the realised outcome, and recomputes every remaining predictive distribution and NOV value.

3. We validated selection in a frozen truth-peek-free synthetic benchmark containing random confounded systems, informative measurements and two mechanism-independent nuisance measurements. At budget two, RACH-SEQ resolved all initial confounding edges on average and converged in 99.0% of systems, versus 60.45% edge resolution and 43.5% convergence under random order. At budget four, random order selected 1.169 nuisance measurements per system versus 0.014 for RACH-SEQ, an 83.5-fold difference, while using 2.673 versus 1.518 observations. Hidden-truth false exclusion was zero throughout.

4. Independent checks recovered the NOV mutual-information identity, exact stored-region conditioning in the deterministic validation model and positive calibration against realised resolvability gains. The contribution is therefore a validated observation-selection method, not an empirical mechanism claim: given a declared candidate family, RACH identifies what remains unresolved, whether any available measurement is informative, and which measurement should be taken next under a limited budget.

**Data/Code for peer review:** An anonymised reviewer bundle containing executable Python code, frozen protocol and result summaries, tests, and figure commands will accompany the submission. No new empirical data are reported.

**Keywords:** approximate Bayesian computation; causal admissibility; experimental design; mechanism inference; mutual information; sequential design; value of information.

---

## 1. Introduction

Ecological studies frequently seek mechanisms from patterns. A trait shift may be compatible with altered mutualistic service, a correlated life-history pathway, shared environmental forcing, or several combinations of these processes. A simulation or statistical model can make each explanation explicit, but explicitness does not guarantee distinguishability. Different mechanism programs may occupy overlapping regions of the observation space and remain plausible after the available data are conditioned upon.

The standard response is model selection: define candidate models and rank them by posterior probability, likelihood or an information criterion. This is useful when the data separate the candidates. Under causal degeneracy, however, the result can be a low-mass winner whose identity depends on modelling choices and whose apparent decisiveness exceeds the information in the observation. Approximate Bayesian computation model choice is one prominent setting in which such reliability concerns have been demonstrated (Robert et al. 2011).

A second response is to collect more data. Yet `more data` is not a design. Field observations, experiments, assays and genetic measurements differ greatly in cost and in the mechanism distinctions they can resolve. A measurement can be precise and biologically respectable while carrying almost no information about the particular ambiguity that remains. When observation budgets are limited, the scientific task is not simply to reduce variance but to select the measurement that most reduces residual mechanism uncertainty.

Restricted Admissible Causal Hypotheses (RACH) changes the inferential target. Rather than asking which single mechanism currently ranks first, it asks:

1. which parameter–mechanism combinations remain compatible with the declared evidence;
2. how much uncertainty remains about mechanism identity;
3. which candidate observation is predicted to reduce that uncertainty most;
4. when the available candidate vocabulary contains no further resolving information.

The method combines prior restriction, explicit biological constraints, entropy and value-of-information logic. Its novelty lies in their joint use for a specific target: preservation and sequential reduction of causal degeneracy. RACH reports the admissible mechanism set and its uncertainty as scientific results rather than hiding them behind a modal model. Its next-observation quantity is not a heuristic priority score. When the predictive outcomes of a candidate measurement are identified by the current admissible region, next-observation value (NOV) is exactly the normalised mutual information between that measurement and the remaining mechanism vector.

This paper makes four contributions. First, it defines a reproducible admissibility object and separates observed targets from context, diagnostics and future measurements. Second, it derives the information interpretation and bounds of validated NOV. Third, it closes the loop through RACH-SEQ, which recomputes the information state after each realised observation. Fourth, it tests observation selection itself in a controlled truth-peek-free benchmark where informative candidates must compete with valid but mechanism-independent nuisance measurements.

The validation claim is intentionally algorithmic and conditional. We do not use a natural system to claim that RACH discovered a true ecological mechanism. We test whether, in a declared family of confounded systems with known hidden truth, the method chooses informative measurements without seeing their outcomes in advance, reduces ambiguity under a limited budget, and avoids excluding the generating explanation. This makes the synthetic benchmark—not an illustrative field narrative—the principal evidence for the observation-selection method.

## 2. Materials and Methods

### 2.1 Restricted admissible causal hypotheses

Let `S in {0,1}^K` be a binary mechanism vector and `theta in Theta` continuous or discrete parameters. Complex pathways are represented by several switches being active together rather than by assigning a single mutually exclusive model label. Let `G(theta)` be a pre-data biological constraint grammar, `x_obs` fixed context, `y_obs` independent observed targets, `f` a simulator or predictive model, `P_sim` and `P_obs` maps into a shared pattern space, `d` a predeclared discrepancy, and `epsilon` an acceptance tolerance.

RACH defines

```text
A_epsilon(y_obs,x_obs)
= {(theta,s) in Theta x S:
   G(theta)=1 and
   d(P_sim(f(x_obs;theta,s)),P_obs(y_obs)) <= epsilon}.
```

The implementation approximates this region by prior sampling and rejection. This resembles ABC restriction, but the inferential output differs from ABC model choice. RACH does not collapse `A_epsilon` to its modal switch state. It retains the joint parameter–mechanism region because its multiplicity is the object needed for degeneracy diagnostics and observation design.

#### 2.1.1 Evidence roles and circularity control

Every empirical or synthetic quantity receives one role before inference:

```text
observed_target     may enter the acceptance discrepancy
input_context       conditions the simulator but is not an independent target
diagnostic_only     evaluates behaviour after inference
future_observation  is withheld and evaluated as a candidate next measurement
```

This taxonomy prevents the same evidence from defining the simulator context, entering the acceptance distance and then being presented again as an independent validation. The constraint grammar is also applied before observed targets are evaluated, so biological feasibility is not tuned to favour the realised pattern.

#### 2.1.2 Admissibility and degeneracy quantities

For switch `j`, causal admissibility is

```text
CA_j = P(s_j=1 | A_epsilon).
```

Let `H(S|A_epsilon)` be the base-2 entropy of the joint switch vector. Causal degeneracy and resolvability are

```text
D_RACH = H(S|A_epsilon),
R_RACH = 1 - D_RACH/K.
```

Because a `K`-bit vector has at most `K` bits of entropy,

```text
0 <= D_RACH <= K,
0 <= R_RACH <= 1.
```

The denominator is maximum switch entropy, not realised prior entropy. This preserves a fixed interpretation across priors: `R_RACH=1` means the switch vector is completely resolved inside the accepted region, while lower values retain joint ambiguity. Pairwise or higher-order mechanism-equivalence summaries can be constructed from the same accepted switch rows. Causal replaceability measures whether one mechanism's accepted contribution can be substituted by alternative programs rather than merely whether its marginal `CA_j` is high.

### 2.2 Validated next-observation value and RACH-SEQ

Let `Q` be a candidate future measurement with finite outcomes `q`. For validated stored-region calculation, the outcome maps must form a mutually exclusive and exhaustive partition of current `A_epsilon`. The predictive probability is then the pushforward of the restricted current region:

```text
Pr(Q=q | A_epsilon).
```

Define next-observation value as expected gain in resolvability:

```text
NOV(Q)
= E_Q[R_RACH(A_epsilon | Q)-R_RACH(A_epsilon)].
```

Using the entropy definition of resolvability,

```text
NOV(Q)
= {H(S|A_epsilon)-H(S|A_epsilon,Q)}/K
= I(S;Q|A_epsilon)/K.
```

Therefore

```text
0 <= NOV(Q) <= 1-R_RACH(A_epsilon) <= 1.
```

`NOV(Q)=0` exactly when `Q` is independent of residual mechanism identity under the current accepted region. The upper bound is attained when the observation removes all remaining switch entropy. An individual realised outcome may increase conditional entropy, but expected gain under the coherent predictive distribution cannot be negative.

A candidate is reported as not estimable when its outcomes overlap, fail to cover the current region or depend on simulator outputs absent from stored rows. A declared external outcome prior is not silently substituted and labelled validated NOV. A legacy structural edge-cut score remains available only as an explicitly named fallback when the predictive partition cannot be computed; provenance records whether a selection step used validated NOV or fallback structure.

#### 2.2.1 Sequential closure

RACH-SEQ repeats the information calculation after every observation:

```text
A_0 = current admissible region
for t = 0,1,... until stopping:
    score each verified remaining Q by I(S;Q|A_t)/K
    select the maximum positive current score
    obtain the realised outcome only after selection
    condition A_t on that outcome to form A_{t+1}
    recompute all predictive probabilities and scores
```

The procedure stops when the budget is exhausted, the declared confounding structure is resolved, or every available verified candidate has zero NOV. The last condition is substantive: unresolved mechanisms may remain, but the declared measurement vocabulary contains no additional information about them.

### 2.3 AI-assisted development disclosure

OpenAI ChatGPT was used interactively to assist with code review, draft editing and repository/documentation maintenance. The author reviewed and takes responsibility for all generated or edited text and code. AI outputs were not treated as empirical observations or independent scientific evidence. Frozen benchmark configurations and reported numerical results were executed and checked through the reproducible workflows described below.

### 2.4 Controlled validation design

We used four complementary controlled checks. None is presented as natural-system causal validation.

#### 2.4.1 Confounding demonstration

A compact synthetic example was constructed in which multiple switch programs reproduce the same ordinal target pattern. The demonstration contrasts a single low-mass MAP switch combination with the retained RACH region, reports degeneracy, and shows how a quantitative candidate observation separates previously equivalent programs.

#### 2.4.2 Known-truth self-consistency

Synthetic observations were generated under declared switch states and passed through the same inference model. The purpose was to check that generating switches remain admissible under pattern-noise strata. Because the target pattern is deliberately non-identifying, additional confounded switches are not required to disappear and exact switch-state accuracy is not expected to equal one.

#### 2.4.3 Frozen G2 truth-peek-free selection benchmark

The primary selection validation is governed by frozen protocol `rach-g2-truth-peek-free-v2`. Five predeclared seeds generate 200 systems each. Every system has `K in {4,5,6}`, one or two disjoint two-driver confounds, random pre-data driver coefficients, 1,500 prior draws and an explicit resolving quantitative observation for each confound. Two additional binary nuisance measurements are generated independently of the mechanism vector. They are valid mutually exclusive and exhaustive candidate observations but have no designed mechanism information.

The same seed-defined systems, hidden truths, candidate sets and budgets 0–4 are supplied to two policies:

```text
RACH-SEQ      choose the remaining candidate with maximum current validated NOV
random_order  choose uniformly among remaining candidates
```

Neither policy observes a hidden outcome before candidate selection. Hidden truth is used only after selection to materialise the chosen candidate's realised benchmark outcome. The accepted region is then conditioned and RACH-SEQ recomputes all current NOV values. The random-order policy is an uninformed selection baseline, not a competing causal inference method.

Primary outcomes are the fraction of initial confounding edges resolved, convergence to an empty confounding graph, number of observations used, number of nuisance measurements selected and false exclusion of the hidden true explanation. Policy contrasts were designated descriptive. The protocol contained no favourable-result threshold requiring RACH-SEQ to outperform random selection, and scientific parameters could not be overridden at execution.

#### 2.4.4 NOV identity and calibration

One implementation independently computes expected resolvability gain and empirical mutual information from the joint `(S,Q)` table. A second check compares stored-region conditioning with fresh deterministic re-inference for quantitative observations. Finally, predicted EVSI/NOV is compared with realised resolvability gains across controlled hidden truths. These checks distinguish an algebraic identity, a computational shortcut and empirical calibration.

## 3. Results

### 3.1 RACH preserves the confound instead of manufacturing a winner

In the compact confounding example, conventional ranking returned a single MAP switch combination with low posterior mass. The accepted sample nevertheless contained multiple coupled mechanism programs. RACH exposed that multiplicity through marginal admissibility, joint entropy and the mechanism-equivalence structure. A candidate quantitative observation with outcomes that separated the coupled switches had positive validated NOV, whereas mechanism-independent candidates had zero or negligible information under the current region.

This example demonstrates the reporting difference between model ranking and admissible-set inference. The result is not that the synthetic generating mechanism was ecologically true, but that the method did not hide observational equivalence behind a modal label.

### 3.2 Known-truth checks retain generating mechanisms

Under the unchanged known-truth defaults, the zero pattern-noise stratum had mean switch-state accuracy 0.6562 and recall of applicable true-ON switches 1.000. Recall remained 1.000 in the 0.1 and 0.2 noise strata. Lower exact-state accuracy reflected retention of additional confounded explanations, which is the expected signature when the observed pattern does not uniquely identify the switch vector.

The benchmark therefore supports self-consistency in a limited sense: generating switches were not discarded merely because equivalent alternatives survived. It does not show universal recovery under simulator misspecification or establish that any retained program is correct in nature.

### 3.3 G2 validates observation selection under limited budget

The frozen G2 benchmark contained 1,000 generated systems per policy. At budget two, RACH-SEQ resolved `1.000 ± 0.000` of initial confounding edges and converged in `0.990 ± 0.0079` of systems across the five predeclared seeds. It used `1.505 ± 0.030` observations and selected `0.001 ± 0.0022` nuisance measurements per system. The matched random-order policy resolved `0.6045 ± 0.0231` of initial edges, converged in `0.435 ± 0.0355` of systems, used `1.821 ± 0.024` observations and selected `0.974 ± 0.0277` nuisance measurements.

The within-seed RACH-SEQ minus random-order contrast was therefore `+0.3955 ± 0.0231` for edge resolution and `+0.555 ± 0.0417` for convergence, while RACH-SEQ used `0.316 ± 0.020` fewer observations. At budget one, convergence was 0.495 under RACH-SEQ and 0.179 under random order.

Budget four isolates measurement efficiency after both policies had resolved all initial confounding edges on average. RACH-SEQ converged in 0.999 of systems and used 1.518 observations, whereas random order converged in 0.940 and used 2.673. Most visibly, random order selected 1.169 mechanism-independent nuisance measurements per system versus 0.014 for RACH-SEQ. The absolute difference was 1.155 nuisance measurements; the ratio was `1.169/0.014=83.5`, equivalent to an approximately 98.8% reduction relative to random order.

The fold ratio is descriptive and is reported with its absolute values because ratios become unstable when the selected count approaches zero. At budget two the aggregate ratio is much larger because RACH-SEQ's mean is 0.001, but the budget-four comparison provides the more conservative headline after both policies have enough budget to resolve all edges on average.

Hidden-truth false exclusion was zero in every policy-by-budget cell. All 10,000 system–policy–budget records retained the hidden generating explanation. Thus the selection advantage was not obtained by narrowing the accepted set so aggressively that the truth was discarded.

### 3.4 NOV implementation and calibration checks

Expected resolvability gain and independently computed `I(S;Q|A_epsilon)/K` agreed to the implementation's display tolerance. For six directly checked quantitative observations, conditioning the stored deterministic admissible region and performing fresh re-inference produced identical resolvability gains; the maximum absolute difference was zero.

Across eight candidate observations and four controlled truths per observation, predictive EVSI correlated positively with mean realised resolvability gain (`r=0.7664`). The mean absolute difference between predictive EVSI and mean realised gain was 0.0739. Individual outcomes remained variable, as expected for preposterior quantities. These results support the intended average information interpretation rather than a claim that NOV predicts every realised gain exactly.

## 4. Software and reproducibility

The public Python surface exposes RACH-first functions for admissibility, degeneracy, resolvability, replaceability, mechanism equivalence, validated NOV/EVSI and sequential selection. Compatibility heuristics remain explicitly named and are excluded from the primary publication API.

The final G2 result is tied to the frozen protocol and stored result summary. Every output row records the protocol SHA-256 and clean execution provenance. The pre-fix benchmark values are excluded from the active manuscript. A clean reproducibility workflow rebuilds Figures 1–3 and Figure S1, reproduces frozen validation summaries, builds and installs the release-candidate wheel outside the repository and checks its public API across Python 3.10–3.12.

The reviewer bundle excludes author metadata and public repository locators while retaining executable source, tests, frozen protocol/result summaries, figure commands and a per-file SHA-256 manifest. No new empirical data are reported, and no ecological mechanism conclusion is derived from the controlled examples.

## 5. Discussion

RACH treats unresolved mechanism multiplicity as a result rather than an inconvenience to be hidden. This matters because a low-mass modal mechanism can look decisive in a table while the accepted region remains broadly degenerate. Reporting the admissible set, its entropy and its replaceability structure makes the remaining ambiguity inspectable and reproducible.

The identity

```text
NOV(Q)=I(S;Q|A_epsilon)/K
```

provides a direct interpretation for observation value. A measurement is useful exactly to the extent that it carries information about the mechanism distinctions still unresolved inside the current admissible region. This differs from ranking candidates by general precision, sample size or ecological prominence. A measurement can be scientifically interesting and still have zero NOV for the ambiguity at hand.

The sequential step is essential. After one observation, the admissible region changes, so the value of every remaining candidate can change. A static initial ranking can waste budget by continuing to collect redundant measurements. RACH-SEQ instead recalculates the information state after each realised outcome. Its stopping rule also makes negative results actionable: if residual degeneracy remains but every candidate has zero validated NOV, the declared observation vocabulary—not merely the current sample size—is insufficient.

The G2 benchmark was designed to test selection rather than observation sufficiency. A candidate set containing only direct resolvers would show that informative measurements can solve confounds, but not that the method distinguishes them from wasted measurements. Adding valid mechanism-independent nuisance candidates created a controlled competition for budget. The resulting approximately 84-fold difference at budget four is therefore not cosmetic. It measures how often the uninformed policy spent scarce observations on candidates that had no designed mechanism information after both policies had enough budget to resolve the edge structure on average.

The benchmark nevertheless defines a narrow claim. RACH-SEQ outperformed uniform random order over one frozen family of random confounded systems. This does not prove global optimality, superiority to every Bayesian design method, or performance under every stochastic ecological simulator. Candidate vocabularies were finite and explicitly represented. The nuisance measurements were independent of mechanisms rather than subtly correlated proxies. Richer baselines and misspecification challenges remain future work.

Admissibility is always relative to a declared mechanism vocabulary, parameter prior, constraint grammar, observation map, discrepancy and tolerance. An omitted mechanism cannot be recovered by retaining the accepted set. A predictive partition must also be identified before stored-region NOV can be computed. When outcomes overlap, are incomplete or require an unmodelled process, the honest result is non-estimability until an additional predictive model is supplied.

Synthetic validation is appropriate to the present claim because the hidden mechanism, candidate information structure and outcome timing must be controlled to test truth leakage and selection behaviour. A natural-system application could demonstrate usability but could not reveal whether the selected measurement was optimal relative to an unknown causal truth. The absence of new empirical data is therefore a boundary, not a missing validation layer: this paper validates an observation-selection algorithm under known controlled conditions and does not claim empirical discovery.

The practical output for ecologists is a disciplined sequence:

```text
declare mechanisms and constraints
→ retain compatible explanations
→ quantify residual mechanism uncertainty
→ verify candidate predictive outcomes
→ select the maximum-current-NOV measurement
→ condition and repeat
→ stop when resolved, budget-limited or information-limited.
```

This reframes causal ambiguity from a reason to force a winner or postpone inference into a quantitative experimental-design problem.

## Figure captions

**Figure 1. Admissible-set reporting under controlled confounding.** A compact synthetic example contrasts a single low-mass MAP switch combination with the full RACH accepted region. Panels report model-ranking mass, causal admissibility and degeneracy, mechanism-equivalence structure, validated NOV for candidate measurements and the change after a confound-breaking observation. The figure diagnoses inferential behaviour and is not a natural-system mechanism claim.

**Figure 2. Truth-peek-free sequential observation selection.** Frozen G2 results compare RACH-SEQ, which selects the remaining candidate with maximum current validated NOV, with a matched uniform random-order policy. Panels show convergence, fraction of initial confounding edges resolved, observations used and mechanism-independent nuisance measurements selected across budgets 0–4. Error bars are sample standard deviations across five predeclared seeds. Hidden-truth false exclusion was zero in every policy-by-budget cell. The budget-four nuisance-selection panel highlights 1.169 selections under random order versus 0.014 under RACH-SEQ, an 83.5-fold difference.

**Figure 3. NOV information identity and calibration.** Left, resolvability gains obtained by filtering the current deterministic admissible region are compared with fresh re-inference for six quantitative observations. Right, predictive EVSI/NOV is compared with realised resolvability gain across controlled hidden truths; individual outcomes and candidate-wise mean realised gains are distinguished.

**Figure S1. Known-truth self-consistency.** Synthetic switch-state recovery under predeclared pattern-noise strata. The figure tests whether generating switches remain admissible. Confounded alternatives are not required to disappear from a deliberately non-identifying pattern.

## References

- Beaumont, M.A., Zhang, W. & Balding, D.J. 2002. Approximate Bayesian computation in population genetics. *Genetics* 162: 2025–2035.
- Beaumont, M.A. 2010. Approximate Bayesian computation in evolution and ecology. *Annual Review of Ecology, Evolution, and Systematics* 41: 379–406.
- Canessa, S., Guillera-Arroita, G., Lahoz-Monfort, J.J., Southwell, D.M., Armstrong, D.P., Chadès, I., Lacy, R.C. & Converse, S.J. 2015. When do we need more data? A primer on calculating the value of information for applied ecologists. *Methods in Ecology and Evolution* 6: 1219–1228.
- Chaloner, K. & Verdinelli, I. 1995. Bayesian experimental design: a review. *Statistical Science* 10: 273–304.
- Csilléry, K., Blum, M.G.B., Gaggiotti, O.E. & François, O. 2010. Approximate Bayesian computation in practice. *Trends in Ecology & Evolution* 25: 410–418.
- Grimm, V., Revilla, E., Berger, U., Jeltsch, F., Mooij, W.M., Railsback, S.F., Thulke, H.-H., Weiner, J., Wiegand, T. & DeAngelis, D.L. 2005. Pattern-oriented modelling of agent-based complex systems: lessons from ecology. *Science* 310: 987–991.
- Hartig, F., Calabrese, J.M., Reineking, B., Wiegand, T. & Huth, A. 2011. Statistical inference for stochastic simulation models: theory and application. *Ecology Letters* 14: 816–827.
- Raiffa, H. & Schlaifer, H. 1961. *Applied Statistical Decision Theory.* Harvard University Press, Boston.
- Robert, C.P., Cornuet, J.-M., Marin, J.-M. & Pillai, N.S. 2011. Lack of confidence in approximate Bayesian computation model choice. *Proceedings of the National Academy of Sciences* 108: 15112–15117.
