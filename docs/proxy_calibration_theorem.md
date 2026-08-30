# Proxy calibration is the boundary between useful and useless channel observations

## Setup

Let total performance and a proxy for the fecundity/survival channel be

```text
W_i(z) = F_i(z) E_i(z)
X_i(z) = q_i(z) F_i(z)
```

for regimes `i in {0,1}`, with all quantities strictly positive. The establishment-proxy case is symmetric.

The central question is not merely whether `X` correlates with `F`. It is whether the proxy-to-channel conversion remains stable enough across the comparison for the desired channel conclusion to survive.

---

## N3 — stable calibration identifies relative channel changes

If

```text
q_0(z) = q_1(z) = q(z) > 0,
```

then

```text
rho_F = F_1/F_0 = X_1/X_0.
```

Because `W=FE`,

```text
rho_E
= [W_1/W_0] / [X_1/X_0].
```

Thus unknown absolute calibration is compatible with point identification of relative channel changes when the conversion is stable across regimes.

---

## N4 — unrestricted calibration drift restores non-identification

Allow

```text
X_0 = q_0 F_0
X_1 = q_1 F_1
```

and define

```text
kappa = q_1/q_0.
```

Then

```text
rho_F = (X_1/X_0) / kappa
```

and

```text
rho_E
= [(W_1/W_0)/(X_1/X_0)] kappa.
```

If `kappa` is unrestricted over positive values, the same observed `W` and `X` are compatible with arbitrary positive channel-change ratios. A proxy whose conversion changes freely across regimes does not identify the latent channel changes.

---

## Bounded bridge between N3 and N4

The practically useful case is neither exact stability nor unrestricted drift. Suppose

```text
1-delta <= kappa <= 1+delta,
0 <= delta < 1.
```

Let

```text
rho_E_hat = (W_1/W_0)/(X_1/X_0)
```

be the N3 value under stable calibration. Retaining `kappa` gives

```text
rho_F = rho_X/kappa
rho_E = rho_E_hat kappa.
```

Therefore the sharp marginal identified sets are

```text
rho_F in [rho_X/(1+delta), rho_X/(1-delta)]
```

and

```text
rho_E in [rho_E_hat(1-delta), rho_E_hat(1+delta)].
```

Both have multiplicative width

```text
(1+delta)/(1-delta).
```

The sets are sharp because every admissible `kappa` can be realised by choosing positive `q_0`, setting `q_1=kappa q_0`, and reconstructing `F_i=X_i/q_i` and `E_i=W_i/F_i`. The same `kappa` links both channels, so the joint identified set is a one-parameter curve satisfying `rho_F rho_E=rho_W`, not the Cartesian product of the marginal intervals.

### Parameterisation warning

Here `delta` directly bounds the **between-regime calibration ratio** `q_1/q_0`. If each `q_i` were independently bounded around a common reference instead, the induced ratio bound would be wider and the interval-width formula would change. The manuscript and software use only the direct ratio-bound definition above.

---

## Breakdown points

A directional conclusion is identified only while the entire interval excludes one.

For the complementary channel,

```text
E decreased iff rho_E_hat(1+delta) < 1
E increased iff rho_E_hat(1-delta) > 1.
```

Thus, for an apparent decline `rho_E_hat<1`,

```text
delta* = 1/rho_E_hat - 1.
```

For an apparent increase `rho_E_hat>1`,

```text
delta* = 1 - 1/rho_E_hat.
```

At `delta=delta*` the interval first touches one, so a strict directional statement holds for `delta<delta*`.

For the proxied channel the corresponding inverse-calibration breakpoints are `1-rho_X` for a decline and `rho_X-1` for an increase.

### 34% illustration

If

```text
rho_E_hat = 1/1.34,
```

then

```text
delta* = 0.34.
```

The correct reporting sentence is:

> The estimated decline in establishment has a calibration-drift breakdown point of 34%: the identified set remains entirely below one for between-regime calibration-ratio drift smaller than 34%.

---

## Sampling uncertainty is separate

The bounded-drift set describes structural identification uncertainty. Sampling uncertainty in `rho_E_hat` should be propagated separately. If `[L,U]` is a confidence interval for `rho_E_hat`, the conservative union under the present parameterisation is

```text
[L(1-delta), U(1+delta)].
```

A sampling-aware decline requires `U(1+delta)<1`. Larger samples may tighten `[L,U]`; they do not remove uncertainty about `kappa` unless they directly inform calibration.

---

## Design Rule 1 — anchor and transport

> Directly measure at least one latent channel in an anchor regime. This anchors the local proxy conversion. For every comparison regime, either revalidate that conversion directly or prespecify an admissible between-regime drift set and report the resulting identified interval and breakdown point.

Operationally:

```text
W + direct channel in each regime
    -> point identification (N2)

anchor + justified stable proxy conversion
    -> point identification of relative change (N3)

anchor + bounded calibration drift
    -> partial identification + breakdown point

proxy comparison + unrestricted drift
    -> no directional identification (N4)
```

---

## Ecological interpretation

The stability assumption is most vulnerable in comparisons where visitor identity, behaviour, habitat context or post-event survival changes. In pollination, visit counts can map differently to successful reproduction when pollen deposition, handling, selfing, resource limitation or seed maturation changes. In dispersal, the same movement or connectivity proxy can map differently to recruitment when safe-site availability or post-dispersal survival changes.

The theorem therefore converts a generic warning into a sensitivity analysis: report the admissible drift set, the resulting sharp interval and the drift magnitude at which the biological conclusion fails.

---

## Scope

- All quantities are strictly positive and the factorisation is multiplicative.
- N3 and the bounded bridge concern relative changes, not absolute factor magnitudes.
- The drift bound is structural information supplied externally or by a calibration design; it is not inferred from the same net response and proxy alone.
- A convenient proxy is not automatically a valid mathematical channel; its biological mapping must still be justified.
