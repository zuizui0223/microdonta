# microdonta / RACH mainline

Status: normative development boundary for the MEE methods submission.

microdonta has one primary MEE scientific product:

> Given observations compatible with multiple declared ecological mechanism programs, retain the admissible explanations, quantify residual mechanism uncertainty, and select the next measurement with maximum current information about that uncertainty.

The N1–N4 channel-identifiability theorem family and bounded proxy-drift interval are a separate boundary-paper programme. They may motivate why non-identifiability matters, but they are not primary contributions or required evidence in the MEE manuscript.

## Product contract

### Input

1. a declared mechanism vocabulary `S`;
2. a pre-data biological constraint grammar `G(theta)`;
3. fixed ecological context `x_obs`;
4. independent observed targets `y_obs` and their observation map;
5. a predeclared distance and tolerance defining `A_epsilon`;
6. candidate future measurements whose predictive outcomes are obtained without access to benchmark truth or inspected outcomes.

### Core computation

```text
observation contract
→ A_epsilon: restricted admissible causal hypotheses
→ CA / D_RACH / R_RACH / CRC
→ mechanism-equivalence structure
→ validated NOV = I(S;Q | A_epsilon)/K
→ RACH-SEQ maximum-current-NOV selection
→ condition A_epsilon and recompute
```

### Output

The default output is not a best mechanism. It is:

- the surviving explanation set and causal-admissibility profile;
- joint degeneracy/resolvability and replaceability diagnostics;
- unresolved mechanism-equivalence structure;
- the next candidate measurement and its validated information value;
- a stopping state when the budget is exhausted, the declared ambiguity is resolved, or no available candidate carries further identified mechanism information.

## MEE publication spine

```text
RACH admissible mechanism set
→ information-theoretic NOV
→ sequential RACH-SEQ recomputation
→ controlled truth-peek-free selection challenge
→ G2 policy and observation-budget results
→ reproducible software and anonymous reviewer evidence
```

The active manuscript contains no natural-system causal claim. Synthetic validation is the correct evidence object for the algorithmic selection claim because hidden mechanism truth, candidate information structure and outcome timing can be controlled.

## Predictive-probability boundary

A candidate outcome distribution is derived from the **current** admissible region when its outcomes form a verified mutually exclusive and exhaustive partition. Hidden benchmark truth is never used as a predictive prior.

For a verified candidate,

```text
NOV(Q)
= sum_q Pr(q | current A_epsilon)
    [R(A_epsilon | Q=q) - R(A_epsilon)]
= I(S;Q | A_epsilon) / K.
```

Thus

```text
0 <= NOV(Q) <= 1-R_RACH(A_epsilon).
```

`NOV(Q)=0` exactly when `Q` carries no information about residual mechanism identity under current `A_epsilon`. If outcomes overlap, are incomplete or require unavailable outputs, validated NOV is non-estimable. The method does not silently substitute a declared prior and relabel it as validated EVSI.

The older target-switch score is retained only as `heuristic_next_observation_value`. An explicit normalized edge-cut fallback can remain available for RACH-SEQ steps lacking an estimable predictive partition, but every such step must record the fallback source and must not call the score validated NOV.

## RACH-SEQ rule

At every step:

1. compute `I(S;Q|current A_epsilon)/K` for each verified remaining candidate;
2. select the candidate with maximum positive current NOV;
3. reveal or collect its outcome only after selection;
4. condition the accepted region;
5. recompute all candidate probabilities and NOV values.

The algorithm stops when the observation budget is exhausted, the declared confounding structure is resolved, or all available validated NOV values are zero.

## Frozen G2 selection challenge

Protocol `rach-g2-truth-peek-free-v2` contains one or two random confounds, explicit resolving measurements and exactly two mechanism-independent binary nuisance candidates per system. It compares matched policies on identical generated systems, hidden truths, candidate sets and budgets:

```text
rach_seq      maximum current validated NOV
random_order  uniform random remaining candidate
```

Hidden truth is materialised only after a candidate is selected. The random-order policy is a selection baseline, not an alternative causal model.

The benchmark reports:

```text
budget
→ fraction of initial confounding edges resolved
→ convergence probability
→ observations used
→ nuisance measurements selected
→ hidden-truth false-exclusion rate
→ within-seed policy contrasts
```

The comparison is descriptive, not an acceptance gate. Favourable, null or adverse frozen results must all be reported.

### Headline frozen values

At budget two, RACH-SEQ achieved 1.000 edge resolution and 0.990 convergence, versus 0.6045 and 0.435 under random order. Hidden-truth false exclusion was zero.

At budget four, random order selected 1.169 nuisance measurements per system versus 0.014 for RACH-SEQ:

```text
1.169/0.014 = 83.5-fold,
1-0.014/1.169 = 98.8% reduction.
```

The absolute counts must accompany the fold ratio. The phrase `mechanism-independent nuisance measurement` is preferred over `noise observation`, which could be confused with measurement error.

## Separate boundary-paper programme

The non-blocking companion programme is:

```text
N1 net-only impossibility
→ N2 exact-channel sufficiency
→ N3 stable-proxy point identification
→ bounded calibration-drift partial identification
→ sign breakdown point and design rules
→ N4 unbounded-drift non-identifiability
```

If `q_1/q_0 in [1-delta,1+delta]`, the complementary-channel ratio lies in

```text
[rho_hat(1-delta), rho_hat(1+delta)]
```

with multiplicative width `(1+delta)/(1-delta)`. This result belongs to the boundary manuscript, not the primary MEE claim spine. Exact one-step ecological projection and prospective Campanula material support that separate programme.

## What is not the MEE mainline

The following may remain for a companion paper, Supplement, compatibility or future work, but do not set MEE development priority:

- N1–N4 proofs and bounded proxy-drift intervals as primary claims;
- exact ecological channel projection and prospective Campanula application;
- rule-transition or endpoint ABM panels;
- provisional ecological-rule discovery;
- structure discovery;
- optional attraction-trait backends;
- Streamlit/UI work;
- external eco-genetic-criticality work;
- the three izu-core empirical translation tracks.

## Public API boundary

The package-level public API remains RACH-first: `compute_causal_admissibility`, `causal_degeneracy`, `causal_resolvability`, replaceability/CRC, `mechanism_equivalence_structure`, `next_observation_evsi`, `run_rach_seq` and `rach_summary`.

Boundary-theory code may remain importable from explicit submodules but is not added to package-level `__all__` for the MEE release. Legacy structure scoring, edge-cut diagnostics and heuristic NOV remain compatibility utilities rather than the advertised product.

## Active development order

1. Maintain the frozen G2 and G5 evidence without retuning.
2. Keep the MEE manuscript, Supporting Information, manifest, reviewer bundle and figure captions aligned to the methods-only spine.
3. Develop bounded-drift theory and its manuscript on the separate boundary track.
4. Add no empirical mechanism claim to either paper without a new explicit evidence audit.
