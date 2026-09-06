"""Submission guards for validated information-limit and prediction-limit wording."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACES = {
    "readme": ROOT / "README.md",
    "theory": ROOT / "docs" / "mechanism_resolution_theory.md",
    "tutorial": ROOT / "docs" / "tutorial.md",
    "mainline": ROOT / "docs" / "mainline.md",
    "si": ROOT / "paper" / "supporting_information.md",
    "manuscript": ROOT / "paper" / "manuscript.md",
}


def test_active_surfaces_require_complete_candidate_coverage_for_information_limit():
    required = {
        "readme": (
            "every declared remaining candidate is estimable",
            "prediction-limited",
        ),
        "theory": (
            "every declared remaining candidate has an estimable validated value",
            "Prediction limit",
        ),
        "tutorial": (
            "every declared remaining candidate has an estimable validated value",
            "prediction-limited",
        ),
        "mainline": (
            "every declared remaining candidate is estimable",
            "prediction-limited",
        ),
        "si": (
            "every declared remaining candidate has an estimable predictive partition",
            "prediction limit",
        ),
        "manuscript": (
            "every declared remaining candidate",
            "prediction-limited",
        ),
    }
    for name, markers in required.items():
        text = SURFACES[name].read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, f"{name}: {marker}"


def test_active_surfaces_do_not_equate_verified_subset_zero_with_full_vocabulary_limit():
    forbidden = (
        "every available verified candidate has zero current information value",
        "all available validated values are zero",
    )
    for name, path in SURFACES.items():
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{name}: {phrase}"
