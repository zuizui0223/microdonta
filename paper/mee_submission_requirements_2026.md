# Methods in Ecology and Evolution submission requirements snapshot

Snapshot checked: **2026-09-05**

Primary source: Methods in Ecology and Evolution Author Guidelines  
`https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines`

Current ethics-policy cross-check: Iossa et al. (2026), *Methods in Ecology and
Evolution* editorial on animal and plant ethics in research, DOI
`10.1111/2041-210x.70290`.

This file records journal requirements enforced locally for the **Mechanism-Resolving Observation Design** submission. It is publication governance, not a scientific protocol.

## Article type

Mechanism-Resolving Observation Design is submitted as a **Research Article**.

The current journal definitions distinguish:

- **Research Articles**: new ecological/evolutionary methods; new computational methods normally include simulation or benchmark testing and should be broadly applicable across taxa/systems; maximum approximately 7,000–8,000 words.
- **Applications**: shorter software/package descriptions focused on uptake of a software implementation.
- **Practical Tools**: short descriptions of new field techniques, hardware, equipment or laboratory protocols.

This submission is an inferential and experimental-design method with a formally defined information objective, adaptive sequential algorithm and controlled truth-peek-free selection benchmark. The software is an implementation of the method, not the sole publication object. A new natural-system dataset is not required for the primary algorithmic claim: the synthetic benchmark is the appropriate validation object because mechanism truth, candidate information and outcome timing are known. `Research Article` is therefore the intended category.

The separate mechanistic-evidence / identification-boundary Perspective is owned by `zuizui0223/boundary`. It is not used to inflate this submission's primary contribution and is not a prerequisite for the MEE submission.

## Initial-submission structure enforced here

The active main manuscript must contain, in this order:

1. Title only (author identity is excluded from the review manuscript).
2. A four-part numbered Abstract (`1`–`4`), no more than 350 words.
3. A Data/Code for peer review statement immediately below the Abstract.
4. No more than eight keywords/short phrases, in alphabetical order.
5. Introduction.
6. Materials and Methods.
7. Results.
8. Discussion.
9. Figure captions.

A separate title-page file contains author names, affiliations, correspondence,
running headline, acknowledgements, author contributions, data availability,
funding and conflict-of-interest information. The current Author Guidelines also
state that a **Statement on inclusion is required during submission**. For this
computational methods paper, the local title page records that the study uses
synthetic benchmarks and does not report place-based empirical research, so
regional stakeholder/place-based inclusion considerations are not applicable.

Fields that require author input (correspondence email, ORCID and final
funding/acknowledgements) remain explicit placeholders and must not be invented.

## Ethics and organism/field-study scope

The 2026 MEE ethics editorial asks authors of methods involving or affecting
organisms or field sites to make the ethical basis of the work explicit. The
present submission reports no new organismal collection, manipulation or field
intervention; its primary validation is synthetic and computational. The title
page therefore carries an explicit not-applicable statement rather than implying
that a biological ethics review was performed.

Any future empirical validation added to this paper would require a fresh ethics
and permits audit before submission; this snapshot does not pre-authorise such an
addition.

## Cover letter

A covering letter is **optional** under the current Author Guidelines. If supplied, it should provide editorially relevant information that is not already present in the manuscript rather than repeat the Abstract.

The local optional cover letter therefore focuses on three editorial points only:

1. why the submission is a Research Article/new computational method rather than a software-only Application;
2. broad applicability of the observation-design framework beyond the worked ecological example;
3. separation from the independent identification-boundary Perspective and availability of a frozen anonymous executable reviewer bundle.

The editor-facing draft is `paper/cover_letter_draft.md`. It is not part of the anonymous reviewer bundle.

## Double-anonymous review

The main manuscript and Supporting Information must not obviously identify the author. The title page is a separate `Supplemental Document Not for Review` submission file. Code/data for review should be supplied in anonymised form. The public archival DOI is minted only after the manuscript/submission files are frozen.

The current Author Guidelines permit initial submission in flexible file formats,
but require a single-column, double-line-spaced review document with continuous
line and page numbering. Code and/or data needed for peer review must be provided
as anonymised files or through a suitable private-for-review archive.

## Code policy

Submitted code must carry an open-source software licence. This repository uses the MIT licence. The anonymous reviewer bundle must preserve the licence while removing unnecessary identifying metadata/links.

## AI-assistance disclosure

The manuscript contains a concise Methods disclosure of interactive ChatGPT assistance and states that all scientific claims, frozen configurations, executed outputs and final text/code were author-reviewed. AI outputs are not treated as observations or independent scientific evidence.

## Current local format status

The validated review manuscript currently satisfies the automated MEE gate:

- Research Article;
- numbered Abstract under 350 words;
- no more than eight keywords;
- separate title page;
- Statement on inclusion present on the title page;
- explicit no-new-organism/no-new-field-work ethics scope statement;
- anonymised main manuscript and Supporting Information;
- methods-only anonymous code-review bundle;
- manuscript length below the Research Article maximum.

The final validated science/package freeze is recorded in `paper/release_readiness.json`.

## Items not enforceable in Markdown

Single-column layout, double line spacing, continuous line numbering and page numbering are properties of the final review document exported for submission. They are checked at document-generation time rather than by the Markdown gate.
