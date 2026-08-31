# Two-paper publication strategy

The integrated theorem-first draft mixed two publishable contributions. They are
now governed as separate papers.

## Paper A — ecological channel-identifiability boundary

**Core contribution**

```text
net-only quotient / k-channel equivalence dimension
→ channel anchors reduce dimension: k-1-r
→ two-channel proxy calibration-transport family
     Gamma=1          : N3 point identification
     1<Gamma<infinity : sharp partial identification + breakdown
     Gamma->infinity  : N4 non-identification
→ calibration-anchor ladder
→ joint-set reporting rule
```

This paper is about the boundary between point identification, partial
identification and non-identification in positive multiplicative ecological
measurement chains. Its main output is not RACH and not a synthetic policy
benchmark.

For a declared positive chain

```text
W = prod_{j=1}^k F_j,
```

net-only observation leaves a `(k-1)`-dimensional product-preserving equivalence
class in log coordinates. If `r` independent channel values or channel ratios are
directly anchored, the residual unidentified dimension is `k-1-r`; `k-1`
independent channel anchors suffice to recover the final channel from the
product.

For the common two-channel proxy case,

```text
W_i = F_i E_i
X_i = q_i F_i
kappa = q_1 / q_0
rho_W = W_1 / W_0
rho_X = X_1 / X_0
rho_E_hat = rho_W / rho_X
```

use the canonical symmetric transport restriction

```text
1/Gamma <= kappa <= Gamma,   Gamma >= 1.
```

Then

```text
rho_E in [rho_E_hat/Gamma, rho_E_hat*Gamma]
```

and the sharp joint set preserves `rho_F rho_E=rho_W`. Stable, bounded and
unrestricted transport are the same family: `Gamma=1` gives N3 point
identification, finite `Gamma>1` gives partial identification, and removing the
finite restriction (`Gamma->infinity`) gives N4.

The primary directional robustness scale is the reference-invariant breakdown
factor

```text
Gamma* = max(rho_hat, 1/rho_hat)
eta*   = |log rho_hat|.
```

The worked `rho_hat=1/1.34` example has `Gamma*=1.34`; “34% upward drift” is only
a directional translation.

Two anchor concepts are kept distinct. **Channel anchors** directly observe
latent stages and reduce the `k`-channel equivalence dimension one coordinate at
a time. **Calibration anchors** observe proxy/channel conversion within regimes:
zero calibration anchors leave transport unrestricted unless assumed, one anchor
plus an external finite `Gamma/eta` supports sharp partial identification, and
two anchors observe `q_0`, `q_1` and therefore `kappa` directly.

The pollination motivation belongs in Paper A: species-specific effective service
has the rate-by-effectiveness form `visitor_rate * direct_effectiveness`, whereas
network degree, abundance or visitation alone are quantity-side descriptors or
proxies rather than effective service. Community aggregation `sum_m V_m E_m`
can add a further allocation ambiguity across visitor types.

## Paper B — RACH observation-selection method

**Target:** *Methods in Ecology and Evolution*, Research Article.

**Core contribution**

```text
RACH admissible mechanism set
→ causal degeneracy and resolvability
→ NOV(Q) = I(S;Q | A_epsilon)/K
→ sequential re-estimation in RACH-SEQ
→ truth-peek-free G2 selection benchmark
```

This paper is a method and validation paper. It does not need a real-data causal
result. Its empirical object is the controlled observation-selection benchmark:
identical random confounded systems, hidden truths, candidate measurements and
budgets are supplied to RACH-SEQ and an uninformed random-order policy.

The headline selection result should include both resolution and waste avoidance:

- at budget 2, edge resolution was `1.000` versus `0.6045`, convergence was
  `0.990` versus `0.435`, and hidden-truth false exclusion was zero for both;
- at budget 4, random order selected `1.169` mechanism-independent nuisance
  measurements per system versus `0.014` for RACH-SEQ, a `83.5-fold` difference
  (about a `98.8%` reduction), while RACH-SEQ used `1.518` observations versus
  `2.673`.

Use **mechanism-independent nuisance measurement** or **distractor measurement**,
not `noise observation`, because measurement noise is a different concept.
Always report the absolute values next to the fold ratio; the ratio is descriptive,
not a preregistered acceptance threshold.

A signed functional starting position such as
`plant_trait - pollinator_functional_center` may be used in Paper B only as an
**evidence-role example**: freeze it before outcome inspection, assign it to
`input_context`, and never recycle the same hypothesis-derived quantity as an
independent observed target. It is not natural-system validation of RACH.

## Separation rules

1. The MEE paper may state structural non-identifiability as motivation, but it
   does not reproduce the boundary-paper quotient, `k-1-r` dimension theorem,
   Gamma family or breakdown results.
2. The boundary paper may use RACH only as a downstream design implication; it
   does not claim the G2 policy benchmark as theorem evidence.
3. Pollinator effective-service decomposition and complete measurement-chain
   examples are Paper A motivation/design consequences, not Paper B validation.
4. Signed functional starting position is a Paper B evidence-role illustration,
   not an empirical validation result unless independent natural-system data are
   later collected.
5. Frozen G2/G5 values and software provenance remain unchanged.
6. No result is counted in both papers as a primary contribution.
