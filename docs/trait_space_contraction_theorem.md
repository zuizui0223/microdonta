# Relationship loss and the contraction of viable trait space

**Comparative statics for a relationship-rewarded costly trait.**

This note formalises a restricted claim used by the spatial-metapopulation
backend: when a relationship contributes a non-negative benefit to a costly
trait, removing that benefit can reduce the trait values that are viable.

The statements below are **conditional algebraic results**. Their proofs are in
this document. The randomised functions in `causal_model/trait_space_theory.py`
and `tests/test_trait_space_theory.py` are regression checks for the
implementation; they do not constitute mathematical proof.

The model does not claim that a particular natural system has this structure, nor
that a trait-space geometry uniquely reveals the channel through which fitness
changed. The latter identifiability question is treated separately in the next
theory stage.

---

## 1. Setup

Let a scalar heritable investment trait be `z ∈ [0, 1]`. A rare mutant at a
quasi-stationary resident has invasion fitness

```text
s(z; I, R) = I · B(z) − C(z) + K + R.
```

| symbol | meaning | assumption |
|---|---|---|
| `B(z)` | benefit supplied by the relationship, e.g. pollinator service | non-decreasing; `B(0)=0` |
| `C(z)` | trait cost to allocation, fecundity, and/or survival | non-decreasing; `C(0)=0` |
| `K` | relationship-independent baseline net fitness | `K ≥ 0` |
| `R` | alternative-route compensation after loss | `R ≥ 0` |
| `I` | relationship state | `1` intact, `0` lost |

The viable trait set is

```text
Ω(I, R) = { z ∈ [0, 1] : s(z; I, R) ≥ 0 }.
```

Before loss it is `Ω(1, 0)`; after loss it is `Ω(0, R)`.

The theorem does not assume that evolution has one preferred direction. It
assumes only a particular cost-benefit structure for an investment trait.

---

## 2. Algebraic results

### T1 — Pure relationship loss weakly contracts the viable set

If `B(z) ≥ 0` for every `z`, then

```text
Ω(0, 0) ⊆ Ω(1, 0),
z_max(0, 0) ≤ z_max(1, 0).
```

**Proof.** For every `z`,

```text
s(z; 1, 0) − s(z; 0, 0) = B(z) ≥ 0.
```

Therefore, `s(z; 0, 0) ≥ 0` implies `s(z; 1, 0) ≥ 0`; hence the first viable
set is a subset of the second. The upper edge of a subset cannot exceed the
upper edge of its superset. ∎

This is intentionally a weak result. It follows from the stated sign
assumption; it is not a discovery about all ecological interactions.

### T2 — Incomplete compensation preserves that inclusion

Let

```text
D = { z : C(z) > K }
```

be traits that are not viable on the baseline alone. If

```text
R ≤ B(z)  for every z ∈ D,
```

then

```text
Ω(0, R) ⊆ Ω(1, 0).
```

**Proof.** Take `z ∈ Ω(0, R)`. If `z ∉ D`, then `C(z) ≤ K`, so
`B(z) − C(z) + K ≥ B(z) ≥ 0`. If `z ∈ D`, the condition gives
`B(z) − C(z) + K ≥ R − C(z) + K ≥ 0`. In both cases `z ∈ Ω(1, 0)`. ∎

### T3 — Exact retention threshold for the existing upper-edge trait

Let

```text
z* = z_max(1, 0)
```

be the largest pre-loss viable trait. Define

```text
R_keep = max(0, C(z*) − K).
```

Then

```text
R ≥ R_keep  iff  z* ∈ Ω(0, R).
```

On a fixed ordered trait grid with non-decreasing `C`, this is also the exact
threshold for preventing the **upper edge** from receding:

```text
R ≥ R_keep  iff  z_max(0, R) ≥ z_max(1, 0).
```

**Proof.** After loss,

```text
s(z*; 0, R) = R − C(z*) + K.
```

This is non-negative exactly when `R ≥ C(z*) − K`; non-negativity of `R` yields
`R_keep`. If `R < R_keep`, monotonicity of `C` makes every `z ≥ z*` non-viable
after loss, so the edge is strictly below `z*`. If `R ≥ R_keep`, `z*` remains
viable. ∎

The often intuitive quantity

```text
R_replace = B(z*)
```

is a **sufficient replacement bound**, not generally the exact threshold. Since
`z*` was viable before loss,

```text
C(z*) − K ≤ B(z*),
```

so `R_replace ≥ R_keep`. Equality occurs only when the pre-loss edge lies on the
invasion boundary, `s(z*; 1, 0)=0`.

See `docs/theory_corrections.md` for the correction record.

### T4 — Under concavity/convexity, the benefit route cannot fragment support

If `B` is concave and `C` is convex, then

```text
s(z; I, R) = I·B(z) − C(z) + K + R
```

is concave. Since `s(0; I, R)=K+R ≥ 0`, its super-level set
`{z : s(z; I, R) ≥ 0}` is an interval containing zero. Thus within this model
family, the relationship-benefit route can recede an edge but cannot split a
connected viable set into multiple components.

This is a statement about this one-dimensional cost-benefit model. It does not
say that fragmentation is a universal signature of a spatial mechanism.

---

## 3. A separate spatial construction

The function `spatial_route_contraction` supplies a **numerical construction**
in which each trait is intrinsically suitable on a subset of patches and
establishment requires reaching at least one suitable patch. Reducing
connectivity can then shrink, or sometimes fragment, the realised viable set
without changing local per-capita invasion fitness.

That construction shows possibility, not a general theorem about all dispersal
loss. It is useful precisely because it forces the theory to distinguish
local-fitness and establishment channels.

---

## 4. Correspondence with the individual-based model

The spatial ABM has a rare-invader growth factor of the form

```text
G(z) = survival(z) · (1 + repro(z)),

repro(z) = floor
         + interaction-gated service(z)
         + mate matching(z, resident)
         + resources
         + compensation
         − trait cost(z).
```

The interaction-gated service and trait cost share the leading `B(z)-C(z)`
structure of T1–T3. The ABM additionally includes density dependence, local
resources, mate matching, demographic stochasticity, and spatial structure.
Therefore ABM outcomes are **robustness checks under relaxed assumptions**, not
proofs of T1–T4.

In the current sampled ABM check, upper-edge recession occurs in many but not
all parameter draws because the mate term and other demographic processes can
counteract the simple benefit-loss channel. That non-universality is expected.

---

## 5. What this theory does and does not identify

These results establish conditional comparative statics:

```text
relationship-gated benefit lost
+ costly trait retained by that benefit
+ insufficient compensation
→ some previously viable trait values may cease to be viable.
```

They do **not** establish the converse:

```text
observed contraction
→ relationship-benefit loss.
```

A different mechanism can yield the same total trait performance. In particular,
trait-correlated loss of reachable patches can mimic an upper-edge contraction.
The next mathematical task is therefore a channel-identifiability theorem:
which observations are structurally insufficient, and which channel-resolved
observations break that equivalence.

---

## 6. Scope

- The theory is mean-field, scalar-trait, and invasion-based.
- `Ω_inv` is a viable/invasible set, not a long-run coevolutionary endpoint.
- Benefit and cost monotonicity are assumptions, not empirical facts.
- Frequency dependence, multidimensional traits, and non-monotone compensation
  can change the geometry.
- All conclusions are conditional on the stated mathematical model; they are not
  causal truths about a natural system.
