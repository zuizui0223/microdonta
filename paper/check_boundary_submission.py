"""Submission-facing checks for the boundary-paper candidate.

This checker is intentionally separate from the frozen MEE submission gate.  It
validates the current Ecology Letters Perspective route without changing the
RACH methods-paper evidence boundary.
"""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper/boundary_manuscript_submission.md"
PROPOSAL = ROOT / "paper/ecology_letters_perspective_proposal.md"
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


def main() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    proposal = PROPOSAL.read_text(encoding="utf-8")
    strategy = STRATEGY.read_text(encoding="utf-8")

    abstract = section(manuscript, "Abstract")
    abstract_words = word_count(abstract)
    if abstract_words > 200:
        raise SystemExit(
            f"Ecology Letters Perspective abstract exceeds 200 words: {abstract_words}"
        )

    proposal_body = proposal.split("## Proposal", 1)[1].split("## Venue-fit notes", 1)[0]
    proposal_lines = proposal_body.strip().splitlines()
    if proposal_lines and proposal_lines[0].startswith("(") and proposal_lines[0].endswith(")"):
        proposal_body = "\n".join(proposal_lines[1:])
    proposal_words = word_count(proposal_body)
    if proposal_words > 300:
        raise SystemExit(
            f"Ecology Letters Perspective proposal exceeds 300 words: {proposal_words}"
        )

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
    print("paper separation: pass")


if __name__ == "__main__":
    main()
