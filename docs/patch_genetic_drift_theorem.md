# Genetic drift as a generational force in interaction-limited patches

## 1. State layers

The patch-interaction theorem gives a deterministic ecological state:

```text
A       patch size
q       interaction availability
```

The genetic layer adds a biallelic trait-associated state in patch `j`:

```text
p_j     high-investment allele frequency
H_j     heterozygosity = 2 p_j (1-p_j).
```

This is not yet a claim that one allele controls a natural trait. It is the
minimal population-genetic state needed to ask how finite reproduction changes
future variation after individual selection.

---

## 2. One generation: selection followed by unavoidable sampling

Let high and low allele relative fitnesses after the ecological interaction state
be `w_H>0` and `w_L>0`. Selection gives

```text
p* = p w_H / [p w_H + (1-p) w_L].
```

Then finite gamete sampling produces the next generation:

```text
2 N_e p' | p* ~ Binomial(2 N_e, p*).
```

This order matters:

```text
individual performance / selection
-> finite reproduction sampling
-> next-generation genetic state.
```

Drift is not an optional extra random disturbance. Once reproduction is finite,
this sampling kernel is part of the generation map.

---

## Theorem G1 — exact one-generation drift moments

Conditional on post-selection frequency `p*`:

```text
E[p' | p*]   = p*
Var[p' | p*] = p*(1-p*) / (2N_e)
```

and for heterozygosity `H(p)=2p(1-p)`:

```text
E[H(p') | p*]
= [1 - 1/(2N_e)] H(p*).
```

### Proof

For `K=2N_e p' ~ Binomial(2N_e,p*)`, the first two moments are the standard
binomial moments. Since

```text
H(p') = 2p' - 2(p')^2,
```

substitute `E[p']` and

```text
E[(p')^2] = Var(p') + E[p']^2
```

to obtain the stated factor. ∎

### Corollary G1.1 — drift strictly erodes expected diversity in every finite interior population

For

```text
0 < p* < 1
and
1/2 < N_e < infinity,
```

```text
0 < 1 - 1/(2N_e) < 1,
```

so

```text
E[H(p') | p*] < H(p*).
```

Thus mutation-free, migration-free finite reproduction necessarily lowers
expected heterozygosity in one generation, even though the expected allele
frequency itself remains `p*`.

This separates two facts often conflated in verbal ecology:

```text
E[p'] = p*                 no directional drift in mean frequency
E[H'] < H(p*)              unavoidable drift erosion of diversity.
```

---

## 3. Ecological closure for effective population size

To connect interaction state to finite-population strength, define

```text
N_e(A,q)
= nu A [b + (1-b)q],
```

where:

```text
nu > 0     density-to-effective-size scale
0 < b <=1  baseline density fraction when interaction availability is low.
```

This closure is an explicit model assumption. It says interaction availability
can support more effective breeders, while a low-interaction patch need not be
immediately extinct.

The one-generation drift erosion coefficient is

```text
D(A,q) = 1/[2N_e(A,q)].
```

For `b<1`, `N_e` increases and `D` decreases strictly with `q`.

---

## Theorem G2 — interaction hysteresis induces genetic-erosion hysteresis

Assume the patch interaction model from P1–P2 has `kappa A>4`. Let `q_L` and
`q_H` be the low and high interaction branch states in the bistable region, with

```text
q_L < q_H.
```

If `0<b<1`, then

```text
N_e(A,q_L) < N_e(A,q_H)
```

and therefore

```text
D(A,q_L) > D(A,q_H).
```

### Proof

`N_e(A,q)` is affine increasing in `q` with derivative

```text
nu A (1-b) > 0.
```

Apply monotonicity of `x -> 1/(2x)` on positive `x`. ∎

### Consequence

Inside the ecological hysteresis window, the same patch size and external barrier
can have two different expected genetic-erosion rates depending on ecological
history.

When a high interaction branch collapses to a low branch, the expected
heterozygosity loss per generation jumps upward by

```text
D(A,q_L) - D(A,q_H) > 0.
```

This is the first eco-genetic tipping statement in the repository. It does not
yet say that alleles have been lost irreversibly; it says the rate at which
within-patch diversity is expected to erode changes discontinuously with the
ecological branch.

---

## 4. Species-level diversity quantities

For patch weights `w_j` and allele frequencies `p_j`, define

```text
H_alpha = sum_j w_j 2p_j(1-p_j)
p_bar   = sum_j w_j p_j
H_gamma = 2p_bar(1-p_bar)
F_ST    = 1 - H_alpha/H_gamma, when H_gamma>0.
```

- `H_alpha` is mean within-patch diversity.
- `H_gamma` is diversity of the pooled metapopulation.
- `F_ST` records differentiation; it is undefined when the entire metapopulation
  is globally fixed, rather than being assigned an arbitrary value.

The current theorem directly concerns `H_alpha` under isolated drift. `H_gamma`
and `F_ST` need migration, mutation, and between-patch selection dynamics before
they can be assigned a general transition theorem.

---

## Theorem G3 — equal isolated partition multiplies local drift erosion

Let total area `T` be divided into `m` equal isolated patches. Hold `q`, `nu`,
and `b` equal across patches. Then

```text
N_e(single) = nu T [b+(1-b)q]
N_e(each patch) = N_e(single)/m.
```

Hence

```text
D(each patch)
= 1/[2N_e(each patch)]
= m/[2N_e(single)]
= m D(single).
```

Thus, with the same total area and the same interaction availability, splitting
into `m` equal isolated patches multiplies the one-generation **within-patch**
drift erosion coefficient by exactly `m`.

### Scope

This is an alpha-diversity result. It does not say pooled gamma diversity follows
the same factor, or that real fragmented landscapes lack migration. Its purpose
is to establish a clean baseline: even before interaction feedback changes `q`,
patch partition creates a mathematically exact genetic non-additivity.

---

## 5. Combined theorem sequence

The present theory stack is:

```text
P1: A_c=4/kappa is the exact onset of possible interaction bistability.
P2: bistable patches have a collapse/recovery hysteresis window.
P3: a high trait mode can inherit discontinuous loss and recovery.
P4: equal habitat partition can remove hysteresis capacity at fixed total area.
G1: finite generation turnover necessarily erodes expected interior heterozygosity.
G2: ecological branch history creates distinct genetic-erosion rates.
G3: equal isolated partition multiplies local drift erosion by patch count.
```

The next mathematical question is deliberately harder:

```text
When mutation, migration, and trait-dependent selection are added,
does a genetic recovery threshold differ from the ecological trait-mode recovery threshold?
```

That requires a new multi-patch stochastic model. It should not be claimed from
P1–P4 and G1–G3 alone.