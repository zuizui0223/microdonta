# Patch-size thresholds, interaction hysteresis, and trait-mode tipping

## Purpose

This is the deterministic interaction-feedback layer of the eco-genetic theorem
sequence. It asks a specific question:

> When individuals collectively sustain an interaction environment, can patch
> size create a sharp threshold between low- and high-interaction trait regimes?

The answer is yes in an analytically tractable mean-field model. The result is not
that every small patch loses a trait. It is that a specific positive-feedback
structure has an exact patch-size boundary for the *possibility* of bistability,
hysteresis, and discontinuous trait-mode loss.

The executable implementation is
`causal_model.patch_interaction_bifurcation_theory`. The finite-population genetic
extension is in `docs/patch_genetic_drift_theorem.md`.

---

## 1. Interaction-state model

Let

```text
q ∈ (0,1)
```

be patch-level interaction availability: an aggregate state representing, for
example, persistent pollinator encounter, compatible-mate encounter, collective
floral display, or partner availability. Let

```text
A > 0      patch size or effective interaction-supporting area
kappa > 0  strength of positive feedback from current interaction state
theta      exogenous interaction barrier / degradation pressure.
```

The equilibrium equation is

```text
q = sigmoid{kappa(Aq - theta)},
```

where

```text
sigmoid(x) = 1 / [1 + exp(-x)].
```

Large `Aq` makes interactions easier to maintain; large `theta` makes them harder.
The equation is a minimal mean-field representation of individual interactions
feeding back on the patch-level interaction environment.

Writing the fixed point as a barrier curve gives

```text
theta(q) = Aq - logit(q)/kappa,

logit(q) = log[q/(1-q)].
```

---

## 2. Theorem P1 — exact critical patch size for possible bistability

Define

```text
A_c = 4/kappa.
```

Then:

```text
A <= A_c  -> exactly one interaction equilibrium for every theta
A >  A_c  -> there exists a nonempty theta interval with three equilibria.
```

### Proof

The derivative of the fixed-point update is

```text
f'(q) = kappa A sigmoid'(kappa[Aq-theta]).
```

At a fixed point, `sigmoid(...)=q`, hence

```text
f'(q) = kappa A q(1-q).
```

Because

```text
q(1-q) <= 1/4,
```

we have

```text
f'(q) <= kappa A / 4.
```

If `kappa A <= 4`, the fixed-point map cannot have slope greater than one; the
barrier curve is monotone and the fixed point is unique. If `kappa A > 4`, the
equation

```text
kappa A q(1-q)=1
```

has two distinct interior solutions. The barrier curve has one local minimum and
one local maximum, producing a nonempty interval of barriers with three
intersections. ∎

The two saddle-node interaction states are

```text
q_- = [1 - sqrt(1 - 4/(kappa A))]/2
q_+ = [1 + sqrt(1 - 4/(kappa A))]/2.
```

Their corresponding barriers are

```text
theta_- = theta(q_-)
theta_+ = theta(q_+),
```

with

```text
theta_- < theta_+.
```

---

## 3. Theorem P2 — hysteresis window

For

```text
theta_- < theta < theta_+,
```

there are three equilibria:

```text
q_L < q_- < q_M < q_+ < q_H.
```

The outer equilibria `q_L` and `q_H` are stable, and the middle equilibrium
`q_M` is unstable.

### Proof

At fixed points, stability is determined by

```text
kappa A q(1-q) < 1.
```

The quadratic inequality is true outside `(q_-,q_+)` and false inside it.
Therefore the two outer branches are stable and the middle branch is unstable. ∎

Under slowly increasing barrier `theta`, a patch on the high branch remains there
until

```text
theta = theta_+,
```

where it disappears and `q` falls discontinuously to the low branch. Under slowly
decreasing barrier, the low branch persists until

```text
theta = theta_-,
```

where it jumps to the high branch. Thus

```text
recovery barrier theta_- < collapse barrier theta_+.
```

This is hysteresis: the same patch size and barrier inside the window can support
two states, depending on history.

---

## 4. Theorem P3 — high-trait mode tipping

Let a high-investment trait mode require interaction availability

```text
q >= q_req,
```

for viability. This is a deliberately general trait-space statement: `q_req` may
be derived later from a full trait-fitness function, but no particular flower or
life history is assumed here.

If

```text
q_- < q_req < q_+,
```

then inside the hysteresis window:

```text
low stable branch:  q_L < q_req  -> high trait mode absent
high stable branch: q_H > q_req  -> high trait mode present.
```

Therefore high-trait viability is history-dependent. It collapses discontinuously
at `theta_+` and reappears only at `theta_-`.

### Proof

Within the three-root interval, `q_L<q_-<q_req<q_+<q_H`. The required mode is
below threshold on the low branch and above threshold on the high branch. P2 gives
the discontinuous branch transitions. ∎

This is a theorem about a trait **mode**, not yet a theorem about mean trait value.
A full trait-space model can later map `q_req` to a high-trait component of
`Omega_tau`.

---

## 5. Theorem P4 — habitat partition is non-additive for hysteresis capacity

Let total area be

```text
A_total = sum_j A_j.
```

For an equal partition into `m` patches, each has

```text
A_j = A_total/m.
```

Patch-level hysteresis is possible iff

```text
A_total/m > 4/kappa.
```

Consequently, for any `A_total > 4/kappa`:

```text
one patch of area A_total
```

is hysteresis-capable, while an equal partition with

```text
m >= ceil(A_total / A_c)
```

has every patch at or below `A_c` and therefore no patch capable of this
hysteresis mechanism.

### Meaning

```text
one patch with area A_total
!=
m equally split patches with the same total area
```

for interaction-feedback capacity. The theorem is not a general persistence law:
it says total habitat area does not by itself determine whether this particular
positive-feedback / hysteresis mechanism can occur. Patch-size distribution is a
state variable.

---

## 6. What is mathematically new here

The previous channel theorems established an observation boundary: net fitness
alone cannot identify the channel that changed. P1--P4 establish a dynamical
boundary:

```text
below A_c:
    no bistability from this logistic interaction feedback

above A_c:
    bistability is possible
    interaction state can collapse discontinuously
    recovery requires a lower barrier than collapse
    high-trait viability can inherit that hysteresis
    equal habitat partition can remove this capacity despite fixed total area.
```

This produces testable phase-diagram questions for later ABMs, rather than a
post-hoc claim that every trait change is caused by patch size.

---

## 7. Scope and genetic extension

- `q` is a mean-field patch interaction state, not a directly observed pollinator
  count or mating probability.
- The model requires positive feedback of the stated logistic form.
- P4 concerns capacity for hysteresis, not guaranteed high-trait persistence.
- P1--P4 contain no allele frequencies by themselves.

The next layer is now implemented rather than merely proposed:
`docs/patch_genetic_drift_theorem.md` adds finite reproduction, expected
heterozygosity loss, interaction-branch-dependent drift erosion, and the exact
within-patch drift cost of equal isolated partition. It still does **not** prove a
separate genetic recovery threshold; that requires mutation, migration, and
trait-dependent selection in a multi-patch model.