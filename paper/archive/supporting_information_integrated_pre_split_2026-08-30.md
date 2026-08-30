# Supporting Information

## RACH: from causal non-identifiability to next-observation design in ecological mechanism inference

This Supporting Information accompanies the anonymised Research Article. It is deliberately subordinate to the Main-text claim spine. It supplies algebraic details, frozen validation tables, the boundary between exact ecological projection and unfactorised simulation, and the reproducibility map. It does **not** introduce additional empirical mechanism claims, ecological-rule panels, structure discovery, or new model families.

---

## S1. Exact channel-identifiability results

### S1.1 Observation class

Let trait-specific total performance in regime `i` be

`W_i(z) = F_i(z) E_i(z)`, with `F_i(z)>0` and `E_i(z)>0`.

A net-only observation is any deterministic operator `Phi(W_i)`. This class includes the complete performance curve and every thresholded viable set `Omega_t={z: W_i(z)>=t}`, and therefore any edge, breadth, component count, or other geometry calculated only from those sets.

### S1.2 N1: net-only observations cannot identify the changed channel

Let `F_0(z),E_0(z)>0`, and let `a(z)>0`. Compare two distinct programs:

`P_F: (F_1,E_1)=(aF_0,E_0)`

`P_E: (F_1,E_1)=(F_0,aE_0)`.

Both give the same pointwise total performance,

`W_1(z)=a(z)F_0(z)E_0(z)`.

Hence `Phi(W_1)` is identical under the two programs for every net-only observation operator `Phi`. The equivalence is structural rather than a low-power sampling result. Because it holds pointwise, complete thresholded trait-space geometry also cannot break the symmetry.

### S1.3 N2: net performance plus one channel is sufficient

If `W_i` and `F_i` are observed, positivity gives the unique reconstruction

`E_i(z)=W_i(z)/F_i(z)`.

Symmetrically, observing `W_i` and `E_i` gives `F_i=W_i/E_i`. Therefore the before/after ratios

`rho_F=F_1/F_0` and `rho_E=E_1/E_0`

are identified without assuming that only one channel changed. Fecundity-only, establishment-only, mixed and unchanged cases can then be distinguished from the reconstructed ratios.

### S1.4 N3: stable proxy conversion identifies relative channel change

Suppose the field measurement is a proxy `X_i(z)=q_i(z)F_i(z)`. If its conversion is stable across the comparison, `q_0(z)=q_1(z)=q(z)>0`, then

`X_1/X_0 = F_1/F_0 = rho_F`.

Because `W_1/W_0=rho_F rho_E`,

`rho_E = (W_1/W_0)/(X_1/X_0)`.

Thus unknown absolute calibration is compatible with relative channel identification when the conversion is stable.

### S1.5 N4: unconstrained calibration drift restores non-identifiability

If `q_0` and `q_1` may differ freely,

`F_1/F_0 = (X_1/X_0)(q_0/q_1)`

and

`E_1/E_0 = (W_1/W_0)(X_0/X_1)(q_1/q_0)`.

The unobserved positive ratio `q_1/q_0` can therefore generate different latent channel changes for the same observed `W_0,W_1,X_0,X_1`. As a constructive example, set all four observed series to one. Stable calibration yields no channel change, whereas choosing any nonconstant positive `h(z)=q_1/q_0` yields `F_1/F_0=1/h` and `E_1/E_0=h` with exactly the same observations.

### S1.6 Scope of N1–N4

The theorem family is exact only for the declared positive multiplicative two-channel output. Zeros, additional channels, nonmultiplicative interactions, or a different life-cycle output require an explicit extension. Measurement error can be propagated statistically, but unknown regime-specific proxy conversion is structural and cannot be repaired by larger sample size alone.

---

## S2. RACH quantities and information-theoretic next-observation value

### S2.1 Admissible region

For switches `S in {0,1}^K`, parameters `theta`, pre-data constraint grammar `G`, simulator `f`, pattern maps `P_sim,P_obs`, discrepancy `d`, tolerance `epsilon`, observed targets `y_obs` and fixed context `x_obs`, RACH defines

`A_epsilon = {(theta,s): G(theta)=1 and d(P_sim(f(x_obs;theta,s)),P_obs(y_obs))<=epsilon}`.

The finite implementation approximates this restricted region by prior sampling. Observations assigned only to `input_context`, `diagnostic_only`, or `future_observation` are not allowed to enter the acceptance discrepancy as if they were independent observed targets.

### S2.2 Causal admissibility, degeneracy and resolvability

For switch `j`, `CA_j=P(s_j=1 | A_epsilon)`. Let `H(S|A_epsilon)` be the base-2 entropy of the joint switch vector. Then

`D_RACH=H(S|A_epsilon)`

and

`R_RACH=1-D_RACH/K`.

Because a `K`-bit switch vector has entropy at most `K`, `0<=D_RACH<=K` and `0<=R_RACH<=1`. The normalisation is by maximum possible switch entropy, not by the realised prior entropy. Observation contribution compares joint resolvability with and without a current observation and can be negative; removing one observation can occasionally reduce apparent ambiguity created by another.

### S2.3 Validated NOV is normalised mutual information

Let a future candidate observation `Q` have a predictive map whose outcomes form a verified mutually exclusive and exhaustive partition of the current admissible region. Its predictive distribution is the pushforward of the restricted current region. Define

`NOV(Q)=E_Q[R_RACH(A_epsilon | Q)-R_RACH(A_epsilon)]`.

Then

`NOV(Q) = [H(S|A_epsilon)-H(S|A_epsilon,Q)]/K = I(S;Q|A_epsilon)/K`.

Consequently,

`0 <= NOV(Q) <= 1-R_RACH(A_epsilon) <= 1`.

`NOV(Q)=0` exactly when `Q` contains no information about residual mechanism identity under the current region. It reaches all remaining resolvability only when observing `Q` removes all remaining switch entropy. If the outcome maps overlap, are incomplete, or require unavailable simulator columns, the stored region does not identify the predictive pushforward and validated NOV is reported as non-estimable rather than silently substituting a prior.

### S2.4 RACH-SEQ

RACH-SEQ repeats the same information objective after every realised observation. At step `t`, verified candidates are ranked by current `NOV_t(Q)=I(S;Q|A_{epsilon,t})/K`; after the selected outcome arrives, the admissible region is conditioned and all predictive distributions are recomputed. The sequence stops when the budget is exhausted, confounding is resolved at the declared resolution, or no available candidate carries positive validated NOV. A normalised expected-edge-cut score exists only as an explicitly labelled compatibility fallback for candidates whose predictive map is not estimable; it is not called validated NOV.

---

## S3. Frozen controlled validation

All numerical values in this section are copied from the frozen submission result summaries. No favourable-result threshold was used to accept or tune these results.

### S3.1 Known-truth specified-simulator self-consistency

The known-truth benchmark uses the unchanged submission defaults: 200 attempts per case, `literature_grounded` preset, `weighted_lax` acceptance, seed 42, and proxy-to-proxy generation/inference. Confounded switches are not required to become unique; the benchmark asks whether generating switches remain admissible.

**Table S1. Known-truth aggregate results.**

| Pattern noise | Cases | Accuracy | Precision | Recall | F1 | Mean CA error | R_RACH | D_RACH |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 8 | 0.6562 | 0.4792 | 1.0000 | 0.6042 | 0.3388 | 0.3699 | 2.5203 |
| 0.1 | 8 | 0.6875 | 0.5729 | 1.0000 | 0.6667 | 0.3359 | 0.4719 | 2.1123 |
| 0.2 | 8 | 0.7083 | 0.5417 | 1.0000 | 0.6429 | 0.2868 | 0.4238 | 2.3050 |

Recall of applicable true-ON switches is 1.0 in every aggregate noise stratum. Accuracy is lower because additional confounded explanations remain admissible; that is the intended signature of a non-identifying benchmark rather than a failure to select a unique model. Figure S1 visualises this benchmark.

### S3.2 Frozen G2 v2 matched-policy selection benchmark

Protocol `rach-g2-truth-peek-free-v2` uses five predeclared seeds, 200 generated systems per seed, 1,500 prior draws per system, `K in {4,5,6}`, one or two disjoint confounds, two mechanism-uninformative binary nuisance candidates, and budgets 0–4. RACH-SEQ and `random_order` receive the same generated systems, hidden truths, candidates and budgets. Hidden truth is materialised only after a candidate is selected.

**Table S2. Policy-specific mean results across the five frozen seeds.**

| Policy | Budget | Converged | Initial edges resolved | Mean observations | Mean distractors | False exclusion |
|---|---:|---:|---:|---:|---:|---:|
| RACH-SEQ | 0 | 0.000 | 0.0000 | 0.000 | 0.000 | 0.000 |
| RACH-SEQ | 1 | 0.495 | 0.7480 | 1.000 | 0.000 | 0.000 |
| RACH-SEQ | 2 | 0.990 | 1.0000 | 1.505 | 0.001 | 0.000 |
| RACH-SEQ | 3 | 0.997 | 1.0000 | 1.515 | 0.011 | 0.000 |
| RACH-SEQ | 4 | 0.999 | 1.0000 | 1.518 | 0.014 | 0.000 |
| random_order | 0 | 0.000 | 0.0000 | 0.000 | 0.000 | 0.000 |
| random_order | 1 | 0.179 | 0.2995 | 1.000 | 0.580 | 0.000 |
| random_order | 2 | 0.435 | 0.6045 | 1.821 | 0.974 | 0.000 |
| random_order | 3 | 0.689 | 0.8650 | 2.386 | 1.152 | 0.000 |
| random_order | 4 | 0.940 | 1.0000 | 2.673 | 1.169 | 0.000 |

At budget two, the across-seed sample SDs for RACH-SEQ were 0.0079 for convergence, 0 for edge resolution, 0.0302 for observations and 0.00224 for distractor selections; random-order SDs were 0.0355, 0.0231, 0.0243 and 0.0277 respectively. All 10,000 system-policy-budget records retained the hidden true explanation. The policy comparison is descriptive: the protocol contains no requirement that RACH-SEQ outperform random order.

### S3.3 Stored-region exactness and NOV calibration

The unchanged NOV-calibration defaults use 1,000 attempts, seed 7, `literature_grounded`, and `strict_all`. The initial admissible region contains 597 draws with `R_RACH=0.1071`.

**Table S3. Stored-region filtering versus fresh deterministic re-inference.**

| Candidate observation | Filter gain | Fresh gain |
|---|---:|---:|
| nectar guide, Hachijo | 0.2684 | 0.2684 |
| selfing rate, Hachijo | 0.1043 | 0.1043 |
| flower size, Hachijo | 0.2581 | 0.2581 |
| nectar guide, Oshima | 0.0215 | 0.0215 |
| selfing rate, Oshima | 0.0672 | 0.0672 |
| flower size, Oshima | 0.2304 | 0.2304 |

The maximum absolute filter-versus-fresh difference is zero for all six directly checked quantitative observations. Across eight candidate observations and four controlled truths per observation, predictive EVSI has Pearson `r=0.7664` with mean realised resolvability gain; mean absolute EVSI-minus-mean-realised difference is 0.0739. Realised gains vary across truths, so this is a calibration check rather than a claim that EVSI predicts every realised outcome.

---

## S4. Ecological projection and simulation boundary

### S4.1 Exact one-step projection

For the declared colonisation life-cycle output, expected juvenile recruits retained after one step for one initial adult factorise exactly as

`W_recruit(z)=F_local(z) E_settlement(z)`, where

`F_local=P(survive) P(conceive | survive)`

and

`E_settlement=(1-p_ext)[D(z)cT + {1-D(z)}L]`.

Here `D(z)` is dispersal investment, `c` corridor connectivity, `T` expected room in a reachable target, and `L` local settlement room. This equality follows the implemented order of survival, conception, mutually exclusive dispersal/local settlement, and the end-of-step extinction draw. N1–N4 therefore apply to this declared output on its strict positive interior.

### S4.2 What is not factorised

Long-run invasion growth, persistence and endpoint trait-space geometry additionally contain surviving parents, repeated generations, density dependence, resource feedback, mutation, stochasticity and changing resident composition. They are therefore labelled `requires_factorization_extension` rather than being used as proofs of N1–N4. ABM families are retained only as supplementary robustness/counterexample machinery under this boundary.

### S4.3 ODD model documentation

The supplementary ODD source documents plant-agent, island-environment and pollinator-environment state variables, stochastic reproduction and inheritance, and diagnostic outputs. It also labels planned variables/submodels separately from implemented ones. Those models are not used to infer an empirical Campanula mechanism and are not promoted into the primary theorem chain.

---

## S5. Reproducibility and reviewer bundle

### S5.1 Frozen evidence map

The reviewer bundle carries anonymised copies of the following evidence classes:

- the review manuscript and this Supporting Information;
- the frozen G2 protocol and frozen G2 summary;
- the frozen known-truth/NOV summary;
- the final figure inventory and generated Figure 1–3 plus Figure S1;
- the primary RACH implementation modules required for admissibility, replaceability, validated NOV and RACH-SEQ;
- the controlled validation generators and figure scripts;
- tests needed to verify the public RACH interface and the principal mathematical/benchmark invariants.

Public repository URLs, author metadata, public commit identifiers and archival-service IDs are deliberately omitted from the reviewer-facing copy for double-anonymous review. The bundle instead contains a SHA-256 manifest of every included file. Public release provenance remains preserved separately in the non-anonymous release metadata.

### S5.2 Frozen protocol identifiers

The final G2 protocol identifier is `rach-g2-truth-peek-free-v2`; its protocol SHA-256 is `3568025f98a671b232e5d6b865063f37baa5bec319a594f831d6b5b953428cb7`. This hash identifies the scientific benchmark configuration without exposing repository identity. The known-truth and NOV calibration configurations are recorded verbatim in the frozen validation summary included in the reviewer bundle.

### S5.3 Software validation

The release-candidate package is version 0.1.0. The clean G5 check rebuilt all four final figures, reproduced the frozen known-truth and NOV values, built and installed the wheel outside the repository, and verified the package boundary. The wheel SHA-256 is `f97308f99caf59a6dd13931e738cee803054c0864b66c4d93db5c944f72f0fa8`. The final test matrix covers Python 3.10, 3.11 and 3.12.

### S5.4 Explicit exclusions

The reviewer bundle and Supporting Information exclude provisional Bergmann/Allen/Foster/Gloger rule panels, causal-structure discovery, externally owned eco-genetic work, the optional attraction-trait incubator, Streamlit/UI material, and unreferenced legacy ABM panels. Their presence elsewhere in development history is not evidence for the submitted claims.

---

## Figure S1 caption

**Figure S1. Known-truth specified-simulator self-consistency.** Recovery summaries under the unchanged frozen proxy-to-proxy benchmark at pattern-noise rates 0, 0.1 and 0.2. The benchmark is designed to retain generating true-ON switches while allowing observationally confounded alternatives to remain admissible; it is not a unique-model recovery target or an empirical mechanism validation.
