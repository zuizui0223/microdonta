# Submission workspace

This directory is the canonical publication workspace for the RACH methods
submission. The primary story is fixed as:

```text
N1–N4 identifiability boundary
→ RACH admissible explanation set
→ NOV / RACH-SEQ observation design
→ controlled synthetic benchmarks
→ exact one-step ecological projection
→ prospective Campanula measurement design
```

## File roles

| Path | Role | Submission status |
|---|---|---|
| `mee_manuscript_draft.md` | theorem-first primary manuscript | active main text |
| `submission_manifest.json` | machine-readable claim/evidence inventory | active governance |
| `check_submission_bundle.py` | verifies the publication boundary in CI | active gate |
| `supplementary_outline.md` | ABM robustness, sensitivity and extended validation | Supplement |
| `supplement/odd_protocol_draft.md` | ODD documentation for model families | Supplement source |
| `archive/mee_manuscript_pre_theorem_2026-08-24.md` | superseded model-first manuscript | archive only |

The submission does not use the provisional Bergmann/Allen/Foster/Gloger rule
panel, structure discovery, the separate eco-genetic program, the optional
attraction-trait backend, or Streamlit as scientific evidence.

## Reproducibility gate

```bash
python paper/check_submission_bundle.py
python scripts/check_repository_boundaries.py
pytest -q
```

The first command checks scope and manuscript structure. The second checks the
implementation.

## Current gates

| Gate | Status | Remaining work |
|---|---|---|
| G1 claim consistency | **Pass** | theorem-first manuscript, README and manifest aligned |
| G2 benchmark validity | **Partial** | freeze generators and produce final error-control/budget table |
| G3 projection honesty | **Pass** | exact/extension-required/not-applicable ledger retained |
| G4 worked-example evidence | **Pass for prospective use** | no empirical channel attribution; primary-source table still needed for final prose |
| G5 reproducible submission | **Partial** | bundle checker added; final full figure rebuild and clean-environment run pending |

No additional ecological example should enter the primary manuscript before G2
and G5 pass.
