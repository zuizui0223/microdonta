# Eco-genetic criticality program: theorems, hypotheses, and dynamic simulations

## Central causal chain

The long-term research program is organised around the proposed chain

```text
patch size
-> interaction intensity
-> trait-space topology
-> population size / effective reproductive size
-> genetic diversity.
```

The chain is **not** itself a theorem. It is a scientific hypothesis program.
Each arrow must be represented by a declared state equation or life-cycle map.

The repository separates four claim types:

```text
Type T  mathematical theorem under explicit assumptions
Type C  conditional theorem once an ecological closure is supplied
Type H  substantive dynamic hypothesis about an ecosystem model
Type S  simulation result for a declared model, not proof of T/C/H.
```

The current roadmap is layered as:

```text
general theorem layer
-> canonical logistic corollary
-> potential viability
-> finite realised trait abundance and occupancy
-> stochastic genetic first-passage experiments
-> future mutation/recolonisation model
```

The phase-diagram layer now uses a declared finite-bin recruitment closure in its
standard and full profiles. It combines `n(z_k)`, allele-linked two-kernel
recruitment, and optional trait/allele interaction feedback. This is Type S: it
supports model-specific comparisons, not a theorem about natural systems.

Each arrow adds assumptions. Later layers may diagnose model-specific transition
regions, but they do not retroactively strengthen earlier theorem claims.

---

## The theorem layer already supplied by PR #48

### G0 — finite transmission variance

If post-selection transmission is unbiased and has positive conditional variance,
expected local gene diversity declines relative to the post-selection state:

```text
E[H(P') | p*] = H(p*) - 2 Var(P'|p*) < H(p*).
```

This is Type T. It makes no ecological claim about patch size, pollination, or
whether a high-interaction patch has a larger effective size.

### P0 — no-bistability certificate

For interaction update

```text
q_next = g{kappa(A q - theta)}
```

with global slope bound `M=sup|g'|`,

```text
kappa A M < 1
```

certifies one fixed point. This is Type T.

Its converse is deliberately not asserted:

```text
kappa A M >= 1
```

only means that the global contraction proof no longer establishes uniqueness.
It is not a proof of bistability.