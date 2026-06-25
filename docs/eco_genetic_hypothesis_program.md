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

### P1 — trait-mode lifting

Given two already-established stable interaction states `q_L<q_H`, a declared
high-trait region `Z_H`, and viability margin

```text
m_H(q) = max_{z in Z_H}[W(z;q)-tau],
```

then

```text
m_H(q_L)<0<m_H(q_H)
```

implies that the high-trait mode is branch dependent. This is Type T conditional
on the existence of those branches and the declared performance map.

### P2 — patchwise non-additivity

If a collective interaction mechanism has a justified patchwise threshold
`A_j>A_c`, then total area alone cannot guarantee that mechanism. This is Type C:
the threshold must first be derived or assumed in the ecological model.

### G1 — conditional eco-genetic ordering

If the life-cycle-derived effective reproductive size `Psi(A,q,xi)` increases
with `q` and transmission variance decreases with effective size, low interaction
branches erode expected local diversity faster. This is Type C, not a universal
claim about interaction systems.

---

## Central hypothesis H_critical

> If individual interactions are positively frequency dependent and interaction
> intensity depends nonlinearly on patch size, then there can be a critical patch
> size A_c across which a high-investment trait mode switches discontinuously
> between present and absent states.

### What would be a theorem

For a specified dynamic system, prove all of the following:

1. a pair of saddle nodes or another rigorously defined branch transition exists;
2. the high-trait viability margin changes sign across its stable branches;
3. the corresponding trait-space component is absent on one branch and present on
   the other.

A logistic feedback model can be a worked corollary. It cannot establish the
claim for all positive-frequency-dependent systems.

### What the dynamic simulation must test

Simulation targets a phase diagram over at least

```text
patch size A
external barrier theta
feedback strength kappa
trait-cost / interaction-benefit parameters.
```

The report must distinguish:

```text
no transition observed
smooth transition
bistable transition under the declared model
transition sensitive to finite population noise.
```

A simulation may locate candidate transition regions and counterexamples. It does
not prove the general theorem.

---

## Central hypothesis H_genetic_lag

> Under identifiable conditions, genetic indicators associated with a high-trait
> mode change before that mode disappears from the viable trait space.

This is presently Type H, not a theorem and not implied by G0/G1.

### Required event definitions

A future dynamic model must predeclare:

```text
tau_trait  first time the high-trait mode is absent from Omega_tau
tau_H      first time local diversity metric crosses its warning boundary
tau_var    first time spatial variance of the high-trait allele crosses boundary
tau_auto   first time spatial autocorrelation crosses boundary.
```

A genetic lead requires a declared inequality such as

```text
tau_H < tau_trait.
```

The warning boundary must be externally specified or justified by a dynamical
criterion; it cannot be chosen after viewing simulation output.

### What must be added before proof is possible

```text
multi-patch allele transmission
mutation or standing variation policy
migration matrix
trait-genotype map
selection map W(z;q)
finite reproductive transmission kernel
patch extinction / recolonisation rules.
```

Only then can one ask whether a leading eigenvalue, quasi-stationary variance, or
other quantity provides a theorem-level early warning condition.

---

## Central hypothesis H_fragmentation

> At fixed total habitat area, subdivision into many small patches can prevent
> maintenance of a high-investment trait mode and its associated genetic diversity
> because more patches fall below the interaction-support threshold.

This contains two distinct claims.

### Ecological component

If each patch must exceed a justified threshold to support the collective
interaction mechanism, P2 gives the limited Type C result:

```text
max_j A_j <= A_c
=> no patch expresses that mechanism.
```

This does not yet prove high-trait loss; the trait-mode lifting condition must
also hold.

### Genetic component

The statement that associated diversity is not maintained is Type H until a
multi-patch transmission model is specified. Fragmentation can reduce local
`H_alpha` through stronger drift while increasing `F_ST`; pooled `H_gamma` can
behave differently. The theory must never collapse these quantities into one
word, 'diversity'.

### Dynamic simulation contrast

At fixed total area, compare at minimum:

```text
one large patch
m equal isolated patches
m equal patches with controlled migration.
```

Report separately:

```text
interaction state q
high-trait viable-set occupancy
census N and effective reproductive size proxy
H_alpha
H_gamma
F_ST
trait-associated allele frequency distribution.
```

---

## Simulation role and stop rules

Dynamic simulation begins only after every update equation is specified. Each run
must state whether it is testing a theorem assumption or a central hypothesis.

Stop and report a counterexample when any of these occurs:

```text
positive feedback but no bistability in the tested range
bistability without high-trait margin sign change
trait-mode collapse without a genetic leading signal
fragmentation lowers H_alpha but raises or preserves H_gamma
interaction increase raises reproductive skew and lowers N_e.
```

These are scientific results, not failed simulations.

---

## The current relation in one sentence

PR #48 provides the **logical joints** of the program: it says exactly which
additional model-specific facts are required to turn H_critical,
H_genetic_lag, and H_fragmentation into theorems, and which facts must instead be
examined by dynamic simulation.