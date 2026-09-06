"""Prevent candidate metadata from silently redefining the scientific target."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_question_target_is_shared_and_not_candidate_target_switch_metadata():
    text = (ROOT / "docs" / "question_target_metadata_guard.md").read_text(encoding="utf-8")
    for marker in (
        "T = tau(S)",
        "CandidateObservation.target_switches",
        "does **not** define this target",
        "one fixed `target_columns` declaration",
        "Changing the target partition is a change in the scientific question/model",
    ):
        assert marker in text, marker
