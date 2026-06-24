# Patch-size-dependent basin hysteresis from individual interaction feedback

## Why add individual interactions?

The patch-partition theorem treats interaction support as a function of patch area
alone. That establishes when a landscape can cross a trait-mode threshold, but it
does not yet capture a familiar ecological feedback:

```text
more interaction-supporting individuals
-> stronger local interaction environment
-> higher fitness of the interaction-supporting trait
-> more interaction-supporting individuals.
```

Examples include floral display maintaining pollinator visitation, mate density
maintaining encounter probability, cooperative defence maintaining local survival,
or host density maintaining mutualist persistence.

This note gives an exact reduced model with that feedback. It proves a
**restoration threshold** and a form of **basin/path hysteresis**. It does not
claim a classical two-fold saddle-node hysteresis diagram.

The executable implementation is `causal_model.patch_feedback_hysteresis_theory`.

---

## 1. Model

Let `x in [0,1]` be the local frequency of a high-investment,
interaction-supporting trait. Let patch area be `A>0`. Define

```text
dx/dt = x(1-x)[eta A^alpha x^h - c],
```

where:

| symbol | meaning |
|---|---|
| `eta>0` | interaction yield per unit area |
| `alpha>0` | area aggregation exponent |
| `h>0` | strength/shape of frequency-dependent interaction feedback |
| `c>0` | net cost of the high-investment trait absent sufficient interaction support |
| `x` | local frequency of the high trait |

The term

```text
eta A^alpha x^h
```

is local interaction support. It rises with patch area and with the frequency of
the trait that helps sustain the interaction.

---

## Theorem F1 — critical patch area for the high-trait state

The boundary equilibrium `x=1` is stable exactly when

```text
eta A^alpha > c.
```

Equivalently, define

```text
A_c = (c/eta)^(1/alpha).
```

Then:

```text
A > A_c  -> x=1 is stable
A = A_c  -> x=1 is neutral
A < A_c  -> x=1 is unstable.
```

### Proof

Near `x=1`, write `x=1-y` for small positive `y`. Then

```text
dx/dt = y[eta A^alpha - c] + o(y).
```

If `eta A^alpha-c>0`, the flow points toward one; if negative, it points away.
The equality case is neutral to first order. ∎

---

## Theorem F2 — bistability and the exact restoration threshold

For every `A>0`, `x=0` is stable because near zero,

```text
dx/dt = -cx + o(x).
```

When `A>A_c`, both boundaries are stable. The unique interior equilibrium solves

```text
eta A^alpha x^h = c,
```

so

```text
x_c(A) = [c/(eta A^alpha)]^(1/h).
```

This equilibrium is unstable.

### Proof of instability

Let

```text
f(x)=x(1-x)[eta A^alpha x^h-c].
```

At `x=x_c`, the bracket vanishes, so differentiation gives

```text
f'(x_c)
= x_c(1-x_c) eta A^alpha h x_c^(h-1)
> 0.
```

Therefore the interior equilibrium repels. ∎

Thus, for `A>A_c`:

```text
0 <= x < x_c(A)  -> x(t) converges to 0
x = x_c(A)       -> unstable threshold state
x_c(A) < x <= 1  -> x(t) converges to 1.
```

The threshold declines with patch area:

```text
x_c(A) proportional to A^(-alpha/h).
```

So larger patches not only permit the high state; they lower the frequency of
high-trait individuals needed to restore it.

---

## Theorem F3 — basin hysteresis under habitat restoration

Consider the sequence:

```text
1. Start in a high-trait state x approximately 1 with A_high > A_c.
2. Reduce area to A_low < A_c.
3. The high state becomes unstable and x can collapse toward 0.
4. Restore area to the original A_high > A_c.
```

After restoration, `x=0` remains stable. Therefore habitat restoration alone
does not force recovery of the high-trait state. Recovery requires a perturbation
such that

```text
x > x_c(A_high).
```

This can represent reseeding, translocation, restoration of a mutualist,
restoration of a pollinator assemblage, or another intervention that moves the
local system across its basin boundary.

### Important terminology

This is **basin/path hysteresis**:

```text
same restored environment A_high
but different long-run state depending on history and x.
```

The model has one unstable interior separator, not two saddle-node folds. Calling
it a universal fold bifurcation or a generic irreversible transition would be too
strong.

---

## Ecological predictions

The theorem produces predictions distinct from a simple linear area effect.

### 1. Critical patch size

Below `A_c`, high interaction-supported trait states cannot persist even when
introduced at high frequency.

### 2. Restoration threshold

Above `A_c`, a patch can still remain trapped in the low-trait state. Habitat
recovery can fail unless the restoring intervention also increases `x` beyond
`x_c(A)`.

### 3. Patch-size effect on restoration effort

Because

```text
x_c(A) proportional to A^(-alpha/h),
```

a larger restored patch needs a smaller high-trait reseeding fraction. This is a
quantitative conservation prediction.

### 4. Individual-interaction mechanism

The feedback term can be fitted or confronted with candidate mechanisms:

```text
floral display and pollinator learning
mate encounter / pollen limitation
cooperative defence
mutualist maintenance
frequency-dependent habitat construction.
```

The theorem does not assume which mechanism is correct. It says what follows if
one supplies the declared local positive feedback.

---

## Relation to genetics

The variable `x` may represent a phenotype frequency, an allele frequency, or a
polygenic high-investment state under a suitable deterministic approximation.

However, it is not itself a full population-genetic model. Drift, mutation,
recombination, migration, and neutral heterozygosity require their own state
variables. The patch-partition theorem's mutation-drift corollary provides an
area-to-equilibrium-diversity mapping; the next genetic theorem should ask when
finite-population drift causes a stochastic crossing below `x_c(A)` before the
deterministic patch threshold is crossed.

That question is genuinely eco-evolutionary: it couples patch size, interaction
feedback, genetic drift, and restoration probability.