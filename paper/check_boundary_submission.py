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

    # Current proposal guidance plus the desk-rejection audit: nature, novelty,
    # broad disciplinary contribution, author qualification, Perspective-vs-Method
    # distinction, cross-domain scope and direct operational consequences.
    for token, label in (
        ("structural measurement boundary", "nature of proposed Perspective"),
        ("The novelty is a quantitative ecological measurement framework", "positive novelty positioning"),
        ("k-1-r", "quantitative anchor consequence"),
        ("breakdown factor", "calibration consequence"),
        ("cannot be reported independently", "joint reporting consequence"),
        ("seed dispersal", "independent cross-domain architecture"),
        ("before any estimator is chosen", "Perspective-vs-Method distinction"),
        ("The author works on ecological measurement", "author qualification"),
    ):
        require(proposal_body, token, label)

    for token in ("RACH-SEQ", "NOV(Q)=I(S;Q", "83.5-fold", "g2_frozen"):
        forbid(proposal_body, token, "RACH/MEE claim in Perspective proposal")

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
        "What changes for a field ecologist tomorrow?",
    ):
        require(editorial_audit, token, "editorial desk-rejection audit")

    # Boundary-paper scientific spine.
    for token, label in (
        ("Theorem N1-k", "k-channel theorem"),
        ("k - 1 - r", "anchor dimension rule"),
        ("1/Gamma <= kappa <= Gamma", "Gamma transport family"),
        ("Gamma*=max(rho_hat,1/rho_hat)", "breakdown factor"),
        ("Design Rule 2", "joint-set reporting rule"),
        ("Channel anchors", "channel-anchor distinction"),
        ("Calibration anchors", "calibration-anchor distinction"),
        ("S_m = V_m E_m", "pollination effective-service example"),
    ):
        require(manuscript, token, label)

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
    print("proposal editorial audit: pass")
    print("proposal email recipients: 2")
    print("paper separation: pass")


if __name__ == "__main__":
    main()
