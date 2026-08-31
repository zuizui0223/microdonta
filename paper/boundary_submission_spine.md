# Boundary paper — submission spine

Status: normative claim-compression note for `paper/boundary_manuscript_draft.md`.

The paper should be sold as a **closed identification workflow**, not as deep new algebra and not as a list of five separate novelties.

## One-sentence claim

For multiplicative ecological responses observed through net outcomes and transported proxies, mechanistic change moves from non-identification to sharp partial identification to point identification according to the amount of calibration information supplied; the same structure yields a reference-invariant breakdown factor and two direct design/reporting rules.

## Three contribution pillars

### Pillar 1 — Net-only information boundary

For `W=FE`, positive functions act by

```text
(F,E) -> (cF,E/c).
```

Every net-only observable `Phi(W)` is invariant on these orbits and therefore factors through the quotient. Complete response curves, all threshold-feasible sets and their geometry/topology remain mechanistically non-identifying.

**Do not sell:** “products have multiple factorizations.”

**Sell:** apparently rich ecological observation objects remain in the same non-identifying equivalence class.

### Pillar 2 — Calibration-transport family and breakdown

For `kappa=q_1/q_0`, use the canonical symmetric restriction

```text
1/Gamma <= kappa <= Gamma,   Gamma >= 1.
```

This is one family:

```text
Gamma = 1          -> point identification (N3)
1 < Gamma < inf    -> sharp partial identification
Gamma -> inf       -> unrestricted non-identification (N4)
```

The complementary-channel marginal is

```text
[rho_hat/Gamma, rho_hat*Gamma]
```

and the joint set satisfies `rho_F rho_E=rho_W`. Directional robustness is summarized by

```text
Gamma* = max(rho_hat, 1/rho_hat)
eta*   = |log rho_hat|.
```

These are invariant to reversing the reference regime. The worked `rho_hat=1/1.34` result has `Gamma*=1.34`; “34% upward drift” is a directional translation, not the canonical robustness scale.

**Do not claim:** `Gamma` is identified from the same net/proxy data.

**Claim:** the family exposes assumption dependence, and the breakdown factor reports the minimum calibration distortion needed to overturn the conclusion.

### Pillar 3 — Operational consequences

**Design Rule 1 — Graded anchor and transport**

```text
0 anchors -> unrestricted transport: non-identification
1 anchor  -> local q + external Gamma/eta: sharp set + breakdown
2 anchors -> observe q0,q1 and kappa directly: point identification
```

**Design Rule 2 — Preserve the coupling**

Do not report channel calibration uncertainty as independently combinable marginal error bars. The primary object is the joint identified set; in log-ratio coordinates it is a slope-`-1` segment because

```text
log rho_F + log rho_E = log rho_W.
```

## Figure 1 message

Figure 1 must visually carry the main theorem without depending on the text:

- `Gamma=1`: one stable-calibration point;
- finite `Gamma`: a sharp segment on `rho_F rho_E=rho_W`;
- larger `Gamma`: expansion along the same one-dimensional set;
- log-ratio panel: exact slope `-1`;
- worked directional breakdown at `Gamma*=1.34`;
- legacy `delta=0.34` should appear, if at all, only as the phrase “34% upward drift” attached to that 1.34-fold endpoint.

Suggested caption core:

> **Figure 1. Calibration transport determines identification strength.** Stable conversion (`Gamma=1`) gives point identification. A finite multiplicative transport bound (`1/Gamma <= kappa <= Gamma`) produces a sharp one-dimensional joint identified set. Because the same `kappa` moves both channel ratios, every admissible pair preserves `rho_F rho_E=rho_W`; after log transformation the set is a line segment of slope `-1`. In the worked example the directional conclusion first reaches no change at the reference-invariant breakdown factor `Gamma*=1.34` (`eta*=log 1.34`), corresponding to 34% upward calibration-ratio drift in that direction. Removing the finite transport restriction recovers N4 non-identification.

## Abstract compression target

The abstract should do only four jobs:

1. state why relative proxy comparisons fail when calibration transport fails;
2. give the Gamma family, joint set and breakdown factor;
3. give the anchor ladder and joint-reporting consequence;
4. concede classical identifiability algebra and state the ecological/operational contribution.

Avoid re-explaining N1, N2, N3 and N4 as four separate discoveries.

## Discussion compression target

The Discussion should close in this order:

```text
hidden stability assumption
-> explicit Gamma-indexed sensitivity
-> breakdown factor
-> anchor ladder converts assumption into measurement
-> joint geometry converts theorem into reporting rule
```

The paper is strongest when described as **coverage and closure**: elementary algebra is carried through from information boundary to partial identification, robustness, field design and reporting. Do not sell mathematical depth.

## Submission stop conditions

Do not submit if any of the following reappears:

- `delta` is the primary robustness scale rather than a directional translation;
- N3, bounded drift and N4 are presented as unrelated headline theorems;
- `Gamma` is described as learned from `W` and `X` alone;
- the 0/1/2-anchor ladder is absent from the main text or figure logic;
- channel marginals are presented as independently combinable uncertainty;
- the novelty paragraph lists more than the three pillars above;
- the boundary paper drifts back into RACH/NOV/G2 claims.
