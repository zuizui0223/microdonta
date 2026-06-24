# Post-intervention resident re-equilibration

The defense and colonization backends now use the same endpoint protocol for their
standard intervention sweeps:

1. Equilibrate the resident under the before regime.
2. Estimate `Omega_inv` against that resident.
3. Switch the same resident community to the after regime.
4. Re-equilibrate the post-intervention resident, including patch resources and
   evolving trait composition.
5. Estimate post-loss `Omega_inv` against this new resident.
6. Classify the trait-space change and accept a pattern only when both resident
   endpoints are stationary.

This replaces the previous comparison of `Omega_inv(before resident, before
regime)` with `Omega_inv(before resident, after regime)`. The latter is useful as
an instantaneous perturbation contrast but not as evidence for a persistent
eco-evolutionary endpoint.

Sweep records retain `stationarity_before`, `stationarity_after`, and
`omega_after_resident`. A downstream analysis can therefore distinguish a genuine
post-loss re-equilibrated outcome from an extinct or not-converged after state.
