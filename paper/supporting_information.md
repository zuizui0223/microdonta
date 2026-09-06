# Supporting Information

## Mechanism-Resolving Observation Design: information-theoretic selection of observations under ecological mechanism ambiguity

This Supporting Information accompanies the anonymised Research Article. It expands the admissible-region quantities, observation-information calculation, sequential design, frozen controlled benchmarks and reproducibility map. The separate mechanistic-evidence / identification-boundary Perspective is owned by the `boundary` repository and is not part of this submission.

---

## S1. Admissible mechanism regions and evidence roles

### S1.1 Admissible region

For switches `S in {0,1}^K`, parameters `theta`, pre-data constraint grammar `G`, simulator `f`, pattern maps `P_sim,P_obs`, discrepancy `d`, tolerance `epsilon`, observed targets `y_obs` and fixed context `x_obs`,

```text
A_epsilon
= {(theta,s): G(theta)=1 and
   d(P_sim(f(x_obs;theta,s)),P_obs(y_obs))<=epsilon}.
```

The finite implementation approximates this region by prior sampling and rejection. The retained region, not its modal switch row, is the inferential object.

### S1.2 Evidence-role contract

Every quantity is assigned one role before inference:

| Role | Use |
|---|---|
| `observed_target` | may enter the acceptance discrepancy |
| `input_context` | conditions the simulator but is not an independent target |
| `diagnostic_only` | evaluates inference or software behaviour after fitting |
| `future_observation` | withheld as a candidate measurement |

The same datum may not be silently used as context, acceptance evidence and independent validation.

### S1.3 Mechanism quantities

For switch `j`,

```text
CA_j=P(s_j=1|A_epsilon).
```

Joint mechanism entropy and resolvability are

```text
D=H(S|A_epsilon),
R=1-D/K.
```

A `K`-bit vector has entropy at most `K`, so `0<=D<=K` and `0<=R<=1`. Mechanism-equivalence and replaceability summaries are calculated from the same accepted switch rows and are not substitutes for the joint entropy.

---

## S2. Observation information value and sequential design

### S2.1 Predictive-partition requirement

For a finite candidate observation `Q`, its outcome maps must be mutually exclusive and exhaustive over the current accepted region. The predictive distribution is then the pushforward

```text
Pr(Q=q|A_epsilon).
```

If outcomes overlap, are incomplete or require unavailable simulator columns, validated stored-region observation information value is non-estimable. An external outcome prior is not silently substituted and relabelled as validated information value.

### S2.2 Information identity

Define expected resolvability gain

```text
V(Q)=E_Q[R(A_epsilon|Q)-R(A_epsilon)].
```

Then

```text
V(Q)
={H(S|A_epsilon)-H(S|A_epsilon,Q)}/K
=I(S;Q|A_epsilon)/K.
```

Therefore

```text
0<=V(Q)<=1-R(A_epsilon)<=1.
```

`V(Q)=0` exactly when the candidate measurement carries no information about residual mechanism identity under the current accepted region.

### S2.3 Sequential recomputation

At step `t`, the information-guided policy scores every candidate whose predictive partition is estimable by

```text
V_t(Q)=I(S;Q|A_t)/K.
```

It selects the largest positive current validated value when the relevant candidate comparison is identified, obtains the realised outcome only after selection, conditions `A_t` on that outcome, and recomputes all remaining predictive probabilities and information values.

The stopping interpretation depends on why no validated singleton selection is made:

- **declared target resolved:** the predeclared confounding or mechanism distinction has been resolved; this does not necessarily imply that all switch-vector entropy is zero;
- **budget exhausted:** observation cannot continue for a resource reason, which is distinct from an information limit;
- **prediction limit:** one or more declared remaining singleton candidates are non-estimable. Zero values among the estimable subset do not establish a complete one-step zero result for the full singleton candidate set, and a positive value identifies only a provisional best among the estimable candidates until the remaining outcome maps are supplied or the candidate set is explicitly narrowed;
- **validated one-step information stop:** every declared remaining singleton candidate has an estimable predictive partition and every validated `V_t(Q)=0`. This means the current positive-singleton greedy rule has no informative immediate move, not that candidate combinations are necessarily uninformative;
- **sequence-information limit:** this stronger statement requires a coherent joint predictive vector for the declared candidate outcomes and `I(S;Q_C|A_t)=0`. Zero singleton values alone are insufficient because complementary observations may carry mechanism information only jointly.

An explicitly named normalized edge-cut fallback is retained for compatibility workflows when a predictive partition is unavailable. Every step records its score source; fallback scores are not reported as validated observation information values and do not by themselves establish zero or positive candidate mutual information. Positive joint information among zero-valued singleton candidates indicates a non-myopic bundle/sequence problem rather than an in-principle information limit.

### S2.4 When recomputation has strict value

Recomputation is not assumed to improve every candidate family. For a two-step finite design, let `X` be the first observation and let `U_q(x)` denote the information value of remaining candidate `q` after branch `X=x`. The adaptive and strongest precommitted-static second-step values are

```text
V_adapt  = E[max_q U_q(X)],
V_static = max_q E[U_q(X)].
```

Then `V_adapt>=V_static`. Equality holds if and only if at least one candidate is branchwise optimal on every positive-probability first-outcome branch. Strict adaptive advantage occurs exactly when the intersection of those branchwise argmax sets is empty. This is a two-step finite-design result; it does not establish global optimality of a full multi-step greedy policy.

---

## S3. Frozen G2 observation-selection benchmark

### S3.1 Protocol and historical labels

The frozen machine-readable protocol retains the historical identifier `rach-g2-truth-peek-free-v2` and stored policy key `rach_seq` to preserve exact provenance. These strings are legacy record identifiers, not the active method name. In this manuscript and current software documentation the policy is called **information-guided sequential design**.

The protocol uses five predeclared seeds, 200 systems per seed, 1,500 prior draws per system, `K in {4,5,6}`, one or two disjoint confounds, random pre-data driver coefficients, two mechanism-independent binary nuisance candidates and budgets 0–4.

The information-guided and `random_order` policies receive identical systems, hidden truths, candidates and budgets. Hidden truth is used only after candidate selection to materialise the chosen outcome. The policy comparison is descriptive and has no favourable-result acceptance threshold.

### S3.2 Policy-specific means

**Table S1. Frozen policy means across five seeds.**

| Policy | Budget | Converged | Initial edges resolved | Mean observations | Mean nuisance selections | False exclusion |
|---|---:|---:|---:|---:|---:|---:|
| information-guided | 0 | 0.000 | 0.0000 | 0.000 | 0.000 | 0.000 |
| information-guided | 1 | 0.495 | 0.7480 | 1.000 | 0.000 | 0.000 |
| information-guided | 2 | 0.990 | 1.0000 | 1.505 | 0.001 | 0.000 |
| information-guided | 3 | 0.997 | 1.0000 | 1.515 | 0.011 | 0.000 |
| information-guided | 4 | 0.999 | 1.0000 | 1.518 | 0.014 | 0.000 |
| random_order | 0 | 0.000 | 0.0000 | 0.000 | 0.000 | 0.000 |
| random_order | 1 | 0.179 | 0.2995 | 1.000 | 0.580 | 0.000 |
| random_order | 2 | 0.435 | 0.6045 | 1.821 | 0.974 | 0.000 |
| random_order | 3 | 0.689 | 0.8650 | 2.386 | 1.152 | 0.000 |
| random_order | 4 | 0.940 | 1.0000 | 2.673 | 1.169 | 0.000 |

At budget two, across-seed sample SDs for the information-guided policy were 0.0079 for convergence, 0 for edge resolution, 0.0302 for observations and 0.00224 for nuisance selections. Random-order SDs were 0.0355, 0.0231, 0.0243 and 0.0277 respectively.

At budget four, the nuisance-selection ratio was

```text
1.169/0.014=83.5,
```

and the relative reduction was

```text
1-0.014/1.169=0.9880.
```

The manuscript reports the absolute counts with the ratio because a fold change is unstable when the denominator approaches zero. All 10,000 system–policy–budget records retained the hidden true explanation.

### S3.3 Post-frozen static initial-information diagnostic

The preregistered G2 comparison above was not changed. To determine whether its guided-versus-random advantage also demonstrated a practical benefit of adaptive recomputation, we subsequently ran a matched diagnostic with a stronger nonadaptive policy. `static_initial_information` ranks candidates once using their information values in the initial admissible region, discards candidates with non-positive initial value, and follows that fixed order without recomputation.

The diagnostic reused the same generator settings, five seeds, 200 systems per seed, hidden truths, candidate vocabularies, nuisance measurements and budgets. It is explicitly **post-frozen and non-preregistered**.

**Table S2. Claim-ceiling diagnostic comparing adaptive and static information ordering.**

| Budget | Policy | Converged | Initial edges resolved | Mean observations | Mean nuisance selections | False exclusion |
|---:|---|---:|---:|---:|---:|---:|
| 2 | information-guided adaptive | 0.990 | 1.0000 | 1.505 | 0.001 | 0.000 |
| 2 | static initial information | 0.990 | 1.0000 | 1.505 | 0.001 | 0.000 |
| 2 | random order | 0.435 | 0.6045 | 1.821 | 0.974 | 0.000 |
| 4 | information-guided adaptive | 0.999 | 1.0000 | 1.518 | 0.014 | 0.000 |
| 4 | static initial information | 0.998 | 1.0000 | 1.518 | 0.014 | 0.000 |
| 4 | random order | 0.940 | 1.0000 | 2.673 | 1.169 | 0.000 |

The two information-based policies are essentially indistinguishable on this family. The frozen G2 evidence therefore supports **information-guided candidate screening** much more strongly than an empirical performance gain from adaptive recomputation. The separate theorem in S2.4 specifies when branch-dependent changes in the best remaining measurement make recomputation strictly valuable.

---

## S4. Auxiliary controlled checks

### S4.1 Known-truth self-consistency

Under unchanged defaults, mean switch-state accuracy in the zero pattern-noise stratum was 0.6562 and recall of applicable true-ON switches was 1.000. Recall remained 1.000 in the 0.1 and 0.2 pattern-noise strata. Additional confounded explanations were allowed to survive, so exact-state accuracy was not expected to equal one.

**Table S3. Known-truth aggregate results.**

| Pattern noise | Cases | Accuracy | Precision | Recall | F1 | Mean admissibility error | R | D |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 8 | 0.6562 | 0.4792 | 1.0000 | 0.6042 | 0.3388 | 0.3699 | 2.5203 |
| 0.1 | 8 | 0.6875 | 0.5729 | 1.0000 | 0.6667 | 0.3359 | 0.4719 | 2.1123 |
| 0.2 | 8 | 0.7083 | 0.5417 | 1.0000 | 0.6429 | 0.2868 | 0.4238 | 2.3050 |

### S4.2 Stored-region conditioning

For six quantitative observations, gains obtained by filtering the stored deterministic accepted region equalled gains from fresh re-inference; the maximum absolute difference was zero.

| Candidate observation | Filter gain | Fresh gain |
|---|---:|---:|
| quantitative candidate 1 | 0.2684 | 0.2684 |
| quantitative candidate 2 | 0.1043 | 0.1043 |
| quantitative candidate 3 | 0.2581 | 0.2581 |
| quantitative candidate 4 | 0.0215 | 0.0215 |
| quantitative candidate 5 | 0.0672 | 0.0672 |
| quantitative candidate 6 | 0.2304 | 0.2304 |

Across eight candidate observations and four controlled truths per candidate, predicted information value correlated with mean realised gain at `r=0.7664`; mean absolute predictive-minus-realised difference was 0.0739.

### S4.3 Post-data candidate reprioritization witness

A separate minimal diagnostic checks the specific distinction between pre-data hypothesis vetting and a post-data next-observation calculation. This is not a benchmark against a named prior-art method and is not included in the frozen G2 performance claim.

Let the declared mechanism vector be `S=(A,B)` with the four binary states equally represented before current evidence. Candidate `Q_A` observes `A` exactly, so under the pre-data state distribution

```text
I(S;Q_A)=1 bit.
```

Candidate `Q_B*` is positive only for state `(A=0,B=1)`. Its positive outcome therefore has pre-data probability `1/4`, giving

```text
I(S;Q_B*)=H_2(1/4)=0.811278 bit.
```

The pre-data information ranking is therefore `Q_A > Q_B*`. Current evidence is then introduced that fixes `A=0` while leaving `B` balanced. On this restricted mechanism region, `Q_A` is constant and has zero mechanism information, whereas `Q_B*` becomes an exact observation of `B` and has one bit:

| Candidate | Pre-data MI | Post-data MI | Pre-data V | Post-data V |
|---|---:|---:|---:|---:|
| `observe_A` | 1.000000 | 0.000000 | 0.5000 | 0.0000 |
| `observe_B_when_A0` | 0.811278 | 1.000000 | 0.4056 | 0.5000 |

Thus the candidate ranking reverses after current evidence restricts the admissible mechanism region. The result is an existence witness only: it does not imply that pre-data multiple-working-hypotheses analysis is inferior, that any named prior-art method keeps a ranking fixed after data arrive, or that ranking reversal is universal. It demonstrates why MROD's **post-current-data** candidate values must be computed from the current mechanism region rather than inherited unchanged from a broader pre-data state distribution.

### S4.4 Mechanism-vocabulary normalization audit

A representation audit checks whether the `K` normalization can manufacture raw mechanism information or change the next-observation decision. The baseline vocabulary is `S=(A,B)` with four equally represented states. A redundant vocabulary appends `A_copy=A`, which is deterministically fixed by the existing state and therefore adds no scientific mechanism distinction.

For any deterministic redundant coordinate `U=g(S)`, the chain rules give

```text
H(S,U|A_epsilon)=H(S|A_epsilon),
I((S,U);Q|A_epsilon)=I(S;Q|A_epsilon).
```

The executable audit reproduces the following values:

| Quantity | Original `(A,B)` | Redundant `(A,B,A_copy)` |
|---|---:|---:|
| raw entropy `H(S)` | 2.0000 bit | 2.0000 bit |
| normalized `R` | 0.0000 | 0.3333 |
| raw MI `observe_A` | 1.000000 bit | 1.000000 bit |
| normalized `V(observe_A)` | 0.5000 | 0.3333 |
| raw MI `observe_A_and_B` | 0.811278 bit | 0.811278 bit |
| normalized `V(observe_A_and_B)` | 0.4056 | 0.2704 |
| candidate ranking | `observe_A` > `observe_A_and_B` | unchanged |

Thus a deterministic duplicate cannot create raw entropy or raw candidate information and cannot change the candidate ranking. It can change the displayed bounded values because the denominator changes from `K=2` to `K=3`. Normalized `R` and `V` are therefore interpreted within a predeclared mechanism vocabulary rather than as universal cross-vocabulary scales.

For reporting, residual entropy `D` is paired with `K`, candidate `I(S;Q|A_epsilon)` is reported in bits alongside normalized `V(Q)`, and absolute normalized scores are not compared across differently encoded mechanism vocabularies without an explicit vocabulary-sensitivity argument. This invariance applies to one-to-one recodings and deterministic redundant coordinates only; a genuinely uncertain subdivision or new mechanism changes the scientific target and may legitimately change raw information and candidate ranking. The audit is a representation diagnostic, not part of frozen G2 performance evidence.

### S4.5 Current resolvability versus evidence-gain audit

A separate audit checks whether positive current `R` can be interpreted as information supplied by the current observations. It cannot without a declared baseline, because the current admissible mechanism distribution already inherits its prior and pre-data constraints.

The controlled baseline contains one binary mechanism with

```text
P(S=1)=0.9,
P(S=0)=0.1
```

before any current observed target is applied. Its entropy is `H_2(0.9)=0.468996...` bit, so with `K=1` the absolute current resolvability is

```text
R=1-H_2(0.9)=0.5310.
```

The positive value is prior concentration rather than observational evidence. Two future candidates evaluated from exactly this current state separate current concentration from incremental information:

| Candidate | Raw MI | Normalized V | Expected R after observation |
|---|---:|---:|---:|
| direct observation of `S` | 0.468996 bit | 0.4690 | 1.0000 |
| mechanism-independent noise | 0.000000 bit | 0.0000 | 0.5310 |

Thus a current region can have `R>0` while a new observation has zero value. Candidate `V` is incremental because it is `I(S;Q|A_current)/K` relative to the current state.

The same audit shows that next-observation ranking can be prior-sensitive. With independent mechanisms `A` and `B`, a direct observation of a balanced coordinate has one bit of information, whereas a coordinate with prior `P(ON)=0.9` has `0.468996` bit. Under `P(A=1)=0.5, P(B=1)=0.9`, `observe_A` ranks first; after swapping these prior concentrations, `observe_B` ranks first.

This is not a claim that priors should be tuned to change the recommended observation. It is the opposite: the prior and pre-data constraint specification are part of the declared current knowledge state and should be fixed before candidate outcomes are inspected. When several prior specifications are scientifically plausible, ranking stability across them is a sensitivity-analysis result.

For current-evidence attribution, let `B` denote the declared pre-observation baseline and `O=o` the realised observation. The realised change is

```text
Delta_R(o)={H(S|B)-H(S|B,O=o)}/K,
```

which may be negative for a surprising outcome. Its expectation is

```text
E[Delta_R(O)]=I(S;O|B)/K>=0.
```

Accordingly, `R` is reported as **current resolvability**, not as information supplied by the observations unless a baseline contrast is explicitly defined. The audit is a conceptual sensitivity diagnostic and is not part of frozen G2 performance evidence.

---

## S5. Reproducibility and reviewer bundle

### S5.1 Frozen evidence

The anonymised reviewer bundle contains the manuscript and Supporting Information, frozen G2 protocol and result summary, frozen auxiliary-validation summary, figure inventory and generated figures, publication-facing observation-design implementation modules, benchmark generators, tests and a per-file SHA-256 manifest.

The static initial-information comparison is a post-frozen claim-ceiling diagnostic rather than preregistered G2 evidence. Its purpose is to constrain interpretation: the frozen G2 random-order contrast establishes information-guided screening, while the adaptive-recomputation theorem states the conditions under which recomputation itself has strict expected value. The S4.3 ranking-reversal witness, S4.4 vocabulary-normalization audit and S4.5 prior/evidence separation audit are separate controlled conceptual diagnostics and are not part of the frozen G2 performance evidence.

### S5.2 Explicit exclusions

The methods submission excludes the separate mechanistic-evidence / identification-boundary Perspective, prospective natural-system mechanism claims, provisional ecological-rule panels, causal-structure discovery, externally owned eco-genetic work, optional incubator backends and UI material.

### S5.3 Software validation

The release-candidate distribution is `mechanism-resolution-design` version 0.1.0. Clean validation rebuilds Figures 1–3 and Figure S1, reproduces frozen values, builds and installs the wheel outside the repository and checks the public API on Python 3.10–3.12.

## Figure S1 caption

**Figure S1. Known-truth self-consistency.** Synthetic switch-state recovery under predeclared pattern-noise strata. The benchmark checks that generating switches remain admissible; confounded alternatives are not required to disappear from a deliberately non-identifying target pattern.
