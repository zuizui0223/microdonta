# Boundary paper: reviewer-objection audit

Status: submission-facing adversarial audit for `paper/boundary_manuscript_submission.md`.

The purpose of this file is not to inflate the novelty claim. It is to force likely objections into one of three categories: answered by the theorem, requiring an explicit qualification, or remaining an external empirical requirement.

## 1. “You are redefining mechanism to mean identification.”

**Response required in manuscript:** no. *Mechanistic proximity*, *mechanistic modelling*, and *mechanistic identification* are related but distinct ideas. Molecular measurements can be close to biological machinery, mechanistic models can explicitly represent processes, and neither fact alone determines whether the available observations discriminate the particular competing mechanisms under study. The paper proposes identification strength as an additional axis for classifying mechanistic evidence, not as the only legitimate meaning of mechanism.

**Pass criterion:** manuscript says biological measurement level/proximity and identification strength are different properties; it does not claim that all mechanistic explanation reduces to formal identifiability.

## 2. “You invented a straw-man hierarchy in which ecology calls field data ‘pattern’ and molecular data ‘mechanism’.”

**Response required in manuscript:** do not claim that ecology formally endorses a universal one-dimensional hierarchy. The defensible claim is narrower: ecological literatures use *mechanistic* for several legitimate evidentiary ambitions, including proximity to genes/pathways and evidence about structures/processes. Those meanings need not coincide with discrimination among competing mechanisms. Ungerer et al. (2008) and Rudman et al. (2018) support the mechanistic aspiration of ecological genomics; Rudman et al. explicitly note that genomic data alone are not sufficient for the eco-evolutionary questions they consider.

**Pass criterion:** primary text says the two meanings can be conflated or left implicit, not that the field has formally adopted a universal hierarchy. The source-by-source claims match `mechanistic_evidence_literature_audit.md`.

## 3. “This is an anti-genomics or anti-molecular argument.”

**Response required in manuscript:** explicitly reject this reading. Molecular and genomic measurements can be mechanistically proximal, experimentally manipulable, highly constraining and point-identifying when alternatives predict different observations. The claim is conditional: proximity alone does not guarantee identification among the declared alternatives. Conversely, field observations are not intrinsically mechanistic; they become strong mechanistic evidence only when their observation map separates alternatives or directly anchors missing channels. Smith et al. (2020) is an independent field-level example of experimental designs testing mechanistic drivers under natural conditions.

**Pass criterion:** both a proximal-but-non-identifying possibility and a field-but-identifying possibility appear, with the evidentiary status conditioned on the candidate mechanism set and observation map.

## 4. “Calling the evidence axes orthogonal claims statistical independence.”

**Response required in manuscript:** concede that *orthogonal* is unnecessary and potentially misleading. The argument requires only non-equivalence: biological proximity does not determine identification strength, and no monotone relationship is assumed. The axes may be correlated in particular research programmes.

**Pass criterion:** primary prose uses **distinct axes**, **non-equivalent properties**, or equivalent wording. It does not claim zero correlation or statistical independence.

## 5. “The product non-identifiability is trivial.”

**Response required in manuscript:** concede the algebra. The claim is not that products have multiple factorizations. The contribution is the ecological evidentiary distinction, the observation class that remains net-only even when apparently rich, the quantitative `k-1-r` equivalence-dimension rule, the calibration-transport family, the sharp joint set and breakdown factor, and the operational design/reporting rules.

**Pass criterion:** N1 is introduced through ecological measurement objects and then closed structurally by the product-preserving group action. Bellman–Åström, Rothenberg and Manski are acknowledged before the novelty sentence.

## 6. “The multiplicative model was chosen to manufacture the theorem.”

**Response required in manuscript:** lead with Schupp, Jordano & Gómez (2010), where seed dispersal effectiveness is explicitly `Quantity × Quality`; then show the independent pollination lineage (Rader; Ballantyne; Reynolds & Fenster) using visitation/rate × per-visit effectiveness.

**Pass criterion:** language says that the architecture recurs in ecology, not that all ecological fitness is multiplicative or that all cited quantities share identical biological semantics. Genomic/molecular examples motivate the two-axis Perspective only and are not claimed to obey the product theorem without a declared product observation map.

## 7. “Pollinator community service is a sum, not one product `W=FE`.”

**Response:** correct. At visitor type `m`, the contribution `S_m=V_mE_m` is a product and the product theorem applies within that interaction type. Community service `S=sum_m V_mE_m` adds an aggregation/allocation problem across visitor types. We do not claim that the two-factor theorem alone identifies the sum-of-products architecture.

**Pass criterion:** manuscript explicitly distinguishes within-type product ambiguity from across-type aggregation ambiguity. Degree, abundance or visitation alone are described as quantity-side descriptors/proxies, not as effective service.

## 8. “The `k-1-r` rule assumes every anchor is independent.”

**Response:** yes. A channel anchor is an independent direct observation of one latent channel coordinate, or one independent channel ratio in a before/after analysis. Redundant measurements do not reduce the dimension twice.

**Pass criterion:** theorem and table say `r independent channel anchors`; `0<=r<=k-1`; the final channel is recovered from the product only after `k-1` independent coordinates are fixed.

## 9. “You are mixing channel anchors with proxy calibration anchors.”

**Response:** they solve different missing-information problems. Channel anchors reduce the `k`-stage product-equivalence dimension. Calibration anchors measure `q_i` within regimes and therefore determine whether proxy conversion transports across a two-regime comparison.

**Pass criterion:** the manuscript has two separately named anchor ladders and never uses the 0/1/2 calibration ladder as if it were the `k-1-r` channel-dimension theorem.

## 10. “A change -> service -> dependency -> response chain is not necessarily multiplicative.”

**Response:** agreed. The `k`-channel theorem applies only after a positive multiplicative endpoint map is scientifically declared. The complete-chain example motivates the design principle—do not infer missing links from endpoints. Nonmultiplicative maps require their own observation-map identifiability analysis. Correia, Dee & Ferraro (2025) is adjacent support for treating intermediary-process inference as a design/assumptions problem, not evidence that all mediation maps are products.

**Pass criterion:** no text implies that every ecological causal chain is literally a product.

## 11. “A relative proxy comparison cancels unknown calibration, so there is no problem.”

**Response:** it cancels absolute calibration only under transport stability, `q_1/q_0=1`. The comparison identifies `rho_F` and `rho_E` only through a restriction on `kappa=q_1/q_0`.

**Pass criterion:** abstract and Introduction state that relative proxy designs are safe only under stable conversion and that this assumption is not testable from `W` and `X` alone.

## 12. “Why should the calibration bound be believed?”

**Response:** neither the canonical `Gamma`/`eta` bound nor the legacy `delta` is inferred from the same `W` and `X` observations. A finite transport tolerance comes from external calibration evidence, validation data, instrument/design knowledge, biological prior information, or a declared sensitivity grid. The purpose is to expose dependence of the ecological conclusion on that bound.

The breakdown factor reverses the burden of specification: report the smallest calibration distortion sufficient to overturn the conclusion, then let readers compare that threshold with knowledge of their own system.

**Pass criterion:** software and paper explicitly state that they do not estimate `Gamma`, `eta` or `delta` from the observations whose identifying power is being assessed.

## 13. “You have only replaced one untestable stability assumption with a family of untestable assumptions.”

**Response:** yes, in the precise partial-identification sense. The analysis indexes the conclusion over an assumption family and reports the failure threshold. This makes assumption dependence visible rather than hiding it at `kappa=1`.

**Pass criterion:** manuscript says explicitly that bounded-transport analysis is a sensitivity / partial-identification device, not an estimator of transportability.

## 14. “The identified intervals for F and E can be reported independently.”

**Response:** no. The same `kappa` generates both ratios. The joint set satisfies `rho_F rho_E=rho_W` exactly. In log-ratio coordinates,

```text
log rho_F + log rho_E = log rho_W,
```

so the set is a line segment of slope `-1`. Pairing both marginal upper endpoints, or both lower endpoints, generally creates impossible latent states.

**Pass criterion:** Design Rule 2 is explicit: report the joint identified set as the primary uncertainty object; marginal intervals are projections only and must not be treated as independently combinable error bars.

## 15. “Calling the errors perfectly negatively correlated is too statistical.”

**Response:** distinguish structural coupling from a stochastic correlation coefficient. Conditional on the observed net ratio and with calibration drift as the only uncertainty dimension, log-channel deviations induced by `kappa` are exactly opposite. If sampling uncertainty is also present, the full stochastic covariance need not equal `-1`.

**Pass criterion:** manuscript uses “exactly coupled along a slope-minus-one joint identified set” rather than generalising to all uncertainty sources.

## 16. “The 34% claim changes if I reverse the reference regime.”

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

## 17. “Sampling uncertainty is being confused with identification uncertainty.”

**Response:** they are separate layers. A structural identified set is conditional on the observed or estimated net/proxy ratios. Sampling uncertainty should be propagated around the structural set, not substituted for it.

## 18. “N3 and N4 are unrelated endpoint statements.”

**Response:** under the symmetric transport family they are exact endpoints:

```text
Gamma=1          -> N3 point identification
1<Gamma<infinity -> sharp partial identification
Gamma->infinity  -> N4 unrestricted-drift non-identification.
```

**Pass criterion:** N4 is never described as the `delta->1` limit.

## 19. “One calibration anchor is insufficient if the system changes.”

**Response:** agreed. One calibration anchor identifies local conversion but not cross-regime transport; finite `Gamma/eta` remains external. Two direct calibration anchors measure both `q_0` and `q_1`, hence `kappa=q_1/q_0`, and remove the need for a sensitivity bound for that comparison.

## 20. “Two calibration anchors do not identify anything unless the true channel is measured.”

**Response:** correct. A calibration anchor means the proxy `X_i` and its corresponding mathematical channel are both directly measured on the same scale/domain, so `q_i=X_i/F_i`, or the symmetric establishment form, is observed. Merely having two proxy observations is not two calibration anchors.

## 21. “Is this just causal-inference terminology applied to ecology?”

**Response:** no claim is made that latent-channel identification exhausts causal inference or mechanistic explanation. The target here is narrower: whether declared competing mechanisms or decompositions are observationally distinguishable under a specified observation map. Classical structural identifiability and partial identification are explicitly acknowledged. Grace et al. (2025), Correia et al. (2025) and Siegel & Dee (2025) are adjacent evidence/design literatures with broader causal targets.

**Pass criterion:** the manuscript never equates the present identified-set calculations with identification of every causal graph, mediated effect or intervention effect.

## 22. “What is the minimum publishable claim?”

The manuscript should survive even if reviewers reject the broadest rhetoric. The minimum defensible contribution has a conceptual distinction plus three quantitative pillars:

- **Conceptual:** biological/mechanistic proximity and identification strength are distinct evidentiary properties; the worked theorems demonstrate the distinction without intrinsically ranking biological levels or claiming statistical independence.
- **Pillar 1:** net-only observations of `W=prod_j F_j` live on a product-preserving quotient, with residual equivalence dimension `k-1-r` after `r` independent channel anchors.
- **Pillar 2:** one two-channel calibration-transport family whose finite bounds yield a sharp joint set and reference-invariant breakdown factor while recovering stable and unrestricted transport as endpoints.
- **Pillar 3:** operational measurement/reporting consequences: distinguish channel anchors from calibration anchors, and preserve the exact joint coupling when uncertainty is reported.

RACH, NOV, synthetic benchmark performance, Campanula causal claims, any claim that multiplicative decomposition is universal, any claim that ecology formally endorses a field-to-molecule hierarchy, and any intrinsic ranking of molecular versus field evidence are not required for this paper.

## Submission stop conditions

Do not submit if any of the following is true:

- ecology is said to formally endorse a universal field-pattern -> molecular-mechanism hierarchy;
- molecular/genomic evidence is described as intrinsically more or less mechanistic than field evidence;
- mechanistic proximity and identification strength collapse back into one axis;
- `orthogonal` is used to imply statistical independence of the two evidence axes;
- the broad two-axis Perspective claim is presented as a universal mathematical theorem;
- the source claims conflict with `mechanistic_evidence_literature_audit.md`;
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
