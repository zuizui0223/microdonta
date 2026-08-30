# Proxy calibration is the boundary between point identification, partial identification and non-identification

## Setup

Let total performance and a proxy for the fecundity/survival channel be

```text
W_i(z) = F_i(z) E_i(z)
X_i(z) = q_i(z) F_i(z)
```

for regimes `i in {0,1}`, with all quantities strictly positive. The establishment-proxy case is symmetric.

The central empirical question is not whether `X` correlates with `F`. It is whether the proxy-to-channel conversion `q_i(z)` is stable enough across the comparison for the desired directional conclusion to survive.

---

## N3 — stable calibration gives point identification of relative changes

If

```text
q_0(z) = q_1(z) = q(z) > 0,
```

then

```text
rho_F(z) = F_1/F_0 = X_1/X_0
```

and, because `W=FE`,

```text
rho_E(z)
= [W_1(z)/W_0(z)] / [X_1(z)/X_0(z)].
```

Define the stable-calibration plug-in ratio for the unproxied channel as

```text
r_tilde(z) = [W_1/W_0] / [X_1/X_0].
```

Unknown absolute calibration is therefore harmless for relative change only under the cross-regime stability condition.

---

## N3b — bounded calibration drift gives a sharp identified set

To turn N4 from a warning into a sensitivity analysis, define the cross-regime calibration ratio

```text
kappa(z) = q_0(z) / q_1(z).
```

Prespecify

```text
1-delta <= kappa(z) <= 1+delta,
0 <= delta < 1.
```

This `delta` directly bounds the **ratio** `q_0/q_1`. It does not mean that `q_0` and `q_1` are independently within `+/- delta` of a common reference calibration.

For a fecundity proxy,

```text
rho_E(z) = r_tilde(z) / kappa(z).
```

Because the map `kappa -> r_tilde/kappa` is continuous and strictly decreasing, the sharp identified set is

```text
I_delta[rho_E(z)]
= [ r_tilde(z)/(1+delta),
    r_tilde(z)/(1-delta) ].
```

Its multiplicative width is

```text
sup(I_delta) / inf(I_delta)
= (1+delta)/(1-delta).
```

### Sharpness

Every point of this interval is attainable. For any admissible `kappa`, choose any `q_1>0`, set `q_0=kappa q_1`, then define

```text
F_i = X_i/q_i
E_i = W_i/F_i.
```

This reconstruction exactly reproduces the observed `W_0,W_1,X_0,X_1` and gives `rho_E=r_tilde/kappa`. Therefore the interval is not merely conservative: it is the exact identified set under the stated drift restriction.

The same construction applies symmetrically when `X` proxies `E`.

### Important alternative parameterization

If instead each regime-specific calibration is independently constrained to lie within `+/- delta` of a common reference, then the induced bound is

```text
(q_0/q_1) in [ (1-delta)/(1+delta),
               (1+delta)/(1-delta) ],
```

and the resulting multiplicative interval width is squared. The manuscript and software therefore define `delta` only as a bound on the **between-regime calibration ratio**.

---

## Breakdown points

The point `rho_E=1` represents no change. A directional conclusion is identified only while the entire interval remains on one side of one.

For an apparent decline `0 < r_tilde < 1`,

```text
r_tilde/(1-delta) < 1
```

is equivalent to

```text
delta < 1-r_tilde.
```

Hence

```text
delta*_decline = 1-r_tilde.
```

For an apparent increase `r_tilde>1`,

```text
r_tilde/(1+delta) > 1
```

is equivalent to

```text
delta < r_tilde-1,
```

so

```text
delta*_increase = r_tilde-1.
```

At the breakdown point the interval first **touches** one. The strict directional conclusion therefore holds for `delta < delta*`, not at equality.

Example: if `r_tilde=0.66`, the decline breakdown point is `0.34`. The reviewer-facing statement is:

> The estimated decline has a calibration-drift breakdown point of 34%: the identified set remains entirely below one for between-regime calibration-ratio drift smaller than 34%.

---

## Sampling uncertainty is separate from identification uncertainty

Let `[L,U]` be a confidence interval for `r_tilde` obtained from the sampling model. Monotonicity gives the conservative region

```text
C_{alpha,delta}
= [ L/(1+delta), U/(1-delta) ].
```

A sampling-aware decline conclusion requires

```text
U/(1-delta) < 1,
```

or

```text
delta < 1-U.
```

Thus `1-r_tilde` is the point-estimate sensitivity breakpoint, whereas `max(0,1-U)` is the sampling-aware breakpoint. They must not be conflated.

---

## N4 — unrestricted calibration drift removes directional identification

If no finite restriction is placed on `kappa=q_0/q_1`, then

```text
rho_E = r_tilde/kappa
```

can take any positive value while the observed `W` and `X` remain unchanged. This is unrestricted non-identification.

N4 is the case where the calibration-ratio restriction is removed. It should not be described as the `delta -> 1` limit of the additive interval above, because that parameterization is only one bounded sensitivity family.

---

## Design Rule 1 — anchor and transport

> Directly measure at least one latent channel in an anchor regime. This estimates the local proxy conversion. For every comparison regime, either revalidate that conversion directly or prespecify an admissible between-regime drift set and report the resulting identified interval and breakdown point.

Operationally:

```text
anchor + justified stable conversion
    -> point identification (N3)

anchor + bounded between-regime conversion drift
    -> partial identification + breakdown point (N3b)

proxy-only comparison + unrestricted conversion drift
    -> no directional identification (N4)
```

This is the empirical design rule implied by N2-N4. A single direct assay does not license unqualified transport of the calibration across habitats, years or disturbance regimes.

---

## Ecological interpretation

The assumption is especially vulnerable in the comparisons ecologists most want to make: fragmented versus connected habitat, urban versus rural habitat, warm versus cool years, or pollinator communities that differ in visitor identity. In pollination, for example, a visit count can map differently to successful reproduction when pollen deposition, handling, pollen quality, selfing, resource limitation or seed maturation changes. In dispersal and recruitment, the same connectivity proxy can map differently to realised establishment when safe-site availability or post-dispersal survival changes.

The result therefore converts a vague robustness claim into a prespecified sensitivity analysis: report the allowable drift set, the resulting identified interval and the drift at which the biological conclusion ceases to be identified.

---

## Scope

- All quantities are strictly positive and the declared factorisation is multiplicative.
- N3-N3b identify relative changes, not absolute factor magnitudes.
- The bounded-drift set is structural uncertainty, not ordinary sampling noise.
- A convenient empirical proxy is not automatically a mathematical channel; its biological mapping must still be justified.
- The same `kappa` links the two reconstructed channel ratios, so joint channel uncertainty is constrained by that common calibration ratio rather than by an arbitrary Cartesian product of marginal intervals.
