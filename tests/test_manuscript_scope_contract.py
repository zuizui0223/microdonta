"""Submission guard for the observation-limit / next-observation boundary."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper" / "manuscript.md"
COVER = ROOT / "paper" / "cover_letter_draft.md"


def test_manuscript_separates_neighboring_inferential_targets():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    required = (
        "Rejecting a designated null hypothesis",
        "Small residual error, or even exact fit",
        "Additional replication can reduce sampling uncertainty",
        "Counterfactual causal identification is different again",
        "Q = h(O)",
        "I(S;Q | O=o) = 0",
        "The converse is false",
        "mechanism projection",
        "A limitation is no longer only a disclaimer",
    )
    for marker in required:
        assert marker in text, marker


def test_manuscript_does_not_overclaim_structural_novelty_as_mechanism_value():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    assert "Structural novelty is therefore a necessary screen" in text
    assert "not a replacement for mechanism-targeted value" in text
    assert "MROD retains `I(S;Q|A_epsilon)/K` as the operative criterion" in text


def test_cover_letter_uses_limitation_to_observation_decision_frame():
    text = COVER.read_text(encoding="utf-8")
    assert "several mechanisms remain compatible" in text
    assert "quantitative observation decision rather than a generic call for more data" in text
    assert "structural novelty is not enough" in text
