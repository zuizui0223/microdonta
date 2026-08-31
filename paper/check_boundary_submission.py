"""Submission-facing checks for the boundary-paper candidate.

This checker is intentionally separate from the frozen MEE submission gate. It
validates the current Ecology Letters Perspective route without changing the
RACH methods-paper evidence boundary.
"""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper/boundary_manuscript_submission.md"
PROPOSAL = ROOT / "paper/ecology_letters_perspective_proposal.md"
PROPOSAL_EMAIL = ROOT / "paper/ecology_letters_perspective_email.md"
EDITORIAL_AUDIT = ROOT / "paper/EL_PERSPECTIVE_EDITORIAL_AUDIT.md"
EVIDENCE_AXIS = ROOT / "paper/mechanistic_evidence_identification_axis.md"
LITERATURE_AUDIT = ROOT / "paper/mechanistic_evidence_literature_audit.md"
STRATEGY = ROOT / "paper/TWO_PAPER_STRATEGY.md"

WORD_RE = re.compile(r"\b[\w*<>/=+.-]+\b", re.UNICODE)


def section(text: str, heading: str, next_heading_prefix: str = "## ") -> str:
    marker = f"## {heading}"
    if marker not in text:
        raise SystemExit(f"missing section: {marker}")
    tail = text.split(marker, 1)[1]
    pieces = tail.split(f"\n{next_heading_prefix}", 1)
    return pieces[0].strip()


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"missing {label}: {token}")


def forbid(text: str, token: str, label: str) -> None:
    if token.lower() in text.lower():
        raise SystemExit(f"forbidden {label}: {token}")


def normalized(text: str) -> str:
    return " ".join(text.split())


def main() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    proposal = PROPOSAL.read_text(encoding="utf-8")
    proposal_email = PROPOSAL_EMAIL.read_text(encoding="utf-8")
    editorial_audit = EDITORIAL_AUDIT.read_text(encoding="utf-8")
    evidence_axis = EVIDENCE_AXIS.read_text(encoding="utf-8")
    literature_audit = LITERATURE_AUDIT.read_text(encoding="utf-8")
    strategy = STRATEGY.read_text(encoding="utf-8")

    abstract = section(manuscript, "Abstract")
    abstract_words = word_count(abstract)
    if abstract_words > 200:
        raise SystemExit(
            f"Ecology Letters Perspective abstract exceeds 200 words: {abstract_words}"
        )

    proposal_body = proposal.split("## Proposal", 1)[1].split("## Venue-fit notes", 1)[0].strip()
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", proposal_body) if part.strip()]
    if len(paragraphs) != 1:
        raise SystemExit(
            f"Ecology Letters Perspective proposal must be one paragraph; found {len(paragraphs)}"
        )
    proposal_body = paragraphs[0]
    proposal_words = word_count(proposal_body)
    if proposal_words > 300:
        raise SystemExit(
            f"Ecology Letters Perspective proposal exceeds 300 words: {proposal_words}"
        )

    # Conceptual headline plus the quantitative and operational consequences.
    for token, label in (
        ("These properties need not coincide", "two-axis problem statement"),
        ("proximity to biological machinery", "mechanistic-proximity axis"),
        ("identification axis", "identification-strength axis"),
        ("k-1-r", "quantitative anchor consequence"),
        ("breakdown factor", "calibration consequence"),
        ("cannot be reported independently", "joint reporting consequence"),
        ("seed dispersal", "independent cross-domain architecture"),
        ("field experiments and ecological genomics", "cross-level conceptual support"),
        ("before any estimator is chosen", "Perspective-vs-Method distinction"),
        ("distinct dimensions", "explicit non-equivalence of evidence axes"),
        ("The author works on ecological measurement", "author qualification"),
    ):
        require(proposal_body, token, label)

    for token in (
        "RACH-SEQ",
        "NOV(Q)=I(S;Q",
        "83.5-fold",
        "g2_frozen",
        "orthogonal axes",
        "ecology formally endorses",
    ):
        forbid(proposal_body, token, "forbidden Perspective-proposal framing")

    # The send-ready email must target both current Editorial Office addresses
    # and carry the exact current proposal prose rather than a stale copy.
    require(proposal_email, "ecolets@cefe.cnrs.fr", "first Editorial Office recipient")
    require(proposal_email, "ecolets2@cefe.cnrs.fr", "second Editorial Office recipient")
    if normalized(proposal_body) not in normalized(proposal_email):
        raise SystemExit("send-ready email does not contain the current proposal text")

    # Preserve the explicit editorial risk audit as part of the send gate.
    for token in (
        "Why is this a Perspective rather than a Method?",
        "What is genuinely new if the algebra is elementary?",
        "Is the scope broad enough for general ecology?",
        "Are we inventing a straw-man pattern-to-molecule hierarchy?",
        "Does this attack molecular or genomic ecology?",
        "Are the two axes really “orthogonal”?",
        "What changes for a field ecologist tomorrow?",
        "Is this just causal-inference relabelling?",
    ):
        require(editorial_audit, token, "editorial desk-rejection audit")

    # The conceptual governance note must retain both the positive claim and the
    # scope guard against ranking biological levels intrinsically.
    for token in (
        "Mechanistic evidence should be classified partly by what it identifies",
        "Measurement level and identification strength are distinct properties",
        "No monotone relation between these axes is assumed",
        "molecular and genomic measurements can provide mechanistic proximity",
        "field observations need not remain merely descriptive",
    ):
        require(evidence_axis, token, "mechanistic-evidence governance")
    forbid(evidence_axis, "orthogonal properties", "overstrong axis-independence claim")

    # The source audit must explicitly carry the two-sided literature position.
    for token in (
        "does not justify claiming that ecology formally endorses a universal one-dimensional hierarchy",
        "genomic data alone are not sufficient",
        "Field-level evidence can become mechanistic through observation design",
        "Avoid orthogonal as the primary adjective",
    ):
        require(literature_audit, token, "mechanistic-evidence literature audit")

    # Boundary-paper scientific and conceptual spine.
    for token, label in (
        ("Mechanistic evidence should be evaluated by what it identifies", "conceptual headline"),
        ("two **distinct** axes", "distinct evidence axes"),
        ("No monotone relation between these axes is assumed", "non-monotone scope guard"),
        ("Theorem N1-k", "k-channel theorem"),
        ("k - 1 - r", "anchor dimension rule"),
        ("1/Gamma <= kappa <= Gamma", "Gamma transport family"),
        ("Gamma*=max(rho_hat,1/rho_hat)", "breakdown factor"),
        ("Design Rule 2", "joint-set reporting rule"),
        ("Channel anchors", "channel-anchor distinction"),
        ("Calibration anchors", "calibration-anchor distinction"),
        ("S_m = V_m E_m", "pollination effective-service example"),
        ("Figure 1. Biological proximity and identification strength are distinct dimensions", "conceptual first figure"),
        ("Figure 2. Direct channel measurements reduce the unresolved dimension", "multichannel figure"),
        ("Figure 3. Calibration transport determines identification strength", "Gamma figure"),
        ("Correia, H.E., Dee, L.E. & Ferraro, P.J. 2025", "intermediary-process reference"),
        ("Smith, J.A., Suraci, J.P., Hunter, J.S. et al. 2020", "field-mechanism reference"),
        ("Siegel, K. & Dee, L.E. 2025", "observational causal-design reference"),
    ):
        require(manuscript, token, label)

    # Reject regressions to either extreme: molecular-level triumphalism or an
    # anti-molecular framing that the Perspective does not support.
    for token in (
        "molecular data are not mechanistic",
        "genomics cannot identify mechanisms",
        "biological scale is irrelevant",
        "two orthogonal axes",
        "ecology has adopted a formal one-dimensional hierarchy",
    ):
        forbid(manuscript, token, "intrinsic biological-level ranking or overclaim")

    # The boundary candidate must not become a second copy of the RACH methods paper.
    for token in (
        "RACH-SEQ",
        "NOV(Q)=I(S;Q",
        "83.5-fold",
        "g2_frozen",
    ):
        forbid(manuscript, token, "RACH/MEE primary claim in boundary manuscript")

    require(strategy, "## Paper A — channel-identifiability boundary", "Paper A separation marker")
    require(strategy, "## Paper B — RACH observation-selection method", "Paper B separation marker")

    print("boundary submission format OK")
    print("candidate venue: Ecology Letters Perspective")
    print(f"abstract words: {abstract_words}")
    print(f"proposal words: {proposal_words}")
    print("proposal paragraphs: 1")
    print("proposal email recipients: 2")
    print("mechanistic evidence axes: distinct/non-monotone")
    print("mechanistic evidence literature audit: pass")
    print("paper separation: pass")


if __name__ == "__main__":
    main()
