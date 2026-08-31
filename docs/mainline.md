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
→ observation information value V(Q)=I(S;Q | A_epsilon)/K
→ maximum-current information-guided selection
→ condition A_epsilon and recompute
```

### Output

The default output is not a best mechanism. It is:

- the surviving explanation set and mechanism-admissibility profile;
- joint entropy/resolvability and replaceability diagnostics;
- unresolved mechanism-equivalence structure;
- the next candidate measurement and its validated observation information value;
- a stopping state when the budget is exhausted, the declared ambiguity is resolved, or no available candidate carries further identified mechanism information.

## Publication spine

```text
admissible mechanism region
→ observation information value
→ sequential recomputation
→ controlled truth-peek-free selection challenge
→ G2 policy and observation-budget results
→ reproducible software and anonymous reviewer evidence
```

The active manuscript contains no natural-system causal claim. Synthetic validation is the correct evidence object for the algorithmic selection claim because hidden mechanism truth, candidate information structure and outcome timing can be controlled.

## Predictive-probability boundary

A candidate outcome distribution is derived from the **current** admissible region when its outcomes form a verified mutually exclusive and exhaustive partition. Hidden benchmark truth is never used as a predictive prior.

For a verified candidate,

```text
V(Q)
= sum_q Pr(q | current A_epsilon)
    [R(A_epsilon | Q=q) - R(A_epsilon)]
= I(S;Q | A_epsilon) / K.
```

Thus

```text
0 <= V(Q) <= 1-R(A_epsilon).
```

`V(Q)=0` exactly when `Q` carries no information about residual mechanism identity under current `A_epsilon`. If outcomes overlap, are incomplete or require unavailable outputs, validated information value is non-estimable. The method does not silently substitute a declared prior and relabel it as validated value.

An explicit normalized edge-cut fallback can remain available for sequential steps lacking an estimable predictive partition, but every such step must record the fallback source and must not call the score validated observation information value.

## Sequential design rule

At every step:

1. compute `I(S;Q|current A_epsilon)/K` for each verified remaining candidate;
2. select the candidate with maximum positive current information value;
3. reveal or collect its outcome only after selection;
4. condition the accepted region;
5. recompute all candidate probabilities and information values.

The algorithm stops when the observation budget is exhausted, the declared confounding structure is resolved, or all available validated values are zero.

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
