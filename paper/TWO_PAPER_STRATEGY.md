# Two-paper publication strategy

The integrated theorem-first draft mixed two publishable contributions. They are
now governed as separate papers.

## Paper A — channel-identifiability boundary

Paper A now covers ecological measurement chains generally; the legacy heading is retained verbatim because the MEE submission-boundary checker uses it as a separation marker.

**Conceptual headline**

```text
mechanistic proximity != mechanistic identification
```

Paper A argues that ecological evidence has two distinct properties: where a measurement sits biologically, and what it identifies among declared competing mechanisms. Molecular/genomic measurements can be highly proximal and highly identifying, but proximity alone does not guarantee identification. Field patterns can be non-identifying, while strategically placed field observations can directly remove mechanism ambiguity. No monotone relationship or statistical independence between the two axes is assumed. The paper therefore adds an explicit identification axis to mechanistic evidence rather than ranking biological levels intrinsically.

**Quantitative contribution**

```text
mechanistic evidence needs an identification axis
→ net-only quotient / k-channel equivalence dimension
→ channel anchors reduce dimension: k-1-r
→ two-channel proxy calibration-transport family
     Gamma=1          : N3 point identification
     1<Gamma<infinity : sharp partial identification + breakdown
     Gamma->infinity  : N4 non-identification
→ calibration-anchor ladder
→ joint-set reporting rule
```

This paper is about the distinction between mechanistic proximity and mechanistic identification, and about the boundary between point identification, partial identification and non-identification in declared ecological observation maps. Its main output is not RACH and not a synthetic policy benchmark.

For a declared positive chain

```text
W = prod_{j=1}^k F_j,
```

net-only observation leaves a `(k-1)`-dimensional product-preserving equivalence
class in log coordinates. If `r` independent channel values or channel ratios are
directly anchored, the residual unidentified dimension is `k-1-r`; `k-1`
independent channel anchors suffice to recover the final channel from the
product. The theorem demonstrates that deeper or more precise measurement of the same invariant endpoint does not change identification; additional independent observation channels do.

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

For compatibility with the pre-split submission guard, the earlier result name **bounded calibration-drift identification interval** is retained here as an alias for the finite-bound partial-identification result. The canonical formulation is now the symmetric `Gamma/eta` family and sharp joint set.

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
can add a further allocation ambiguity across visitor types. Seed dispersal provides an independent Quantity × Quality architecture.

Genomic and molecular examples belong in Paper A only as conceptual motivation for separating mechanistic proximity from identification strength. Ungerer et al. (2008) and Rudman et al. (2018) should be treated as allies to mechanistic integration; the latter explicitly notes that genomic data alone are not sufficient for the eco-evolutionary questions considered. Smith et al. (2020) supplies a field-level example of mechanistic testing under natural conditions. Paper A must not claim that molecular data are intrinsically less mechanistic, nor imply that all genomic observation maps follow the multiplicative theorem. The exact literature claims are governed by `paper/mechanistic_evidence_literature_audit.md`.

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

The conceptual handoff from Paper A to Paper B is one-way but real:

```text
Paper A: what can the current observation map identify in principle?
Paper B: which candidate observation should be acquired next to reduce ambiguity?
```

Paper B may use this motivation, but it does not inherit Paper A's theorems as its headline contribution.

## Separation rules

1. The MEE paper may state structural non-identifiability as motivation, but it
   does not reproduce the boundary-paper two-axis evidentiary argument, quotient,
   `k-1-r` dimension theorem, Gamma family or breakdown results.
2. The boundary paper may mention observation selection only as a downstream design implication; it
   does not claim RACH, NOV, RACH-SEQ or the G2 policy benchmark as theorem evidence.
3. Pollinator effective-service decomposition and complete measurement-chain
   examples are Paper A motivation/design consequences, not Paper B validation.
4. Genomic/molecular examples in Paper A illustrate the proximity/identification distinction; they are not anti-molecular claims and not additional product-theorem domains unless an appropriate observation map is declared.
5. Signed functional starting position is a Paper B evidence-role illustration,
   not an empirical validation result unless independent natural-system data are
   later collected.
6. Frozen G2/G5 values and software provenance remain unchanged.
7. No result is counted in both papers as a primary contribution.
