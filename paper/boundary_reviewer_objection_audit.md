# Boundary paper: reviewer-objection audit

Status: submission-facing adversarial audit for `paper/boundary_manuscript_submission.md`.

The purpose of this file is not to inflate the novelty claim. It is to force likely objections into one of three categories: answered by the theorem, requiring an explicit qualification, or remaining an external empirical requirement.

## 1. “The product non-identifiability is trivial.”

**Response required in manuscript:** concede the algebra. The claim is not that products have multiple factorizations. The contribution is the ecological observation class that remains net-only even when apparently rich, the quantitative `k-1-r` equivalence-dimension rule, the calibration-transport family, the sharp joint set and breakdown factor, and the operational design/reporting rules.

**Pass criterion:** N1 is introduced through ecological measurement objects and then closed structurally by the product-preserving group action. Bellman–Åström, Rothenberg and Manski are acknowledged before the novelty sentence.

## 2. “The multiplicative model was chosen to manufacture the theorem.”

**Response required in manuscript:** lead with Schupp, Jordano & Gómez (2010), where seed dispersal effectiveness is explicitly `Quantity × Quality`; then show the independent pollination lineage (Rader; Ballantyne; Reynolds & Fenster) using visitation/rate × per-visit effectiveness.

**Pass criterion:** language says that the architecture recurs in ecology, not that all ecological fitness is multiplicative or that all cited quantities share identical biological semantics.

## 3. “Pollinator community service is a sum, not one product `W=FE`.”

**Response:** correct. At visitor type `m`, the contribution `S_m=V_mE_m` is a product and the product theorem applies within that interaction type. Community service `S=sum_m V_mE_m` adds an aggregation/allocation problem across visitor types. We do not claim that the two-factor theorem alone identifies the sum-of-products architecture.

**Pass criterion:** manuscript explicitly distinguishes within-type product ambiguity from across-type aggregation ambiguity. Degree, abundance or visitation alone are described as quantity-side descriptors/proxies, not as effective service.

## 4. “The `k-1-r` rule assumes every anchor is independent.”

**Response:** yes. A channel anchor is an independent direct observation of one latent channel coordinate (or one independent channel ratio in a before/after analysis). Redundant measurements do not reduce the dimension twice.

**Pass criterion:** theorem and table say `r independent channel anchors`; `0<=r<=k-1`; the final channel is recovered from the product only after `k-1` independent coordinates are fixed.

## 5. “You are mixing channel anchors with proxy calibration anchors.”

**Response:** they solve different missing-information problems. Channel anchors reduce the `k`-stage product-equivalence dimension. Calibration anchors measure `q_i` within regimes and therefore determine whether proxy conversion transports across a two-regime comparison.

**Pass criterion:** the manuscript has two separately named anchor ladders and never uses the 0/1/2 calibration ladder as if it were the `k-1-r` channel-dimension theorem.

## 6. “A change -> service -> dependency -> response chain is not necessarily multiplicative.”

**Response:** agreed. The `k`-channel theorem applies only after a positive multiplicative endpoint map is scientifically declared. The complete-chain example motivates the design principle—do not infer missing links from endpoints. Nonmultiplicative maps require their own observation-map identifiability analysis.

**Pass criterion:** no text implies that every ecological causal chain is literally a product.

## 7. “A relative proxy comparison cancels unknown calibration, so there is no problem.”

**Response:** it cancels absolute calibration only under transport stability, `q_1/q_0=1`. The comparison identifies `rho_F` and `rho_E` only through a restriction on `kappa=q_1/q_0`.

**Pass criterion:** abstract and Introduction state that relative proxy designs are safe only under stable conversion and that this assumption is not testable from `W` and `X` alone.

## 8. “Why should the calibration bound be believed?”

**Response:** neither the canonical `Gamma`/`eta` bound nor the legacy `delta` is inferred from the same `W` and `X` observations. A finite transport tolerance comes from external calibration evidence, validation data, instrument/design knowledge, biological prior information, or a declared sensitivity grid. The purpose is to expose dependence of the ecological conclusion on that bound.

The breakdown factor reverses the burden of specification: report the smallest calibration distortion sufficient to overturn the conclusion, then let readers compare that threshold with knowledge of their own system.

**Pass criterion:** software and paper explicitly state that they do not estimate `Gamma`, `eta` or `delta` from the observations whose identifying power is being assessed.

## 9. “You have only replaced one untestable stability assumption with a family of untestable assumptions.”

**Response:** yes, in the precise partial-identification sense. The analysis indexes the conclusion over an assumption family and reports the failure threshold. This makes assumption dependence visible rather than hiding it at `kappa=1`.

**Pass criterion:** manuscript says explicitly that bounded-transport analysis is a sensitivity / partial-identification device, not an estimator of transportability.

## 10. “The identified intervals for F and E can be reported independently.”

**Response:** no. The same `kappa` generates both ratios. The joint set satisfies `rho_F rho_E=rho_W` exactly. In log-ratio coordinates,

```text
log rho_F + log rho_E = log rho_W,
```

so the set is a line segment of slope `-1`. Pairing both marginal upper endpoints, or both lower endpoints, generally creates impossible latent states.

**Pass criterion:** Design Rule 2 is explicit: report the joint identified set as the primary uncertainty object; marginal intervals are projections only and must not be treated as independently combinable error bars.

## 11. “Calling the errors perfectly negatively correlated is too statistical.”

**Response:** distinguish structural coupling from a stochastic correlation coefficient. Conditional on the observed net ratio and with calibration drift as the only uncertainty dimension, log-channel deviations induced by `kappa` are exactly opposite. If sampling uncertainty is also present, the full stochastic covariance need not equal `-1`.

**Pass criterion:** manuscript uses “exactly coupled along a slope-minus-one joint identified set” rather than generalising to all uncertainty sources.

## 12. “The 34% claim changes if I reverse the reference regime.”

**Response:** this is why the canonical robustness scale is the multiplicatively symmetric factor

```text
1/Gamma <= kappa <= Gamma.
```

The breakdown factor is

```text
Gamma_star=max(rho_hat,1/rho_hat),
eta_star=|log rho_hat|,
```

so `rho_hat=1/1.34` and `rho_hat=1.34` both have `Gamma_star=1.34`. The 34% statement is retained only as the directional translation of the decline example.

**Pass criterion:** primary theory and cross-contrast reporting use `Gamma_star` or `eta_star`; legacy `delta` language is clearly directional/additive-around-one.

## 13. “Sampling uncertainty is being confused with identification uncertainty.”

**Response:** they are separate layers. A structural identified set is conditional on the observed or estimated net/proxy ratios. Sampling uncertainty should be propagated around the structural set, not substituted for it.

## 14. “N3 and N4 are unrelated endpoint statements.”

**Response:** under the symmetric transport family they are exact endpoints:

```text
Gamma=1          -> N3 point identification
1<Gamma<infinity -> sharp partial identification
Gamma->infinity  -> N4 unrestricted-drift non-identification.
```

**Pass criterion:** N4 is never described as the `delta->1` limit.

## 15. “One calibration anchor is insufficient if the system changes.”

**Response:** agreed. One calibration anchor identifies local conversion but not cross-regime transport; finite `Gamma/eta` remains external. Two direct calibration anchors measure both `q_0` and `q_1`, hence `kappa=q_1/q_0`, and remove the need for a sensitivity bound for that comparison.

## 16. “Two calibration anchors do not identify anything unless the true channel is measured.”

**Response:** correct. A calibration anchor means the proxy `X_i` and its corresponding mathematical channel are both directly measured on the same scale/domain, so `q_i=X_i/F_i` (or the symmetric establishment form) is observed. Merely having two proxy observations is not two calibration anchors.

## 17. “What is the minimum publishable claim?”

The manuscript should survive even if reviewers reject broader rhetoric. The minimum defensible contribution has three pillars:

1. a structural ecological audit showing that net-only observations of `W=prod_j F_j` live on a product-preserving quotient, with residual equivalence dimension `k-1-r` after `r` independent channel anchors;
2. one two-channel calibration-transport family whose finite bounds yield a sharp joint set and reference-invariant breakdown factor while recovering stable and unrestricted transport as endpoints;
3. operational measurement/reporting consequences: distinguish channel anchors from calibration anchors, and preserve the exact joint coupling when uncertainty is reported.

RACH, NOV, synthetic benchmark performance, Campanula causal claims and any claim that multiplicative decomposition is universal are not required for this paper.

## Submission stop conditions

Do not submit if any of the following is true:

- `Gamma`, `eta` or `delta` is described as estimated from the same net/proxy data;
- bounded-transport analysis is said to prove transportability rather than index sensitivity;
- 34% is used as the canonical reversal-invariant robustness metric instead of `Gamma_star=1.34` / `eta_star`;
- marginal F/E intervals are presented as independent uncertainty;
- N4 is described as the `delta -> 1` limit;
- channel anchors and calibration anchors are conflated;
- `k-1-r` is stated without the word **independent** or without direct channel information;
- `sum_m V_mE_m` is presented as if it were a single two-factor product;
- network degree or abundance is labelled effective service without an effectiveness term;
- the complete-chain example is assumed multiplicative without declaring an endpoint map;
- the literature paragraph implies identical channel semantics across pollination and seed dispersal;
- elementary identifiability algebra itself is presented as the primary novelty;
- the boundary paper drifts back into the RACH/MEE methods claim spine.
