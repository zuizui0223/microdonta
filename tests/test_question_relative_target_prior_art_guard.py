"""Claim-ceiling guard for question-relative mechanism targets."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_question_relative_target_audit_concedes_standard_information_theory():
    text = (ROOT / "docs" / "question_relative_target_prior_art_guard.md").read_text(encoding="utf-8")
    for marker in (
        "standard information theory",
        "H(T|A) <= H(S|A)",
        "I(T;Q|A) <= I(S;Q|A)",
        "does not claim novelty",
        "executable ranking reversal",
    ):
        assert marker in text, marker
