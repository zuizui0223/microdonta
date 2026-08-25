# RACH — Causal Admissibility, Degeneracy, and Observation Design

> **Version**: 2.1 — theorem-first RACH mainline  
> **Worked example**: Izu Islands *Campanula microdonta* system. Older literature may refer to the broader *C. punctata* complex.  
> **Mathematical foundations**: see [`docs/rach_mathematical_foundations.md`](rach_mathematical_foundations.md) for Propositions 1–7 and the information-theoretic NOV result.

---

## Overview

RACH is a **causal admissibility and degeneracy framework** for ecological mechanism inference.
It does not select a single best mechanism simply because a ranking can be computed, and it does not claim that an admissible mechanism is the true mechanism in nature.

RACH asks:

> Under the current biological constraints and independent observations, which latent causal mechanisms remain admissible, how much mechanism uncertainty remains, which mechanisms are observationally replaceable, and what observation would remove the most remaining uncertainty?

The framework itself is not ABC, ABM, or pattern-oriented modelling. Those can be computational components used to approximate the admissible region. The inferential objects are the admissible causal region, causal admissibility, causal degeneracy, causal resolvability, replaceability/equivalence structure, and next-observation value.

```text
observation contract
→ A_epsilon
→ CA / D_RACH / R_RACH / CRC
→ mechanism-equivalence structure
→ validated NOV/EVSI
→ RACH-SEQ
```

Where an ecological output has an exact positive factorisation such as `W=F*E`, the N1–N4 identifiability gate precedes this sequence. That theorem layer and RACH are complementary: the theorem states when an observation class cannot identify a channel; RACH reports the surviving explanation set and designs the observation that would reduce the ambiguity.

---

## 1. The RACH object

A RACH analysis is specified as

```text
RACH = (X, Y, Theta, S, G, f, P_sim, P_obs, d, epsilon, pi, A_epsilon)
```

with derived quantities `CA`, `D`, `R`, `OC`, replaceability/equivalence structure, and `NOV`.

### 1.1 Spaces and maps

| Symbol | Meaning | Campanula example |
|---|---|---|
| `X` | fixed ecological context, not an ABC target | island isolation, observed pollinator context |
| `Y` | independent observation space | source-supported trait gradients |
| `Theta` | latent ecological parameter space | costs, benefits, demographic slopes |
| `S` | finite mechanism-switch space `{0,1}^K` | guide attraction, selfing syndrome, common cause, substitution |
| `G` | pre-data biological feasibility grammar | sign/range/compatibility constraints |
| `f` | declared generative dynamics | phenomenological or ABM backend |
| `P_sim`, `P_obs` | maps into a common observation/pattern space | ordinal gradients or measured quantitative summaries |
| `d`, `epsilon` | predeclared discrepancy and tolerance | weighted pattern mismatch |
| `pi` | prior over `(theta,s)` | fixed before outcome inspection |

### 1.2 The admissible causal region

For fixed context `x_obs` and independent observations `y_obs`, define

```text
A_epsilon(y_obs, x_obs)
= { (theta,s) in Theta x S :
      G(theta)=1
      and d(P_sim(f(x_obs;theta,s)), P_obs(y_obs)) <= epsilon }
```

`A_epsilon` is the central inferential object. ABC is one way to approximate it by Monte Carlo sampling; RACH is not defined by ABC itself.

The evidence-role boundary is mandatory:

- `input_context`: may enter `f`, never the acceptance distance;
- `observed_target`: independent data allowed to enter `d`;
- `diagnostic_only`: checked after inference, not used for acceptance;
- `future_observation`: candidate observation used for observation design;
- hypothesis-derived predictions are never recycled as independent `y_obs`.

This separation blocks the circular operation “assume the mechanism’s predicted pattern, then use that same pattern to identify the mechanism.”

### 1.3 Campanula observation space

The current prospective Campanula example uses source-supported ordinal directions along the isolation axis as the primary observed pattern class. Pairwise endpoint displays, predicted syndromes, and internally generated genetic proxies are not automatically independent observations. Quantitative future assays may enter only after their measurement map is declared.

---

## 2. Core RACH quantities

### 2.1 Causal admissibility

For switch `j`,

```text
CA_j = P(s_j=1 | A_epsilon).
```

`CA_j` is the conditional mass of the admissible region in which mechanism `j` is active. It is not a p-value and not proof of causal truth.

Interpretation is relative to the declared mechanism vocabulary, prior, constraints, simulator, observation map, distance, and tolerance. A mechanism omitted from `S` cannot be recovered by RACH.

Code: `causal_model.causal_admissibility.causal_admissibility()`; package-level callable `compute_causal_admissibility()`.

### 2.2 Causal degeneracy

```text
D_RACH = H(S | A_epsilon).
```

For `K` binary switches,

```text
0 <= D_RACH <= K.
```

High `D_RACH` is not a failed analysis. It is the reportable statement that the current observations leave many mechanism combinations compatible with the declared system.

### 2.3 Causal resolvability

```text
R_RACH = 1 - H(S | A_epsilon) / K
       = 1 - D_RACH / K.
```

The denominator is the maximum switch entropy `K`, not the prior entropy. This guarantees `R_RACH in [0,1]` even when event conditioning increases entropy relative to a non-uniform prior.

- `R=0`: maximum unresolved mechanism uncertainty;
- `R=1`: one mechanism combination remains;
- intermediate values: partial resolution.

### 2.4 Observation contribution

For an already collected observation pattern `o_k`,

```text
OC_k = R_RACH(O) - R_RACH(O \ {o_k}).
```

`OC_k` is pattern-level and joint over the full switch vector. It may be negative: removing a noisy, contradictory, or over-constraining observation can increase resolvability. Correct leave-one-out calculation requires re-acceptance from all evaluated draws because dropping one pattern may admit simulations that were previously rejected.

### 2.5 Causal replaceability and mechanism equivalence

Marginal admissibility alone does not reveal whether two mechanisms substitute for each other. RACH therefore also reports the mechanism-equivalence structure of current `A_epsilon`:

- pinned mechanisms;
- free mechanisms;
- confounding edges / coupled mechanism pairs;
- logical relations supported by the admissible region;
- replaceability / ablation cost (CRC).

The point is structural: two mechanisms can each have substantial `CA_j` because either can reproduce the same observation, not because both are independently identified.

---

## 3. Validated next-observation value

### 3.1 Predictive observation map

Let `Q` be a candidate future observation. A publication-level RACH NOV requires a predictive distribution for `Q` under the **current** admissible region.

For a deterministic stored-region implementation, candidate outcomes must form a mutually exclusive and exhaustive partition of current `A_epsilon`. Then

```text
Pr(Q=q | A_epsilon)
```

is the fraction of current admissible mass predicting outcome `q`.

If outcome maps overlap, are incomplete, or required simulator outputs are missing, the stored region does not identify this predictive distribution. In that case `next_observation_evsi` reports the validated EVSI as **not estimable**. A declared prior is not silently substituted and relabelled as validated NOV.

### 3.2 NOV is normalized mutual information

For a verified predictive map,

```text
NOV(Q)
= E_Q[ R_RACH(A_epsilon | Q) - R_RACH(A_epsilon) ]
```

and therefore

```text
NOV(Q)
= [H(S | A_epsilon) - H(S | A_epsilon,Q)] / K
= I(S;Q | A_epsilon) / K.
```

This identity is the operational meaning of next-observation value in the RACH mainline: the value of a candidate measurement is the fraction of the maximum `K` mechanism bits that the measurement is expected to remove from the current admissible region.

Consequently,

```text
0 <= NOV(Q) <= 1 - R_RACH(A_epsilon) <= 1.
```

and

```text
NOV(Q)=0
iff I(S;Q | A_epsilon)=0,
```

so a zero-value observation is one that carries no information about the remaining mechanism vector under the current admissible region.

The maximum residual gain `1-R_RACH` is attained exactly when observing `Q` reduces the remaining switch entropy to zero.

A particular realised outcome can decrease `R_RACH`; the theorem concerns the coherent **predictive mean** over the current admissible-region pushforward. Hence validated expected NOV is non-negative even though realised gain is not guaranteed to be.

### 3.3 Exact stored-region filtering

If `f` is deterministic given `(x_obs,theta,s)`, a fresh inference conditioned on observed `Q=q` accepts exactly

```text
A_epsilon | {Q=q}.
```

Therefore the conditional region can be obtained by filtering stored admissible draws rather than rerunning the simulator. `causal_model/nov_calibration.py` checks this identity against fresh re-inference in controlled systems.

The implementation in `causal_model/nov_evsi.py` also computes the empirical joint table `(S,Q)` independently and regression-checks

```text
EVSI = I(S;Q|A_epsilon)/K.
```

### 3.4 Legacy heuristic boundary

The repository historically contained a target-switch ambiguity score called `next_observation_value`. That score is useful only as a heuristic compatibility helper when no predictive outcome model exists.

It is now exposed explicitly as

```text
heuristic_next_observation_value
```

and is not part of the primary package `__all__`. The publication-level function is

```text
next_observation_evsi
```

which refuses to manufacture a validated EVSI from an unidentified outcome distribution.

---

## 4. RACH-SEQ: sequential observation design

Single-shot NOV asks which one observation is valuable now. RACH-SEQ closes the loop:

```text
A_0 <- current A_epsilon
for t = 1..budget:
    recover mechanism-equivalence structure of A_{t-1}
    if no confounding edge remains: stop
    recompute candidate predictive distributions from A_{t-1}
    rank verified candidates by current NOV = I(S;Q | A_{t-1}) / K
    use normalized edge-cut fallback only when NOV is not estimable
    take the highest-valued available observation
    condition on the realised outcome
    A_t <- A_{t-1} | outcome
```

For each candidate with a verified current-region outcome partition, RACH-SEQ uses

```text
Pr(Q=q | current A_epsilon)
```

at the current step, not a stale probability frozen at step 0.

For every candidate with a verified stored-region outcome partition, RACH-SEQ uses exactly the same validated objective as single-shot NOV: `I(S;Q|A)/K`. A field-design candidate whose outcome map does not identify that quantity may still be ranked by the explicit compatibility score `expected_edge_cuts / current_edge_count`. The score source is recorded in each sequence step. A predeclared outcome prior may be used only to materialise an otherwise unavailable outcome in that fallback path; neither the fallback score nor its prior is relabelled as validated NOV.

In controlled benchmarks, hidden synthetic truth is used only after ranking to materialise the realised observation. Feeding truth into the candidate predictive distribution before ranking is prohibited.

---

## 5. Epistemic-role separation

RACH separates what is assumed, observed, inferred, and designed.

| Role | Function | Allowed in acceptance distance? |
|---|---|---:|
| biological axiom / model equation | declares simulator family | no |
| pre-data constraint `G` | removes infeasible parameter space | no |
| fixed context `x_obs` | simulator input | no |
| independent observation `y_obs` | restricts `A_epsilon` | yes |
| diagnostic / hypothesis prediction | posterior check | no |
| future observation | NOV / RACH-SEQ candidate | not until collected |

A candidate measurement can be scientifically attractive yet have no validated stored-region EVSI if its predictive map has not been declared. That is an information-model limitation, not permission to invent a probability.

### Campanula prospective design

For Campanula, candidate observations should attack specific unresolved links rather than merely repeat correlated endpoints. Examples include:

- masked/unmasked guide assays with visitor-specific pollen transfer;
- autonomous-selfing / bagging assays;
- independent neutral-marker structure along isolation;
- direct tests of small-pollinator functional substitution.

These are prospective observation designs, not empirical validation already contained in the published record.

---

## 6. Validation strategy

The main submission separates four validation questions.

### 6.1 Known-truth recovery

Generate controlled synthetic observations under known switch states and test recovery/calibration. This is simulator self-consistency or misspecification robustness depending on the generator/inference backend pair; it is not proof of real ecological causation.

### 6.2 Generality and error control

The frozen G2 random-system benchmark measures, over a preregistered controlled family:

- convergence to no remaining confounding edges;
- fraction of confounding edges resolved;
- observations used under each budget;
- hidden-truth false-exclusion rate.

There is no favourable-result acceptance threshold. The frozen result is reported whether favourable, null, or adverse.

### 6.3 NOV calibration

For validated candidates, check:

1. stored-region filtering vs fresh deterministic re-inference;
2. `EVSI = I(S;Q|A_epsilon)/K`;
3. calibration of predicted expected value against realised gains across controlled truths.

### 6.4 Sensitivity

Vary priors, `epsilon`, distance/weight choices only as sensitivity analysis. The predeclared main setting remains the reported inference; the setting that maximizes `R_RACH` is never selected post hoc.

---

## 7. Relationship to the N1–N4 channel theorem

RACH does not make a rich simulator theorem-exact. The theorem layer requires a declared ecological factorisation and observation map.

For positive

```text
W(z)=F(z)E(z),
```

N1 shows that net-only observations cannot distinguish an `F` change from the same multiplicative `E` change. N2 shows that observing net performance plus either exact channel identifies the other. N3/N4 show that a proxy is identifying for relative change only under stable or calibrated conversion.

When N1 says the current observation class is structurally non-identifying, RACH does not try to recover a winner anyway. It retains the compatible explanations and asks which observation has information about the unresolved mechanism vector.

The current exact ecological bridge is one-step expected retained juvenile recruitment. Long-run invasion growth, persistence, and endpoint trait-space geometry remain extension-required unless separately factorised.

---

## 8. Software boundary

Primary RACH package callables are:

```text
compute_causal_admissibility
causal_degeneracy
causal_resolvability
causal_replaceability_cost / crc_profile
mechanism_equivalence_structure
next_observation_evsi
run_rach_seq
rach_summary
```

Canonical submodules such as `causal_model.causal_admissibility` and `causal_model.rach_seq` remain importable and are not shadowed by root-level functions.

Supplementary ABMs, structure discovery, Streamlit, provisional ecological-rule examples, and the optional attraction simulator do not define the publication API.

---

## 9. Manuscript framing

A compact statement of the method is:

> RACH replaces forced mechanism selection with an admissible explanation set. It quantifies residual mechanism entropy, reports replaceability structure, and converts unresolved mechanism uncertainty into an observation-design problem. When a candidate observation has a predictive map over the current admissible region, its validated next-observation value is exactly the normalized mutual information `I(S;Q|A_epsilon)/K`; RACH-SEQ recomputes that information state after each collected observation.

The scientific stopping rule is therefore not “a model won.” It is one of:

- the mechanism-equivalence structure has been resolved at the declared resolution;
- the observation budget is exhausted;
- no available candidate has an identified or useful resolving observation map;
- the declared model family itself requires revision.
