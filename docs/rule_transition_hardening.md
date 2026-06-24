# Rule-transition hardening

The rule-transition pipeline separates **assumptions** from **simulated outcomes**.
This prevents circularity when a legacy caller includes labels such as
`trait_space_contraction` in a program motif set.

- `SweepRecord.motifs` is treated as a set of structural assumptions only.
- The public program-motif factories remove every trait-space outcome label,
  including the broad `trait_space_reconfiguration` label.
- An outcome is inferred only from matching simulator metadata:
  `metadata["trait_space_primary"]` or the simulator POM trait-space state.
- `ProgramRun.outcome_motifs` retains that derived evidence separately from
  `ProgramRun.motifs`.
- The invariant report exposes separate common assumptions and common outcomes.

## Isolated intervention channels

The spatial intervention factory now changes one biological mechanism at a time:

- mutualism loss changes `interaction_scale` only;
- predator loss changes `predation_scale` only; and
- dispersal loss changes `dispersal_scale` only.

Alternative compensation uses `repro_baseline`, a separate parameter. It can be
set to zero for a pure channel intervention or varied independently in a
counterexample or sensitivity sweep. A protocol regression test checks the exact
set of changed channels for every intervention.

## Endpoint sensitivity and uncertainty

`causal_model.rule_transition_diagnostics` provides an endpoint-sensitivity runner
for the spatial backend. Each cell records the invasion-grid density, invasion
duration, replicate count, invasion threshold, and stationarity window; it then
re-equilibrates the post-intervention resident before estimating `Omega_inv`.

Every sweep can be summarized as a Wilson interval overall and separately by
predeclared region and stochastic seed. The benchmark-report builder writes the
required sections: assumptions, observed outcomes and provenance, conditional
necessity, counterexamples, uncertainty, and unresolved limitations.

A contraction label supplied by a caller cannot be recovered as an invariant unless
the matching simulations actually returned `contraction`. When independent
backends return contraction and shift, respectively, their common outcome is
`trait_space_reconfiguration`, while neither specific geometry is reported as
cross-system.

These are provenance and design safeguards, not universal ecological laws. Results
remain conditional on the model family, parameter regions, intervention design,
stationarity criterion, and acceptance rule.
