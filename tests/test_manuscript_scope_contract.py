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


def test_manuscript_concedes_multiple_working_hypotheses_prior_art():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    for marker in (
        "Betini et al. (2017)",
        "Yanco et al. (2020)",
        "pre-data workflow",
        "does not claim to originate multiple-hypothesis reasoning",
        "starting point is later in the inferential cycle",
        "closed-loop combination of these steps for a post-data ecological mechanism target",
    ):
        assert marker in text, marker

    for forbidden in (
        "ecology has no procedure",
        "ecology lacked a procedure",
        "first method to use multiple working hypotheses",
    ):
        assert forbidden not in text.lower(), forbidden


def test_manuscript_does_not_overclaim_structural_novelty_as_mechanism_value():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    assert "Structural novelty is therefore a necessary screen" in text
    assert "not a replacement for mechanism-targeted value" in text
    assert "MROD retains `I(S;Q|A_epsilon)/K` as the operative criterion" in text


def test_cover_letter_uses_post_data_prior_art_frame():
    text = COVER.read_text(encoding="utf-8")
    for marker in (
        "builds on established traditions of multiple working hypotheses",
        "distinct starting point is post-data",
        "potentially non-exclusive admissible mechanism region",
        "pre-data multiple-working-hypotheses workflows",
        "structural novelty is not enough",
    ):
        assert marker in text, marker
