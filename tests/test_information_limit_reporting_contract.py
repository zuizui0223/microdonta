"""Submission guards for prediction, one-step and sequence-limit wording."""
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


def test_active_surfaces_separate_prediction_from_complete_singleton_coverage():
    required = {
        "readme": ("prediction-limited", "every declared remaining singleton candidate is estimable"),
        "theory": ("Prediction limit", "every declared remaining singleton candidate is estimable"),
        "tutorial": ("prediction-limited", "every declared remaining singleton candidate is estimable"),
        "mainline": ("prediction-limited", "every declared remaining singleton candidate is estimable"),
        "si": ("prediction limit", "every declared remaining singleton candidate has an estimable predictive partition"),
        "manuscript": ("prediction-limited", "every declared remaining singleton candidate"),
    }
    for name, markers in required.items():
        text = SURFACES[name].read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, f"{name}: {marker}"


def test_active_surfaces_label_all_zero_singletons_as_one_step_not_sequence_impossibility():
    required = {
        "readme": ("validated one-step information stop", "Zero singleton values alone are not sufficient"),
        "theory": ("Validated one-step information stop", "Zero singleton values alone are insufficient"),
        "tutorial": ("validated one-step information stop", "do **not** promote that one-step stop"),
        "mainline": ("validated one-step information stop", "zero singleton values do **not** prove sequence-level impossibility"),
        "si": ("validated one-step information stop", "zero singleton values alone"),
        "manuscript": ("validated one-step information stop", "zero singleton values alone"),
    }
    for name, markers in required.items():
        text = SURFACES[name].read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, f"{name}: {marker}"


def test_active_surfaces_require_joint_zero_for_sequence_information_limit():
    for name, path in SURFACES.items():
        text = path.read_text(encoding="utf-8")
        assert "sequence-information limit" in text, name
        assert "I(S;Q_C" in text, name


def test_active_surfaces_do_not_use_old_overclaims():
    forbidden = (
        "every available verified candidate has zero current information value",
        "all available validated values are zero",
        "complete declared candidate vocabulary contains no expected information",
    )
    for name, path in SURFACES.items():
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{name}: {phrase}"
