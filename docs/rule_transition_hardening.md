# Rule-transition hardening

The rule-transition pipeline separates **assumptions** from **simulated outcomes**.
This prevents circularity when a legacy caller includes labels such as
`trait_space_contraction` in a program motif set.

- `SweepRecord.motifs` is treated as a set of structural assumptions only.
- Any trait-space outcome label in that legacy field is discarded by the hardened
  adapter.
- An outcome is inferred only from the matching record's
  `metadata["trait_space_primary"]`, which is emitted by the simulator.
- `ProgramRun.outcome_motifs` retains that derived evidence separately from
  `ProgramRun.motifs`.
- The invariant report exposes separate common assumptions and common outcomes.

Consequently a contraction label supplied by a caller cannot be recovered as an
invariant unless the matching simulations actually returned `contraction`. When
independent backends return contraction and shift, respectively, their common
outcome is `trait_space_reconfiguration`, while neither specific geometry is
reported as cross-system.

This is a provenance safeguard. It does not turn any conditional result into a
universal ecological law: results remain conditional on the model family, parameter
regions, intervention design, and the stationarity and acceptance criteria.
