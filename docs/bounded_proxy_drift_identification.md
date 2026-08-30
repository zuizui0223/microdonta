# Bounded proxy drift: partial identification and breakdown points

## 1. Position between N3 and N4

Let

```text
W_i(z)=F_i(z)E_i(z)
X_i(z)=q_i(z)F_i(z)
```

with positive quantities, and define

```text
kappa(z)=q_1(z)/q_0(z)
rho_W=W_1/W_0
rho_X=X_1/X_0
rho_E_hat=rho_W/rho_X.
```

N3 fixes `kappa=1`. N4 places no finite restriction on positive `kappa`. The bounded bridge instead prespecifies

```text
1-delta <= kappa(z) <= 1+delta,    0<=delta<1.
```

Here `delta` directly bounds the between-regime calibration ratio. No distribution inside the interval is assumed.

## 2. Sharp identified sets

Because

```text
rho_X=kappa rho_F
rho_W=rho_F rho_E,
```

we obtain

```text
rho_F=rho_X/kappa
rho_E=rho_E_hat kappa.
```

Hence

```text
rho_F in [rho_X/(1+delta), rho_X/(1-delta)]
```

and

```text
rho_E in [rho_E_hat(1-delta), rho_E_hat(1+delta)].
```

Every endpoint and every interior point is attainable by an admissible `kappa`, so the intervals are sharp. Their multiplicative width is

```text
(1+delta)/(1-delta).
```

The same `kappa` generates both channel ratios, so the **joint** identified set is the curve

```text
{(rho_X/kappa, rho_E_hat*kappa):
  kappa in [1-delta,1+delta]}
```

with `rho_F rho_E=rho_W`. It is not the Cartesian product of the two marginal intervals.

At `delta=0` the set collapses to N3. N4 should be described as **removing the calibration-ratio restriction**, not as the `delta -> 1` limit of this additive bounded family: that limit does not span all positive values of the multiplicatively placed channel.

The establishment-proxy case is symmetric after swapping `F` and `E`.

## 3. Directional conclusions and breakdown points

For the complementary channel,

```text
E decreased iff rho_E_hat(1+delta)<1
E increased iff rho_E_hat(1-delta)>1.
```

Therefore, if `rho_E_hat<1`,

```text
delta* = 1/rho_E_hat - 1,
```

and if `rho_E_hat>1`,

```text
delta* = 1 - 1/rho_E_hat.
```

For the proxied channel the conversion enters inversely. A decrease survives while `rho_X/(1-delta)<1`, giving `delta*=1-rho_X`; an increase survives while `rho_X/(1+delta)>1`, giving `delta*=rho_X-1`.

At `delta=delta*` the relevant endpoint first touches one. Strict directional language is therefore valid for `delta<delta*`.

### 34% illustration

If

```text
rho_E_hat=1/1.34=0.746268...
```

then

```text
delta*=0.34.
```

The conclusion `E decreased` survives between-regime calibration-ratio drift smaller than 34%; at exactly 34% the upper endpoint equals one. This is a sensitivity breakpoint, not an estimate that calibration actually drifted by 34%.

## 4. Sampling uncertainty is distinct

If `[L,U]` is a sampling confidence interval for `rho_E_hat`, the conservative union under the bounded calibration family is

```text
[L(1-delta), U(1+delta)].
```

A sampling-aware decline requires `U(1+delta)<1`. Replication can shrink `[L,U]`; it cannot identify `kappa` unless the additional data measure calibration or the channel directly.

## 5. Design Rule 1 — anchor and transport

> Directly measure at least one latent channel in an anchor regime. This anchors the local proxy conversion. For every comparison regime, either revalidate that conversion directly or prespecify an admissible between-regime drift set and report the resulting sharp interval and breakdown point.

| Available information | Permitted conclusion | Required action |
|---|---|---|
| `W` only | channel attribution not identified (N1) | add a channel-resolved observation |
| `W` plus exact `F` or `E` | point identification (N2) | reconstruct the other factor |
| `W` plus stable proxy | point identification of relative change (N3) | state and defend transport stability |
| `W` plus bounded proxy drift | partial identification | report interval, width and `delta*` |
| `W` plus unrestricted drift | no directional channel identification (N4) | calibrate or measure a channel directly |

## 6. Executable calculation

```python
from causal_model.bounded_proxy_drift import (
    design_rule_for_interval,
    identify_under_bounded_proxy_drift,
)

result = identify_under_bounded_proxy_drift(
    net_ratio=0.60,
    proxy_ratio=0.80,
    delta=0.20,
    proxy_channel="fecundity",
)

assert result.establishment.lower == 0.60
assert result.establishment.upper == 0.90
assert result.establishment.direction_at_declared_bound == "decrease"
```

`causal_model.bounded_proxy_drift` performs deterministic identified-set calculations. It does not infer `delta`, certify proxy validity, or turn an assumed drift bound into empirical evidence.
