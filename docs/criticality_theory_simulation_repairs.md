# Criticality theorem and simulation repair addendum

This addendum supersedes any stronger reading of C3 and specifies the theorem-to-simulation bridge.

## R1. Corrected C3 fragmentation conclusion

For the canonical logistic interaction system, let equal isolated patches have

```text
A_patch = A_total / m.
```

If

```text
A_total > 4/kappa
A_patch <= 4/kappa,
```

then one large patch is capable of the canonical bistable interaction mechanism,
while every equal subpatch has only a unique equilibrium `q_*(A_patch,theta)`.

This alone does not imply high-trait absence. The stronger conclusion requires

```text
m_H(q_*(A_patch,theta)) < 0,
m_H(q)=max_(z in Z_H)[W(z;q)-tau].
```

Only under this additional margin condition is the high-investment potential mode
absent in every subpatch. Thus C3 is a theorem about loss of the canonical
high-interaction route; trait-mode loss is conditional on the subcritical margin.

## R2. Potential viability is not realised occupancy

`Omega_tau(q)` is a potential viable trait set. The current simulator records
potential high-trait component presence and component count. It does not track a
resident trait distribution `mu_t(z)` or trait-bin abundances. Therefore current
simulation claims must use:

```text
potential high-trait viability loss
```

not:

```text
realised high-trait population extinction.
```

A later trait-distribution state is required for the latter.

## R3. Expected theorem paths versus realised stochastic paths

L1/L2 concern an expected diversity path `h_t`. A finite Wright--Fisher
simulation returns realised `H_alpha,t^(r)` for replicate `r`. The correct bridge
reports:

```text
mean_r H_alpha,t^(r)
Pr_r[tau_H^(r)<tau_trait^(r)]
median_r[tau_H^(r)-tau_trait^(r)]
full first-passage-time distribution.
```

A single stochastic run cannot validate or refute L1/L2.

## R4. Canonical reduction requirement

The multi-patch simulator is an extended feedback model, not the C1 map. It must
be tested in the reduction

```text
density D=1
interaction_memory_weight=1
high-allele contribution to q=0
```

where its interaction update is exactly

```text
q_(t+1)=sigma[kappa((A/A_ref)q_t-theta)].
```

Only in that reduction may the exact canonical threshold be used as a simulator
regression target.

## R5. Reproductive timing convention

The simulator samples `p_(t+1)` using an effective size derived from the newly
formed cohort `N_(t+1),q_(t+1)`. This is a valid life cycle only under:

```text
selection -> recruitment/demographic update -> breeder cohort -> gamete sampling.
```

Documentation and output labels must call this quantity
`N_e,next_breeder`, rather than `N_e,t`, to avoid an indexing claim that the
implementation does not make.

## R6. Diversity weighting convention

Current `H_alpha` and `H_gamma` are census-weighted. Drift uses reproductive
effective size. Future reports must either retain the label `census-weighted` or
also report `N_e`-weighted diversity. The two are not interchangeable under
reproductive skew.