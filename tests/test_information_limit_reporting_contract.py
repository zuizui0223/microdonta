"""Submission guards for prediction, one-step and sequence-limit wording."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACES = {
    "readme": ROOT / "README.md",
    "conceptual": ROOT / "docs" / "conceptual_scope_mechanism_ambiguity.md",
    "theory": ROOT / "docs" / "mechanism_resolution_theory.md",
    "tutorial": ROOT / "docs" / "tutorial.md",
    "mainline": ROOT / "docs" / "mainline.md",
    "literature": ROOT / "docs" / "literature_comparison.md",
    "si": ROOT / "paper" / "supporting_information.md",
    "manuscript": ROOT / "paper" / "manuscript.md",
}


def _text_lower(name: str) -> str:
    return SURFACES[name].read_text(encoding="utf-8").lower()


def test_active_surfaces_separate_prediction_from_complete_singleton_coverage():
    required = {
        "readme": ("prediction-limited", "every declared remaining singleton candidate is estimable"),
        "conceptual": ("if some declared candidate values are non-estimable, report prediction limitation", "predictive partitions"),
        "theory": ("Prediction limit", "every declared remaining singleton candidate is estimable"),
        "tutorial": ("prediction-limited", "every declared remaining singleton candidate is estimable"),
        "mainline": ("prediction-limited", "every declared remaining singleton candidate is estimable"),
        "literature": ("If candidate predictions are missing, report prediction limitation", "verify singleton candidate predictive partitions"),
        "si": ("prediction limit", "every declared remaining singleton candidate has an estimable predictive partition"),
        "manuscript": ("prediction-limited", "every declared remaining singleton candidate"),
    }
    for name, markers in required.items():
        text = _text_lower(name)
        for marker in markers:
            assert marker.lower() in text, f"{name}: {marker}"


def test_active_surfaces_label_all_zero_singletons_as_one_step_not_sequence_impossibility():
    required = {
        "readme": ("validated one-step information stop", "Zero singleton values alone are not sufficient"),
        "conceptual": ("validated one-step information stop", "do not call that one-step stop a sequence-level impossibility"),
        "theory": ("Validated one-step information stop", "Zero singleton values alone are insufficient"),
        "tutorial": ("validated one-step information stop", "do **not** promote that one-step stop"),
        "mainline": ("validated one-step information stop", "zero singleton values do **not** prove sequence-level impossibility"),
        "literature": ("validated one-step information stop", "does not imply that the full declared candidate vector is uninformative"),
        "si": ("validated one-step information stop", "Zero singleton values alone"),
        "manuscript": ("validated one-step information stop", "Zero singleton values alone"),
    }
    for name, markers in required.items():
        text = _text_lower(name)
        for marker in markers:
            assert marker.lower() in text, f"{name}: {marker}"


def test_active_surfaces_require_joint_zero_for_sequence_information_limit():
    for name in SURFACES:
        text = _text_lower(name)
        assert "sequence-information limit" in text, name
        assert "i(s;q_c" in text, name


def test_active_surfaces_do_not_use_old_overclaims():
    forbidden = (
        "every available verified candidate has zero current information value",
        "all available validated values are zero",
        "complete declared candidate vocabulary contains no expected information",
        "stop when resolved, budget-limited or information-limited",
    )
    for name in SURFACES:
        text = _text_lower(name)
        for phrase in forbidden:
            assert phrase.lower() not in text, f"{name}: {phrase}"
