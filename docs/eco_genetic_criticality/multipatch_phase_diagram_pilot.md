# Finite occupancy phase-diagram pilot

This is a model-specific stochastic pilot, not a theorem and not an empirical
ecosystem projection.

## Design

- profile: finite-bin standard profile, reduced to 54 scenario x parameter cells
- generations: 20
- replicates per cell: 8
- landscapes: one_large, equal_isolated, equal_migrating
- closure: finite_trait_bin_recruitment + two_kernel_recruitment + coupled q feedback

The run is reproducible with:

```bash
python examples/eco_genetic_criticality/multipatch_phase_diagram_pilot.py
```

## Main Mathematical Takeaways

1. One large patch retained realised high-trait occupancy in every pilot cell.
2. Fragmented landscapes produced model-specific transition regions where realised high-trait persistence fell sharply.
3. Genetic first-passage warnings often preceded realised high-trait loss among valid event pairs.
4. H_alpha, H_gamma, and F_ST did not collapse to one diversity signal.
5. These results are parameter-specific simulation outcomes; they do not establish universal early warning.

## Selected Landscape Contrasts

| scenario | A_ref | interaction feedback | theta | Pr(realised persists) | H_alpha mean | H_gamma mean | F_ST mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| one_large | 0.8 | 3.0 | 0.55 | 1.000 | 0.178 | 0.178 | 0.000 |
| equal_isolated | 0.8 | 3.0 | 0.55 | 0.750 | 0.057 | 0.076 | 0.157 |
| equal_migrating | 0.8 | 3.0 | 0.55 | 0.625 | 0.087 | 0.099 | 0.118 |
| one_large | 0.8 | 4.5 | 0.75 | 1.000 | 0.102 | 0.102 | 0.000 |
| equal_isolated | 0.8 | 4.5 | 0.75 | 0.250 | 0.029 | 0.046 | 0.331 |
| equal_migrating | 0.8 | 4.5 | 0.75 | 0.125 | 0.018 | 0.023 | 0.232 |
| one_large | 1.0 | 4.5 | 0.55 | 1.000 | 0.163 | 0.163 | 0.000 |
| equal_isolated | 1.0 | 4.5 | 0.55 | 0.250 | 0.043 | 0.050 | 0.152 |
| equal_migrating | 1.0 | 4.5 | 0.55 | 0.000 | 0.011 | 0.014 | 0.188 |
| one_large | 1.2 | 4.5 | 0.75 | 1.000 | 0.135 | 0.135 | 0.000 |
| equal_isolated | 1.2 | 4.5 | 0.75 | 0.000 | 0.000 | 0.000 | NA |
| equal_migrating | 1.2 | 4.5 | 0.75 | 0.250 | 0.039 | 0.042 | 0.087 |

## Severe Fragmented Cell

For `equal_isolated`, `A_ref=1.2`, `interaction_feedback=4.5`, `theta=0.75`:

- final realised high-trait persistence probability: 0.000
- final potential high-trait viability probability: 0.000
- median tau_trait_realised: 14.000
- median tau_H_alpha: 8.000
- median tau_H_gamma: 8.000
- median tau_FST: 8.000
- Pr(tau_H_alpha < tau_trait_realised): 1.000
- Pr(tau_H_gamma < tau_trait_realised): 1.000
- Pr(tau_FST < tau_trait_realised): 0.857
- Pr(tau_allele_loss < tau_trait_realised): 0.500

This cell is a useful mathematical witness that genetic warnings can precede
realised trait loss under the declared closure. It is not evidence that this
ordering is universal.

## Lead Signal Coverage

35 of 54 pilot rows had at least one nonzero genetic/allele lead probability.
Rows with no valid event pairs retain censoring rather than being counted as
no-lead evidence.

## Interpretation Discipline

The pilot preserves the central non-equivalence:

```text
Omega_tau^potential != realised N_H > 0 != p > 0 != H_alpha > 0
```

The next empirical step is to decide which observations would identify these
quantities, not to map them onto Campanula immediately.
