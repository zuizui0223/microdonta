# Methods in Ecology and Evolution submission requirements snapshot

Snapshot checked: **2026-08-25**

Primary source: Methods in Ecology and Evolution Author Guidelines
`https://besjournals.onlinelibrary.wiley.com/hub/journal/2041210x/author-guidelines`

This file records the journal requirements that are enforced locally for the
RACH submission. It is publication governance, not a scientific protocol.

## Article type

RACH is submitted as a **Research Article**.

The current journal definitions distinguish:

- **Research Articles**: new ecological/evolutionary methods; new computational
  methods normally include simulation or benchmark testing and should be broadly
  applicable across taxa/systems; maximum approximately 7,000–8,000 words.
- **Applications**: short software/package descriptions, up to about 4,000 words.
- **Practical Tools**: short descriptions of new field techniques, hardware,
  equipment or laboratory protocols, about 3,000–4,000 words.

RACH is an inferential method with mathematical guarantees, controlled
simulation/benchmark validation and an ecological projection. Its software is an
implementation of the method, not the sole publication object. `Research Article`
is therefore the correct category; the earlier working label `Methods / Practical
Tools` is retired.

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
funding and conflict-of-interest information. Fields that require author input
(email, ORCID, final funding/acknowledgements) remain explicit placeholders and
must not be invented.

## Double-anonymous review

The main manuscript and Supporting Information must not obviously identify the
author. The title page is a separate `Not for Review` submission file. Code/data
for review should be supplied in anonymised form. The public archival DOI is
minted only after the manuscript/submission files are frozen.

## Code policy

Submitted code must carry an open-source software licence. This repository uses
the MIT licence. The anonymous reviewer bundle must preserve the licence while
removing unnecessary identifying metadata/links.

## AI-assistance disclosure

The current Author Guidelines require a Methods statement when LLMs or comparable
AI tools contributed to the work, including application name/version, with the
corresponding or senior author taking responsibility for generated text/code.
The RACH manuscript therefore contains a concise disclosure of interactive
ChatGPT assistance and states that all scientific claims, frozen configurations,
executed outputs and final text/code were author-reviewed.

## Items not enforceable in Markdown

Single-column layout, double line spacing, continuous line numbering and page
numbering are properties of the final review document exported for submission.
They are checked at document-generation time rather than by the Markdown gate.
