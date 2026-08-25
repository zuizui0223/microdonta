# Submission workspace

This directory is the canonical publication workspace for the RACH **Research Article**
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
| `g2_frozen_benchmark_protocol.json` | preregistered G2 v2 selection benchmark | frozen |
| `results/g2_frozen_v2_summary.json` | frozen G2 numerical/provenance record | final evidence |
| `results/submission_validation_summary.json` | frozen known-truth and NOV-calibration record | final evidence |
| `results/g5_reproducibility_summary.json` | clean figure/wheel/CI reproducibility record | final evidence |
| `final_figure_inventory.json` | exact Main/Supp figure rebuild inventory | frozen |
| `release_readiness.json` | v0.1.0 package/release freeze record | active release governance |
| `mee_submission_requirements_2026.md` | current MEE Research Article requirements snapshot | active publication governance |
| `check_mee_submission.py` | article-type/abstract/anonymity/word-count gate | active publication gate |
| `title_page_draft.md` | separate author/title metadata file | Not for Review; human fields pending |
| `campanula_primary_literature_audit.md` | source-bounded audit of the prospective example | completed editorial evidence audit |
| `archive/g2_frozen_benchmark_protocol_v1_pre_execution.json` | exact unexecuted v1 protocol | archive only |
| `archive/g2_protocol_v1_supersession.md` | why v1 was replaced before any final run | audit trail |
| `supplementary_outline.md` | ABM robustness, sensitivity and extended validation | Supplement |
| `supplement/odd_protocol_draft.md` | ODD documentation for model families | Supplement source |
| `archive/mee_manuscript_pre_theorem_2026-08-24.md` | superseded model-first manuscript | archive only |

The submission does not use the provisional Bergmann/Allen/Foster/Gloger rule
panel, structure discovery, the externally owned eco-genetic programme, the
optional attraction-trait backend, or Streamlit as scientific evidence.

## G2 v2 selection test

Protocol `rach-g2-truth-peek-free-v2` superseded the unexecuted v1 protocol before
any final output was inspected. V2 tests selection rather than merely observation
sufficiency by adding two mechanism-uninformative nuisance observations and
comparing matched policies:

```text
RACH-SEQ      maximum current validated NOV; explicit fallback only if NOV is not estimable
random_order  uniform random remaining-candidate selection
```

The policy comparison had no favourable-result acceptance threshold. The frozen
budget-2 result is therefore reported as observed: RACH-SEQ resolved all initial
confounding edges on average and converged in 99.0% of systems, versus 60.45%
edge resolution and 43.5% convergence under random order, with hidden-truth false
exclusion equal to zero in every policy × budget cell. Exact values and provenance
are in `results/g2_frozen_v2_summary.json`.

## Reproducibility gate

```bash
python paper/check_submission_bundle.py
python scripts/check_repository_boundaries.py
pytest -q
```

The final clean G5 run additionally rebuilds Figure 1–3 and Figure S1 from
`final_figure_inventory.json`, reproduces frozen known-truth/NOV values, builds
the `rach` wheel, audits its ZIP members, installs it outside the repository, and
checks the frozen public API.

## Current gates

| Gate | Status | Remaining work |
|---|---|---|
| G1 claim consistency | **Pass** | theorem-first manuscript, theory, API, README and manifest aligned |
| G2 benchmark validity | **Pass** | frozen v2 executed with protocol/code provenance; final numbers fixed in `paper/results/` |
| G3 projection honesty | **Pass** | exact/extension-required/not-applicable ledger retained |
| G4 worked-example evidence | **Pass for prospective use** | qualitative main-text claims audited against the primary Inoue series; exact historical tables must be transcribed only if future numeric values are introduced |
| G5 reproducible submission | **Pass** | clean rebuild, frozen-value reproduction, wheel audit and Python 3.10–3.12 matrix all passed |

### G5 provenance

- validated code commit: `d67eb2d22387334477e94ca8ecd0d58ac070c4a0`
- G5 workflow run: `32803339282`
- G5 artifact: `9547280912`
- artifact digest: `sha256:ab3049b4bcfb3ce5a7fa965aac3cc7e19596dd5ac12758f62c249d96a093a2ea`
- Python 3.10–3.12 CI run: `32803339284` — all three versions passed
- wheel: `rach-0.1.0-py3-none-any.whl`
- wheel SHA-256: `f97308f99caf59a6dd13931e738cee803054c0864b66c4d93db5c944f72f0fa8`
- forbidden wheel members: `0`

The reproducibility artifact contains the four rebuilt figures, their SHA-256
hashes, the wheel, and `g5_reproducibility_summary.json`. A stable copy of that
summary is committed under `results/`.

## Numerical and release freeze

The pre-fix 99.2%/98.5% generality values are not submission evidence and CI
forbids them from re-entering the active manuscript. The accepted G2 values are
only those tied to the frozen protocol SHA and execution commit.

The software release candidate is frozen at `rach` version `0.1.0`; the exact
package/release state is recorded in `release_readiness.json` and `CITATION.cff`.
An archival DOI has **not** been minted in this repository. DOI minting is an
external archival step and should be recorded later without altering frozen
scientific results.

With G2 and G5 passed, the main scientific implementation is frozen. Remaining
work should be limited to the anonymous reviewer bundle, human-supplied title-page
metadata, final document export/line numbering, and external archive/DOI metadata
unless a new version/protocol is explicitly opened.
