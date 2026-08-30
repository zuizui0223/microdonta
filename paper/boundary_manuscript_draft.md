# From proxy stability to breakdown points: partial identification of multiplicative ecological channels

> **Boundary-paper draft.** This manuscript is separate from the RACH observation-selection submission. Its contribution is the N1–N4 information boundary, the sharp joint identified set under bounded proxy-calibration drift, and the observation-design and reporting rules implied by that boundary.

## Abstract

Proxy-based estimates of relative change identify channel-specific change only when the proxy-to-channel conversion is stable across the compared regimes. That assumption is not testable from the net response and proxy observations alone, and it is especially vulnerable in habitat, climate, fragmentation and community-composition contrasts where relative proxy designs are often treated as safest. We formalise this problem for positive multiplicative ecological channels.

Let total performance be `W_i(z)=F_i(z)E_i(z)` and let a proxy for one channel be `X_i(z)=q_i(z)F_i(z)`. Stable conversion gives point identification of relative channel changes (N3), whereas unrestricted conversion drift makes them non-identified (N4). The practically useful result lies between these extremes. If the between-regime calibration ratio `kappa=q_1/q_0` is restricted to `[1-delta,1+delta]`, both channel ratios are partially identified. Their marginal intervals have multiplicative width `(1+delta)/(1-delta)`, but they are not independent: the same `kappa` forces `rho_F rho_E=rho_W`. In log-ratio coordinates the sharp joint identified set is therefore a line segment of slope `-1`. A directional conclusion survives exactly while the relevant marginal projection excludes one, yielding a directly reportable calibration-drift breakdown point. In the worked illustration, the conclusion that establishment decreased survives calibration-ratio drift below 34%; at 34% the identified set first touches no change.

We place this result in a broader identification framework. Even the complete net performance curve, all threshold-feasible sets and every geometry or topology derived from them remain net-only and cannot reveal which latent channel changed (N1). One exact channel measurement breaks that equivalence (N2), but transport through a proxy requires either stable calibration or an explicit drift bound. The resulting **anchor-and-transport rule** converts structural non-identification into a field-design prescription. A second operational rule follows from the joint set: calibration uncertainty for the two latent channels must not be reported as independent error bars because the admissible errors are perfectly negatively linked on the log-ratio scale.

The algebra is elementary and related identification arguments are established in structural-identifiability and partial-identification theory. Our contribution is to apply that logic to a recurring ecological measurement architecture, show that apparently rich net-response objects remain non-identifying, derive an operational sharp joint set and breakdown point for proxy drift, and turn the boundary into explicit field-design and reporting rules.

## 1. Introduction

Ecologists often compare mechanisms through quantities that collapse several processes into one observed response. Pollination service is commonly represented by interaction quantity combined with per-visit effectiveness. Seed dispersal effectiveness is explicitly decomposed into a quantity term and a post-dispersal quality term. Recruitment can similarly be represented, over a declared census interval, by propagule production combined with subsequent establishment. These decompositions are scientifically useful because they map biological stages onto measurable components. They also create an identification problem: observing their product does not necessarily reveal which component changed.

The problem becomes sharper when one component is observed only through a proxy. Relative comparisons are often treated as robust because an unknown absolute calibration cancels in a ratio. That is true only if the proxy-to-channel conversion is stable across the comparison. Yet the conversion is most likely to change in precisely the contrasts ecologists care about: fragmented versus connected habitat, urban versus rural sites, warm versus cool years, or communities with different visitor identities and behaviour.

Consider

```text
W_i(z)=F_i(z)E_i(z),    F_i(z)>0, E_i(z)>0,
```

for regimes `i in {0,1}` and trait or state value `z`. Suppose an empirical assay is

```text
X_i(z)=q_i(z)F_i(z),
```

where `q_i(z)>0` converts proxy units into the mathematical channel. We ask four questions. First, how much mechanistic information is retained by arbitrarily rich observations of the net response `W`? Second, what assumptions make a proxy comparison identify relative channel changes? Third, when exact stability is not credible but bounded drift is, what set of channel changes remains compatible with the observations? Fourth, how should that set be reported without inventing impossible combinations of the latent channels?

N1 and N2 establish the endpoints for net-response observations. N1 shows that a broad class of seemingly rich objects—the complete `W(z)` curve, all threshold-feasible sets and every edge, width, component count or topology derived from them—remains invariant to reciprocal reallocations between `F` and `E`. N2 shows that one exact channel observation breaks this invariance by division.

N3 and N4 then locate the practically important proxy boundary. N3 shows that unknown absolute calibration cancels from relative comparisons if `q_1=q_0`. N4 shows that if `q_1/q_0` is unrestricted, channel changes can vary arbitrarily while the observed `W` and `X` remain fixed. The main result fills the gap: a defensible bound on calibration drift generates a sharp identified set and a breakdown point. The output is no longer the unhelpful statement that “the proxy may differ,” but a quantitative statement of how much cross-regime calibration drift is required to overturn the biological conclusion.

A key consequence has been under-emphasised in ecological reporting. Once `W` is fixed, uncertainty in `F` and `E` generated by a common calibration ratio cannot move independently. One channel rises exactly as the other falls on the log-ratio scale. Reporting two marginal intervals as if any pair of endpoints could occur creates a rectangular uncertainty region that contains impossible latent states. The correct object is one-dimensional.

This is a partial-identification problem in the sense of Manski: the data and assumptions may restrict a target parameter to a set even when they do not point-identify it. Structural identifiability itself is long established in system identification and compartmental modelling. We therefore do not claim that the algebra of non-identification is new. The contribution is ecological and operational: identifying which common ecological observation classes are net-only, deriving the exact bounded-drift joint set and its failure threshold, and converting the result into minimal field-design and reporting rules.

## 2. Observation model

### 2.1 Multiplicative channel architecture

Let

```text
W_i(z)=F_i(z)E_i(z).
```

`W` is the declared net output; `F` and `E` are positive latent channels. The symbols do not assert that every ecological fitness measure is multiplicative. The factorisation must be justified for the declared biological output and census interval before any theorem is applied.

### 2.2 Net-only observation class

A net-only observation is any deterministic functional

```text
O_i = Phi(W_i).
```

This includes the full pointwise curve `W_i(z)`. Therefore it also includes, for every threshold `t`,

```text
Omega_t = {z : W_i(z) >= t},
```

and all quantities derived solely from those sets: boundaries, widths, volumes, diameters, maxima, connected-component counts and topological summaries.

The important distinction is between richness of measurement and richness of identifying information. A dense response surface can be extremely informative about `W` and still contain no data-based information about the allocation of that product between `F` and `E`.

### 2.3 Proxy observations

For a proxy of `F`, let

```text
X_i(z)=q_i(z)F_i(z).
```

Define

```text
rho_W = W_1/W_0,
rho_X = X_1/X_0,
rho_F = F_1/F_0,
rho_E = E_1/E_0,
kappa = q_1/q_0.
```

Then

```text
rho_X = kappa rho_F,
rho_W = rho_F rho_E,
```

so

```text
rho_F = rho_X/kappa,
rho_E = (rho_W/rho_X) kappa.
```

Write

```text
rho_E_hat = rho_W/rho_X
```

for the stable-calibration value obtained by setting `kappa=1`.

## 3. Exact identification boundary

### 3.1 N1 — what does not survive decomposition

**Theorem N1.** For any positive functions `F(z)`, `E(z)` and `c(z)`, define

```text
F_c(z)=c(z)F(z),
E_c(z)=E(z)/c(z).
```

Then

```text
F_c(z)E_c(z)=F(z)E(z)=W(z)
```

pointwise. Consequently every net-only observation `Phi(W)` is invariant over

```text
[(F,E)]_W = {(cF,E/c): c(z)>0}.
```

**Proof.** Immediate by substitution. Because equality holds pointwise, applying any deterministic functional `Phi` preserves equality. ∎

The ecological consequence is stronger than the statement that one product has two factors. The complete performance curve, all feasible sets `Omega_t`, and all geometry and topology derived from those sets are unchanged across the entire equivalence class. Hence none of these observations identifies how the observed product is divided between the latent channels.

A before/after corollary makes the channel-change problem explicit. For any positive multiplier `a(z)`,

```text
P_F: (F_1,E_1)=(aF_0,E_0)
P_E: (F_1,E_1)=(F_0,aE_0)
```

produce identical `W_1=aF_0E_0`. No net-only comparison can distinguish them.

### 3.2 N2 — exact channel measurement and Design Rule 1

**Theorem N2.** If `W_i` and one positive mathematical channel are observed on the same domain and census scale, the other is uniquely recovered:

```text
E_i=W_i/F_i
```

or symmetrically

```text
F_i=W_i/E_i.
```

Thus both relative channel changes are point identified, and the result can be fecundity-only, establishment-only, mixed or unchanged without assuming in advance that exactly one channel changed.

**Design Rule 1 — Anchor and transport.** Directly measure at least one latent channel in an anchor regime. This anchors the local proxy conversion. For every comparison regime, either revalidate that conversion directly or prespecify an admissible between-regime drift set for `kappa` and report the resulting identified set and breakdown point.

N2 therefore does not imply that one calibration measurement can be transported without qualification. Exact transport gives N3; bounded transport gives partial identification; unrestricted transport gives N4.

### 3.3 N3 — stable proxy conversion

**Theorem N3.** If

```text
q_1(z)=q_0(z)>0,
```

then `kappa=1`, so

```text
rho_F=rho_X,
rho_E=rho_W/rho_X.
```

Unknown absolute and trait-dependent calibration can therefore cancel from relative comparisons. What matters is cross-regime stability of the conversion, not knowledge of its absolute scale.

### 3.4 N4 — unrestricted drift

**Theorem N4.** If `kappa=q_1/q_0` is unrestricted over positive values, then the same observed `rho_W` and `rho_X` are compatible with

```text
rho_F=rho_X/kappa,
rho_E=rho_E_hat kappa
```

for every positive `kappa`. Both the magnitude and direction of latent channel change can therefore vary while the observations remain unchanged.

N4 is an information boundary, not a claim that proxies are biologically useless. A proxy becomes identifying only through an explicit restriction on its conversion.

## 4. Main result: bounded calibration drift

### 4.1 Sharp marginal intervals

Suppose the cross-regime calibration ratio is prespecified to satisfy

```text
1-delta <= kappa <= 1+delta,    0<=delta<1.
```

This `delta` directly bounds the **between-regime ratio** `q_1/q_0`. It is not a statement that `q_0` and `q_1` independently lie within `+/-delta` of a common calibration constant.

Retaining `kappa` in the N3 algebra gives

```text
rho_F = rho_X/kappa,
rho_E = rho_E_hat kappa.
```

Therefore

```text
rho_F in [rho_X/(1+delta), rho_X/(1-delta)]
rho_E in [rho_E_hat(1-delta), rho_E_hat(1+delta)].
```

Both marginal intervals have multiplicative width

```text
(1+delta)/(1-delta).
```

The sets are **sharp**. For every admissible `kappa`, choose positive `q_0`, set `q_1=kappa q_0`, then reconstruct `F_i=X_i/q_i` and `E_i=W_i/F_i`. This reproduces the observed `W` and `X` exactly and attains the corresponding channel ratios. Every point in each marginal interval is therefore observationally compatible and no point outside it is compatible with the drift restriction.

### 4.2 The sharp joint set is one-dimensional

The same `kappa` simultaneously determines both channel ratios. The sharp joint identified set is therefore

```text
J_delta = {(rho_X/kappa, rho_E_hat*kappa):
           kappa in [1-delta,1+delta]}.
```

Every admissible pair satisfies

```text
rho_F rho_E = rho_W.
```

Hence `J_delta` is **not** the Cartesian product of the two marginal intervals. In the original ratio plane it is the relevant segment of the hyperbola

```text
rho_E = rho_W/rho_F.
```

The geometry becomes especially transparent after taking logs. Define

```text
u = log rho_F,
v = log rho_E.
```

Because

```text
u + v = log rho_W,
```

`J_delta` becomes a straight line segment of slope `-1`. Varying `kappa` gives

```text
du = - d log kappa,
dv = + d log kappa,
```

so one channel log-ratio rises by exactly the amount the other falls. Conditional on the observed `rho_W` and `rho_X`, structural uncertainty arising from calibration drift is therefore perfectly negatively dependent across the two channel log-ratios.

This log-coordinate statement does not change the `delta` parameterisation or the 34% breakpoint below. It is a representation of the same identified set. Sensitivity may additionally be indexed by `eta=log kappa` if a log-symmetric horizontal axis is desirable.

### 4.3 Design Rule 2 — report the joint set, not independent error bars

**Design Rule 2 — Preserve the coupling.** Do not report calibration-drift uncertainty for `rho_F` and `rho_E` as two independently combinable intervals. Report the joint identified set `J_delta`, preferably as the slope-`-1` segment in `(log rho_F, log rho_E)` space; if marginal intervals are also reported, state explicitly that they are linked by `rho_F rho_E=rho_W`.

This rule matters because the upper endpoint of the `rho_F` interval and the upper endpoint of the `rho_E` interval arise from opposite ends of the admissible `kappa` range. They cannot occur together. A conventional presentation such as

```text
F changed by estimate +/- a
E changed by estimate +/- b
```

can therefore be misleading when readers treat the two uncertainties as independent. It creates a rectangular uncertainty region that both exaggerates the apparent two-dimensional uncertainty and includes channel pairs that cannot reproduce the observed net ratio. The correct structural calibration uncertainty is one-dimensional.

This statement concerns calibration uncertainty conditional on the observed net and proxy ratios. Sampling uncertainty in `W` and `X` can add further covariance and should be propagated separately.

### 4.4 Directional robustness and breakdown points

A directional claim is identified only when its relevant marginal projection lies entirely on one side of one.

For the complementary channel,

```text
E decreased  iff  rho_E_hat(1+delta)<1,
E increased  iff  rho_E_hat(1-delta)>1.
```

If `rho_E_hat<1`, the decrease conclusion first reaches no change when

```text
rho_E_hat(1+delta*)=1,
```

so

```text
delta* = 1/rho_E_hat - 1.
```

If `rho_E_hat>1`, the increase conclusion breaks at

```text
delta* = 1 - 1/rho_E_hat.
```

At `delta=delta*` the interval first touches one. A strict directional statement therefore holds for `delta<delta*`, not at equality.

### 4.5 The 34% statement

Take the worked value

```text
rho_E_hat = 1/1.34 = 0.746268...
```

Then

```text
delta* = 0.34.
```

The directly reportable result is:

> The estimated decline in establishment has a calibration-drift breakdown point of 34%: the identified set remains entirely below one for between-regime calibration-ratio drift smaller than 34%.

At the breakdown point, `kappa=1.34` and the upper establishment endpoint reaches one. On the joint log segment, the corresponding fecundity ratio moves in the opposite direction by exactly the compensating amount needed to keep `rho_F rho_E=rho_W`.

### 4.6 Sampling uncertainty is a separate layer

The identified set above conditions on the observed ratio estimates. Sampling variability should be propagated separately. If a confidence interval for `rho_E_hat` is `[L,U]`, monotonicity gives the conservative union

```text
[L(1-delta), U(1+delta)]
```

under the present `kappa=q_1/q_0` parameterisation. A sampling-aware decline claim therefore requires

```text
U(1+delta)<1.
```

Identification uncertainty and sampling uncertainty answer different questions and should be reported separately rather than collapsed into one standard error.

## 5. Why the multiplicative form is not an idiosyncratic assumption

The theorem applies only when a multiplicative architecture is scientifically declared. The relevance is that such architectures already recur in ecological measurement.

Schupp, Jordano & Gómez (2010) provide the clearest cross-domain example. Their seed dispersal effectiveness framework is explicitly `Quantity × Quality`, with quantity defined by the number of seeds dispersed and quality by the probability that a dispersed seed ultimately produces a new adult; both components are context dependent. This is useful here because it shows that the multiplicative measurement problem is not peculiar to pollination.

Pollination provides an independent family of the same architecture. Rader et al. (2012) define overall pollinator effectiveness as pollen-transfer efficiency multiplied by visitation frequency. Ballantyne et al. (2017) measure pollinator importance as visitation frequency multiplied by single-visit pollen deposition effectiveness. Reynolds & Fenster (2008) likewise define pollinator importance as the product of visitation rate and pollinator effectiveness.

These papers do not establish the exact `F` and `E` semantics for every ecological application. They establish something narrower and sufficient for our positioning: quantity-by-quality or rate-by-effectiveness products are standard ecological measurement architectures in at least two distinct ecological literatures. N1–N4 therefore audit an existing inferential practice rather than introduce multiplication solely to manufacture a theorem. The page- and definition-level source audit is maintained in `paper/multiplicative_measurement_literature_audit.md`.

## 6. Observation-design sequence

The two design rules imply the following operational sequence.

1. **Only net performance observed.** Do not attribute the response to a latent channel. Finer or more precise measurement of `W` cannot break N1.
2. **Net performance and one exact channel observed.** Reconstruct the other channel under N2 and propagate statistical uncertainty.
3. **A proxy is transported under defended stable conversion.** Report relative channel changes under N3 and state the stability assumption explicitly.
4. **Calibration drift is bounded but not fixed.** Report the sharp joint set, its marginal projections, multiplicative width and breakdown point. The joint set—not the pair of independent marginals—is the identified object.
5. **Calibration drift is unrestricted.** Do not make a directional channel claim. Directly measure a channel, revalidate calibration in the comparison regime, or justify a drift bound.
6. **A marginal projection includes one.** Additional net-outcome sampling cannot recover that channel direction. The next observation should target calibration or the channel itself.
7. **When displaying uncertainty.** Preserve the coupling. A joint log-ratio plot should show the slope-`-1` identified segment; marginal error bars may be secondary annotations but must not imply a rectangular admissible region.

A high within-regime correlation between proxy and channel is not sufficient evidence for transport. The identifying object is the cross-regime conversion ratio `q_1/q_0` on the comparison domain.

## 7. Relation to existing identification theory

The algebra behind N1–N4 is elementary. Structural identifiability has long asked whether internal model structure can be recovered from input-output observations (Bellman & Åström 1970), and general parametric identification theory is classical (Rothenberg 1971). Partial-identification theory makes explicit that scientifically useful conclusions can be set-valued when assumptions restrict but do not point-identify a target (Manski 2003).

Our novelty claim is therefore deliberately narrow and positive. We contribute four linked ecological results: (i) a broad class of response objects that ecologists may regard as mechanistically rich is shown to be net-only; (ii) regime-specific proxy drift produces a sharp identified set and directly reportable breakdown point; (iii) the same boundary yields a minimal anchor-and-transport observation-design rule; and (iv) the joint-set geometry yields a reporting rule that prevents marginal uncertainty from being misrepresented as independent. The contribution is the ecological application, identified set and operational consequences, not the invention of identifiability algebra itself.

## 8. Scope and extensions

The model assumes positive multiplicative channels. Zeros require separate handling because ratios and division fail. More than two channels creates a higher-dimensional identified set unless enough factors are measured or bounded. Nonmultiplicative interactions require a different observation map.

The result is pointwise in `z`. Uniform conclusions over a trait domain require the interval to exclude one at every predeclared `z`, or require an explicitly defined aggregate estimand. Choosing the trait domain or drift bound after seeing the outcome would invalidate the intended sensitivity interpretation.

The calibration bound is an assumption or externally estimated constraint. The software does not infer `delta` from the same net response and proxy observations whose identifying power is being assessed.

The statement of perfect negative dependence is conditional on the observed `rho_W` and `rho_X` and refers to structural uncertainty from the common calibration ratio. Additional sampling error, process error or uncertainty in the multiplicative factorisation can widen the overall joint uncertainty set beyond this one-dimensional segment.

## 9. Discussion

The useful boundary is not simply identifiable versus non-identifiable. Stable calibration gives point identification; unrestricted drift gives N4; bounded drift yields an intermediate sharp set whose width and directional failure threshold can be reported. This changes an impossibility theorem into a practical robustness analysis.

The joint-set geometry adds an equally practical reporting consequence. The two latent channels do not inherit two free uncertainty dimensions from one unknown calibration ratio. Their calibration-induced errors move in opposite directions while preserving the observed net ratio. Reporting independent uncertainty for the two channels therefore discards information that the model actually retains. In this sense, partial identification can be more informative than two separately propagated error bars: it preserves the exact dependence structure among the latent quantities.

N1 also clarifies why more detailed net-response geometry cannot substitute for channel information. A complete response curve and all of its threshold geometry may describe the ecological pattern exquisitely while remaining invariant to the latent channel decomposition. The remedy is not automatically more samples of the same object, but a measurement that anchors one factor or its conversion.

The boundary paper is intentionally separate from the RACH observation-selection paper. RACH can rank resolving measurements when the admissible mechanism family is too complex for closed-form identification, but it does not make N1 disappear. Here the contribution is the information boundary itself and the field-design and reporting rules it implies.

## Code availability

Deterministic bounded-drift calculations are implemented in `causal_model.bounded_proxy_drift`. Stable-proxy and unrestricted-drift constructions are in `causal_model.proxy_calibration_theory`. Regression tests verify zero-drift recovery, interval width, endpoint attainability, exact joint product consistency, the slope-`-1` log identified segment, rejection of impossible upper-upper marginal combinations, and the 34% breakdown illustration. The implementation does not estimate the calibration bound or treat an assumed bound as empirical evidence.

## References

- Ballantyne, G., Baldock, K.C.R., Rendell, L. & Willmer, P.G. 2017. Pollinator importance networks illustrate the crucial value of bees in a highly speciose plant community. *Scientific Reports* 7:8383. doi:10.1038/s41598-017-08798-x.
- Bellman, R. & Åström, K.J. 1970. On structural identifiability. *Mathematical Biosciences* 7:329–339. doi:10.1016/0025-5564(70)90132-X.
- Manski, C.F. 2003. *Partial Identification of Probability Distributions*. Springer, New York. doi:10.1007/b97478.
- Rader, R. et al. 2012. Spatial and temporal variation in pollinator effectiveness: do unmanaged insects provide consistent pollination services to mass flowering crops? *Journal of Applied Ecology*. doi:10.1111/j.1365-2664.2011.02066.x.
- Reynolds, R.J. & Fenster, C.B. 2008. Point and interval estimation of pollinator importance: a study using pollination data of *Silene caroliniana*. *Oecologia* 156:325–332. doi:10.1007/s00442-008-0982-5.
- Rothenberg, T.J. 1971. Identification in parametric models. *Econometrica* 39:577–591.
- Schupp, E.W., Jordano, P. & Gómez, J.M. 2010. Seed dispersal effectiveness revisited: a conceptual review. *New Phytologist* 188:333–353. doi:10.1111/j.1469-8137.2010.03402.x.
