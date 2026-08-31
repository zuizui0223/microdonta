# Ecology Letters Perspective proposal

Status: pre-submission proposal candidate. Current Ecology Letters guidance requires an unsolicited Perspective proposal to be one paragraph, no more than 300 words, describing the nature and novelty of the work and its contribution to the discipline before a full manuscript is considered. The journal's editorial guidance also recommends stating the qualifications of the proposed author(s).

## Proposed title

**Mechanistic evidence is an identification property: measurement boundaries in ecological chains**

## Proposal

Ecology often treats evidence as if mechanistic strength increases with biological depth, from field patterns toward physiology, genomics and molecular processes. We propose a Perspective arguing that this conflates two different properties: proximity to biological machinery and identification among competing mechanisms. A molecular signature can be mechanistically proximal yet remain compatible with several explanations, whereas a simple field measurement can be strongly mechanistic evidence when it excludes alternatives. The novelty is a quantitative ecological framework that makes this distinction operational before any estimator is chosen. For a positive `k`-stage product `W=prod_j F_j`, net-only observation leaves `k-1` product-preserving degrees of freedom; `r` independent direct channel anchors leave `k-1-r`, so measurement effort can be matched explicitly to desired identification strength. In common proxy comparisons `X_i=q_iF_i`, a symmetric transport bound `1/Gamma <= q_1/q_0 <= Gamma` yields a sharp joint identified set and a reference-invariant breakdown factor, showing how much calibration failure overturns a directional conclusion and why channel uncertainties coupled by one calibration ratio cannot be reported independently. Pollination supplies an immediate rate-by-effectiveness example, seed dispersal an independent quantity-by-quality architecture, and the same observation-map logic applies to declared multiplicative recruitment and demographic chains. The proposed article therefore replaces a one-dimensional hierarchy from “pattern” to “mechanism” with two axes—biological proximity and identification strength—and derives field-design and reporting rules from the latter. The author works on ecological measurement and pollination-focused study design and has developed the tested open-source implementation used to instantiate these results.

## Venue-fit notes

- Perspective proposal, not a full direct submission.
- The conceptual headline is `mechanistic proximity != mechanistic identification`.
- Keep the pitch broad across ecology; pollination is the lead example, not the scope boundary.
- The quantitative hook is the `k-1-r` equivalence-dimension rule plus the `Gamma` transport family.
- The Perspective-vs-Method distinction is explicit: the claim changes how ecological evidence is classified before estimator choice; code is an instantiation, not the primary contribution.
- Do not attack molecular ecology. Molecular/genomic measurements can be proximal and highly informative; proximity simply does not guarantee identification among the alternatives under study.
- The proposal itself must remain one paragraph.
- A conceptual figure should show biological measurement level and identification strength as orthogonal axes; the product/proxy theorems then supply worked quantitative examples.
