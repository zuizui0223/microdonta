# Exact one-step factorisation in the colonization life cycle

## What is being factorised

The colonization backend's published trait-space outcome is a stochastic,
multi-step rare-lineage growth rate. That quantity is **not** automatically the
positive product required by N1--N4.

This module therefore does something narrower and exact. For one initial adult,
in one specified local context, it calculates the expectation of **juvenile
recruits produced in the next step**. It mirrors the actual order of events in
`_colonization_step`:

```text
survive
-> conceive
-> disperse through a corridor and settle
   OR remain local and settle.
```

Let:

```text
S(z)  = probability that the initial adult survives to reproduce
C(z)  = probability of conception after survival
D(z)  = dispersal-investment probability, benefit_shape(z)
L     = local settlement room
T     = expected settlement room in a uniformly selected reachable target
c     = corridor connectivity probability.
```

Then the expected juvenile recruitment is

```text
W_recruit(z)
= [S(z) C(z)]
  [D(z)cT + {1-D(z)}L].
```

We name the two factors:

```text
F_local(z) = S(z)C(z)
E_settlement(z) = D(z)cT + {1-D(z)}L.
```

Thus

```text
W_recruit(z) = F_local(z) E_settlement(z)
```

**exactly** for the declared one-step context.

---

## Why the settlement factor has this form

The IBM has two mutually exclusive offspring paths.

```text
with probability D(z):
    attempt a corridor move
    succeed with c
    settle with expected room T

with probability 1-D(z):
    remain local
    settle with room L
```

A failed dispersal attempt does not fall back to local settlement in the current
IBM. Hence the two branch expectations add exactly as above.

---

## Theorem applicability

The factorisation creates a legitimate target for N1--N4 **only in the strict
interior**:

```text
F_local(z) > 0
E_settlement(z) > 0.
```

At zero survival, zero conception, or zero settlement, the biology is still
valid, but division-based recovery and proxy-ratio theorems are not defined. The
function `require_theorem_interior()` makes this exclusion explicit.

Within the positive interior, the channel-identifiability results apply to
`W_recruit`, `F_local`, and `E_settlement`:

```text
W_recruit only
    -> cannot distinguish a local reproductive loss from a settlement loss

W_recruit + F_local
    -> recovers E_settlement

W_recruit + a stable proxy for F_local
    -> identifies relative F_local and E_settlement changes
```

---

## What this does *not* claim

```text
W_recruit != long-run invasion lambda
W_recruit != population persistence probability
W_recruit != a full empirical fitness estimate
```

Long-run invasion in the actual colonization IBM additionally contains surviving
parents, repeated generations, resource feedback, local density, patch extinction,
mutation, and changing resident composition. The one-step submodel is a precise
bridge for a specified life-cycle component, not a shortcut around those processes.

The next robustness question is whether conclusions based on this factorisation
remain informative when compared against the full multistep IBM. That is an ABM
test, not a proof of the factorisation itself.
