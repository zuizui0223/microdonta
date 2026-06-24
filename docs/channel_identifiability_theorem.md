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

The answer is negative for observations based only on `W`, and positive only
under explicit extra observations and restrictions.

The executable finite-grid form is
`causal_model.channel_identifiability_theory`.

---

## 1. Observation class

Let the trait domain be any set `Z`, and let an observation be a deterministic
function of net performance alone:

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

It can also include any other statistic that sees only the product `F E`.

---

## 2. Theorem N1 — exact channel non-identifiability

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

for every net-performance-only observation operator `Phi`.

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

Thus even complete knowledge of the viable trait-space geometry at all
thresholds cannot identify the changed channel in this model class.

This is stronger than the earlier toy result that two examples happened to share
an upper-edge contraction. The equivalence holds for **any** positive baseline
functions and **any** trait-dependent attenuation `a(z)`.

---

## 3. Theorem N2 — conditional identification with channel-resolved observations

Now observe both channels separately before and after the transition, and define
pointwise ratios

```text
rho_F(z) = F_1(z) / F_0(z)
rho_E(z) = E_1(z) / E_0(z).
```

Under an explicit exclusive-channel model class:

```text
exactly one channel changed,
all rates are observed on the same trait domain,
measurement error is absent or bounded by a declared tolerance,
```

the decision rule is:

```text
rho_F != 1 somewhere and rho_E = 1 everywhere  -> fecundity-only change
rho_E != 1 somewhere and rho_F = 1 everywhere  -> establishment-only change
both differ from 1                              -> mixed; no exclusive conclusion
neither differs from 1                           -> unchanged
```

### Proof

If `rho_E = 1` pointwise, then `E_1 = E_0`; if `rho_F` differs from one at at
least one trait, the only changed channel is `F`. The converse case is symmetric.
If both differ, the exclusive-channel assumption is violated. If neither differs,
there is no observed change. ∎

This is deliberately conditional. It does **not** identify a causal channel when
both channels can change and only imperfect proxies are observed.

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
same net performance multiplier.

To break the symmetry, observation must resolve channels. A study therefore needs
some direct information corresponding to each factor:

| mathematical channel | ecological measurements that could inform it |
|---|---|
| `F(z)` | visitation, pollen deposition, pollen limitation, hand-pollination response, fruit/seed set conditional on local establishment |
| `E(z)` | seed or pollen movement, dispersal/colonisation, patch reachability, recruitment conditional on seed production, landscape connectivity |

The theorem does not prescribe a single field assay. It says what sort of
measurement is mathematically necessary: something that does not collapse the
two channels back into their product.

---

## 5. Relation to RACH and ABMs

RACH's role is now clearer:

1. A net-performance POM may retain multiple channel-level causal programs.
2. Trait-space geometry can sometimes reduce that set in a restricted simulator
   family, but theorem N1 shows it cannot generally identify the channel when the
   observation depends only on `W=FE`.
3. Channel-resolved observations provide the next-observation design implied by
   theorem N2.
4. ABMs should test robustness after adding density dependence, stochasticity,
   frequency dependence, and spatial state -- not serve as proof of N1 or N2.

---

## 6. Scope

- The factorisation is multiplicative and all channel values are positive.
- The result applies to any trait domain; the one-dimensional geometry is only a
  convenient representation.
- Other model structures may introduce additional information, but then that
  information must be stated explicitly rather than attributed to geometry alone.
- This is a mathematical identifiability statement. It does not say that any
  particular organism follows this factorisation.
