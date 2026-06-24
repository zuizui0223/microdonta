# Channel identifiability from trait performance

## Question

Suppose a trait's total performance can be written as

```text
W(z) = F(z) E(z),
```

where:

- `F(z) > 0` is a local fecundity/survival channel, such as pollinator-mediated
  seed production, flower-level mating success, or survival; and
- `E(z) > 0` is an establishment/reachability channel, such as dispersal,
  colonisation, access to suitable patches, or recruitment.

Can a before/after trait-space geometry identify **which** channel changed?

The answer is no for observations based only on `W`. But in this positive
two-factor model, observing `W` plus either one of the factors is sufficient to
reconstruct the other and hence identify the channel changes.

The executable finite-grid form is
`causal_model.channel_identifiability_theory`.

---

## 1. Observation class

Let the trait domain be any set `Z`, and let a net-only observation be a
deterministic function of total performance:

```text
O = Phi(W).
```

This includes, for every threshold `t > 0`, the viable set

```text
Omega_t = {z in Z : W(z) >= t},
```

and therefore all geometry calculated from it:

```text
lower edge
upper edge
breadth / measure
number of connected components
all thresholded trait-space geometries
```

It also includes any other summary that sees only the product `F E`.

---

## 2. Theorem N1 — exact channel non-identifiability from net-only observations

Let a baseline system have positive channels `F_0(z)` and `E_0(z)`. Let
`a(z) > 0` be any trait-dependent multiplier. Consider two distinct causal
programs:

```text
P_F:  F_1(z) = a(z) F_0(z),   E_1(z) = E_0(z)
P_E:  F_1(z) = F_0(z),        E_1(z) = a(z) E_0(z).
```

For ecological loss, restrict `0 < a(z) <= 1`; the algebra does not require
that restriction.

Then

```text
W_F,1(z) = [a(z) F_0(z)] E_0(z)
           = a(z) F_0(z) E_0(z)
           = F_0(z) [a(z) E_0(z)]
           = W_E,1(z).
```

Therefore

```text
Phi(W_F,1) = Phi(W_E,1)
```

for every net-only observation operator `Phi`.

### Consequence

> **No observation that is only a function of total trait performance can
> distinguish a fecundity/survival-channel change from an
> establishment/reachability-channel change.**

This is an exact structural symmetry, not a low-power statistical result and not
a claim that the two biological processes are the same. The underlying channel
states differ, but their product is identical.

### Corollary N1.1 — geometry cannot rescue net-only observations

Because `W_F,1 = W_E,1` pointwise, for every threshold `t`,

```text
Omega_t(F-loss) = Omega_t(E-loss).
```

Thus even complete knowledge of viable trait-space geometry at all thresholds
cannot identify the changed channel in this model class.

This is stronger than the earlier toy result that two examples happened to share
an upper-edge contraction. The equivalence holds for **any** positive baseline
functions and **any** trait-dependent attenuation `a(z)`.

---

## 3. Theorem N2 — one channel plus net performance is sufficient

Observe total performance and one positive channel before and after a transition.
For example, suppose `W_0`, `W_1`, `F_0`, and `F_1` are observed. Then the
unobserved establishment channel is uniquely recovered pointwise:

```text
E_0(z) = W_0(z) / F_0(z)
E_1(z) = W_1(z) / F_1(z).
```

Symmetrically, observing `W` and `E` yields

```text
F_i(z) = W_i(z) / E_i(z),  i in {0, 1}.
```

### Proof

All factors are strictly positive, so division is defined. Substitution into
`W_i = F_i E_i` gives the stated recovery formula and uniqueness: any candidate
factor compatible with the observed product and observed positive factor must
equal the quotient. ∎

Thus the ratios

```text
rho_F(z) = F_1(z) / F_0(z)
rho_E(z) = E_1(z) / E_0(z)
```

are identified from **net performance plus one resolved channel**. They may then
be classified without falsely forcing a single channel:

```text
rho_F != 1 somewhere and rho_E = 1 everywhere  -> fecundity-only change
rho_E != 1 somewhere and rho_F = 1 everywhere  -> establishment-only change
both differ from 1                              -> mixed change
neither differs from 1                           -> unchanged
```

No exclusive-change assumption is needed to detect a mixed result. An exclusive
causal interpretation is warranted only after the reconstructed ratios show that
one channel is invariant.

### Observation-design contrast

Within this positive two-factor model:

```text
W only                 -> structurally insufficient (N1)
W + F, or W + E        -> sufficient to recover both channels (N2)
```

This is the useful mathematical boundary for field or simulation design. It does
not say that a particular assay measures an exact mathematical factor; that
mapping must be justified in the biological model.

---

## 4. What follows for trait-space studies

An observed contraction, shift, or fragmentation may still be biologically
valuable. But it is not a universal causal fingerprint of one vital-rate channel.

For a flower trait, a net-only observation might be:

```text
flower size / colour distribution
trait-space edge
mean reproductive performance
population persistence
```

None can, by itself, separate a loss of pollinator-mediated fecundity from a
trait-correlated loss of reachability or recruitment, when both act through the
same net-performance multiplier.

Theorem N2 says that a study need not measure every channel independently. It
needs total performance plus at least one factor that can be given a defensible
channel interpretation:

| mathematical quantity | ecological measurements that could inform it |
|---|---|
| `W(z)` | trait-specific lifetime performance or a declared demographic-growth proxy |
| `F(z)` | visitation, pollen deposition, pollen limitation, hand-pollination response, fruit/seed set before recruitment limitation |
| `E(z)` | seed or pollen movement, dispersal/colonisation, patch reachability, recruitment conditional on seed production, landscape connectivity |

For example, if `W` and a defensible pollination/fecundity factor `F` are
measured, the model implies an inferred establishment term `E=W/F`. Whether that
inference is biologically valid depends on whether the factorisation itself is
valid for the system.

---

## 5. Relation to RACH and ABMs

RACH's role is now clearer:

1. A net-performance POM may retain multiple channel-level causal programs.
2. Trait-space geometry can sometimes reduce that set in a restricted simulator
   family, but theorem N1 shows it cannot generally identify the channel when the
   observation depends only on `W=FE`.
3. A next-observation design should add one channel-resolved measurement to the
   net-performance POM, as formalised by theorem N2.
4. ABMs should test robustness after adding density dependence, stochasticity,
   frequency dependence, and spatial state -- not serve as proof of N1 or N2.

---

## 6. Scope

- The factorisation is multiplicative and all channel values are positive.
- The result applies to any trait domain; one-dimensional geometry is only a
  convenient representation.
- Other model structures may introduce additional information, but then that
  information must be stated explicitly rather than attributed to geometry alone.
- This is a mathematical identifiability statement. It does not say that any
  particular organism follows this factorisation.
