# From ecological products to mechanisms: identification and calibration transport in multiplicative chains

## Abstract

Ecologists often infer mechanism from quantities that multiply several biological stages. Such products can be measured precisely while remaining structurally uninformative about how performance is allocated among their latent channels. We formalise this problem for positive multiplicative ecological chains. For `W=prod_j F_j`, net-only observations are invariant under product-preserving reallocations of the factors; in log coordinates the observational equivalence class has dimension `k-1` for a `k`-channel chain. Each independent direct channel anchor removes one dimension, so `r` anchors leave `k-1-r` unresolved dimensions and `k-1` anchors point-identify the final channel from the product. We then treat the common two-channel proxy case `W_i=F_iE_i`, `X_i=q_iF_i`. Stable, bounded and unrestricted proxy transport form one family under `1/Gamma <= q_1/q_0 <= Gamma`. Finite `Gamma` yields a sharp joint identified set and a reference-invariant breakdown factor; the same calibration ratio couples the two latent channel ratios exactly, producing a slope-`-1` segment in log-ratio coordinates. Direct calibration creates a separate 0/1/2 calibration-anchor ladder, and the joint geometry implies that channel uncertainties must not be reported as independently combinable error bars. The algebra is elementary; the contribution is to close a recurring ecological measurement architecture from information boundary through partial identification to field-design and reporting rules.

## 1. Introduction

Ecological performance is frequently assembled from multiple biological stages. Pollination offers a concrete example. At visitor-type `m`, effective contribution can be written as

```text
S_m = V_m E_m,
```

where `V_m` is interaction quantity (for example visitation rate) and `E_m` is per-interaction effectiveness. Community service then aggregates those contributions,

```text
S = sum_m V_m E_m.
```

Network degree, visitor abundance or visitation alone may describe or proxy the quantity side of this architecture, but they are not effective service unless the effectiveness term is fixed or otherwise known. The product problem therefore occurs within each interaction type, while summation across types can add a second allocation ambiguity. This is not a special construction for our theorem: pollination studies explicitly combine visitation with per-visit effectiveness, and seed-dispersal theory explicitly combines quantity with post-dispersal quality.

The same logic appears in longer ecological measurement chains. A pollinator-change study may wish to connect change in the visitor community to effective service, dependency or reproductive assurance, and finally a demographic or trait response. Observing only an endpoint does not, by itself, identify which unobserved intermediate stage changed. If a declared endpoint factorises as a product of positive stages, the number of unresolved stages has a precise structural meaning.

A second problem appears when one stage is observed only through a proxy. Relative comparisons are commonly used to avoid unknown absolute calibration. If the proxy is `X_i=q_iF_i`, an unknown constant scale indeed cancels when `q_1=q_0`. But the scientifically relevant question is not whether absolute calibration is known. It is whether calibration transports across the regimes being compared. Fragmented versus connected habitat, urban versus rural sites, warm versus cool years, or communities with different visitor identities are precisely the contrasts in which the proxy-to-channel conversion may change.

We develop three linked results. First, net-only observations define an equivalence class rather than a unique mechanism decomposition. For a `k`-channel product this class has `k-1` free dimensions; each independent direct channel anchor removes one. Second, in the common two-channel proxy case, stable, bounded and unrestricted proxy transport form one calibration family that yields point identification, sharp partial identification and non-identification as limiting cases, together with a reference-invariant breakdown factor. Third, these boundaries generate operational rules: distinguish channel anchors from calibration anchors, match direct measurement effort to the desired identification strength, and report calibration-induced uncertainty as the coupled joint set rather than as independent marginal error bars.

The argument belongs to the established traditions of structural identifiability and partial identification. We do not claim new identifiability algebra. The contribution is ecological and operational: to identify a recurring measurement architecture, quantify the dimension of its unresolved mechanism space, derive a sharp transport-sensitive identified set, and carry those boundaries through sensitivity analysis to concrete field-design and reporting consequences.

## 2. Observation models

### 2.1 A positive multiplicative chain

Let a declared ecological output be

```text
W(z) = prod_{j=1}^k F_j(z),    F_j(z)>0.
```

The factorisation must be biologically justified for the chosen output, domain and census interval. The theory does not assert that every ecological response is multiplicative. It asks what follows when investigators already use a multiplicative measurement architecture.

A net-only observation is any deterministic functional

```text
O = Phi(W).
```

This includes the full response curve `W(z)`, all threshold-feasible sets `Omega_t={z:W(z)>=t}`, and any geometry or topology derived solely from them.

### 2.2 The two-channel proxy case

For regimes `i in {0,1}`, let

```text
W_i(z)=F_i(z)E_i(z),
X_i(z)=q_i(z)F_i(z),    q_i(z)>0.
```

At a fixed `z`, define

```text
rho_W=W_1/W_0,
rho_X=X_1/X_0,
rho_F=F_1/F_0,
rho_E=E_1/E_0,
kappa=q_1/q_0.
```

Then

```text
rho_X=kappa rho_F,
rho_W=rho_F rho_E,
```

and therefore

```text
rho_F=rho_X/kappa,
rho_E=(rho_W/rho_X)kappa.
```

Write `rho_E_hat=rho_W/rho_X` for the value obtained under stable calibration `kappa=1`.

## 3. Net-only observations define a quotient, not a mechanism

### Theorem N1 — two-channel net-only invariance

For any positive function `c(z)`, define

```text
F_c(z)=c(z)F(z),
E_c(z)=E(z)/c(z).
```

Then `F_cE_c=FE=W` pointwise. Consequently every deterministic net-only observation `Phi(W)` is invariant under `(F,E)->(cF,E/c)`.

The positive functions form a multiplicative group acting on latent decompositions, and `W=FE` is invariant under that action. Every net-only observable therefore factors through the quotient by these orbits. Complete performance curves, all threshold-feasible sets and every boundary, width, connected-component count or topological summary derived from them belong to the same invariant class. They can describe the net ecological pattern arbitrarily well while containing no data-based information about how the product is allocated between latent channels.

### Theorem N1-k — a `k`-channel chain leaves `k-1` unresolved dimensions

For

```text
W = prod_{j=1}^k F_j,
```

let positive multipliers `c_1,...,c_k` satisfy

```text
prod_{j=1}^k c_j = 1.
```

Then the transformation

```text
F_j -> c_j F_j
```

leaves `W` unchanged. In log coordinates, product-preserving perturbations satisfy

```text
sum_{j=1}^k d_j = 0,
```

which is a `(k-1)`-dimensional subspace. Hence net-only observation of a positive `k`-channel product leaves a `(k-1)`-dimensional mechanism-equivalence class.

The result has an immediate anchor corollary. If `r` independent channel values (or, in a before/after analysis, `r` independent channel ratios) are directly observed, each anchor fixes one independent coordinate. The residual unidentified dimension is

```text
k - 1 - r,    0 <= r <= k-1.
```

When `r=k-1`, the final channel is recovered by division:

```text
F_k = W / prod_{j=1}^{k-1} F_j.
```

Thus a four-stage chain observed only at its endpoint has three unresolved structural dimensions; one independent channel anchor leaves two; two leave one; and three point-identify the fourth stage from the product.

**Channel-anchor rule.** For a declared positive `k`-stage product, `k-1` independent channel anchors are sufficient for point identification of all stages. Fewer anchors reduce, but do not eliminate, the dimension of the observational equivalence class.

This rule concerns direct information about the latent stages themselves. It is distinct from the calibration-anchor ladder below, which concerns whether a proxy conversion transports between two regimes.

## 4. Calibration transport is one identification family

Let the between-regime calibration ratio satisfy the multiplicatively symmetric bound

```text
1/Gamma <= kappa <= Gamma,    Gamma>=1.
```

Equivalently, with `eta=log Gamma`, require `|log kappa|<=eta`.

### Theorem T1 — calibration-transport family

Conditional on positive observed `rho_W` and `rho_X`, the sharp joint identified set is

```text
J_Gamma={(rho_X/kappa, rho_E_hat*kappa):
         1/Gamma <= kappa <= Gamma}.
```

Its marginal projections are

```text
rho_F in [rho_X/Gamma, rho_X*Gamma],
rho_E in [rho_E_hat/Gamma, rho_E_hat*Gamma].
```

Every admissible pair satisfies

```text
rho_F rho_E=rho_W.
```

The set is sharp. For any admissible `kappa`, choose a positive `q_0`, set `q_1=kappa q_0`, reconstruct `F_i=X_i/q_i`, and then set `E_i=W_i/F_i`. The observations are reproduced exactly, so every point in the stated set is attainable and no point outside it is compatible with the transport restriction.

The familiar cases are endpoints of the same family:

```text
Gamma=1          -> kappa=1 -> point identification (stable calibration; N3)
1<Gamma<infinity -> sharp partial identification
Gamma->infinity  -> unrestricted kappa -> non-identification (N4)
```

Identification strength therefore changes continuously with the amount of transport information supplied.

## 5. The joint identified set carries more information than two marginals

The same `kappa` generates both channel ratios. The identified object is one-dimensional, not the Cartesian product of the two marginal intervals. In the original ratio plane it lies on

```text
rho_E=rho_W/rho_F.
```

In log-ratio coordinates, with `u=log rho_F` and `v=log rho_E`, every admissible pair satisfies

```text
u+v=log rho_W.
```

Hence `J_Gamma` is a straight line segment of slope `-1`. Moving the calibration ratio changes the two log-channel ratios by exactly opposite amounts:

```text
d log rho_F=-d log kappa,
d log rho_E=+d log kappa.
```

**Design Rule 2 — Preserve the coupling.** Calibration-drift uncertainty for the two channels must not be reported as independently combinable intervals. The primary uncertainty object is the joint identified set. Marginal intervals may be shown as projections, but readers must not be invited to combine arbitrary endpoints. In particular, both marginal upper endpoints generally correspond to opposite values of `kappa` and cannot occur simultaneously. Treating them as independent creates a rectangular uncertainty region containing latent states that cannot reproduce the observed net ratio.

This is a statement about structural calibration uncertainty conditional on the observed net and proxy ratios. Sampling uncertainty is a separate layer and may enlarge the joint region.

## 6. Breakdown factors make assumption dependence explicit

A finite `Gamma` is not identified from the same `W` and `X` observations whose identifying power is being assessed. Bounded-transport analysis therefore does not establish that a particular tolerance is true. It replaces the hidden point assumption `kappa=1` with an explicit family of assumptions and shows exactly how the biological conclusion depends on them.

For a stable-calibration channel ratio `rho_hat`, the smallest symmetric multiplicative calibration distortion that reaches no change is

```text
Gamma*=max(rho_hat,1/rho_hat),
eta*=|log rho_hat|.
```

These measures are invariant to reversing the reference regime. `rho_hat=1/1.34` and `rho_hat=1.34` both give `Gamma*=1.34` and `eta*=log(1.34)`.

For the worked decline,

```text
rho_E_hat=1/1.34=0.746268...,
```

so the directly reportable result is:

> The inferred establishment decline has a calibration-distortion breakdown factor of 1.34. The identified set first reaches no change when the between-regime calibration ratio differs from stability by a factor of 1.34; in the upward direction this corresponds to 34% drift.

The strict decline holds below this boundary, not at equality. The earlier additive-around-one percentage parameterisation may be retained as a directional translation, but the symmetric factor `Gamma*` is the primary robustness scale because it is unchanged by reversing the comparison.

The breakdown factor changes the role of the external assumption. The analyst need not assert one uniquely correct `Gamma` in order to communicate robustness. Instead, the analysis reports the minimum calibration distortion sufficient to overturn the conclusion, and readers can compare that threshold with independent calibration experiments, instrument knowledge, biological prior information or direct validation data.

## 7. Two different anchor ladders answer two different design questions

The word *anchor* can refer to two distinct measurements and they should not be conflated.

### 7.1 Channel anchors reduce the dimension of a `k`-stage chain

A channel anchor directly observes one latent stage (or one stage ratio in a before/after comparison). For `W=prod_j F_j`, `r` independent channel anchors leave `k-1-r` unresolved dimensions. This is the quantitative extension of the instruction to observe missing links rather than inferring them from endpoints.

A change -> service -> dependency/assurance -> response study, for example, should first declare which stages enter the endpoint map. If the declared map is multiplicative and contains `k` positive stages, endpoint-only observation leaves `k-1` free dimensions. Each directly measured intermediate stage removes one. If the biological map is not multiplicative, the same design question remains but requires the appropriate observation map rather than the product theorem.

### 7.2 Calibration anchors measure proxy transport across regimes

A calibration anchor is a regime in which the proxy and the mathematical channel it targets are both directly measured on the same comparison domain, so the local conversion `q_i` is observed.

Direct calibration effort produces a separate ladder:

| Calibration anchors | Transport information | Consequence |
|---:|---|---|
| 0 | no direct information on `q_1/q_0` | unrestricted transport gives non-identification |
| 1 | one local `q_i` observed; cross-regime transport remains unknown | an external finite `Gamma/eta` gives sharp partial identification and a breakdown factor |
| 2 | `q_0` and `q_1` observed, hence `kappa=q_1/q_0` measured | point identification without an external transport bound |

With two calibration anchors,

```text
q_0=X_0/F_0,
q_1=X_1/F_1,
kappa=q_1/q_0,
```

and substituting the observed `kappa` into the equations for `rho_F` and `rho_E` point-identifies both channel ratios.

**Design Rule 1 — Measure the missing identification information.** Match direct measurement effort to the inference required. For a `k`-stage product, each independent channel anchor removes one structural degree of freedom and `k-1` suffice for point identification. For proxy transport across two regimes, one calibration anchor supports externally bounded partial identification, whereas two calibration anchors measure `kappa` directly and remove the transport sensitivity assumption.

The question “where does the calibration bound come from?” and the question “which intermediate link is unresolved?” are therefore both experimental-design questions, but they concern different missing information.

## 8. Why the multiplicative architecture is ecologically relevant

Schupp, Jordano & Gómez (2010) provide the clearest cross-domain example: seed dispersal effectiveness is explicitly decomposed as `Quantity × Quality`, with quantity determined by the number of dispersed seeds and quality by the probability that a dispersed seed ultimately contributes to recruitment. Pollination provides an independent lineage. Rader et al. (2012) combine pollen-transfer efficiency with visitation frequency; Ballantyne et al. (2017) combine visitation frequency with single-visit pollen deposition effectiveness; and Reynolds & Fenster (2008) define pollinator importance as visitation rate multiplied by pollinator effectiveness.

These studies do not imply identical channel semantics across ecological systems. They establish the narrower point required here: rate-by-effectiveness and quantity-by-quality products are recurring ecological measurement architectures. The theorem audits the inferential consequences of an existing practice rather than introducing multiplication solely to create an identifiability result.

The pollinator-service example also clarifies the relation between product and aggregation. The present theorems apply directly to each positive contribution `V_m E_m`. If only the aggregate `sum_m V_mE_m` is observed, attribution among visitor types adds further ambiguity that is not removed by the within-type product theorem. Treating network degree or abundance as service therefore risks two distinct collapses: a proxy can replace the quantity channel, and aggregation can hide which visitor types supplied the measured service.

## 9. Relation to identification theory and scope

Structural identifiability has long studied whether internal model components are recoverable from input-output observations (Bellman & Åström 1970), and general parametric identification theory is classical (Rothenberg 1971). Partial-identification theory formalises the case in which data and assumptions restrict a target to a set rather than a point (Manski 2003). The algebra used here is elementary relative to those literatures.

The contribution has three parts: a net-only ecological observation class whose `k`-channel equivalence dimension is explicitly quantified; a calibration-transport family that supplies a sharp joint set and reference-invariant breakdown factor; and operational consequences that connect both channel and calibration anchors to identification strength while preserving the exact dependence structure when uncertainty is reported. The paper is therefore about coverage and closure—from information boundary to sensitivity, field design and reporting—rather than mathematical depth.

The results assume positive multiplicative stages where the product map is declared. Zeros require separate treatment because ratios and division fail. Sum-of-products architectures, additive interactions and other nonlinear maps can create additional equivalence structures and require their own observation maps. The transport result is pointwise in `z`; uniform statements over a trait domain require a predeclared aggregate estimand or exclusion of one throughout the domain. Transport bounds must be prespecified or externally informed rather than chosen after seeing the desired conclusion.

## 10. Discussion

The practical problem is not merely that a product has several factors. It is that ecological measurement routinely collapses mechanistically distinct stages into products, proxies and aggregates, then asks those collapsed quantities to support channel-specific conclusions. The `k`-channel theorem makes the information loss quantitative: endpoint-only observation of a positive `k`-stage product leaves `k-1` structural degrees of freedom, and each independent direct channel measurement removes one.

This dimension rule gives a precise version of a common field recommendation. A complete change -> service -> dependency/assurance -> response chain cannot be reconstructed simply because its endpoints covary. The investigator must either observe enough intermediate stages, impose scientifically defended restrictions, or report the remaining equivalence set rather than silently filling missing links.

Relative proxy comparisons add a different identification problem. They are not automatically protected by taking ratios; they are protected only by transport of the proxy-to-channel conversion. Once that hidden assumption is written as `kappa=q_1/q_0`, stable calibration, bounded uncertainty and unrestricted drift become one identification family rather than three disconnected cases.

The partial-identification region is useful precisely because it does not pretend to estimate transportability from data that cannot identify it. A finite `Gamma` is an external tolerance; the breakdown factor reports how strong that tolerance must become before the ecological conclusion fails. The calibration-anchor ladder then shows how the assumption can be progressively replaced by measurement. One calibration anchor supports a sensitivity analysis; two measure transport itself.

The same algebra constrains how uncertainty should be communicated. Because one calibration ratio moves the two channel ratios in opposite directions while preserving the observed net ratio, structural calibration uncertainty is one-dimensional. Two independently drawn error bars throw away that information and admit impossible channel combinations. The correct object is the joint identified set.

The resulting workflow is therefore: identify the declared observation map; count the unresolved dimensions or transport parameters it leaves; measure channel or calibration anchors according to the strength of inference required; report the corresponding sharp set or point estimate; and preserve the identified dependence structure when results are communicated. Better description of an ecological product is not automatically better identification of the mechanisms that generated it.

## Figure 1 caption

**Figure 1. Calibration transport determines identification strength in the two-channel proxy case.** Stable conversion (`Gamma=1`) gives point identification. A finite multiplicative transport bound (`1/Gamma <= kappa <= Gamma`) produces a sharp one-dimensional joint identified set. Because the same `kappa` moves both channel ratios, every admissible pair preserves `rho_F rho_E=rho_W`; after log transformation the set is a line segment of slope `-1`. In the worked example the directional conclusion first reaches no change at the reference-invariant breakdown factor `Gamma*=1.34` (`eta*=log 1.34`), corresponding to 34% upward calibration-ratio drift in that direction. Removing the finite transport restriction recovers N4 non-identification.

## Code availability

The `k`-channel quotient dimension and channel-anchor rule are implemented in `causal_model.multichannel_identifiability`. Symmetric transport calculations, reference-invariant breakdown factors and the calibration-anchor ladder are implemented in `causal_model.calibration_transport_family`. The legacy additive-around-one drift calculations remain in `causal_model.bounded_proxy_drift` for reproducibility and directional percentage translation. Regression tests verify the `k-1-r` dimension rule, product-preserving log-gauge basis, final-channel reconstruction under `k-1` anchors, stable-endpoint recovery, finite-bound sharp intervals, reference-reversal invariance of `Gamma*`, direct recovery of `kappa` from two calibration anchors, exact joint-product consistency, slope-`-1` log geometry and rejection of impossible marginal endpoint combinations.

## References

- Ballantyne, G., Baldock, K.C.R., Rendell, L. & Willmer, P.G. 2017. Pollinator importance networks illustrate the crucial value of bees in a highly speciose plant community. *Scientific Reports* 7:8383. doi:10.1038/s41598-017-08798-x.
- Bellman, R. & Åström, K.J. 1970. On structural identifiability. *Mathematical Biosciences* 7:329–339. doi:10.1016/0025-5564(70)90132-X.
- Manski, C.F. 2003. *Partial Identification of Probability Distributions*. Springer, New York. doi:10.1007/b97478.
- Rader, R. et al. 2012. Spatial and temporal variation in pollinator effectiveness: do unmanaged insects provide consistent pollination services to mass flowering crops? *Journal of Applied Ecology*. doi:10.1111/j.1365-2664.2011.02066.x.
- Reynolds, R.J. & Fenster, C.B. 2008. Point and interval estimation of pollinator importance: a study using pollination data of *Silene caroliniana*. *Oecologia* 156:325–332. doi:10.1007/s00442-008-0982-5.
- Rothenberg, T.J. 1971. Identification in parametric models. *Econometrica* 39:577–591.
- Schupp, E.W., Jordano, P. & Gómez, J.M. 2010. Seed dispersal effectiveness revisited: a conceptual review. *New Phytologist* 188:333–353. doi:10.1111/j.1469-8137.2010.03402.x.
