# Boundary paper: reviewer-objection audit

Status: submission-facing adversarial audit for `paper/boundary_manuscript_draft.md`.

The purpose of this file is not to inflate the novelty claim. It is to force every likely objection into one of three categories: already answered by the theorem, requires an explicit manuscript qualification, or remains an external empirical requirement.

## 1. “The product non-identifiability is trivial.”

**Response required in manuscript:** concede the algebra. The claim is not that products have multiple factorizations. The contribution is the ecological observation class that remains net-only even when apparently rich, the calibration-transport family, the sharp joint set and breakdown factor under finite transport bounds, and the operational design/reporting rules.

**Pass criterion:** N1 is introduced through the complete performance curve, all threshold-feasible sets and their geometry/topology, not through `W=FE` alone. Immediately after the concrete examples, note that positive functions act by `(F,E)->(cF,E/c)` and that every net-only statistic factors through the quotient. Bellman–Åström, Rothenberg and Manski are acknowledged before the novelty sentence.

## 2. “The multiplicative model was chosen to manufacture the theorem.”

**Response required in manuscript:** lead with Schupp, Jordano & Gómez (2010), where seed dispersal effectiveness is explicitly `Quantity × Quality`; then show the independent pollination lineage (Rader; Ballantyne; Reynolds & Fenster) using visitation/rate × per-visit effectiveness.

**Pass criterion:** language says that the architecture recurs in ecology, not that all ecological fitness is multiplicative or that all cited quantities share identical biological semantics.

## 3. “A relative proxy comparison cancels unknown calibration, so there is no problem.”

**Response:** it cancels absolute calibration only under transport stability, `q_1/q_0=1`. The comparison identifies `rho_F` and `rho_E` only through a restriction on `kappa=q_1/q_0`.

**Pass criterion:** the abstract and Introduction state that relative proxy designs are safe only under stable conversion and that this assumption is not testable from `W` and `X` alone.

## 4. “Why should the calibration bound be believed?”

**Response:** neither the canonical `Gamma`/`eta` bound nor the legacy `delta` is inferred from the same `W` and `X` observations. A finite transport tolerance comes from external calibration evidence, validation data, instrument/design knowledge, biological prior information, or a declared sensitivity grid. The purpose is not to claim that the bound is known; it is to expose the dependence of the ecological conclusion on that bound.

The breakdown factor reverses the burden of specification: report the smallest calibration distortion sufficient to overturn the conclusion, then let readers compare that threshold with knowledge of their own system.

**Pass criterion:** the software and paper explicitly state that they do not estimate `Gamma`, `eta` or `delta` from the observations whose identifying power is being assessed.

## 5. “You have only replaced one untestable stability assumption with a family of untestable assumptions.”

**Response:** yes, in the precise partial-identification sense. The analysis does not transform an untestable assumption into empirical knowledge. It indexes the conclusion over an assumption family and reports the failure threshold. This makes assumption dependence visible rather than hiding it at `kappa=1`.

**Pass criterion:** manuscript says explicitly that bounded-drift analysis is a sensitivity analysis / partial-identification device, not an estimator of transportability.

## 6. “The identified intervals for F and E can be reported independently.”

**Response:** no. The same `kappa` generates both ratios. The joint set satisfies `rho_F rho_E=rho_W` exactly. In log-ratio coordinates,

```text
log rho_F + log rho_E = log rho_W,
```

so the set is a line segment of slope `-1`. Pairing both marginal upper endpoints, or both lower endpoints, generally creates impossible latent states.

**Pass criterion:** Design Rule 2 is explicit: report the joint identified set as the primary uncertainty object; marginal intervals are projections only and must not be treated as independently combinable error bars.

## 7. “Calling the errors perfectly negatively correlated is too statistical.”

**Response:** distinguish structural coupling from a stochastic correlation coefficient. Conditional on the observed net ratio and with calibration drift as the only uncertainty dimension, log-channel deviations induced by `kappa` are exactly opposite: `d log rho_E = - d log rho_F`. If sampling uncertainty is also present, the full stochastic covariance need not equal `-1`.

**Pass criterion:** manuscript uses “exactly coupled along a slope-minus-one joint identified set” as the primary wording; “perfect negative dependence” is restricted to the calibration-drift dimension, not generalized to all uncertainty sources.

## 8. “The 34% claim changes if I reverse the reference regime.”

**Response:** this is why the canonical robustness scale is now the multiplicatively symmetric factor

```text
1/Gamma <= kappa <= Gamma.
```

The breakdown factor is

```text
Gamma_star=max(rho_hat,1/rho_hat),
eta_star=|log rho_hat|,
```

so `rho_hat=1/1.34` and `rho_hat=1.34` both have `Gamma_star=1.34`. The 34% statement is retained only as the directional translation of the decline example (`kappa=1.34` at failure), not as the invariant cross-study robustness scale.

**Pass criterion:** primary theory and cross-contrast reporting use `Gamma_star` or `eta_star`; the legacy `delta` language is clearly identified as directional/additive-around-one.

## 9. “Why not define drift symmetrically on the log scale?”

**Response:** we now do. The canonical bound is `1/Gamma <= kappa <= Gamma`, equivalently `|log kappa|<=eta` with `eta=log Gamma`. The old `kappa in [1-delta,1+delta]` implementation remains for reproducibility and the reader-facing 34% worked example.

**Pass criterion:** do not silently reinterpret `delta`; state the conversion in words and keep `Gamma/eta` as the canonical family.

## 10. “Sampling uncertainty is being confused with identification uncertainty.”

**Response:** they are separate layers. A calibration identified set is conditional on the observed or estimated net/proxy ratios. Sampling uncertainty in those ratios should be propagated around the structural set, not substituted for it.

**Pass criterion:** standard errors do not replace the identified set, and calibration sensitivity does not replace sampling uncertainty.

## 11. “N3 and N4 are unrelated endpoint statements.”

**Response:** under the symmetric transport family they are exact endpoints:

```text
Gamma=1          -> N3 point identification
1<Gamma<infinity -> sharp partial identification
Gamma->infinity  -> N4 unrestricted-drift non-identification.
```

**Pass criterion:** N4 is never described as the `delta->1` limit of the legacy additive bound. It is the `Gamma->infinity` endpoint of the canonical multiplicative family.

## 12. “One anchor calibration is insufficient if the system changes.”

**Response:** agreed. Design Rule 1 is therefore graded rather than binary. One anchor identifies local conversion but not cross-regime transport; finite `Gamma/eta` remains external. Two direct anchors measure both `q_0` and `q_1`, hence `kappa=q_1/q_0`, and remove the need for a sensitivity bound for that comparison.

**Pass criterion:** include the anchor ladder:

```text
0 anchors -> unrestricted transport: non-identification
1 anchor  -> external finite transport bound: partial identification + breakdown
2 anchors -> observed kappa: point identification
```

Clarify that this ladder concerns direct transport calibration; an analyst can always *assume* stable transport without anchors, but that assumption is not validated by the net/proxy data.

## 13. “Two anchors do not identify anything unless the true channel is actually measured.”

**Response:** correct. An anchor means the proxy `X_i` and its corresponding mathematical channel are both directly measured on the same scale/domain, so `q_i=X_i/F_i` (or the symmetric establishment form) is observed. Merely having two proxy observations is not two anchors.

**Pass criterion:** define an anchor operationally in Methods.

## 14. “What is the minimum publishable claim?”

The manuscript should survive even if reviewers reject broader rhetoric. The minimum defensible contribution is:

1. a structural ecological audit showing that complete net-response geometry is invariant under the positive-function group action and therefore factors through a quotient;
2. one calibration-transport family whose stable, bounded and unrestricted cases recover N3, sharp partial identification, and N4;
3. a reference-invariant breakdown factor `Gamma_star` / `eta_star` plus the sharp **joint** identified set;
4. **Design Rule 1 — graded anchor and transport**;
5. **Design Rule 2 — Preserve the coupling**.

RACH, NOV, synthetic benchmark performance, Campanula causal claims and any claim that multiplicative decomposition is universal are not required for this paper.

## Submission stop conditions

Do not submit if any of the following is true:

- `Gamma`, `eta` or `delta` is described as estimated from the same net/proxy data;
- the manuscript implies bounded-drift analysis proves transportability rather than indexing sensitivity to it;
- the 34% statement includes equality as a strict decline;
- 34% is used as the canonical reversal-invariant robustness metric instead of `Gamma_star=1.34` / `eta_star`;
- marginal F/E intervals are visually or verbally presented as independent uncertainty;
- N4 is described as the `delta -> 1` limit;
- “anchor” is used for a proxy-only observation without direct measurement of the corresponding mathematical channel;
- the literature paragraph implies identical channel semantics across pollination and seed dispersal;
- the manuscript presents elementary identifiability algebra itself as the primary novelty;
- the boundary paper drifts back into the RACH/MEE methods claim spine.
