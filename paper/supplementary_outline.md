# Supplementary Information outline

The Supplement supports the primary theorem → RACH → benchmark → projection
chain. It does not carry an independent empirical-identification claim.

## S1. Algebraic foundations

- Full proofs and edge cases for N1–N4.
- Positivity, zero-boundary and additional-channel limitations.
- Finite-grid regression checks.

Sources:

- `docs/channel_identifiability_theorem.md`
- `docs/proxy_calibration_theorem.md`
- matching theory modules and tests.

## S2. RACH definitions and guarantees

- Admissible region and constraint grammar.
- Degeneracy, resolvability and replaceability.
- NOV/EVSI derivation.
- RACH-SEQ stopping rule and observation budget.

Sources:

- `docs/rach_theory.md`
- `docs/rach_mathematical_foundations.md`
- `causal_model/causal_admissibility.py`
- `causal_model/causal_replaceability.py`
- `causal_model/rach_seq.py`.

## S3. Controlled validation

Report predeclared generators and the full table for:

- known-truth recovery;
- false exclusion;
- false invariant detection;
- calibration;
- observation efficiency and budget curves;
- prior, tolerance and distance sensitivity;
- stochastic Monte Carlo uncertainty.

The final table must be regenerated from a frozen seed/configuration registry.
Point estimates already in the working draft are not the submission freeze.

## S4. ABM robustness and counterexamples

Spatial, colonisation and defence backends test whether restricted conclusions
persist after extra processes are added. Every result must be labelled:

- `exact`;
- `requires_factorization_extension`; or
- `not_applicable`.

The exact one-step colonisation factorisation is Main text; multistep endpoint
sweeps are Supplement only. The ODD source is
`paper/supplement/odd_protocol_draft.md`.

## S5. Reproducibility

- environment and dependency versions;
- one-command figure rebuild;
- test matrix for Python 3.10–3.12;
- figure-to-command and claim-to-test mapping;
- frozen random seeds and output checksums.

## Explicit exclusions

The following are not Supplement claims for this submission:

- provisional Bergmann, Allen, Foster and Gloger encodings;
- structure discovery;
- eco-genetic H1–H3 work;
- the attraction-trait incubator;
- Streamlit or tutorials as evidence.

They remain in repository history or separate program areas and may be promoted
only through a later, explicit publication decision.
