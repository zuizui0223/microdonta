# Projection ledger: where the channel-identifiability theorems do and do not apply

## Purpose

Theorems N1--N4 are exact mathematical statements about a positive,
trait-specific factorisation

```text
W(z) = F(z) E(z).
```

They do not automatically transfer to every simulator that has reproduction,
survival, dispersal, and a trait. Nor do they automatically transfer to every
empirical record that contains a flower trait and a pollinator name.

This ledger is the repository's explicit rule for projection:

> **A theorem may be used outside its abstract model only after the target's
> output, factorisation, and observation map have been stated and checked.**

The executable registry is `causal_model.theorem_projection_ledger`.

---

## Status definitions

| status | meaning |
|---|---|
| `exact` | the target provides the theorem's factorisation and required observation map |
| `requires_factorization_extension` | the target contains relevant biological processes but does not currently output the declared trait-level factorisation or channel observations |
| `not_applicable` | the target record has no observation class to which N1--N4 can be applied yet |

`requires_factorization_extension` does not mean that a model is wrong. It means
that the theorem has not been earned for that particular output.

---

## Current ledger

### 1. Abstract positive two-factor model — `exact`

```text
W(z)=F(z)E(z), F(z)>0, E(z)>0.
```

N1--N4 apply exactly.

```text
W only
    -> non-identifying
W + F or W + E
    -> channel changes recoverable
W + stable proxy q(z)F
    -> relative channel changes recoverable
W + proxy q_i(z)F with unconstrained q_i
    -> non-identifying again
```

### 2. Colonization one-step expected juvenile recruitment — `exact`

The colonization IBM now exposes an exact, narrow life-cycle submodel in
`causal_model.colonization_recruitment_factorization`.

For one initial adult in a declared local context,

```text
W_recruit(z)
= [survival_probability(z) * conception_probability(z)]
  [dispersal_probability(z) * connectivity * expected_target_room
   + {1-dispersal_probability(z)} * local_room].
```

Thus

```text
F_local(z) = survival_probability(z) * conception_probability(z)
E_settlement(z) = dispersal_probability(z) * connectivity * expected_target_room
                  + {1-dispersal_probability(z)} * local_room
W_recruit(z) = F_local(z) E_settlement(z).
```

This matches the one-step branch structure of the IBM exactly, including the fact
that a failed dispersal attempt has no local fallback. N1--N4 apply only when
`F_local>0` and `E_settlement>0`.

This does **not** identify or factorise the IBM's multi-step invasion `lambda`.
The one-step recruitment component is a legitimate theorem target; it is not a
replacement for the full demographic outcome.

### 3. Spatial pollination ABM — `requires_factorization_extension`

The current spatial backend estimates a stochastic multi-step rare-invader log
growth rate

```text
lambda(z' | Z*)
```

and uses it to form `Omega_inv`. Its deterministic helper has a one-step product

```text
G(z) = survival(z) [1 + repro(z)].
```

That product is real, but it is **not** the theorem's local-reproduction versus
establishment/reachability factorisation:

- `repro` contains interaction-gated service, mate matching, resources,
  compensation, and trait cost;
- `survival` is survival, not a declared establishment/reachability factor;
- the multistep `lambda` additionally contains density dependence, movement,
  stochasticity, and changing resident state.

Thus an `Omega_inv` contraction under pollination loss cannot currently be called
a theorem-N1/N2 result about pollination factor `F` versus establishment factor
`E`.

To make the bridge testable, the backend must emit for each trait and regime:

```text
W(z)  trait-specific total performance on a declared scale
F(z)  local reproductive/pollination factor
E(z)  establishment/reachability factor
r(z)  factorisation residual, e.g. W(z) / [F(z)E(z)]
```

Only then can the code test whether the factorisation is exact, approximate, or
rejected for that ABM.

### 4. Colonization connectivity ABM: multistep lambda — `requires_factorization_extension`

The reported colonization outcome remains a stochastic multi-step lineage log
growth rate. The exact one-step `W_recruit` submodel now exists, but moving from
it to `lambda` requires an explicit treatment of surviving parents, repeated
generations, density, patch extinction, resources, and changing residents.

Therefore the full corridor-loss ABM can now ask a sharper robustness question:

> Do conclusions derived for exact one-step recruitment remain informative for
> multistep invasion and endpoint trait space?

It cannot yet answer that by invoking N1--N4 directly.

### 5. Defense backend — `requires_factorization_extension`

The defense model is useful as an independent survival-mediated mechanism model.
It does not currently export a local `F` and an establishment `E` on the theorem's
trait-performance scale. A shift or contraction there cannot validate the
channel-identifiability theorem without a new declared factorisation.

### 6. Published Campanula microdonta record — `not_applicable`

The source-confirmed record currently contains:

```text
selfing rate increases with isolation
flower size decreases with isolation
Bombus to halictid pollinator transition
```

It does not contain a trait-specific total performance `W`, a declared factor
mapping, or a before/after channel proxy with stable or measured calibration.

The current published record can therefore support a RACH statement of
unresolved competing explanations. It cannot support a theorem-N1/N2/N3/N4 claim
that one vital-rate channel has been identified.

---

## What this changes in the research sequence

```text
1. Prove the identifiability boundary in the abstract model.
2. State whether a simulator or empirical system satisfies the factorisation.
3. Extract an exact life-cycle submodel where possible.
4. Test whether its conclusion survives in the full ABM rather than assuming it.
5. Map field measurements to W and one channel/proxy.
6. Check calibration stability, not merely correlation.
7. Only then project the channel conclusion to ecology.
```

This keeps ABMs in their proper role: they test robustness of a theorem under
additional assumptions; they do not retroactively prove a theorem whose
factorisation they never represented.