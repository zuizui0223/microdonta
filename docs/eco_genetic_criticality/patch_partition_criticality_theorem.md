# Patch partition criticality: interaction-supported trait modes and genetic thresholds

## Question

Can landscapes with the same total habitat area support different trait modes
solely because one landscape is divided into many patches and the other is
concentrated into fewer patches?

The answer depends on how interaction service scales with patch area. This note
states the exact result for a deliberately transparent model.

Let a landscape have positive patch areas

```text
A = (A_1, ..., A_n),
A_total = sum_j A_j.
```

Let aggregate interaction service be

```text
I(A) = eta * sum_j A_j^alpha,
```

with `eta>0` and `alpha>0`.

Interpretations of `I` include aggregate pollinator support, floral display
service, mate encounter opportunity, cooperative defence, or any interaction
whose contribution is nonlinear in local patch area. The exponent is a model
assumption, not a universal empirical constant:

```text
alpha > 1  accelerating / aggregation / Allee-like interaction regime
alpha = 1  area-linear regime
0 < alpha < 1  saturating regime
```

A focal high-investment trait mode is viable when

```text
I(A) >= I_required.
```

For example, if

```text
W_high = W_baseline + s_high I(A)
```

and viability requires `W_high >= tau`, then

```text
I_required = (tau - W_baseline) / s_high.
```

The executable implementation is `eco_genetic_criticality.patch_partition_theory`.

---

## Theorem P1 — coarsening direction is determined by the aggregation exponent

For two positive patches `a,b`, define the service change from merging them:

```text
Delta(a,b) = eta[(a+b)^alpha - a^alpha - b^alpha].
```

Then:

```text
alpha > 1  -> Delta(a,b) > 0
alpha = 1  -> Delta(a,b) = 0
0 < alpha < 1 -> Delta(a,b) < 0.
```

### Proof

For `alpha>1`, `x^alpha` is strictly convex on positive `x`, and because
`f(0)=0`, strict superadditivity follows:

```text
(a+b)^alpha > a^alpha + b^alpha.
```

For `0<alpha<1`, `x^alpha` is strictly concave and the inequality reverses. The
linear case is equality. Multiplication by `eta>0` preserves the sign. ∎

### Ecological consequence

> **Same total area does not imply same interaction support.**

When interaction service is superlinear, merging patches increases support; when
it is saturating, splitting patches can increase support. There is no universal
rule that fragmentation is always harmful or always beneficial.

---

## Theorem P2 — exact equal-partition criticality

For `n` equal patches,

```text
A_j = A_total / n,
```

so

```text
I_n = eta * A_total^alpha * n^(1-alpha).
```

For `alpha != 1`, the continuous critical patch count is

```text
n_crit = [eta * A_total^alpha / I_required]^(1/(alpha-1)).
```

### Superlinear regime: `alpha > 1`

`I_n` strictly decreases in `n`. Therefore

```text
high trait mode survives  iff  n <= n_crit.
```

For integer `n`, the maximum equal-patch count is the greatest integer satisfying
this inequality.

### Sublinear regime: `0 < alpha < 1`

`I_n` strictly increases in `n`. Therefore

```text
high trait mode survives  iff  n >= n_crit.
```

For integer `n`, there is a minimum equal-patch count.

### Linear regime: `alpha=1`

```text
I_n = eta A_total
```

for every partition count. Only total area matters.

### Example

Let

```text
A_total=10, eta=1, alpha=2, I_required=25.
```

Then

```text
I_n = 100/n.
```

The high trait mode survives through four equal patches:

```text
n=4 -> I_4=25
n=5 -> I_5=20.
```

Thus five equal patches lose a trait mode that one through four equal patches
retain, despite exactly the same total habitat area.

---

## Trait-space interpretation

Suppose the high trait mode requires interaction support above a threshold. In the
superlinear regime, increasing patch count can move the system across

```text
I(A) = I_required.
```

At that boundary, the high trait mode is removed from viable trait space. This is
a **patch-configuration-induced trait-space transition**.

It is not yet a full eco-evolutionary hysteresis theorem: the present result has
no feedback from trait composition to `I`. The next theorem layer will add that
feedback and ask when the transition becomes bistable or irreversible under
reversal of habitat conditions.

---

## Corollary P3 — a conditional genetic threshold mapping

Assume a local patch of area `A` has

```text
N_e(A) = kappa A
```

and is at neutral diploid mutation-drift equilibrium:

```text
H*(A) = 4 kappa A mu / [1 + 4 kappa A mu].
```

The critical local area for the high trait mode is

```text
A_c = (I_required / eta)^(1/alpha).
```

Because `H*(A)` is strictly increasing in `A`, define

```text
H_c = H*(A_c).
```

Then, under these assumptions,

```text
A >= A_c  iff  H*(A) >= H_c.
```

### What this does and does not say

This maps an ecological interaction threshold to an equilibrium heterozygosity
threshold. It does **not** prove that heterozygosity universally provides an
early-warning signal:

- real populations may be far from mutation-drift equilibrium;
- selection, migration, bottlenecks, and linked loci can dominate;
- `N_e` need not be proportional to area;
- the high trait mode may depend on landscape-level rather than local service.

The useful next question is therefore conditional and empirical:

> Under what separation of ecological and genetic timescales does a decline in a
> genetic summary precede the patch-configuration trait transition?

---

## Why this is stronger than an ordinary area effect

The theorem does not say merely that larger patches support more individuals. It
states that, under a nonlinear interaction law, the **distribution of a fixed
amount of habitat area** changes the existence of a trait mode.

This gives three distinct quantities:

```text
A_total             total habitat area
n                   patch partition count
alpha               interaction aggregation exponent
```

A conservation intervention can preserve `A_total` while changing `n`, and hence
change trait viability when `alpha != 1`.

---

## Next theorem: feedback and hysteresis

The next extension will make interaction support depend on both patch area and
trait composition, for example

```text
I(A, x) = eta * A^alpha * q(x),
```

where `x` is the frequency or mean expression of an interaction-supporting trait
and `q` is increasing. The central question is then whether feedback produces
multiple stable equilibria and a fold bifurcation:

```text
high-trait / high-interaction state
low-trait / low-interaction state
```

The present P1--P3 results provide the patch-size threshold that such a
hysteresis theory must build on.
