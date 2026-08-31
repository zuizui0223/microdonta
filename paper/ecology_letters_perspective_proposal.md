# Ecology Letters Perspective proposal

Status: pre-submission proposal candidate. Current Ecology Letters guidance requires an unsolicited Perspective proposal to be one paragraph, no more than 300 words, describing the nature and novelty of the work and its contribution to the discipline before a full manuscript is considered. The journal's editorial guidance also recommends stating the qualifications of the proposed author(s).

## Proposed title

**Mechanistic evidence needs an identification axis: measurement boundaries in ecological chains**

## Proposal

Across ecology, *mechanistic* can refer both to measurements close to biological machinery and to evidence that distinguishes among competing process explanations. These properties need not coincide. A molecular signature can be mechanistically proximal yet remain compatible with several explanations, whereas a simple field measurement can be strongly discriminating when alternatives predict different outcomes. We propose a Perspective that adds an explicit identification axis to mechanistic evidence and makes it operational before any estimator is chosen. For a positive `k`-stage product `W=prod_j F_j`, net-only observation leaves `k-1` product-preserving degrees of freedom; `r` independent direct channel anchors leave `k-1-r`, so measurement effort can be matched explicitly to desired identification strength. In common proxy comparisons `X_i=q_iF_i`, a symmetric transport bound `1/Gamma <= q_1/q_0 <= Gamma` yields a sharp joint identified set and a reference-invariant breakdown factor, showing how much calibration failure overturns a directional conclusion and why channel uncertainties coupled by one calibration ratio cannot be reported independently. Pollination supplies an immediate rate-by-effectiveness example, seed dispersal an independent quantity-by-quality architecture, and field experiments and ecological genomics illustrate why biological level alone does not determine inferential strength. The article therefore treats biological proximity and identification strength as distinct dimensions of mechanistic evidence and derives field-design and reporting rules from the latter. The author works on ecological measurement and pollination-focused study design and has developed the tested open-source implementation used to instantiate these results.

## Venue-fit notes

- Perspective proposal, not a full direct submission.
- The conceptual headline is `mechanistic proximity != mechanistic identification`.
- Do not claim that ecology formally endorses a universal field-to-molecule hierarchy; separate two legitimate uses of “mechanistic”.
- Keep the pitch broad across ecology; pollination is the lead example, not the scope boundary.
- The quantitative hook is the `k-1-r` equivalence-dimension rule plus the `Gamma` transport family.
- The Perspective-vs-Method distinction is explicit: the claim changes how ecological evidence is classified before estimator choice; code is an instantiation, not the primary contribution.
- Do not attack molecular ecology. Molecular/genomic measurements can be proximal and highly informative; proximity simply does not guarantee identification among the alternatives under study.
- The proposal itself must remain one paragraph.
- A conceptual figure should show biological measurement level and identification strength as distinct axes; no statistical independence or monotone relation is implied.
