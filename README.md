# Mechanism-Resolving Observation Design

[![CI](https://github.com/zuizui0223/mrod/actions/workflows/ci.yml/badge.svg)](https://github.com/zuizui0223/mrod/actions/workflows/ci.yml)

**Mechanism-Resolving Observation Design** is the software and reproducibility project for a *Methods in Ecology and Evolution* methods paper on choosing the next observation that best reduces unresolved ecological mechanism ambiguity.

The separate mechanistic-evidence / identification-boundary Perspective lives in **[zuizui0223/boundary](https://github.com/zuizui0223/boundary)**. Its active theory, manuscript, figures and reviewer assets are not part of this project.

## Scientific question

When several ecological mechanisms remain compatible with the observations already collected,

> **Which measurement should be acquired next to reduce the remaining mechanism ambiguity?**

The workflow is deliberately set-valued rather than winner-first:

```text
declare mechanisms, parameters, constraints and evidence roles
→ retain the admissible mechanism region
→ quantify residual mechanism entropy / resolvability / replaceability
→ score verified candidate observations by normalized mechanism information
→ select the maximum-current-value candidate
→ reveal its outcome only after selection
→ condition the region and recompute
→ stop when the declared target is resolved or budget is exhausted,
  pause the positive-singleton greedy policy when every estimable singleton value is zero,
  and report prediction limits when candidate values remain non-estimable
```

## What kind of uncertainty is this?

MROD targets **multiplicity of compatible mechanism explanations**, not generic uncertainty.

```text
rejecting a null hypothesis        != resolving which non-null mechanism remains
small residuals / excellent fit    != unique mechanism identity
more replication                   != a new identification direction
causal counterfactual identification != complete mechanism decomposition
```

Replication and precision can reduce sampling uncertainty, and causal estimands retain their own identification requirements. MROD asks a different question: conditional on the declared model family and current evidence, which candidate observation is predicted to separate the mechanism distinctions that still remain?

The detailed scope audit is in `docs/conceptual_scope_mechanism_ambiguity.md`.

## Admissible mechanism region

For fixed context `x_obs`, observed targets `y_obs`, parameters `theta`, mechanism vector `s`, biological constraints `G`, simulator `f`, pattern maps `P_sim,P_obs`, discrepancy `d` and tolerance `epsilon`,

```text
A_epsilon(y_obs, x_obs)
= { (theta, s) :
    G(theta)=1
    and d(P_sim(f(x_obs;theta,s)), P_obs(y_obs)) <= epsilon
  }.
```

The inferential object is the retained region, not its modal mechanism row.

For a binary mechanism vector `S in {0,1}^K`, define

```text
D = H(S | A_epsilon)
R = 1 - D/K.
```

`D` is residual mechanism entropy and `R` is normalized mechanism resolvability. Here `residual` means ambiguity remaining inside the admissible mechanism region; it is not a regression residual or an unexplained-variance term. Mechanism-equivalence and replaceability summaries describe additional structure within the same retained region.

`R` summarizes the concentration of the current declared mechanism distribution. Because that distribution already reflects the declared priors, pre-data constraints, context and accepted observations, `R` does not by itself attribute that concentration to the observations. Evidence attribution requires a declared pre-observation baseline and an entropy or mutual-information contrast relative to it.

## Observation information value

For a candidate observation `Q` whose outcomes form a verified mutually exclusive and exhaustive partition of the current admissible region,

```text
V(Q) = I(S;Q | A_epsilon) / K.
```

This is the publication-level **observation information value**. It is zero exactly when the candidate carries no information about residual mechanism identity represented in the current region.

Unlike current `R`, `V(Q)` is incremental conditional information: it asks what the candidate is expected to add beyond everything already encoded in the current admissible region. Candidate values can therefore depend on scientifically different prior or constraint specifications; when alternatives are plausible, ranking stability is a sensitivity-analysis result.

A candidate whose predictive outcome partition is unavailable is reported as non-estimable for this quantity. An external outcome prior is not silently substituted and relabelled as validated information value.

## Sequential observation design

The adaptive policy recomputes candidate value after every realised measurement:

```text
A_0 = current admissible region
for t = 0,1,...:
    compute V_t(Q)=I(S;Q | A_t)/K for each estimable candidate
    select the largest positive current validated value
    reveal the selected candidate's outcome
    condition A_t to form A_{t+1}
    recompute all remaining values
```

The stopping interpretation has several distinct levels:

- **declared target resolved:** stop the predeclared sequence; this need not imply full switch-vector entropy is zero;
- **budget exhausted:** stop for a resource reason, which is distinct from an information limit;
- **prediction-limited:** one or more declared remaining candidates are non-estimable; zero values among the estimable subset do not establish a limit for the full candidate vocabulary, and a positive value is only a provisional best among the estimable subset;
- **validated one-step information stop:** every declared remaining singleton candidate is estimable and all have `V_t(Q)=0`; then the current positive-singleton greedy rule has no informative immediate move;
- **sequence-information limit:** this stronger statement requires a coherent joint predictive model for the declared candidate vector and zero joint information `I(S;Q_C|A_t)=0`. Zero singleton values alone are not sufficient, because complementary measurements can each have zero marginal information yet carry positive information jointly.

An explicitly labelled structural or edge-cut fallback can remain available for compatibility workflows, but it is not relabelled as validated `I(S;Q|A_t)/K`. Likewise, positive joint information among zero-valued singletons indicates a non-myopic bundle/sequence problem; it does not by itself identify the best acquisition order.

## Public Python API

```python
from causal_model import (
    compute_admissible_mechanisms,
    mechanism_entropy,
    mechanism_resolvability,
    mechanism_resolution_summary,
    mechanism_equivalence_structure,
    observation_information_value,
    sequential_observation_design,
)
```

Publication-facing modules are:

```text
causal_model/admissible_mechanisms.py
causal_model/observation_value.py
causal_model/sequential_design.py
causal_model/mechanism_equivalence.py
causal_model/mechanism_replaceability.py
```

Historical implementation labels are retained only where needed for compatibility or frozen benchmark provenance; they are not the advertised scientific vocabulary. In particular, historical `counterfactual_ablation` helpers perform switch-OFF filtering inside an already computed admissible region; they do not by themselves identify causal intervention counterfactuals.

## Controlled validation

The frozen G2 benchmark evaluates an **information-guided sequential policy** against uniform random ordering on identical generated systems, hidden truths, candidate sets and observation budgets. Hidden truth is used only after a policy has selected a candidate, solely to materialise the realised outcome.

The frozen protocol identifier and stored policy key retain their historical labels for exact provenance. Active prose, figures and public software documentation use **information-guided sequential design**.

At budget two:

| outcome | information-guided | random order |
|---|---:|---:|
| initial confounding edges resolved | 1.000 | 0.6045 |
| systems converged | 0.990 | 0.435 |
| observations used | 1.505 | 1.821 |
| nuisance selections | 0.001 | 0.974 |

At budget four, both policies resolved all initial confounding edges on average. The information-guided policy selected `0.014` mechanism-independent nuisance measurements per system versus `1.169` under random order, an `83.5`-fold contrast (approximately `98.8%` fewer), while using `1.518` versus `2.673` observations. Hidden-truth false exclusion was zero in every policy-by-budget cell.

Exact frozen values remain in `paper/results/g2_frozen_v2_summary.json` and are not retuned during the naming migration.

## Evidence-role discipline

Every quantity is assigned one role before inference:

| Role | Use |
|---|---|
| `observed_target` | may enter the acceptance discrepancy |
| `input_context` | conditions the simulator but is not independent acceptance evidence |
| `diagnostic_only` | evaluates inference/software behaviour after fitting |
| `future_observation` | withheld as a candidate measurement |

A signed functional starting position such as `plant_trait - pollinator_functional_center` is an example of `input_context`: freeze it before outcome inspection and do not recycle it as an independent observed target.

## Repository roles

```text
causal_model/
  admissible_mechanisms.py       publication-facing admissible-region API
  observation_value.py           V(Q)=I(S;Q|A_epsilon)/K
  sequential_design.py           adaptive observation selection
  mechanism_equivalence.py       residual equivalence structure
  mechanism_replaceability.py    mechanism replaceability
  generality_sweep.py            frozen G2 benchmark generator

paper/
  manuscript.md                  active methods manuscript
  supporting_information.md      active SI
  submission_manifest.json       active evidence inventory
  g2_frozen_benchmark_protocol.json
  results/g2_frozen_v2_summary.json
  results/g5_reproducibility_summary.json
```

Supplementary ABM backends, adapters and archived exploratory material are not primary evidence unless explicitly listed in the submission manifest.

## Installation and checks

```bash
pip install -e ".[dev]"
python paper/check_submission_bundle.py
python paper/check_mee_submission.py
python scripts/check_repository_boundaries.py
pytest -q
```

## Scope

The methods paper validates observation selection over a declared frozen family of controlled confounded systems. It does not establish universal optimality, superiority to every Bayesian design method, a natural-system causal mechanism, or identification of intervention counterfactuals from accepted-row filtering. Admissibility and observation information value are always conditional on the declared mechanism vocabulary, parameter/prior structure, constraints, observation map, discrepancy and tolerance.
