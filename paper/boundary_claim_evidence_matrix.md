# Boundary Perspective — claim–evidence matrix

Status: submission-facing evidence map for `boundary_manuscript_submission.md`.

This file keeps the broadened Perspective claim proportional to its support. Every headline statement should have a clear evidence role: ecological literature motivates the distinction, the identification theorems establish exact results for declared observation maps, figures communicate the logic, and scope guards prevent a worked theorem from becoming a universal claim.

| Claim | Evidence role | Primary support | Quantitative / figure support | Scope guard |
|---|---|---|---|---|
| **Mechanistic proximity and identification strength are non-equivalent properties.** | Perspective synthesis | Ungerer et al. 2008; Rudman et al. 2018; Grace et al. 2025; `mechanistic_evidence_literature_audit.md` | Figure 1; N1/N1-k provide an exact worked case in which measurement richness does not remove observational equivalence | Do not claim statistical independence, a universal ecology-wide hierarchy, or that identification exhausts all meanings of mechanism |
| **Molecular/genomic evidence can be highly mechanistically informative without automatically identifying a unique ecological explanation.** | Literature-backed scope statement | Ungerer et al. 2008; Rudman et al. 2018 | Figure 1 upper examples | Treat ecological genomics as an ally; never claim that molecular data are intrinsically weak or non-mechanistic |
| **Field-level evidence can test mechanisms when the design separates alternatives or measures an intermediate process.** | Literature-backed counterweight to a level hierarchy | Smith et al. 2020; Siegel & Dee 2025; Correia, Dee & Ferraro 2025 | Figure 1 lower-right example; channel-anchor rule is a structural worked case | Do not claim all field observations identify mechanisms or that experiments are always required |
| **Endpoint-only observation of a declared positive `k`-channel product leaves `k-1` unresolved dimensions; `r` independent direct channel anchors leave `k-1-r`.** | Formal theorem | N1-k; `causal_model.multichannel_identifiability` | Figure 2 | Applies to the declared positive multiplicative endpoint map; redundant anchors do not reduce dimension; nonmultiplicative maps require their own analysis |
| **Relative proxy comparisons identify latent channel changes only to the extent that proxy calibration transports across regimes.** | Formal theorem + sensitivity framework | T1; `causal_model.calibration_transport_family` | Figure 3 | `Gamma` is externally supplied or sensitivity-indexed unless direct calibration data are collected; it is not learned from the same `W,X` observations |
| **Stable, finitely bounded and unrestricted proxy transport form one family.** | Formal unification | `Gamma=1`, finite `Gamma`, `Gamma->infinity` | Figure 3 | N4 is removal of the finite transport restriction; never describe it as `delta->1` |
| **Directional robustness should be reported with the reference-invariant breakdown factor.** | Operational sensitivity result | `Gamma*=max(rho_hat,1/rho_hat)`, `eta*=|log rho_hat|` | Figure 3 worked `Gamma*=1.34` example | “34% upward drift” is a directional translation, not the canonical symmetric robustness scale |
| **Calibration uncertainty in the two latent channels is coupled, not independently combinable.** | Formal reporting rule | `rho_F rho_E=rho_W`; log joint set slope `-1` | Figure 3; Design Rule 2 | This is structural calibration uncertainty conditional on observed/estimated ratios; sampling uncertainty is a separate layer |
| **Ecological service architectures provide real applications of the product boundary.** | Empirical measurement-architecture motivation | Schupp, Jordano & Gómez 2010; Rader et al. 2012; Reynolds & Fenster 2008; Ballantyne et al. 2017 | Pollination `V_m E_m`; seed-dispersal Quantity × Quality | Do not imply identical biological semantics across domains; community `sum_m V_mE_m` adds aggregation ambiguity and is not itself one two-factor product |
| **Missing intermediate links should be treated as measurement/design questions rather than inferred from endpoint association alone.** | Perspective/design consequence | Correia, Dee & Ferraro 2025; channel-anchor theorem | Figure 2; Design Rule 1 | The `k-1-r` count applies only when the declared endpoint map is the stated product; broader missing-link principle requires the appropriate observation map |

## Minimum publishable claim

If an editor or reviewer rejects the broadest rhetoric, the paper should still stand on the following closed package:

1. **Evidentiary distinction:** biological proximity and identification strength are distinct, target-dependent properties of evidence.
2. **Product boundary:** a declared positive `k`-stage product has a `k-1-r` residual equivalence dimension after `r` independent direct channel anchors.
3. **Transport boundary:** a symmetric `Gamma` family gives point identification, sharp partial identification and unrestricted non-identification in the two-channel proxy case, with a reference-invariant breakdown factor.
4. **Operational consequences:** distinguish channel anchors from calibration anchors and preserve the exact joint coupling when reporting structural uncertainty.

The paper does not require RACH/NOV/G2, a claim of new identifiability algebra, a universal multiplicative ecology, or an intrinsic ranking of molecular versus field evidence.

## Claim escalation stop rule

A sentence should not enter the abstract, proposal or Discussion as a general ecological statement unless it has one of the following forms:

- directly supported by the literature audit;
- an exact theorem under an explicitly stated observation map;
- an operational consequence logically derived from those theorems; or
- clearly labelled as a Perspective-level proposal rather than an established universal fact.
