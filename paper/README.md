# Submission workspace

This directory is the canonical publication workspace for the RACH methods
submission. The normative development boundary is
[`docs/mainline.md`](../docs/mainline.md). The primary story is fixed as:

```text
N1–N4 identifiability boundary
→ RACH admissible explanation set
→ validated NOV = I(S;Q | A_epsilon)/K
→ RACH-SEQ observation selection
→ controlled selection/error validation
→ exact one-step ecological projection
→ prospective Campanula measurement design
```

## File roles

| Path | Role | Submission status |
|---|---|---|
| `mee_manuscript_draft.md` | theorem-first primary manuscript | active main text |
| `submission_manifest.json` | machine-readable claim/evidence inventory | active governance |
| `check_submission_bundle.py` | verifies the publication boundary in CI | active gate |
| `g2_frozen_benchmark_protocol.json` | preregistered G2 v2 selection benchmark | frozen before final run |
| `run_g2_frozen_benchmark.py` | protocol-locked matched-policy G2 runner | active validation |
| `archive/g2_frozen_benchmark_protocol_v1_pre_execution.json` | exact unexecuted v1 protocol | archive only |
| `archive/g2_protocol_v1_supersession.md` | why v1 was replaced before any final run | audit trail |
| `supplementary_outline.md` | ABM robustness, sensitivity and extended validation | Supplement |
| `supplement/odd_protocol_draft.md` | ODD documentation for model families | Supplement source |
| `archive/mee_manuscript_pre_theorem_2026-08-24.md` | superseded model-first manuscript | archive only |

The submission does not use the provisional Bergmann/Allen/Foster/Gloger rule
panel, structure discovery, the externally owned eco-genetic programme, the
optional attraction-trait backend, or Streamlit as scientific evidence.

## G2 v2: what is actually being tested

Protocol `rach-g2-truth-peek-free-v2` supersedes the unexecuted v1 protocol.
Static pre-execution review found that v1 contained only directly resolving
candidate observations. That design could show that a sufficient observation
*vocabulary* solves a confound, but did not challenge the **selection algorithm**.
No final v1 output was inspected.

V2 therefore evaluates the same generated systems under two predeclared policies:

```text
RACH-SEQ      expected confounding-edge-cut selection
random_order  uniform random remaining-candidate selection
```

Each system also contains two binary nuisance measurements generated
independently of the mechanism vector. They are valid predictive observations but
are mechanism-uninformative by construction. Both policies receive the same
systems, hidden truths, candidate sets and observation budgets; hidden truth is
materialised only *after* a candidate has been selected.

The policy comparison is descriptive, not a success gate. The protocol does not
require RACH-SEQ to beat random selection. Favourable, null or adverse differences
are all valid frozen results.

## Reproducibility gate

```bash
python paper/check_submission_bundle.py
python scripts/check_repository_boundaries.py
pytest -q
```

The first command checks scope, theory/API alignment, the v2 selection design and
manuscript structure. The second checks repository ownership boundaries.

## Current gates

| Gate | Status | Remaining work |
|---|---|---|
| G1 claim consistency | **Pass** | theorem-first manuscript, theory, API, README and manifest aligned |
| G2 benchmark validity | **Partial** | truth-peek-free inference, current-A predictive reweighting, information-theoretic NOV and v2 matched-policy protocol are implemented/frozen; pass CI, run frozen v2, rerun known-truth/NOV calibration, then insert only protocol-tagged numbers |
| G3 projection honesty | **Pass** | exact/extension-required/not-applicable ledger retained |
| G4 worked-example evidence | **Pass for prospective use** | no empirical channel attribution; primary-source table still needed for final prose |
| G5 reproducible submission | **Partial** | final full figure rebuild, clean-environment validation and wheel inspection pending |

**G2 numerical quarantine.** The pre-fix 99.2%/98.5% generality values are not
submission evidence and CI forbids them from re-entering the active manuscript.
The frozen v2 runner has no favourable performance threshold. Whatever the
protocol-tagged result returns is the result to report.

No additional ecological example should enter the primary manuscript before G2
and G5 pass.
