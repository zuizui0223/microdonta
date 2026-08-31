# Boundary paper — submission spine

Status: normative claim-compression note for `paper/boundary_manuscript_submission.md`.

The paper should be sold as a **Perspective on ecological evidence** with quantitative identification theorems, not as deep new algebra and not as a critique of molecular ecology.

## One-sentence claim

Mechanistic evidence is an identification property, not a biological-level label: measurements that are close to biological machinery can remain non-identifying, while strategically chosen field observations can strongly identify mechanism; recurring ecological product and proxy architectures make this distinction quantitatively exact.

## Governing conceptual distinction

Keep these two axes separate:

```text
Axis 1: biological measurement level / mechanistic proximity
Axis 2: identification strength
        non-identifying -> partially identifying -> point-identifying
```

The theory does **not** assert a monotone relation between the axes.

Use the sentence:

> Mechanistic evidence should be classified by what it identifies, not by the biological level at which it is measured.

Also keep the scope guard visible:

- molecular/genomic data can be highly proximal and highly identifying;
- proximity alone does not guarantee identification among the declared alternatives;
- field patterns can be non-identifying, but a field measurement can be strongly identifying when it separates alternatives or anchors a missing channel;
- the evidentiary status of any measurement is conditional on the candidate mechanism set and observation map.

## Three quantitative pillars

### Pillar 1 — Net-only information boundary and its dimension

For a two-channel product `W=FE`, positive functions act by

```text
(F,E) -> (cF,E/c).
```

Every net-only observable `Phi(W)` is invariant on these orbits and therefore factors through the quotient. Complete response curves, all threshold-feasible sets and their geometry/topology remain mechanistically non-identifying.

For the general positive chain

```text
W = prod_{j=1}^k F_j,
```

product-preserving log perturbations satisfy `sum_j d_j=0`, so the net-only equivalence class has dimension `k-1`. If `r` independent **channel anchors** directly fix channel values or channel ratios, the residual unidentified dimension is

```text
k - 1 - r.
```

At `r=k-1`, the final channel is recovered from the product.

**Do not sell:** “products have multiple factorizations.”

**Sell:** measuring an invariant endpoint more deeply or precisely does not change identification; changing the observation map by adding independent channel information does.

### Pillar 2 — Calibration-transport family and breakdown

For the common two-channel proxy case with `kappa=q_1/q_0`, use the canonical symmetric restriction

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

Keep two anchor concepts separate.

**Channel anchors — resolve stages of a `k`-channel product**

```text
r independent channel anchors -> residual dimension k-1-r
k-1 channel anchors            -> point identification
```

**Calibration anchors — resolve proxy transport across two regimes**

For compatibility with the earlier two-channel design-rule wording, these are also referred to as the **0 anchors / 1 anchor / 2 anchors** calibration ladder when the context is unambiguous:

```text
0 anchors = 0 calibration anchors -> unrestricted transport: non-identification
1 anchor  = 1 calibration anchor  -> local q + external Gamma/eta: sharp set + breakdown
2 anchors = 2 calibration anchors -> observe q0,q1 and kappa directly: point identification
```

**Design Rule 1 — Measure the missing identification information.** Use channel anchors to reduce unresolved mechanism dimensions and calibration anchors to replace transport assumptions with measurement.

**Design Rule 2 — Preserve the coupling.** Do not report channel calibration uncertainty as independently combinable marginal error bars. The primary object is the joint identified set; in log-ratio coordinates it is a slope-`-1` segment because

```text
log rho_F + log rho_E = log rho_W.
```

## Ecological motivation that belongs in the paper

The paper should begin with the evidence-classification problem, then use pollination and seed dispersal as concrete architectures.

At visitor type `m`,

```text
service_m = visitation_m * direct_effectiveness_m,
```

and community service is `sum_m service_m`. Degree, abundance or visitation alone can at most describe/proxy the quantity side; they are not effective service unless effectiveness is fixed. This is the concrete ecological instance of the product/proxy boundary. Aggregation across visitor types can create an additional allocation ambiguity beyond the within-type product.

Seed dispersal supplies an independent quantity-by-quality architecture and prevents the paper from reading as a pollination-specific critique.

A declared change -> service -> dependency/assurance -> response chain illustrates the `k`-channel dimension rule: endpoint observation does not license inference of missing links. If the declared endpoint map is multiplicative with `k` positive stages, `k-1` independent channel anchors suffice for point identification; fewer leave an explicit residual dimension.

Genomic/molecular examples belong only in the conceptual framing. Their role is to show why *proximity* should not be conflated with *identification*, not to claim that molecular data follow the multiplicative theorem.

## Figure messages

The Perspective ultimately benefits from a conceptual first figure with two orthogonal axes:

```text
vertical: biological measurement level / proximity
horizontal: identification strength
            non-ID -> partial ID -> point ID
```

Illustrative placements should include both directions:

- proximal but non-identifying measurement compatible with several mechanisms;
- proximal and identifying intervention/measurement;
- distal net pattern that is non-identifying;
- field channel anchor that is strongly identifying.

The figure must state that positions are conditional on the candidate mechanism set and observation map.

The existing Gamma figure then carries the quantitative proxy theorem:

- `Gamma=1`: one stable-calibration point;
- finite `Gamma`: a sharp segment on `rho_F rho_E=rho_W`;
- larger `Gamma`: expansion along the same one-dimensional set;
- log-ratio panel: exact slope `-1`;
- worked directional breakdown at `Gamma*=1.34`;
- legacy `delta=0.34` appears, if at all, only as “34% upward drift”.

A compact dimension graphic may show `k-1-r` versus the number of independent channel anchors for a representative chain.

## Abstract compression target

The abstract should do only five jobs:

1. separate mechanistic proximity from identification strength;
2. state the `k-1-r` dimension rule as the exact product-chain demonstration;
3. give the Gamma family, joint set and breakdown factor for the two-channel proxy case;
4. distinguish channel anchors from calibration anchors and give the joint-reporting consequence;
5. state the ecological evidentiary contribution without selling mathematical depth.

Avoid re-explaining N1, N2, N3 and N4 as four separate discoveries.

## Discussion compression target

Close in this order:

```text
mechanistic proximity != mechanistic identification
-> endpoint/product equivalence dimension
-> direct channel anchors reduce the dimension
-> hidden proxy-stability assumption
-> explicit Gamma-indexed sensitivity + breakdown factor
-> calibration anchors replace transport assumptions with measurement
-> joint geometry converts theorem into reporting rule
```

The paper is strongest when described as **evidentiary reclassification plus coverage and closure**: elementary algebra is carried through from ecological measurement collapse to partial identification, robustness, field design and reporting.

## Boundary with the RACH paper

Paper A asks:

```text
What can the current observation map identify in principle?
```

Paper B / RACH asks:

```text
Which candidate observation should be acquired next to reduce mechanism ambiguity?
```

Do not merge these claims. RACH/NOV/RACH-SEQ remain non-headline and non-required for the Perspective.

## Submission stop conditions

Do not submit if any of the following reappears:

- the paper intrinsically ranks molecular/genomic evidence above or below field evidence;
- “molecular data are not mechanistic” or an equivalent claim appears;
- the conceptual headline loses the distinction between mechanistic proximity and identification strength;
- the broad two-axis claim is presented as a theorem for all ecological observation maps rather than a Perspective supported by worked theorems;
- `delta` is the primary robustness scale rather than a directional translation;
- N3, bounded drift and N4 are presented as unrelated headline theorems;
- `Gamma` is described as learned from `W` and `X` alone;
- channel anchors and calibration anchors are conflated;
- the `k-1-r` dimension rule is stated without specifying independent direct channel information;
- channel marginals are presented as independently combinable uncertainty;
- pollination is presented as the scope boundary rather than a lead example;
- the boundary paper drifts back into RACH/NOV/G2 claims.
