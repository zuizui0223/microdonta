# Submission workspace

This directory is the canonical publication workspace for the RACH methods
submission. The normative development boundary is
[`docs/mainline.md`](../docs/mainline.md). The primary story is fixed as:

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
| `g2_frozen_benchmark_protocol.json` | preregistered final RACH-SEQ benchmark settings | frozen before final run |
| `run_g2_frozen_benchmark.py` | protocol-locked G2 runner | active validation |
| `supplementary_outline.md` | ABM robustness, sensitivity and extended validation | Supplement |
| `supplement/odd_protocol_draft.md` | ODD documentation for model families | Supplement source |
| `archive/mee_manuscript_pre_theorem_2026-08-24.md` | superseded model-first manuscript | archive only |

The submission does not use the provisional Bergmann/Allen/Foster/Gloger rule
panel, structure discovery, the externally owned eco-genetic programme, the
optional attraction-trait backend, or Streamlit as scientific evidence.

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
| G2 benchmark validity | **Partial** | truth-peek-free sequential reweighting and the outcome-neutral final protocol are frozen; run the protocol, rerun known-truth/NOV calibration, and replace quarantined manuscript numbers |
| G3 projection honesty | **Pass** | exact/extension-required/not-applicable ledger retained |
| G4 worked-example evidence | **Pass for prospective use** | no empirical channel attribution; primary-source table still needed for final prose |
| G5 reproducible submission | **Partial** | bundle checker added; final full figure rebuild and clean-environment run pending |

**G2 numerical quarantine.** Any generality percentages or mean-resolvability
values already written in manuscript §4.3 came from the pre-fix benchmark and are
provisional. They must not be treated as submission evidence or copied into the
abstract/results. The final G2 runner has no favourable performance threshold:
whatever the frozen protocol returns—favourable, null, or adverse—is the result
that must replace those numbers.

No additional ecological example should enter the primary manuscript before G2
and G5 pass.
