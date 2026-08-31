# Ecology Letters Perspective proposal

Status: pre-submission proposal candidate. Current Ecology Letters guidance requires an unsolicited Perspective proposal to be one paragraph, no more than 300 words, describing the nature and novelty of the work and its contribution to the discipline before a full manuscript is considered. The journal's editorial guidance also recommends stating the qualifications of the proposed author(s).

## Proposed title

**When ecological products hide mechanism: identification and measurement design for ecological chains**

## Proposal

Ecologists often treat precisely measured composite quantities as evidence about the mechanism that produced them—for example visitation × per-visit effectiveness, seed delivery × post-dispersal quality, or endpoint responses connected by partially observed stages. We propose a Perspective arguing that this practice has a structural measurement boundary: a net product can be known exactly while allocation among latent processes remains unidentified. The novelty is not new identifiability algebra, but a quantitative ecological measurement framework that converts this boundary into field-design rules. For a positive `k`-stage product `W=prod_j F_j`, net-only observation leaves `k-1` product-preserving degrees of freedom; `r` independent direct channel anchors leave `k-1-r`, so measurement effort can be matched explicitly to desired identification strength. In common proxy comparisons `X_i=q_iF_i`, a symmetric bound `1/Gamma <= q_1/q_0 <= Gamma` yields a sharp joint identified set and a reference-invariant breakdown factor, showing how much calibration transport failure overturns a directional conclusion and why channel uncertainties coupled by one calibration ratio cannot be reported independently. Pollination is an immediate application—visitation or network degree is not effective service without per-interaction effectiveness—while seed dispersal supplies an independent quantity-by-quality architecture, and the same logic extends to declared multiplicative recruitment and demographic chains. The proposed article therefore reframes composite ecological measurements as equivalence classes and measurement-budget problems, changing what can count as mechanistic evidence before any estimator is chosen. The author works on ecological measurement and pollination-focused study design and has developed the tested open-source implementation used to instantiate these results.

## Venue-fit notes

- Perspective proposal, not a full direct submission.
- Keep the pitch broad across ecology; pollination is the lead example, not the scope boundary.
- The quantitative hook is the `k-1-r` equivalence-dimension rule plus the `Gamma` transport family.
- The Perspective-vs-Method distinction is explicit: the claim changes what ecological observations can identify before estimator choice; code is an instantiation, not the primary contribution.
- Do not sell mathematical depth or invention of identifiability algebra; sell closure from information boundary to field-design and reporting consequences.
- The proposal itself must remain one paragraph.
- A conceptual figure may accompany the proposal if useful: endpoint product -> equivalence dimension -> anchors -> partial/point identification, with the two-channel `Gamma` family as the worked special case.
