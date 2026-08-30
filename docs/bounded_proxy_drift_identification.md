# Bounded proxy drift: partial identification and breakdown points

## 1. Position between N3 and N4

Let positive total performance in regimes `i in {0,1}` be

```text
W_i(z) = F_i(z) E_i(z)
```

and let the observed field assay be a proxy of `F`:

```text
X_i(z) = q_i(z) F_i(z).
```

N3 assumes `q_1/q_0 = 1` and point-identifies relative channel change. N4 allows
`q_1/q_0` to be any positive function and therefore does not identify the channel
ratios. A useful intermediate case is **bounded calibration drift**.

Define

```text
kappa(z) = q_1(z)/q_0(z)
rho_W(z) = W_1(z)/W_0(z)
rho_X(z) = X_1(z)/X_0(z)
rho_E_hat(z) = rho_W(z)/rho_X(z).
```

Assume only

```text
1-delta <= kappa(z) <= 1+delta,     0 <= delta < 1.
```

No distribution inside this interval is required.

## 2. Identified sets

Because

```text
rho_X = kappa rho_F,
rho_W = rho_F rho_E,
```

we have

```text
rho_F = rho_X/kappa,
rho_E = rho_E_hat kappa.
```

Hence the sharp pointwise identified sets are

```text
rho_F in [rho_X/(1+delta), rho_X/(1-delta)]
```

and

```text
rho_E in [rho_E_hat(1-delta), rho_E_hat(1+delta)].
```

Every value in each interval is attained by some admissible `kappa`, so the sets
cannot be narrowed without further calibration information. Both intervals have
multiplicative width

```text
upper/lower = (1+delta)/(1-delta).
```

At `delta=0` they collapse to the N3 point estimates. As `delta` approaches one,
the intervals widen toward the N4 boundary.

The establishment-proxy case is symmetric after swapping `F` and `E`.

## 3. Directional conclusions and breakdown points

For the complementary channel `E`, a decrease is robust exactly when

```text
rho_E_hat(1+delta) < 1.
```

If `rho_E_hat < 1`, the sign conclusion breaks at

```text
delta* = 1/rho_E_hat - 1.
```

An increase is robust exactly when

```text
rho_E_hat(1-delta) > 1,
```

with breakdown

```text
delta* = 1 - 1/rho_E_hat
```

when `rho_E_hat > 1`.

For the proxied channel, calibration enters inversely. A decrease in `F` survives
while `rho_X/(1-delta)<1`, giving `delta*=1-rho_X`; an increase survives while
`rho_X/(1+delta)>1`, giving `delta*=rho_X-1`.

Breakdown values at or above one mean that the sign survives every bound in the
declared family `delta<1`; implementations report these as censored at one.

### Worked numerical illustration

Suppose stable calibration would give

```text
rho_E_hat = 1/1.34 = 0.746268...
```

Then

```text
delta* = 1/rho_E_hat - 1 = 0.34.
```

The statement `E decreased` therefore survives calibration drift smaller than
34%. At exactly 34%, the upper endpoint reaches one; beyond it the direction is
not identified. This is an illustration of the decision rule, not an empirical
estimate of calibration drift.

## 4. Design rules

| Available information | Permitted conclusion | Required reporting / next action |
|---|---|---|
| `W` only | channel attribution is not identified (N1) | measure a channel or calibrated proxy |
| `W` plus exact `F` or `E` | both relative channel changes point-identified (N2) | report reconstructed ratios and uncertainty |
| `W` plus stable proxy | relative channel changes point-identified under stability (N3) | state and defend the stability condition |
| `W` plus bounded proxy drift | partial identification | report the interval, multiplicative width and `delta*` |
| `W` plus unbounded drift | directional channel claim not identified (N4) | calibrate across regimes or measure the channel directly |

The bounded result changes the operational message from `a proxy may be wrong` to
a quantitative sensitivity analysis. A sign claim is defensible exactly while
the identified interval excludes one. When it includes one, larger sample size in
`W` or `X` alone cannot repair the missing calibration information.

## 5. Executable calculation

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

rule = design_rule_for_interval(
    result.establishment,
    target_channel="establishment",
)
assert rule.status == "sign_identified"
```

`causal_model.bounded_proxy_drift` performs deterministic interval calculations.
It does not infer `delta`, certify a proxy, or convert an assumed bound into
calibration evidence.
