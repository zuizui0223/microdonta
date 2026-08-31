# Publication workspace

The integrated theorem-first draft has been split into two papers. The normative separation is `paper/TWO_PAPER_STRATEGY.md`.

## Active MEE Research Article

The primary submission to *Methods in Ecology and Evolution* is the observation-selection method paper:

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

At budget four, random order selected 1.169 mechanism-independent nuisance measurements per system versus 0.014 for RACH-SEQ while using 2.673 observations versus 1.518. The manuscript reports absolute values beside any fold comparison.

## Separate boundary paper

The companion manuscript is explicitly headed by the proxy-transport identification problem rather than by the elementary N1 product symmetry. The canonical theory spine is now:

```text
N1 rich net-only invariance / quotient structure
→ graded Design Rule 1: anchor ladder
→ one calibration-transport family
     Gamma = 1       : N3 stable-proxy point identification
     1 < Gamma < inf : sharp joint partial identification + breakdown
     Gamma -> inf    : N4 unrestricted-drift non-identification
→ Design Rule 2: preserve the coupling
```

The canonical symmetric transport restriction is

```text
1/Gamma <= kappa=q_1/q_0 <= Gamma,   Gamma >= 1
```

or equivalently `|log kappa| <= eta` with `eta=log Gamma`. For a stable-calibration complementary-channel value `rho_hat`,

```text
rho_complement in [rho_hat/Gamma, rho_hat*Gamma].
```

The two channel marginals are not independent. The same `kappa` generates the sharp joint set and preserves

```text
rho_F rho_E = rho_W
```

exactly. In log-ratio coordinates the joint set is a line segment of slope `-1`; marginal intervals are projections only and must not be combined as independent error bars.

The primary directional robustness measure is now the reference-invariant multiplicative breakdown factor

```text
Gamma_star = max(rho_hat, 1/rho_hat)
eta_star = |log rho_hat|.
```

For the worked decline `rho_hat=1/1.34`, `Gamma_star=1.34`. The existing statement that the decline survives less than 34% upward calibration-ratio drift is retained as a reader-facing directional translation of the same boundary, not as the canonical cross-study robustness scale.

### Anchor ladder

Design Rule 1 is graded by direct calibration effort:

```text
0 direct anchors
→ cross-regime kappa unrestricted unless assumed
→ N4 non-identification

1 direct anchor
→ local q known but transport remains uncertain
→ external finite Gamma/eta gives sharp partial identification + breakdown

2 direct anchors
→ q_0 and q_1 observed, hence kappa=q_1/q_0 measured
→ point identification without an external drift bound
```

A finite `Gamma`, `eta`, or legacy `delta` is not estimated from the same net/proxy observations whose identifying power is being assessed. Bounded-drift analysis exposes sensitivity to an external transport tolerance; the breakdown factor reports how large that tolerance must be to overturn the conclusion. Two direct anchors remove the need for that sensitivity assumption by measuring transport itself.

N1 is also closed structurally. Positive functions `c(z)` act on latent decompositions by `(F,E) -> (cF,E/c)`. The net response `W=FE` is invariant under this group action, so every net-only statistic `Phi(W)` factors through the corresponding quotient. The manuscript retains the concrete performance-curve and feasible-set examples for ecological interpretation.

The boundary paper also contains a separate primary-literature audit showing that rate-by-effectiveness and quantity-by-quality products are established ecological measurement architectures rather than assumptions introduced only for this theorem. Schupp, Jordano & Gómez (2010) is the lead cross-domain example; the independent pollination lineage is provided by Rader, Ballantyne, and Reynolds & Fenster. The audit is `multiplicative_measurement_literature_audit.md`; the Campanula audit remains separate and serves a different historical/taxonomic purpose.

### Boundary-paper submission assets

```text
boundary_manuscript_draft.md
→ calibration_transport_family.md
→ multiplicative_measurement_literature_audit.md
→ make_boundary_identification_figure.py
→ boundary_reviewer_objection_audit.md
→ causal_model/calibration_transport_family.py
→ tests/test_calibration_transport_family.py
→ tests/test_bounded_proxy_drift.py
→ tests/test_boundary_identification_figure.py
```

`calibration_transport_family.md` is the normative bridge for the symmetric `Gamma/eta` theory, anchor ladder, reference-invariant breakdown factor and N1 group-action statement. The legacy additive-around-one `delta` API remains for reproducibility and the 34% directional example. `make_boundary_identification_figure.py` visualises the joint set in ratio space and in log-ratio space. `boundary_reviewer_objection_audit.md` is an adversarial stop-list protecting the external origin of sensitivity bounds, strict breakpoint wording, N4 interpretation, joint-set reporting and the deliberately narrow novelty claim.

## File roles

| Path | Role | Status |
|---|---|---|
| `mee_manuscript_draft.md` | RACH/NOV/RACH-SEQ/G2 methods manuscript | active MEE main text |
| `supporting_information.md` | methods validation and reproducibility | active MEE SI |
| `boundary_manuscript_draft.md` | N1–N4, sharp joint bounded-drift set, breakdown and two design rules | separate boundary-paper draft |
| `calibration_transport_family.md` | canonical Gamma/eta family, anchor ladder and quotient interpretation | boundary-paper theory bridge |
| `make_boundary_identification_figure.py` | deterministic boundary identification geometry figure | boundary-paper figure source |
| `boundary_reviewer_objection_audit.md` | adversarial reviewer-response and submission stop audit | boundary-paper governance |
| `multiplicative_measurement_literature_audit.md` | primary-source audit of recurring multiplicative ecological measurements | boundary-paper evidence audit |
| `campanula_primary_literature_audit.md` | historical/taxonomic audit for Campanula material | separate evidence audit |
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
python paper/make_boundary_identification_figure.py
pytest -q
```

The frozen MEE scientific outputs and public RACH API remain unchanged. Boundary-paper development must not retune G2 or G5.

## Release boundary

The release candidate remains `rach` version 0.1.0 until a genuine public API or versioned scientific change is accepted. Boundary-theory functions remain explicit submodule utilities; the advertised package-level surface remains RACH-first.
