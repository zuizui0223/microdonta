# Mechanism-Resolving Observation Design — publication mainline

Status: normative development boundary for the *Methods in Ecology and Evolution* methods submission.

The project has one primary scientific product:

> Given observations compatible with multiple declared ecological mechanism programs, retain the admissible explanations, quantify residual mechanism uncertainty, and select the next measurement with maximum current information about that uncertainty.

The separate mechanistic-evidence / identification-boundary Perspective is owned by `zuizui0223/boundary`. Its theory, manuscript, figures and reviewer assets are external to this repository.

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
→ A_epsilon: admissible mechanism region
→ marginal admissibility / mechanism entropy D / resolvability R / replaceability
→ mechanism-equivalence structure
→ singleton observation information value V(Q)=I(S;Q | A_epsilon)/K
→ maximum-current positive-singleton selection
→ condition A_epsilon and recompute
```

### Output

The default output is not a best mechanism. It is:

- the surviving explanation set and mechanism-admissibility profile;
- joint entropy/resolvability and replaceability diagnostics;
- unresolved mechanism-equivalence structure;
- validated singleton candidate information values where predictive partitions are estimable;
- a best immediate candidate when the complete declared singleton candidate set is estimable and contains positive validated information;
- explicit distinction among target resolution, budget limitation, prediction limitation and zero-singleton greedy stopping;
- a sequence-level information-limit statement only when a coherent joint candidate predictive model has also shown zero joint mechanism information.

## Publication spine

```text
admissible mechanism region
→ observation information value
→ exact condition for adaptive recomputation value
→ controlled truth-peek-free selection challenge
→ G2 policy and observation-budget results
→ reproducible software and anonymous reviewer evidence
```

The active manuscript contains no natural-system causal claim. Synthetic validation is the correct evidence object for the algorithmic selection claim because hidden mechanism truth, candidate information structure and outcome timing can be controlled.

## Predictive-probability boundary

A candidate outcome distribution is derived from the **current** admissible region when its outcomes form a verified mutually exclusive and exhaustive partition. Hidden benchmark truth is never used as a predictive prior.

For a verified singleton candidate,

```text
V(Q)
= sum_q Pr(q | current A_epsilon)
    [R(A_epsilon | Q=q) - R(A_epsilon)]
= I(S;Q | A_epsilon) / K.
```

Thus `0 <= V(Q) <= 1-R(A_epsilon)`.

`V(Q)=0` exactly when that singleton candidate carries no information about residual mechanism identity under current `A_epsilon`. If outcomes overlap, are incomplete or require unavailable outputs, validated information value is non-estimable. The method does not silently substitute a declared prior and relabel it as validated value.

An explicit normalized edge-cut fallback can remain available for sequential steps lacking an estimable predictive partition, but every such step must record the fallback source and must not call the score validated observation information value.

## Sequential design rule

At every validated-information step:

1. compute `I(S;Q|current A_epsilon)/K` for each estimable remaining singleton candidate;
2. select the candidate with maximum positive current validated information value when the relevant candidate comparison is fully identified;
3. reveal or collect its outcome only after selection;
4. condition the accepted region;
5. recompute all singleton candidate probabilities and information values.

Stopping and limitation states are not interchangeable:

- the **declared design target** may be resolved even while residual entropy remains in mechanism dimensions outside that target;
- the **observation budget** may be exhausted even though a best future candidate is known;
- if one or more declared remaining candidates are non-estimable, the singleton comparison is **prediction-limited**. Zero values among the estimable subset do not establish even a complete one-step result for the full candidate vocabulary, and any positive candidate is only provisionally best among the estimable subset;
- if every declared remaining singleton candidate is estimable and all validated values are zero, the current positive-singleton greedy policy has a **validated one-step information stop**: no individual next candidate has positive immediate mechanism information;
- zero singleton values do **not** prove sequence-level impossibility. Complementary candidates can have `I(S;Q1)=I(S;Q2)=0` but `I(S;Q1,Q2)>0`;
- a **sequence-information limit** for the declared candidate vocabulary requires a coherent joint predictive model and zero joint information `I(S;Q_C|A_epsilon)=0`. By data processing, no transcript composed solely of those candidate outcomes can then inform `S`.

Compatibility fallback selection can still occur in historical/backend workflows, but fallback availability remains a separately labelled operational layer and does not alter the validated-information claim. Positive joint information among zero-valued singleton candidates indicates a non-myopic design problem; it does not by itself choose an acquisition order.

## Exact condition for when recomputation adds value

Recomputation is not defended merely by saying that rankings *may* change. Fix a first observation `X` and let `U_q(x)` be the second-step mechanism-information value of remaining candidate `q` after outcome branch `X=x`.

The adaptive second-step value is

```text
V_adapt = E[max_q U_q(X)],
```

whereas the strongest possible precommitted second measurement achieves

```text
V_static = max_q E[U_q(X)].
```

Theorem A1–A2 in `docs/adaptive_recomputation_theorem_2026-09-03.md` proves `V_adapt >= V_static`, with equality **if and only if** at least one remaining candidate is branchwise optimal on every positive-probability first-outcome branch. Therefore adaptive recomputation has strict expected value exactly when the intersection of the branchwise argmax sets is empty.

This is stronger than comparison with random ordering. A deterministic four-world witness gives `1.0` bit of adaptive second-step value versus `0.5` bits for the best precommitted candidate; an exhaustive three-world check shows that this two-branch deterministic rank-switch witness is minimal in the declared class.

The result also places a ceiling on the claim: recomputation is not universally useful. If one candidate is best in every branch, a fixed second measurement matches the adaptive value. The theorem does not prove that greedy maximum-current information is globally optimal over arbitrary multi-step trees; the zero-singleton XOR witness now also shows that a positive-only singleton rule can stop before an informative multi-observation bundle. Global sequence design would require additional structural conditions or a non-myopic objective.

## Frozen G2 selection challenge

The frozen protocol contains one or two random confounds, explicit resolving measurements and exactly two mechanism-independent binary nuisance candidates per system. It compares matched policies on identical generated systems, hidden truths, candidate sets and budgets.

Active terminology:

```text
information-guided  maximum current V(Q)
random_order        uniform random remaining candidate
```

The machine-readable protocol retains historical protocol and policy identifiers for exact provenance. Those labels are not the active method name.

Hidden truth is materialised only after a candidate is selected. The random-order policy is a selection baseline, not an alternative causal model. The comparison is descriptive, not an acceptance gate; favourable, null or adverse frozen results must all be reported.

### Headline frozen values

At budget two, information-guided design achieved 1.000 edge resolution and 0.990 convergence, versus 0.6045 and 0.435 under random order. Hidden-truth false exclusion was zero.

At budget four, random order selected 1.169 nuisance measurements per system versus 0.014 under information-guided design:

```text
1.169/0.014 = 83.5-fold,
1-0.014/1.169 = 98.8% reduction.
```

The absolute counts must accompany the fold ratio. The phrase `mechanism-independent nuisance measurement` is preferred over `noise observation`, which could be confused with measurement error.

## Public API boundary

The advertised package-level API is descriptive:

```text
compute_admissible_mechanisms
mechanism_entropy
mechanism_resolvability
mechanism_resolution_summary
mechanism_equivalence_structure
observation_information_value
sequential_observation_design
```

Historical implementation labels may remain only as private compatibility backends or frozen-provenance identifiers. They do not define the scientific API.

## What is not the mainline

The following do not set development priority for this methods paper:

- the mechanistic-evidence / identification-boundary Perspective now owned by `zuizui0223/boundary`;
- natural-system mechanism claims not directly supported by new evidence;
- provisional ecological-rule discovery;
- causal-structure discovery;
- optional attraction-trait backends;
- Streamlit/UI work;
- external eco-genetic-criticality work.

## Active development order

1. Maintain the frozen G2 and G5 evidence without retuning.
2. Keep manuscript, Supporting Information, manifest, reviewer bundle and figure captions aligned to the methods-only spine.
3. Keep the public vocabulary descriptive and free of retired method branding.
4. Add no empirical mechanism claim without a new explicit evidence audit.
