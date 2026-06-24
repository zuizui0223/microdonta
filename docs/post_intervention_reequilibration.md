# Post-intervention resident re-equilibration

The defense and colonization backends use a common endpoint protocol for their
standard intervention sweeps:

1. Equilibrate the resident under the before regime.
2. Estimate `Omega_inv` against that resident.
3. Switch the same resident community to the after regime.
4. Re-equilibrate the post-intervention resident, including patch resources and
   evolving trait composition.
5. Estimate post-loss `Omega_inv` only when this new resident is stationary.
6. Classify a supported trait-space transition only when both resident endpoints
   are identifiable and stationary.

This replaces the previous comparison of `Omega_inv(before resident, before
regime)` with `Omega_inv(before resident, after regime)`. The latter is an
instantaneous perturbation contrast, not evidence for a persistent
eco-evolutionary endpoint.

A failed after-resident equilibrium is not repaired by evaluating an empty
population as if it had an invasion set. In particular, the colonization backend
has recurrent local extinction; after complete corridor loss it can lack any
stationary resident because recolonisation is unavailable. Such runs are recorded
as `not_stationary` or `extinct`, rejected from the endpoint invariant, and cannot
be counted as a third independent support system.

Sweep records retain `stationarity_before`, `stationarity_after`, and
`omega_after_resident`, so downstream analysis can distinguish an actual
post-loss re-equilibrated outcome from a rejected endpoint.