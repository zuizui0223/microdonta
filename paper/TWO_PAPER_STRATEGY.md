# Two-paper publication strategy

The integrated theorem-first draft mixed two publishable contributions. They are
now governed as separate papers.

## Paper A — channel-identifiability boundary

**Core contribution**

```text
N1 net-only impossibility
→ N2 exact-channel sufficiency
→ N3 stable-proxy ratio identification
→ bounded calibration-drift identification interval
→ breakdown point for sign conclusions
→ N4 unbounded-drift non-identifiability
→ observation-design rules
```

This paper is about the boundary between point identification, partial
identification and non-identification in positive multiplicative ecological
channels. Its main output is not RACH and not a synthetic policy benchmark. It
returns an identified interval and a calibration-drift breakdown point whenever
proxy drift can be bounded.

For a proxy of `F`, write

```text
X_i = q_i F_i
kappa = q_1 / q_0
rho_W = W_1 / W_0
rho_X = X_1 / X_0
rho_E_hat = rho_W / rho_X
```

If `kappa in [1-delta, 1+delta]`, then

```text
rho_E in [rho_E_hat (1-delta), rho_E_hat (1+delta)]
```

and the interval has multiplicative width

```text
(1+delta)/(1-delta).
```

A conclusion `E decreased` is robust while
`rho_E_hat (1+delta) < 1`; the corresponding breakdown point is
`delta* = 1/rho_E_hat - 1`, capped to the admissible range `[0,1)`.
The increasing case is symmetric: `delta* = 1 - 1/rho_E_hat` when
`rho_E_hat > 1`.

The design rule is operational: measure the channel directly, calibrate the
proxy, or report the bounded identified interval and its breakdown point. Do not
replace unbounded drift with a point estimate.

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

## Separation rules

1. The MEE paper may state structural non-identifiability as motivation, but it
   does not reproduce the N1–N4 proof sequence or bounded-drift theorem.
2. The boundary paper may use RACH only as a downstream design implication; it
   does not claim the G2 policy benchmark as theorem evidence.
3. The exact one-step colonisation projection and prospective Campanula material
   are supporting examples for the boundary programme, not required evidence for
   the MEE method paper.
4. Frozen G2/G5 values and software provenance remain unchanged.
5. No result is counted in both papers as a primary contribution.
