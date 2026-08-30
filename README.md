# RACH: Causal Admissibility and Observation Design

[![CI](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml/badge.svg)](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml)

## Publication paths

microdonta now supports two deliberately separate papers.

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
N1 net-only non-identifiability
→ N2 exact-channel sufficiency
→ N3 stable-proxy point identification
→ bounded calibration-drift identified intervals
→ directional breakdown points and design rules
→ N4 unbounded-drift non-identifiability
```

If `q_1/q_0 in [1-delta,1+delta]`, the complementary-channel ratio lies in
`[rho_hat(1-delta),rho_hat(1+delta)]`, with multiplicative width
`(1+delta)/(1-delta)`. This theory is maintained separately and does not block the
MEE method submission.

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
  causal_admissibility.py          admissible regions, CA, D_RACH, R_RACH
  causal_replaceability.py         causal replaceability / CRC
  mechanism_equivalence.py         residual equivalence structure
  nov_evsi.py                      validated NOV / EVSI
  rach_seq.py                      sequential observation selection
  generality_sweep.py              frozen G2 policy benchmark generator
  bounded_proxy_drift.py           separate boundary-paper partial identification
  channel_identifiability_theory.py
  proxy_calibration_theory.py      separate N1–N4 boundary theory

paper/
  mee_manuscript_draft.md          active RACH method manuscript
  supporting_information.md        active method SI
  boundary_manuscript_draft.md     separate boundary-paper draft
  TWO_PAPER_STRATEGY.md            no-double-counting governance
  submission_manifest.json         active MEE evidence inventory
```

The repository also retains supplementary ABM backends, adapters and archived
exploratory programmes. They are not primary evidence for the MEE paper unless
explicitly listed in the submission manifest.

## izu-core translation tracks

The three izu-core questions remain nonblocking real-system translation tracks:

| Source question | RACH observation contract |
|---|---|
| signed functional starting position | freeze `plant_trait - pollinator_functional_center` before outcome inspection |
| network context to effective service | measure `sum_k(visitor_rate_k * direct_effectiveness_k)` rather than treating degree or abundance as service |
| complete pollinator-change chain | observe change → service → dependency/assurance → response without inferring missing links |

Their estimands and evidence gates are specified, but they are not yet empirical
validation of RACH or of the ecological mechanisms.

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

## Boundary-theory calculation

```python
from causal_model.bounded_proxy_drift import (
    design_rule_for_interval,
    identify_under_bounded_proxy_drift,
)

result = identify_under_bounded_proxy_drift(
    net_ratio=0.60,
    proxy_ratio=0.80,
    delta=0.20,
    proxy_channel="fecundity",
)

print(result.establishment.lower, result.establishment.upper)
# 0.60, 0.90

rule = design_rule_for_interval(
    result.establishment,
    target_channel="establishment",
)
print(rule.status)
# sign_identified
```

This calculation reports the identified set implied by a declared calibration
bound. It does not estimate `delta` or certify the proxy.

## Documentation

- `docs/mainline.md` — normative MEE RACH/NOV/RACH-SEQ boundary
- `paper/TWO_PAPER_STRATEGY.md` — two-paper split and no-double-counting rules
- `paper/boundary_manuscript_draft.md` — N1–N4/bounded-drift paper draft
- `docs/bounded_proxy_drift_identification.md` — identified sets and breakdowns
- `docs/rach_theory.md` — RACH method definition
- `docs/rach_mathematical_foundations.md` — NOV information identity and bounds
- `paper/g2_frozen_benchmark_protocol.json` — frozen selection protocol
- `paper/results/g2_frozen_v2_summary.json` — final G2 numerical evidence
- `examples/island_pollination_translation/` — empirical intake and gate audit

## Scope

The MEE result is a validated observation-selection method over a declared frozen
synthetic family. It does not establish universal optimality or a natural-system
mechanism. The boundary theorem is universal only over declared positive
multiplicative channel models. Neither scope statement should be weakened during
submission preparation.
