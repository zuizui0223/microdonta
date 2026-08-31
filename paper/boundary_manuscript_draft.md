# From proxy stability to breakdown factors: partial identification of multiplicative ecological channels

> **Boundary-paper draft.** This manuscript is separate from the RACH observation-selection submission. Its contribution is the net-only information boundary, one calibration-transport family linking point identification, partial identification and non-identification, and the observation-design and reporting rules implied by that boundary.

## Abstract

Proxy-based estimates of relative change identify channel-specific change only when the proxy-to-channel conversion is stable across the compared regimes. That assumption is not testable from the net response and proxy observations alone, and it is especially vulnerable in habitat, climate, fragmentation and community-composition contrasts where relative proxy designs are often treated as safest. We formalise this problem for positive multiplicative ecological channels.

Let total performance be `W_i(z)=F_i(z)E_i(z)` and let a proxy for one channel be `X_i(z)=q_i(z)F_i(z)`, with `kappa=q_1/q_0`. We place stable, bounded and unrestricted proxy transport in one multiplicatively symmetric family, `1/Gamma <= kappa <= Gamma`, `Gamma>=1`. `Gamma=1` gives stable-calibration point identification (N3); finite `Gamma>1` gives a sharp joint identified set; and `Gamma->infinity` recovers unrestricted-drift non-identification (N4). For the complementary channel, the sharp marginal interval is `[rho_hat/Gamma, rho_hat*Gamma]`. The same `kappa` determines both channels, so `rho_F rho_E=rho_W` exactly and the joint identified set is a slope-`-1` line segment in log-ratio coordinates. Directional robustness is summarized by the reference-invariant breakdown factor `Gamma*=max(rho_hat,1/rho_hat)` or `eta*=|log rho_hat|`. In the worked decline, `Gamma*=1.34`; equivalently, the conclusion survives upward calibration-ratio drift smaller than 34% and first reaches no change at a factor of 1.34.

We place this result in a broader identification framework. Even the complete net performance curve, all threshold-feasible sets and every geometry or topology derived from them remain net-only and cannot reveal which latent channel changed (N1). This closure follows structurally from the action of positive functions `(F,E)->(cF,E/c)`, under which all net-only observables are invariant. Direct calibration effort then forms an anchor ladder: with no transport anchors, unrestricted drift remains non-identified; one anchor localises calibration but finite transport tolerance remains external, yielding partial identification and a breakdown factor; two anchors measure `q_0`, `q_1` and therefore `kappa` directly, restoring point identification without a sensitivity bound. A second operational rule follows from the joint set: the two channel uncertainties induced by calibration drift must not be reported as independent error bars.

The algebra is elementary and related identification arguments are established in structural-identifiability and partial-identification theory. Our contribution is to apply that logic to a recurring ecological measurement architecture, show that apparently rich net-response objects remain non-identifying, close stable and unstable proxy transport into one operational partial-identification family, and turn the boundary into explicit field-design and reporting rules.

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

where `q_i(z)>0` converts proxy units into the mathematical channel. We ask four questions. First, how much mechanistic information is retained by arbitrarily rich observations of the net response `W`? Second, how does proxy transport move continuously between stable calibration, bounded uncertainty and unrestricted non-identification? Third, what direct measurements are required to move from non-identification to partial or point identification? Fourth, how should the resulting uncertainty be reported without inventing impossible combinations of the latent channels?

N1 establishes the net-response boundary. A broad class of seemingly rich objects—the complete `W(z)` curve, all threshold-feasible sets and every edge, width, component count or topology derived from them—remains invariant to reciprocal reallocations between `F` and `E`. N2 shows that exact channel measurement breaks this invariance by division. The proxy problem is then governed by one transport ratio, `kappa=q_1/q_0`.

Rather than treating stable calibration (N3), bounded drift and unrestricted drift (N4) as separate results, we place them in one calibration-transport family. A multiplicatively symmetric bound `1/Gamma <= kappa <= Gamma` gives a continuum from point identification at `Gamma=1`, through sharp partial identification for finite `Gamma>1`, to N4 as `Gamma->infinity`. This formulation also supplies a reference-invariant breakdown factor. It avoids the asymmetry of additive-around-one percentage bounds when the reference regime is reversed.

A key consequence has been under-emphasised in ecological reporting. Once `W` is fixed, uncertainty in `F` and `E` generated by a common calibration ratio cannot move independently. One channel rises exactly as the other falls on the log-ratio scale. Reporting two marginal intervals as if any pair of endpoints could occur creates a rectangular uncertainty region that contains impossible latent states. The correct structural object is one-dimensional.

This is a partial-identification problem in the sense of Manski: the data and assumptions may restrict a target parameter to a set even when they do not point-identify it. Structural identifiability itself is long established in system identification and compartmental modelling. We therefore do not claim that the algebra of non-identification is new. The contribution is ecological and operational: identifying which common ecological observation classes are net-only, deriving the exact transport-family joint set and its failure threshold, and converting the result into graded field-design and reporting rules.

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

## 3. Net-only identification boundary

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

The closure is structural. Positive functions `c(z)>0` form a multiplicative group acting on latent decompositions by

```text
c . (F,E) = (cF,E/c).
```

`W=FE` is invariant under this action. Therefore every net-only observable `Phi(W)` is constant on each orbit and factors through the quotient of latent decompositions by this action. The complete performance curve, all feasible sets `Omega_t`, and all geometry and topology derived from those sets are examples of the same invariant class, not separate exceptions that must be checked one by one.

A before/after corollary makes the channel-change problem explicit. For any positive multiplier `a(z)`,

```text
P_F: (F_1,E_1)=(aF_0,E_0)
P_E: (F_1,E_1)=(F_0,aE_0)
```

produce identical `W_1=aF_0E_0`. No net-only comparison can distinguish them.

### 3.2 N2 — exact channel measurement

**Theorem N2.** If `W_i` and one positive mathematical channel are observed on the same domain and census scale, the other is uniquely recovered:

```text
E_i=W_i/F_i
```

or symmetrically

```text
F_i=W_i/E_i.
```

Thus both channel values are point identified within that regime. Relative channel changes are point identified across two regimes when the corresponding channel is directly observed in both regimes or when proxy transport between regimes is otherwise known.

N2 does not imply that one calibration measurement can be transported without qualification. That transport problem is the subject of the next section.

## 4. Main theorem: the calibration-transport family

Let the between-regime proxy conversion ratio satisfy

```text
1/Gamma <= kappa <= Gamma,    Gamma>=1.
```

Equivalently, define `eta=log Gamma` and require

```text
|log kappa| <= eta.
```

### 4.1 Calibration-transport theorem

**Theorem T1 — Calibration transport family.** Conditional on observed positive `rho_W` and `rho_X`, and with `rho_E_hat=rho_W/rho_X`, the admissible channel ratios under `1/Gamma <= kappa <= Gamma` are

```text
rho_F = rho_X/kappa,
rho_E = rho_E_hat kappa,
```

with sharp marginals

```text
rho_F in [rho_X/Gamma, rho_X*Gamma],
rho_E in [rho_E_hat/Gamma, rho_E_hat*Gamma].
```

The sharp joint identified set is

```text
J_Gamma = {(rho_X/kappa, rho_E_hat*kappa):
           1/Gamma <= kappa <= Gamma}.
```

Every admissible pair satisfies

```text
rho_F rho_E = rho_W.
```

For every admissible `kappa`, choose any positive `q_0`, set `q_1=kappa q_0`, reconstruct `F_i=X_i/q_i`, and set `E_i=W_i/F_i`. This reproduces the observations exactly, so the set is sharp. ∎

The stable, bounded and unrestricted cases are the same family:

```text
Gamma = 1          -> kappa=1 exactly -> point identification (N3)
1 < Gamma < inf    -> sharp partial identification
Gamma -> infinity  -> kappa unrestricted over positive values -> N4
```

Thus N3 and N4 are endpoint corollaries of T1 rather than unrelated theorem statements.

### 4.2 N3 as the stable endpoint

At `Gamma=1`, `kappa=1`, so

```text
rho_F=rho_X,
rho_E=rho_W/rho_X.
```

Unknown absolute and trait-dependent calibration cancels from the relative comparison. What matters is cross-regime stability of the conversion, not knowledge of its absolute scale.

### 4.3 N4 as the unrestricted endpoint

As the finite restriction is removed, equivalently `Gamma->infinity`, every positive `kappa` becomes admissible. The same observed `rho_W` and `rho_X` are then compatible with arbitrary positive movements along

```text
rho_F=rho_X/kappa,
rho_E=rho_E_hat kappa.
```

Both the magnitude and direction of latent channel change can vary while the observations remain unchanged. N4 is an information boundary, not a claim that proxies are biologically useless; a proxy becomes identifying only through an explicit restriction on its conversion or direct calibration of that conversion.

## 5. Joint geometry and Design Rule 2

### 5.1 The sharp joint set is one-dimensional

Because the same `kappa` simultaneously determines both channel ratios, `J_Gamma` is not the Cartesian product of the two marginal intervals. In the original ratio plane it is the relevant segment of the hyperbola

```text
rho_E = rho_W/rho_F.
```

Define

```text
u = log rho_F,
v = log rho_E.
```

Then

```text
u + v = log rho_W,
```

so `J_Gamma` becomes a straight line segment of slope `-1`. Varying `kappa` gives

```text
du = - d log kappa,
dv = + d log kappa.
```

One channel log-ratio therefore rises by exactly the amount the other falls. Conditional on the observed `rho_W` and `rho_X`, calibration drift contributes one structural uncertainty dimension.

### 5.2 Design Rule 2 — Preserve the coupling

**Design Rule 2.** Do not report calibration-drift uncertainty for `rho_F` and `rho_E` as two independently combinable intervals. Report the joint identified set `J_Gamma`, preferably as the slope-`-1` segment in `(log rho_F, log rho_E)` space; if marginal intervals are also reported, state explicitly that they are linked by `rho_F rho_E=rho_W`.

The upper endpoint of the `rho_F` interval and the upper endpoint of the `rho_E` interval arise from opposite ends of the admissible `kappa` range and cannot occur together. Treating the marginals as independent creates a rectangular uncertainty region that exaggerates the dimensionality of the uncertainty and includes channel pairs that cannot reproduce the observed net ratio.

This statement concerns structural calibration uncertainty conditional on the observed net and proxy ratios. Sampling uncertainty in `W` and `X` can add further covariance and should be propagated separately.

## 6. Breakdown factors and the role of external assumptions

### 6.1 Reference-invariant breakdown factor

A directional claim is identified only when the relevant marginal projection lies entirely on one side of one. Under T1, the smallest symmetric multiplicative distortion that reaches no change is

```text
Gamma* = max(rho_hat, 1/rho_hat).
```

Equivalently,

```text
eta* = |log rho_hat|.
```

These measures are invariant to reversing the reference regime. If `rho_hat=1/1.34` or `rho_hat=1.34`, both give

```text
Gamma*=1.34,
eta*=log(1.34).
```

This invariance is the reason `Gamma*` or `eta*` is the primary robustness metric.

### 6.2 The 34% directional translation

For the worked decline

```text
rho_E_hat = 1/1.34 = 0.746268...
```

we obtain

```text
Gamma*=1.34.
```

The reader-facing directional translation is:

> The estimated decline in establishment has a calibration-distortion breakdown factor of 1.34: equivalently, the identified set remains entirely below one for upward between-regime calibration-ratio drift smaller than 34%, and first touches no change when the calibration ratio reaches 1.34.

The strict decline therefore holds below the boundary, not at equality.

The previous additive-around-one sensitivity display

```text
1-delta <= kappa <= 1+delta
```

is retained in the software for reproducibility and for this directional 34% interpretation. It is not the canonical cross-contrast robustness scale because reversing the reference regime changes its percentage breakpoint. The symmetric `Gamma/eta` family removes that artefact.

### 6.3 Gamma is not identified from the same data

A finite `Gamma` or `eta` is not identified from the same net-response and proxy observations whose identifying power is being assessed. Bounded-drift analysis does not claim otherwise. Its purpose is to expose the dependence of the ecological conclusion on an externally supplied transport tolerance.

This replaces a hidden single assumption (`kappa=1`) with an explicit family of assumptions indexed by `Gamma`. The gain is transparency, not magical identification. The breakdown factor reverses the usual burden of specification: rather than requiring the analyst to assert one uniquely correct finite bound, it reports the smallest multiplicative calibration distortion sufficient to overturn the conclusion. Readers can compare that threshold with independent calibration experiments, instrument knowledge, biological prior information, validation data or direct anchor measurements.

The software therefore does not infer `Gamma`, `eta` or the legacy `delta` from the same `W` and `X` observations.

### 6.4 Sampling uncertainty is a separate layer

The identified set above conditions on the observed ratio estimates. Sampling variability should be propagated separately. Standard errors do not replace identification analysis, and a sensitivity bound does not replace sampling uncertainty. If uncertainty in `rho_W` or `rho_X` is material, the sampling distribution or confidence region should be propagated through the structural joint set.

## 7. Design Rule 1 as an anchor ladder

An **anchor** means that the proxy and the corresponding mathematical channel are both directly measured in the same regime and on the same comparison domain, so a local conversion `q_i` is observed. Merely observing the proxy twice does not create two anchors.

Direct calibration effort produces a graded design ladder.

| direct anchors | transport information | identification consequence |
|---:|---|---|
| 0 | no direct information on `q_1/q_0` | with unrestricted `kappa`, N4 non-identification |
| 1 | one local `q_i` observed; cross-regime transport still unknown | external finite `Gamma/eta` gives sharp partial identification + breakdown |
| 2 | `q_0` and `q_1` observed, hence `kappa=q_1/q_0` measured | point identification; no external transport bound required |

With two anchors,

```text
q_0 = X_0/F_0,
q_1 = X_1/F_1,
kappa = q_1/q_0,
```

or symmetrically when the proxy targets establishment. Substituting the observed `kappa` into

```text
rho_F=rho_X/kappa,
rho_E=rho_W/rho_F
```

point-identifies both channel ratios.

**Design Rule 1 — Graded anchor and transport.** Choose direct calibration effort according to the strength of inference required. With no direct transport calibration, do not make a channel claim under unrestricted drift. With one anchor, combine local calibration with a prespecified external transport bound and report the sharp joint set plus its breakdown factor. With two anchors, measure both local conversions and use the observed `kappa` for point identification.

The ladder concerns what direct measurement buys. An analyst may always impose stable transport without anchors, but that is an assumption (`Gamma=1`), not a fact validated by the net and proxy observations.

## 8. Why the multiplicative form is not an idiosyncratic assumption

The theorem applies only when a multiplicative architecture is scientifically declared. The relevance is that such architectures already recur in ecological measurement.

Schupp, Jordano & Gómez (2010) provide the clearest cross-domain example. Their seed dispersal effectiveness framework is explicitly `Quantity × Quality`, with quantity defined by the number of seeds dispersed and quality by the probability that a dispersed seed ultimately produces a new adult; both components are context dependent. This is useful here because it shows that the multiplicative measurement problem is not peculiar to pollination.

Pollination provides an independent family of the same architecture. Rader et al. (2012) define overall pollinator effectiveness as pollen-transfer efficiency multiplied by visitation frequency. Ballantyne et al. (2017) measure pollinator importance as visitation frequency multiplied by single-visit pollen deposition effectiveness. Reynolds & Fenster (2008) likewise define pollinator importance as the product of visitation rate and pollinator effectiveness.

These papers do not establish the exact `F` and `E` semantics for every ecological application. They establish something narrower and sufficient for our positioning: quantity-by-quality or rate-by-effectiveness products are standard ecological measurement architectures in at least two distinct ecological literatures. The theorem therefore audits an existing inferential practice rather than introducing multiplication solely to manufacture a result. The page- and definition-level source audit is maintained in `paper/multiplicative_measurement_literature_audit.md`.

## 9. Observation-design sequence

The two design rules imply the following operational sequence.

1. **Only net performance observed.** Do not attribute the response to a latent channel. Finer or more precise measurement of `W` cannot break N1.
2. **Exact channel measured within a regime.** Reconstruct the complementary channel under N2 on that regime and census scale.
3. **Proxy transport assumed stable.** This is the `Gamma=1` endpoint. Report point-identified relative channel changes and state the stability assumption explicitly.
4. **Proxy transport bounded but not known.** Choose an externally justified finite `Gamma/eta`, report the sharp joint set, its marginal projections and `Gamma*`/`eta*` breakdown.
5. **Two calibration anchors available.** Measure `q_0`, `q_1` and `kappa`; use observed transport for point identification instead of an external sensitivity bound.
6. **Calibration drift unrestricted.** Do not make a directional channel claim. Add an anchor, revalidate calibration, or justify a finite transport bound.
7. **When displaying uncertainty.** Preserve the coupling. A joint log-ratio plot should show the slope-`-1` identified segment; marginal error bars may be secondary annotations but must not imply a rectangular admissible region.

A high within-regime correlation between proxy and channel is not sufficient evidence for transport. The identifying object is the cross-regime conversion ratio `q_1/q_0` on the comparison domain.

## 10. Relation to existing identification theory

The algebra behind N1, T1 and its endpoint corollaries is elementary. Structural identifiability has long asked whether internal model structure can be recovered from input-output observations (Bellman & Åström 1970), and general parametric identification theory is classical (Rothenberg 1971). Partial-identification theory makes explicit that scientifically useful conclusions can be set-valued when assumptions restrict but do not point-identify a target (Manski 2003).

Our novelty claim is deliberately narrow and positive. We contribute five linked ecological results: (i) a broad class of response objects that ecologists may regard as mechanistically rich is shown to be net-only and structurally closed under a positive-function group action; (ii) stable, bounded and unrestricted proxy transport are organised as one calibration-transport family; (iii) finite transport bounds yield a sharp joint identified set and reference-invariant breakdown factor; (iv) the same boundary yields a graded anchor-and-transport observation-design rule; and (v) the joint-set geometry yields a reporting rule that prevents marginal uncertainty from being misrepresented as independent. The contribution is the ecological application, identified-set closure and operational consequences, not the invention of identifiability algebra itself.

## 11. Scope and extensions

The model assumes positive multiplicative channels. Zeros require separate handling because ratios and division fail. More than two channels creates a higher-dimensional identified set unless enough factors are measured or bounded. Nonmultiplicative interactions require a different observation map.

The result is pointwise in `z`. Uniform conclusions over a trait domain require the relevant set to exclude one at every predeclared `z`, or require an explicitly defined aggregate estimand. Choosing the trait domain or transport bound after seeing the outcome would invalidate the intended sensitivity interpretation.

The calibration bound is an assumption or externally estimated constraint unless enough direct anchors measure `kappa`. The statement of exact negative coupling is conditional on the observed `rho_W` and `rho_X` and refers to structural uncertainty from the common calibration ratio. Additional sampling error, process error or uncertainty in the multiplicative factorisation can widen the overall joint uncertainty set beyond this one-dimensional segment.

## 12. Discussion

The useful boundary is not simply identifiable versus non-identifiable. One calibration-transport family contains three regimes: stable calibration gives point identification, finite transport uncertainty gives a sharp partial-identification set, and unrestricted transport gives N4. The family turns an impossibility result into a robustness analysis while making clear that the robustness bound itself is external unless transport is directly calibrated.

The anchor ladder makes that externality operational rather than embarrassing. Zero direct anchors leave transport unconstrained unless assumed. One anchor identifies local conversion but still requires an external statement about transport, making partial identification the appropriate language. Two anchors measure the transport ratio itself and restore point identification. The question “where does the sensitivity bound come from?” therefore becomes a field-design question: how much direct calibration is the investigator willing to buy?

The joint-set geometry adds an equally practical reporting consequence. The two latent channels do not inherit two free uncertainty dimensions from one unknown calibration ratio. Their calibration-induced deviations move in opposite directions while preserving the observed net ratio. Reporting independent uncertainty for the two channels discards information that the model actually retains.

N1 clarifies why more detailed net-response geometry cannot substitute for channel information. A complete response curve and all of its threshold geometry may describe the ecological pattern exquisitely while remaining invariant to the latent channel decomposition. The group-action formulation makes this closure explicit: net-only observables live on the quotient, so they cannot distinguish points within an equivalence orbit.

The boundary paper is intentionally separate from the RACH observation-selection paper. RACH can rank resolving measurements when the admissible mechanism family is too complex for closed-form identification, but it does not make N1 disappear. Here the contribution is the information boundary itself and the field-design and reporting rules it implies.

## Code availability

Deterministic symmetric transport calculations, reference-invariant breakdown factors and the anchor ladder are implemented in `causal_model.calibration_transport_family`. The legacy additive-around-one drift calculations and 34% directional illustration remain in `causal_model.bounded_proxy_drift`; stable-proxy and unrestricted-drift constructions remain in `causal_model.proxy_calibration_theory`. Regression tests verify stable-endpoint recovery, finite-bound sharp intervals, reference-reversal invariance of `Gamma*`, direct recovery of `kappa` from two anchors, exact joint product consistency, the slope-`-1` log identified segment, rejection of impossible upper-upper marginal combinations, and the worked 1.34 breakdown factor. The implementation does not estimate a calibration bound from the observations whose identifying power is under assessment.

## References

- Ballantyne, G., Baldock, K.C.R., Rendell, L. & Willmer, P.G. 2017. Pollinator importance networks illustrate the crucial value of bees in a highly speciose plant community. *Scientific Reports* 7:8383. doi:10.1038/s41598-017-08798-x.
- Bellman, R. & Åström, K.J. 1970. On structural identifiability. *Mathematical Biosciences* 7:329–339. doi:10.1016/0025-5564(70)90132-X.
- Manski, C.F. 2003. *Partial Identification of Probability Distributions*. Springer, New York. doi:10.1007/b97478.
- Rader, R. et al. 2012. Spatial and temporal variation in pollinator effectiveness: do unmanaged insects provide consistent pollination services to mass flowering crops? *Journal of Applied Ecology*. doi:10.1111/j.1365-2664.2011.02066.x.
- Reynolds, R.J. & Fenster, C.B. 2008. Point and interval estimation of pollinator importance: a study using pollination data of *Silene caroliniana*. *Oecologia* 156:325–332. doi:10.1007/s00442-008-0982-5.
- Rothenberg, T.J. 1971. Identification in parametric models. *Econometrica* 39:577–591.
- Schupp, E.W., Jordano, P. & Gómez, J.M. 2010. Seed dispersal effectiveness revisited: a conceptual review. *New Phytologist* 188:333–353. doi:10.1111/j.1469-8137.2010.03402.x.
