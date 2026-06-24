# Proxy calibration is the boundary between useful and useless channel observations

## Why this theorem is needed

Theorem N2 in `docs/channel_identifiability_theorem.md` states that, for

```text
W(z) = F(z) E(z),
```

observing total performance `W` and one mathematical factor (`F` or `E`) is
sufficient to recover the other by division.

Field measurements, however, are usually not a mathematical factor itself. A
visitation rate, pollen-load index, fruit set, or landscape-connectivity score is
a **proxy**. Let a proxy for `F` be

```text
X_i(z) = q_i(z) F_i(z),
```

where `q_i(z)>0` is the unknown conversion from proxy units to the factor at
regime/time `i`.

The question is not merely whether a proxy correlates with `F`. The question is:

> **What assumption on the proxy conversion is required for it to break the
> net-performance non-identifiability?**

The executable finite-grid construction is
`causal_model.proxy_calibration_theory`.

---

## Theorem N3 — unknown but time-stable proxy calibration identifies changes

Assume the proxy conversion is stable between before and after states:

```text
q_0(z) = q_1(z) = q(z) > 0.
```

Then

```text
X_1(z) / X_0(z)
= [q(z) F_1(z)] / [q(z) F_0(z)]
= F_1(z) / F_0(z).
```

Hence the relative change in the proxied factor is identified despite an unknown,
trait-dependent absolute calibration:

```text
rho_F(z) = F_1(z)/F_0(z) = X_1(z)/X_0(z).
```

Because

```text
W_1(z)/W_0(z) = rho_F(z) rho_E(z),
```

the other channel's relative change follows:

```text
rho_E(z)
= [W_1(z)/W_0(z)] / [X_1(z)/X_0(z)].
```

The same derivation holds symmetrically for a stable proxy of `E`.

### Consequence

> **A channel proxy need not have known absolute calibration to identify relative
> channel changes. It must have a conversion that is stable across the compared
> regimes, or whose change is known.**

This is stronger and more usable than demanding a direct assay of a pure
mathematical factor.

---

## Theorem N4 — time-varying calibration restores non-identifiability

Now allow the conversion to vary freely:

```text
X_0(z) = q_0(z) F_0(z)
X_1(z) = q_1(z) F_1(z).
```

Then

```text
F_1(z)/F_0(z)
= [X_1(z)/X_0(z)] [q_0(z)/q_1(z)],
```

and therefore

```text
E_1(z)/E_0(z)
= [W_1(z)/W_0(z)] [X_0(z)/X_1(z)] [q_1(z)/q_0(z)].
```

The unobserved positive ratio

```text
h(z) = q_1(z)/q_0(z)
```

can be arbitrary. Thus the same observed `W_0,W_1,X_0,X_1` is compatible with a
family of different latent channel changes.

### Constructive proof

Take an observed series with no apparent change:

```text
W_0(z)=W_1(z)=1,
X_0(z)=X_1(z)=1.
```

One latent explanation sets `q_0=q_1=1`, yielding no change in either channel.
Another sets `q_0=1` and `q_1=h(z)`, yielding

```text
F_1/F_0 = 1/h(z),
E_1/E_0 = h(z).
```

For any nonconstant `h`, both channels changed in opposite directions, although
both observed series are exactly unchanged. ∎

### Consequence

> **An uncalibrated proxy is not automatically a channel observation. If its
> conversion changes across populations, habitats, or regimes, it can reintroduce
> the same non-identifiability that N2 was meant to solve.**

---

## Combined observation-design boundary

Within the positive multiplicative model:

```text
W only
    -> insufficient (N1)

W + F, or W + E
    -> sufficient (N2)

W + proxy X=qF, q stable across comparison
    -> sufficient for relative channel changes (N3)

W + proxy X=q_i F, q_i unconstrained across comparison
    -> insufficient (N4)
```

This is the exact mathematical condition that needs to be carried into an
empirical design.

---

## Ecological interpretation without overclaiming

For floral systems, a visit count could be treated as a proxy for a
pollination/fecundity channel only under an explicit stability argument, for
example that the conversion from visits to successful pollen deposition and seed
set is stable over the comparison. A change in visitor quality, pollen carryover,
floral handling, resource limitation, or selfing could change `q_i(z)`.

Therefore a useful field design does not merely record visit number. It must
measure or defend the stability of the path

```text
visit -> pollen transfer -> fertilisation -> seed output,
```

or directly calibrate that path in each regime. Hand-pollination controls,
pollen-deposition measurements, and trait-specific seed set are examples of
measurements that can constrain the conversion. They are not automatically valid
factors; their role depends on the declared biological factorisation.

For spatial establishment proxies, a connectivity index has the same issue. It
only identifies change in `E` if its mapping to realised establishment/recruitment
is stable or calibrated across the comparison.

---

## Scope

- All quantities are strictly positive and the factorisation is multiplicative.
- N3 identifies **relative change**, not absolute factor magnitudes.
- The result does not turn a convenient proxy into a valid biological factor. It
  states the calibration condition required for a proxy to have identifying power
  within the model.
- Measurement error can be handled with a declared tolerance, but unknown
  regime-specific calibration drift is structural rather than sampling noise.
