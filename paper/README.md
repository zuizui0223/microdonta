# Publication workspace

The integrated theorem-first draft has been split into two papers. The normative separation is `paper/TWO_PAPER_STRATEGY.md`.

## Active MEE Research Article

The primary submission to *Methods in Ecology and Evolution* is now the observation-selection method paper:

```text
RACH admissible mechanism set
→ causal degeneracy / resolvability / replaceability
→ validated NOV = I(S;Q | A_epsilon)/K
→ sequential recomputation in RACH-SEQ
→ truth-peek-free G2 matched-policy benchmark
→ reproducible software and reviewer bundle
```

No new empirical data are required for this claim. The validation object is the controlled synthetic selection benchmark, where the hidden mechanism and candidate information structure are known and hidden outcomes are revealed only after selection.

### Headline G2 results

At budget two, RACH-SEQ resolved all initial confounding edges on average and converged in 99.0% of systems, versus 60.45% edge resolution and 43.5% convergence under random order. Hidden-truth false exclusion was zero in every policy-by-budget cell.

At budget four, both policies resolved all initial edges on average, but random order selected 1.169 mechanism-independent nuisance measurements per system versus 0.014 for RACH-SEQ. This is an `83.5-fold` difference, or approximately a `98.8%` reduction, while RACH-SEQ used 1.518 observations versus 2.673. The manuscript always reports the absolute values beside the fold ratio.

Use `mechanism-independent nuisance measurement` or `distractor measurement`, not `noise observation`, because measurement noise is a separate concept.

## Separate boundary paper

The companion boundary manuscript contains:

```text
N1 net-only non-identifiability
→ N2 exact-channel sufficiency
→ N3 stable-proxy identification
→ bounded calibration-drift identified interval
→ directional breakdown point
→ N4 unbounded-drift non-identifiability
→ measurement-design rules
```

Its key partial-identification result is

```text
rho_complement in [rho_hat(1-delta), rho_hat(1+delta)]
```

when `q_1/q_0 in [1-delta,1+delta]`, with multiplicative width `(1+delta)/(1-delta)`. The paper reports identified intervals and breakdown points rather than folding proxy uncertainty into the RACH methods claim.

## File roles

| Path | Role | Status |
|---|---|---|
| `mee_manuscript_draft.md` | RACH/NOV/RACH-SEQ/G2 methods manuscript | active MEE main text |
| `supporting_information.md` | methods validation and reproducibility | active MEE SI |
| `boundary_manuscript_draft.md` | N1–N4 plus bounded-drift boundary paper | separate non-blocking draft |
| `TWO_PAPER_STRATEGY.md` | normative separation and no-double-counting rules | active governance |
| `submission_manifest.json` | machine-readable MEE evidence boundary | active governance |
| `check_submission_bundle.py` | checks MEE scientific boundary | active CI gate |
| `check_mee_submission.py` | checks article format/anonymity | active CI gate |
| `g2_frozen_benchmark_protocol.json` | frozen selection benchmark | frozen |
| `results/g2_frozen_v2_summary.json` | frozen G2 numerical/provenance record | final evidence |
| `results/submission_validation_summary.json` | frozen known-truth and NOV checks | final evidence |
| `results/g5_reproducibility_summary.json` | clean figure/wheel/CI record | final evidence |
| `archive/*integrated_pre_split*` | preserved pre-split manuscript/SI | archive only |

## Reproducibility

```bash
python paper/check_submission_bundle.py
python paper/check_mee_submission.py
python scripts/check_repository_boundaries.py
pytest -q
```

The frozen scientific outputs and public RACH API remain unchanged. The split changes publication claims and adds bounded-drift theory; it does not retune G2 or G5.

## Release boundary

The release candidate remains `rach` version 0.1.0 until a genuine public API or versioned scientific change is accepted. The boundary-theory module is not added to the package-level `__all__`; the advertised public surface remains RACH-first.
