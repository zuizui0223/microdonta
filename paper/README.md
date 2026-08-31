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

A signed functional starting position such as `plant_trait - pollinator_functional_center` is an **evidence-role example** for this paper only: freeze it before outcome inspection, use it as `input_context`, and do not recycle the same hypothesis-derived quantity as an independent observed target. It is not natural-system validation of RACH.

## Separate boundary paper

The companion manuscript is now broader than the original two-factor proxy statement but remains one closed identification programme:

```text
net-only quotient / k-channel equivalence dimension
→ channel anchors: residual dimension k-1-r
→ two-channel proxy calibration-transport family
     Gamma = 1       : N3 stable-proxy point identification
     1 < Gamma < inf : sharp joint partial identification + breakdown
     Gamma -> inf    : N4 unrestricted-drift non-identification
→ calibration-anchor ladder
→ joint-set reporting rule
```

For a positive chain

```text
W = prod_{j=1}^k F_j,
```

net-only observation leaves a `(k-1)`-dimensional product-preserving equivalence class in log coordinates. If `r` independent channel values or channel ratios are directly anchored, the residual unidentified dimension is

```text
k - 1 - r.
```

At `r=k-1`, the final channel is recovered from the product.

For the common two-channel proxy case, the canonical symmetric transport restriction is

```text
1/Gamma <= kappa=q_1/q_0 <= Gamma,   Gamma >= 1
```

or equivalently `|log kappa| <= eta` with `eta=log Gamma`. For a stable-calibration complementary-channel value `rho_hat`,

```text
rho_complement in [rho_hat/Gamma, rho_hat*Gamma].
```

The same `kappa` generates both channel ratios and preserves `rho_F rho_E=rho_W` exactly. In log-ratio coordinates the joint set is a line segment of slope `-1`; marginal intervals are projections only and must not be combined as independent error bars.

The primary directional robustness measure is the reference-invariant multiplicative breakdown factor

```text
Gamma_star = max(rho_hat, 1/rho_hat)
eta_star = |log rho_hat|.
```

For the worked decline `rho_hat=1/1.34`, `Gamma_star=1.34`. The statement that the decline survives less than 34% upward calibration-ratio drift is retained as a reader-facing directional translation, not as the canonical cross-study robustness scale.

### Two anchor concepts

**Channel anchors** resolve stages of a declared `k`-channel product:

```text
r independent channel anchors -> residual dimension k-1-r
k-1 channel anchors            -> point identification
```

**Calibration anchors** resolve proxy transport across two regimes:

```text
0 calibration anchors -> unrestricted transport: non-identification
1 calibration anchor  -> local q + external Gamma/eta: sharp set + breakdown
2 calibration anchors -> observe q0,q1 and kappa directly: point identification
```

A finite `Gamma`, `eta`, or legacy `delta` is not estimated from the same net/proxy observations whose identifying power is being assessed. Partial identification exposes sensitivity to an external transport tolerance; direct calibration can replace that assumption with measurement.

### Ecological motivation recovered from izu-core

The effective-service question is now part of the boundary-paper motivation rather than a deferred translation track. At visitor type `m`,

```text
service_m = visitor_rate_m * direct_effectiveness_m
```

and community service is `sum_m service_m`. Network degree, abundance or visitation alone can describe or proxy the quantity side but are not effective service without an effectiveness term. Aggregation across visitor types adds an allocation ambiguity beyond the within-type product.

The complete change -> service -> dependency/assurance -> response question motivates the `k`-channel design theorem. If a declared endpoint map is a positive `k`-stage product, endpoint-only observation leaves `k-1` free dimensions and each independent channel anchor removes one. If the biological map is not multiplicative, the same missing-link design question remains but requires the appropriate observation map.

The boundary paper also contains a primary-literature audit showing that rate-by-effectiveness and quantity-by-quality products are established ecological measurement architectures rather than assumptions introduced only for this theorem. Schupp, Jordano & Gómez (2010) is the lead cross-domain example; the independent pollination lineage is provided by Rader, Ballantyne, and Reynolds & Fenster.

### Boundary-paper submission assets

```text
boundary_manuscript_submission.md
→ boundary_submission_spine.md
→ boundary_reviewer_objection_audit.md
→ calibration_transport_family.md
→ multiplicative_measurement_literature_audit.md
→ ecology_letters_perspective_proposal.md
→ EL_PERSPECTIVE_VENUE_CHECK.md
→ make_boundary_identification_figure.py
→ make_multichannel_anchor_figure.py
→ causal_model/multichannel_identifiability.py
→ causal_model/calibration_transport_family.py
→ tests/test_multichannel_identifiability.py
→ tests/test_multichannel_boundary_publication.py
→ tests/test_calibration_transport_family.py
→ tests/test_boundary_identification_figure.py
```

`boundary_manuscript_draft.md` remains the longer audit draft. `boundary_manuscript_submission.md` is the compressed submission-facing candidate. `ecology_letters_perspective_proposal.md` is a <=300-word pre-submission proposal candidate; journal requirements must be rechecked immediately before sending.

## File roles

| Path | Role | Status |
|---|---|---|
| `mee_manuscript_draft.md` | RACH/NOV/RACH-SEQ/G2 methods manuscript | active MEE main text |
| `supporting_information.md` | methods validation and reproducibility | active MEE SI |
| `boundary_manuscript_submission.md` | multichannel quotient + Gamma family + design/reporting rules | active boundary submission candidate |
| `boundary_manuscript_draft.md` | longer theorem/audit draft | boundary audit |
| `boundary_submission_spine.md` | three-pillar claim governance | active boundary governance |
| `calibration_transport_family.md` | canonical Gamma/eta family and calibration anchors | boundary theory bridge |
| `make_boundary_identification_figure.py` | two-channel Gamma/joint-set figure | boundary Figure 1 source |
| `make_multichannel_anchor_figure.py` | `k-1-r` anchor-dimension figure | boundary/proposal figure source |
| `boundary_reviewer_objection_audit.md` | adversarial reviewer-response and submission stop audit | boundary governance |
| `multiplicative_measurement_literature_audit.md` | primary-source audit of recurring multiplicative ecological measurements | boundary evidence audit |
| `ecology_letters_perspective_proposal.md` | <=300-word Perspective proposal candidate | venue pitch |
| `EL_PERSPECTIVE_VENUE_CHECK.md` | dated journal-requirement check | venue governance |
| `TWO_PAPER_STRATEGY.md` | normative separation and no-double-counting rules | active governance |
| `submission_manifest.json` | machine-readable MEE evidence boundary | active governance |
| `g2_frozen_benchmark_protocol.json` | frozen selection benchmark | frozen |
| `results/g2_frozen_v2_summary.json` | frozen G2 numerical/provenance record | final MEE evidence |
| `results/g5_reproducibility_summary.json` | clean figure/wheel/CI record | final MEE evidence |

## Reproducibility

```bash
python paper/check_submission_bundle.py
python paper/check_mee_submission.py
python scripts/check_repository_boundaries.py
python paper/make_boundary_identification_figure.py
python paper/make_multichannel_anchor_figure.py
pytest -q
```

The frozen MEE scientific outputs and public RACH API remain unchanged. Boundary-paper development must not retune G2 or G5.

## Release boundary

The release candidate remains `rach` version 0.1.0 until a genuine public API or versioned scientific change is accepted. Boundary-theory functions remain explicit submodule utilities; the advertised package-level surface remains RACH-first.
