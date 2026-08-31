# Boundary paper: reviewer-objection audit

Status: submission-facing adversarial audit for `paper/boundary_manuscript_draft.md`.

The purpose of this file is not to inflate the novelty claim. It is to force every likely objection into one of three categories: already answered by the theorem, requires an explicit manuscript qualification, or remains an external empirical requirement.

## 1. “The product non-identifiability is trivial.”

**Response required in manuscript:** concede the algebra. The claim is not that products have multiple factorizations. The contribution is the ecological observation class that remains net-only even when apparently rich, the bounded-drift sharp joint set and breakdown point, and the two operational design/reporting rules.

**Pass criterion:** N1 is introduced through the complete performance curve, all threshold-feasible sets and their geometry/topology, not through `W=FE` alone. Bellman–Åström, Rothenberg and Manski are acknowledged before the novelty sentence.

## 2. “The multiplicative model was chosen to manufacture the theorem.”

**Response required in manuscript:** lead with Schupp, Jordano & Gómez (2010), where seed dispersal effectiveness is explicitly `Quantity × Quality`; then show the independent pollination lineage (Rader; Ballantyne; Reynolds & Fenster) using visitation/rate × per-visit effectiveness.

**Pass criterion:** language says that the architecture recurs in ecology, not that all ecological fitness is multiplicative or that all cited quantities share identical biological semantics.

## 3. “A relative proxy comparison cancels unknown calibration, so there is no problem.”

**Response:** it cancels absolute calibration only under transport stability, `q_1/q_0=1`. The comparison identifies `rho_F` and `rho_E` only through a restriction on `kappa=q_1/q_0`.

**Pass criterion:** the abstract and Introduction state that relative proxy designs are safe only under stable conversion and that this assumption is not testable from `W` and `X` alone.

## 4. “Why should delta be believed?”

**Response:** `delta` is not inferred from the same `W` and `X` observations. It is prespecified from external calibration evidence, validation data, design knowledge, or a scientific sensitivity grid.

**Pass criterion:** the software and paper explicitly state that they do not estimate `delta` from the observations whose identifying power is being assessed.

## 5. “The identified intervals for F and E can be reported independently.”

**Response:** no. The same `kappa` generates both ratios. The joint set satisfies `rho_F rho_E=rho_W` exactly. In log-ratio coordinates,

```text
log rho_F + log rho_E = log rho_W,
```

so the set is a line segment of slope `-1`. Pairing both marginal upper endpoints, or both lower endpoints, generally creates impossible latent states.

**Pass criterion:** Design Rule 2 is explicit: report the joint identified set as the primary uncertainty object; marginal intervals are projections only and must not be treated as independently combinable error bars.

## 6. “Calling the errors perfectly negatively correlated is too statistical.”

**Response:** distinguish structural coupling from a stochastic correlation coefficient. Conditional on the observed net ratio and with calibration drift as the only uncertainty dimension, log-channel deviations induced by `kappa` are exactly opposite: `d log rho_E = - d log rho_F`. If sampling uncertainty is also present, the full stochastic covariance need not equal `-1`.

**Pass criterion:** manuscript uses “exactly coupled along a slope-minus-one joint identified set” as the primary wording; “perfect negative dependence” is restricted to the calibration-drift dimension, not generalized to all uncertainty sources.

## 7. “The 34% claim is imprecise at the boundary.”

**Response:** the directional decline holds for `delta<0.34`. At `delta=0.34`, the identified set first touches one; strict decline is no longer identified.

**Pass criterion:** never say “through 34%” or “up to and including 34%.” Use “breakdown point 34%” and “survives drift smaller than 34%.”

## 8. “Why not define drift symmetrically on the log scale?”

**Response:** the current scientific sensitivity parameter is the direct bound `kappa in [1-delta,1+delta]`, retained because the 34% breakpoint and field interpretation are already expressed in that scale. Log-ratio coordinates are used for the geometry of the joint set. A supplementary sensitivity parameter `eta=log kappa` may be reported when a multiplicatively symmetric drift bound is scientifically preferable.

**Pass criterion:** do not silently replace the definition of `delta`. Clearly distinguish the geometry coordinate transformation from an alternative drift parameterization.

## 9. “Sampling uncertainty is being confused with identification uncertainty.”

**Response:** they are separate layers. For a sampling interval `[L,U]` on the stable-calibration complementary ratio, the conservative bounded-drift union is `[L(1-delta), U(1+delta)]`; the sign claim requires `U(1+delta)<1`.

**Pass criterion:** standard errors do not replace the identified set, and calibration sensitivity does not replace sampling uncertainty.

## 10. “N4 is just the delta→1 limit.”

**Response:** no. In the additive ratio-bound family, `delta<1` implies `kappa<2`; letting `delta` approach one does not span all positive calibration ratios. N4 is obtained by removing the restriction on `kappa`, not by taking that limit.

**Pass criterion:** this distinction appears wherever N3 → bounded drift → N4 is diagrammed.

## 11. “One anchor calibration is insufficient if the system changes.”

**Response:** agreed; that is exactly Design Rule 1. An anchor fixes local conversion. Comparison regimes require revalidation or an externally defended transport bound.

## 12. “What is the minimum publishable claim?”

The manuscript should survive even if reviewers reject broader rhetoric. The minimum defensible contribution is:

1. a formal ecological audit showing that complete net-response geometry remains invariant to reciprocal channel reallocation;
2. the sharp **joint** identified set under bounded between-regime proxy drift, including its marginal width and sign breakdown point;
3. **Design Rule 1 — Anchor and transport**;
4. **Design Rule 2 — Preserve the coupling**.

RACH, NOV, synthetic benchmark performance, Campanula causal claims and any claim that multiplicative decomposition is universal are not required for this paper.

## Submission stop conditions

Do not submit if any of the following is true:

- `delta` is described as estimated from the same net/proxy data;
- the 34% statement includes equality as a strict decline;
- marginal F/E intervals are visually or verbally presented as independent uncertainty;
- N4 is described as the `delta -> 1` limit;
- the literature paragraph implies identical channel semantics across pollination and seed dispersal;
- the manuscript presents elementary identifiability algebra itself as the primary novelty;
- the boundary paper drifts back into the RACH/MEE methods claim spine.
