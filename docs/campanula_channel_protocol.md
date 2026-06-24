# Campanula channel-identification protocol

## Purpose

The N1--N4 theorem family says what is and is not identifiable after total trait
performance has been factorised as

```text
W(z) = F(z) E(z).
```

For a Campanula study, this cannot be applied merely because flower size, selfing,
or visitor identity varies among islands. This protocol makes the necessary
mapping explicit before field data are interpreted.

The executable checker is `causal_model.campanula_channel_protocol`.

---

## 1. The question that the theorem can answer

For a predeclared floral trait `z`, the narrow theorem-compatible question is:

> Did the between-regime change arise through **total local reproduction** `F(z)`
> or through **establishment/reachability conditional on viable seed production**
> `E(z)`?

A workable life-cycle definition is:

```text
W(z) = expected retained recruits per maternal individual
       over a stated census window

F(z) = viable seed output per maternal individual,
       conditional on adult survival

E(z) = retained recruitment conditional on viable seed output.
```

This is a declared modelling choice. It is not an assertion that every process in
a natural population is exactly multiplicative or independent.

### What this question does not yet answer

`F(z)` is **total local reproduction**. It can include autonomous selfing,
animal-mediated pollination, resource limitation, pollen quality, and other local
processes. Thus:

```text
F versus E identified
≠ pollinator-mediated reproduction versus autonomous selfing identified.
```

To attribute variation inside `F` specifically to pollinator service, a separate
component model and experiment must be declared.

---

## 2. Minimum theorem-compatible observation set

### A. Common trait domain

The same trait values or predeclared bins must be evaluated in every compared
regime. For example:

```text
flower-size bins defined before sampling
or
individual-level standardized flower-size values
or
a specified multivariate floral phenotype score.
```

Comparing island-level means alone does not create a common trait domain.

### B. Total performance `W(z)`

Choose one census scale before collecting data, such as:

```text
retained seedlings per maternal individual by the following census season.
```

The interval, survival stage, and treatment of zero values must be declared. A
fruit-set rate alone can be a local reproductive output, but is not automatically
`W` when recruitment differs among islands.

### C. Local reproductive factor `F(z)` or a proxy

The direct version is:

```text
viable seeds per maternal individual, conditional on adult survival.
```

The proxy version is:

```text
X_i(z) = q_i(z) F_i(z).
```

N3 permits relative inference only when the conversion `q_i(z)` is stable across
the compared regimes or separately calibrated. A visit count is therefore not a
valid `F` observation by default.

### D. Positive interior and boundary states

N1--N4 use division, so `W`, `F`, and `E` must be positive in the stratum to
which the theorem is applied. Zeros are biologically meaningful; they must be
handled separately, for example by a predeclared zero-inflated or extinction
analysis rather than silently dividing by zero.

---

## 3. Current published record

The current source-confirmed Izu-island record contains directional patterns in:

```text
selfing rate
flower size
Bombus to halictid pollinator transition.
```

It does not currently contain:

```text
trait-specific W(z)
trait-specific F(z)
a factorisation statement W=FE
a validated stable proxy q(z) for F.
```

The correct theorem status is therefore:

```text
not ready for F-versus-E identification
```

This is not a failure of the record. It tells us exactly why trait geometry,
flower-size means, selfing rates, and visitor identity cannot settle the channel
question on their own.

---

## 4. Planned prospective design

The protocol checker includes a **planned**, not-yet-collected design:

```text
trait z:
    common individual flower-trait values or fixed bins

W(z):
    retained recruits per maternal individual over a shared census window

F(z):
    viable seed output per maternal individual conditional on adult survival

E(z):
    recruitment/reachability conditional on viable seed output
```

Once collected, this design would be theorem-ready for the local-reproduction
versus establishment comparison. It does not make the current published data
ready, and it does not by itself establish a pollinator-specific component inside
`F`.

---

## 5. Pollinator-specific follow-up is a separate causal layer

To ask whether the local-reproduction difference is specifically pollinator
mediated, specify an operational component model before analysis. A possible
family of contrasts is:

```text
open flowers
visitor exclusion / bagging
supplemental pollination
```

But these treatments do not automatically have an additive interpretation. For
example, bagging can alter microclimate or autonomous selfing, and supplemental
pollination measures a particular capacity/limitation contrast rather than a
universal pollinator factor. The study must state what component is estimated and
what assumptions make that interpretation defensible.

The protocol therefore distinguishes:

```text
F-versus-E theorem ready
from
pollinator component model declared and validated.
```

---

## 6. Readiness states emitted by the checker

| readiness | meaning |
|---|---|
| `not_ready` | missing `W`, a local factor, common trait domain, factorisation, boundary handling, or informative proxy calibration |
| `ready_direct_factor` | direct `F` and `W` are defined and collected within the declared factorisation |
| `ready_relative_stable_proxy` | a validated stable proxy provides relative `F` change with `W` |
| `conditional_on_proxy_stability` | identification would follow only if the stated proxy-stability assumption is defended; it is not silently upgraded to validation |

The checker separately labels the pollinator-specific status:

```text
not_addressed
requires_component_decomposition
component_model_declared.
```

---

## 7. Relation to the current RACH study design

The existing `campanula_real_data` workflow uses the published gradients to retain
competing explanations and rank next observations by resolution value. This
protocol does not replace that workflow. It adds a theorem-derived admissibility
constraint:

> A candidate measurement has channel-identification value only when it supplies
> `W` plus a direct factor or a proxy whose conversion is stable/calibrated across
> the comparison.

Thus the framework now distinguishes three results:

```text
published pattern resolves neither mechanism nor channel
RACH design ranks useful next observations
channel theorem states which observation class can actually break F/E equivalence.
```
