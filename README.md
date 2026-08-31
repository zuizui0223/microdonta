# RACH: Causal Admissibility and Observation Design

[![CI](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml/badge.svg)](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml)

## Publication paths

microdonta supports two deliberately separate papers.

### MEE method paper

The active *Methods in Ecology and Evolution* Research Article is:

```text
RACH admissible mechanism set
→ causal degeneracy / resolvability / replaceability
→ validated NOV = I(S;Q | A_epsilon)/K
→ sequential RACH-SEQ selection
→ truth-peek-free G2 benchmark
```

Its validation object is a controlled synthetic observation-selection challenge,
not a natural-system causal claim. At budget four, the matched random-order policy
selected 1.169 mechanism-independent nuisance measurements per system versus 0.014
for RACH-SEQ: an 83.5-fold difference, or approximately 98.8% fewer nuisance
selections, while using 2.673 versus 1.518 observations.

### Boundary paper

The companion boundary programme is:

```text
net-only quotient / k-channel equivalence dimension
→ channel anchors reduce residual dimension: k-1-r
→ two-channel calibration-transport family
     Gamma=1          : point identification (N3)
     1<Gamma<infinity : sharp partial identification + breakdown
     Gamma->infinity  : non-identification (N4)
→ calibration-anchor ladder
→ joint-set reporting rule
```

For a declared positive chain `W=prod_j F_j`, net-only observation leaves a
`(k-1)`-dimensional product-preserving equivalence class in log coordinates. If
`r` independent channel values or channel ratios are directly anchored, the
residual unidentified dimension is `k-1-r`; `k-1` channel anchors suffice for
point identification of the final factor from the product.

For the common two-channel proxy case, the canonical transport restriction is

```text
1/Gamma <= kappa=q_1/q_0 <= Gamma,   Gamma>=1.
```

The complementary-channel marginal is `[rho_hat/Gamma,rho_hat*Gamma]`, and the
sharp joint set preserves `rho_F rho_E=rho_W`. Directional robustness is reported
with the reference-invariant factor `Gamma*=max(rho_hat,1/rho_hat)` (or
`eta*=|log rho_hat|`). The worked decline has `Gamma*=1.34`; 34% upward drift is
a directional translation rather than the canonical robustness scale.

The normative split is in [`paper/TWO_PAPER_STRATEGY.md`](paper/TWO_PAPER_STRATEGY.md).
The active MEE evidence boundary is
[`paper/submission_manifest.json`](paper/submission_manifest.json). Run
`python paper/check_submission_bundle.py`, `python paper/check_mee_submission.py`
and `python scripts/check_repository_boundaries.py` before publication changes.

## RACH

**RACH** means **Restricted Admissible Causal Hypotheses**. It keeps every causal
explanation compatible with a declared model family, biological constraints and
observed pattern, quantifies what remains unresolved, and identifies which next
measurement carries the most information about residual mechanism identity.

```text
A_epsilon(y_obs, x_obs)
= { (theta, s) in Theta x S :
    G(theta) = 1
    and d(P_sim(f(x_obs; theta, s)), P_obs(y_obs)) <= epsilon
  }
```

| symbol | meaning |
|---|---|
| `x_obs` | fixed empirical context |
| `theta` | parameters over biologically admissible ranges |
| `s` | causal mechanism/switch vector |
| `G(theta)` | pre-data biological constraints |
| `P_sim`, `P_obs` | simulated and observed pattern maps |
| `d`, `epsilon` | predeclared discrepancy and tolerance |

For a verified predictive partition of the current admissible region,

```text
NOV(Q)=I(S;Q | A_epsilon)/K.
```

RACH-SEQ selects the maximum-current-NOV candidate, observes its outcome only
after selection, conditions the admissible region and recomputes all remaining
candidate values.

RACH is not a best-model selector and does not convert conditional simulation
results into empirical proof.

## Repository roles

```text
causal_model/
  causal_admissibility.py            admissible regions, CA, D_RACH, R_RACH
  causal_replaceability.py           causal replaceability / CRC
  mechanism_equivalence.py           residual equivalence structure
  nov_evsi.py                        validated NOV / EVSI
  rach_seq.py                         sequential observation selection
  generality_sweep.py                frozen G2 policy benchmark generator
  multichannel_identifiability.py    k-channel quotient dimension / channel anchors
  calibration_transport_family.py    symmetric Gamma/eta transport family
  bounded_proxy_drift.py             legacy directional-delta sensitivity
  channel_identifiability_theory.py
  proxy_calibration_theory.py        stable/unrestricted proxy constructions

paper/
  mee_manuscript_draft.md            active RACH method manuscript
  supporting_information.md          active method SI
  boundary_manuscript_submission.md  compressed boundary-paper candidate
  boundary_manuscript_draft.md       longer boundary-paper audit draft
  boundary_submission_spine.md       three-pillar claim governance
  TWO_PAPER_STRATEGY.md              no-double-counting governance
  submission_manifest.json           active MEE evidence inventory
```

The repository also retains supplementary ABM backends, adapters and archived
exploratory programmes. They are not primary evidence for the MEE paper unless
explicitly listed in the submission manifest.

## izu-core questions: resolved publication roles

The three izu-core questions no longer share one generic “translation track”.
Their roles differ.

| Source question | Publication role | Contract |
|---|---|---|
| signed functional starting position | **RACH paper evidence-role example** | freeze `plant_trait - pollinator_functional_center` before outcome inspection; use as `input_context`, not an independent acceptance target |
| network context to effective service | **boundary paper ecological motivation** | at visitor type `m`, measure `visitor_rate_m * direct_effectiveness_m`; community service is `sum_m` of those contributions; do not treat degree or abundance alone as service |
| complete pollinator-change chain | **boundary paper k-channel design generalisation** | declare the change → service → dependency/assurance → response observation map; do not infer missing links from endpoints; in a declared positive k-stage product, r independent channel anchors leave dimension `k-1-r` |

The signed-starting-position example does not validate a natural-system RACH
mechanism claim. The effective-service and complete-chain questions are now part
of the boundary paper's measurement-theory motivation and design consequences,
not deferred empirical validation.

## Installation and core checks

```bash
pip install -e ".[dev]"
python paper/check_submission_bundle.py
python paper/check_mee_submission.py
python scripts/check_repository_boundaries.py
pytest -q
```

## Controlled validation

The frozen G2 protocol compares two policies on identical generated systems,
hidden truths, candidate sets and budgets:

```text
RACH-SEQ      choose the verified candidate with maximum current NOV
random_order  choose uniformly among remaining candidates
```

Hidden truth is used only after selection to materialise the chosen outcome. The
comparison is descriptive, not a favourable-result acceptance gate.

At budget two:

| outcome | RACH-SEQ | random order |
|---|---:|---:|
| initial confounding edges resolved | 1.000 | 0.6045 |
| systems converged | 0.990 | 0.435 |
| observations used | 1.505 | 1.821 |
| nuisance selections | 0.001 | 0.974 |

At budget four, both policies resolved all initial edges on average, while
RACH-SEQ selected 0.014 nuisance observations versus 1.169 under random order.
Hidden-truth false exclusion was zero in every policy-by-budget cell.

Exact frozen values and provenance are in
[`paper/results/g2_frozen_v2_summary.json`](paper/results/g2_frozen_v2_summary.json).

## Boundary-theory calculations

```python
from causal_model.multichannel_identifiability import (
    residual_equivalence_dimension,
)

chain = residual_equivalence_dimension(channels=4, independent_anchors=2)
print(chain.residual_dimension)
# 1
```

For proxy transport:

```python
from causal_model.calibration_transport_family import (
    breakdown_factor,
    symmetric_interval,
)

interval = symmetric_interval(1 / 1.34, gamma=1.20)
print(interval.lower, interval.upper)

gamma_star, eta_star = breakdown_factor(1 / 1.34)
print(gamma_star)
# 1.34
```

These calculations report structural consequences of declared observation maps
and transport bounds. They do not estimate the calibration bound or certify a
proxy from the same net/proxy observations.

## Documentation

- `docs/mainline.md` — normative MEE RACH/NOV/RACH-SEQ boundary
- `paper/TWO_PAPER_STRATEGY.md` — two-paper split and no-double-counting rules
- `paper/boundary_manuscript_submission.md` — compressed boundary-paper candidate
- `paper/boundary_submission_spine.md` — three-pillar boundary-paper governance
- `paper/calibration_transport_family.md` — Gamma/eta family and calibration anchors
- `docs/bounded_proxy_drift_identification.md` — legacy delta identified sets and breakdowns
- `docs/rach_theory.md` — RACH method definition
- `docs/rach_mathematical_foundations.md` — NOV information identity and bounds
- `paper/g2_frozen_benchmark_protocol.json` — frozen selection protocol
- `paper/results/g2_frozen_v2_summary.json` — final G2 numerical evidence
- `examples/island_pollination_translation/` — empirical intake and gate audit

## Scope

The MEE result is a validated observation-selection method over a declared frozen
synthetic family. It does not establish universal optimality or a natural-system
mechanism. The boundary theorem is universal only over declared positive
multiplicative channel models and the observation maps explicitly analysed.
Neither scope statement should be weakened during submission preparation.
