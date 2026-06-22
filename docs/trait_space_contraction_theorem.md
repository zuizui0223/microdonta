# Relationship loss and the contraction of viable trait space

**A comparative-statics theorem for the spatial-metapopulation rule-transition backend.**

This note formalises the headline result of
`causal_model.spatial_metapopulation_abm`: that losing an ecological relationship
which *rewards* a costly trait contracts the set of trait values that can invade and
persist. We give a mean-field invasion-fitness model, prove four comparative-statics
results, separate a second (spatial) route as a proposition, and state the link to
the individual-based simulation and the empirical predictions. Every theorem is
machine-verified in `causal_model/trait_space_theory.py`
(`tests/test_trait_space_theory.py`), in the spirit of
`docs/rach_mathematical_foundations.md`.

The claims are **conditional and structural**: they say *what must follow from the
stated trade-off structure*, not that any particular system in nature obeys it.

---

## 1. Setup

A scalar heritable trait (investment) `z ∈ [0,1]`. A rare mutant `z'` introduced into
a monomorphic resident at quasi-stationary density has mean-field invasion fitness

```
s(z; I, R) = I · B(z) − C(z) + K + R
```

| symbol | meaning | assumption |
|---|---|---|
| `B(z)` | reproductive benefit conferred by the relationship (e.g. pollinator service), increasing in investment | `B` non-decreasing, `B(0)=0` |
| `C(z)` | cost of the trait (allocation trade-off, to fecundity and/or survival) | `C` non-decreasing, `C(0)=0` |
| `K` | relationship-independent baseline net fitness (resources, mating, mortality) | `K ≥ 0` |
| `R` | compensation supplied by an alternative route after the loss | `R ≥ 0` |
| `I` | relationship state: `1` intact, `0` lost | — |

The **direction** of trait evolution is never assumed. The only structural input is a
trade-off: both benefit and cost increase with investment. `K ≥ 0` encodes that a
zero-investment phenotype persists without the relationship (the organism is not
obligately dependent on the costly trait).

The **viable trait set** is

```
Ω(I, R) = { z ∈ [0,1] : s(z; I, R) ≥ 0 } .
```

Before the loss: `Ω(1, 0)`. After: `Ω(0, R)`.

---

## 2. Theorems

### T1 — Pure relationship loss contracts the viable set

*If `B, C` are non-decreasing with `B(0)=0` and `K ≥ 0`, then with no compensation*

```
Ω(0, 0) ⊆ Ω(1, 0),   and   z_max(0,0) ≤ z_max(1,0),
```

*where `z_max(·)` is the upper edge of the viable set.*

**Proof.** For every `z`, `s(z;1,0) − s(z;0,0) = B(z) ≥ 0`, so `s(z;0,0) ≥ 0 ⇒
s(z;1,0) ≥ 0`; hence `Ω(0,0) ⊆ Ω(1,0)`, and the supremum of a subset cannot exceed
that of the superset. ∎

### T2 — Incomplete compensation still contracts

*Call the relationship-dependent traits `D = { z : C(z) > K }` (the traits that are
not viable on the baseline alone). If the alternative route is weaker than the
relationship on every such trait,*

```
R ≤ B(z)  for all z ∈ D,
```

*then `Ω(0, R) ⊆ Ω(1, 0)`.*

**Proof.** Take `z ∈ Ω(0,R)`, i.e. `R − C(z) + K ≥ 0`. If `z ∉ D` then `C(z) ≤ K`, so
`s(z;1,0) = B(z) − C(z) + K ≥ B(z) ≥ 0`. If `z ∈ D` then by hypothesis `R ≤ B(z)`, so
`s(z;1,0) = B(z) − C(z) + K ≥ R − C(z) + K ≥ 0`. Either way `z ∈ Ω(1,0)`. ∎

The condition `R ≤ B(z)` on `D` is the formal meaning of **incomplete compensation**:
the substitute route does not, for any relationship-dependent trait, exceed the
benefit it replaces.

### T3 — The compensation threshold

*Let the upper edge be `z* = z_max(1,0)` and `R* = B(z*)`. Then:*

* *(sufficient compensation) `R ≥ R* ⇒ z_max(0,R) ≥ z_max(1,0)`: the upper edge does
  not recede — no contraction;*
* *(strict contraction) if the edge trait is itself relationship-dependent
  (`C(z*) > K`), then with `R = 0`, `z_max(0,0) < z_max(1,0)` strictly.*

`R*` is the exact threshold separating "trait loss" from "trait retention".

**Proof.** *(sufficient)* `s(z*;0,R) = R − C(z*) + K ≥ B(z*) − C(z*) + K = s(z*;1,0) ≥ 0`,
so `z*` stays viable, hence `z_max(0,R) ≥ z*`. *(strict)* `s(z*;0,0) = −C(z*) + K < 0`
because `C(z*) > K`, so `z*` is no longer viable and the edge moves strictly below
`z*` (the set is left-anchored at `0`, which is viable since `s(0;·)=K+R≥0`). ∎

### T4 — Contraction, not fragmentation (a signature)

*If benefit has diminishing returns and cost is accelerating — `B` concave, `C`
convex — then `s(·;I,R)` is concave, so `Ω(I,R)` is an interval `[0, z_max]`. The
relationship route can only recede the upper edge; it can never split the viable
set.*

**Proof.** `s = I·B − C + (K+R)` is concave (concave minus convex plus constant), and
`s(0;·) = K+R ≥ 0`. A concave function that is non-negative at `0` has a super-level
set `{s ≥ 0}` that is an interval containing `0`. ∎

**Consequence (mechanism signature).** Under the standard trade-off convexity, the
relationship route produces **contraction or shift of the upper boundary** but never
**fragmentation**. Observing a *fragmented* viable trait set therefore implicates a
different mechanism — see Proposition S1.

---

## 3. Proposition S1 — the spatial route is fitness-independent

Realised persistence in a metapopulation needs more than `s(z) ≥ 0`: a lineage must
**establish** across reachable patches. Let each trait be intrinsically suitable on a
patch-dependent subset, and let establishment require reaching at least one suitable
patch from the seeded patch, with reachability increasing in dispersal connectivity.

**Proposition S1.** *Reducing dispersal connectivity (e.g. habitat fragmentation,
loss of dispersal vectors) shrinks the realised viable set even when per-capita
invasion fitness `s(z)` is unchanged, and — because suitable patches are scattered in
trait space — can split it into multiple components.*

This is demonstrated numerically by `spatial_route_contraction`: cutting connectivity
from high to zero contracts the realised viable set in 200/200 random landscapes and
fragments it in ~97% of them. It is a **second, independent route** to trait-space
loss, with a distinct signature (fragmentation) from the relationship route (interval
contraction, T4).

---

## 4. Correspondence with the individual-based simulation

The spatial ABM's rare-invader one-step growth factor (mutation off, age-0 invader
against a monomorphic resident; `abm_invasion_factor`) is

```
G(z) = survival(z) · (1 + repro(z)),
repro(z) ∝ floor + investment_reward · [I · benefit · z · availability]   (= service, increasing, gated by I)
              + 0.20 · mate(z; resident)                                   (secondary, frequency-dependent)
              + resources + R(compensation) − trait_cost · z              (cost, increasing)
survival(z) = base − survival_tradeoff · z − predation .
```

The dominant trait-level structure is exactly `I·B(z) − C(z) + K`: an
increasing, relationship-gated benefit minus an increasing cost. The simulation adds
a **secondary mate-matching term** (stabilising selection toward the resident), which
is the one component the clean theorem omits. Empirically the theorem's prediction —
the viable upper edge recedes when the relationship is lost under incomplete
compensation — holds in ~94% of randomly drawn ABM ecosystems
(`tests/test_trait_space_theory.py::test_abm_upper_edge_recedes_under_loss`); the
remaining ~6% are cases where the mate term keeps a near-resident high trait viable.
So the simulation result is, to leading order, an instance of T1–T3, with the mate
term and demographic stochasticity as the documented second-order departures.

---

## 5. Why this is more than a restatement of relaxed selection

Classical *relaxed-selection* theory (Lahti et al. 2009) predicts that traits decay
when the selection maintaining them weakens. The results here sharpen that in three
ways that are testable:

1. **Object.** The prediction is about the *viable set* `Ω_inv` (its volume,
   connectedness, and upper edge), not a mean trait. T4 makes a falsifiable
   distinction between **contraction/shift** (relationship route) and
   **fragmentation** (spatial route) — two mechanisms that a mean-trait analysis
   conflates.
2. **Threshold.** T3 gives an explicit **compensation threshold** `R* = B(z_max)`:
   trait loss occurs *iff* the alternative route is weaker than the lost benefit at
   the trait it supported. This converts "relaxed selection" into a quantitative
   condition — e.g. *flowers shrink after pollinator loss only if autonomous selfing
   returns less than the pollinator did at the current flower size.*
3. **Dissociation.** The channel-decomposition control
   (`spatial_metapopulation_analysis.decompose_channels`) shows the prediction is
   specific: removing a *predator* (with the trait-supporting relationship intact)
   does **not** contract trait space, whereas removing the trait-supporting
   relationship does. "Any relationship loss → trait loss" is false.

---

## 6. Empirical predictions (for testing against data)

* **Pollinator decline → flower display.** The viable set of display sizes should
  contract at its *upper* edge (large displays disappear first), not fragment, and
  only when autonomous selfing / alternative pollinators return less than the lost
  service at large display (T3). The Izu *Campanula microdonta* gradient (this
  repository's worked example) is the target system.
* **Habitat fragmentation → trait space.** Loss of connectivity should *fragment*
  the realised trait set (S1), a signature distinct from pollinator loss, even where
  mean trait barely moves.
* **Predator removal.** Should produce trait-space *shift / expansion*, not the
  contraction expected from losing a trait-supporting mutualism (dissociation, §5.3).

---

## 7. Scope and limitations

* Mean-field, monomorphic-resident invasion fitness; `Ω_inv` is the *instantaneously
  invasible* set against the pre-change resident, not the long-run co-evolutionary
  endpoint (no evolutionary branching is modelled).
* Scalar trait; "covariance" in the ABM is `cov(trait, genotype)`, and the trade-off
  "matrix" is a trait→(fecundity, survival) vector. Multi-trait `Ω_inv` geometry is
  future work.
* The benefit-increasing-in-trait assumption is a trade-off structure, not a trait
  direction, but it is an assumption; saturating or frequency-dependent benefits
  would modify T3.
* All statements are conditional on the model family, constraints, and observed
  pattern — admissibility and conditional necessity, not causal truth in nature.
