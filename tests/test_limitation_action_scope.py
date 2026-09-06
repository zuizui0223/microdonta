"""Scope guards for the internal limitation-to-action reporting prototype."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEORY = ROOT / "docs" / "limitation_action_theory.md"
NOTE = ROOT / "docs" / "limitation_to_action_reporting.md"
PUBLIC_INIT = ROOT / "causal_model" / "__init__.py"
MANIFEST = ROOT / "paper" / "submission_manifest.json"
MANUSCRIPT = ROOT / "paper" / "manuscript.md"
MODULE = "causal_model/limitation_action_report.py"


def test_limitation_action_theory_preserves_key_distinctions():
    text = THEORY.read_text(encoding="utf-8")
    for marker in (
        "Proposition L1 — validated actionability dichotomy under complete candidate coverage",
        "Proposition L2 — incomplete predictive coverage blocks global actionability claims",
        "Proposition L4 — budget limitation is orthogonal to epistemic recommendation",
        "Proposition L5 — declared target resolution is weaker than full mechanism resolution",
        "a non-estimable candidate has zero information",
        "make the logical status of `limitations -> next action` explicit",
    ):
        assert marker in text, marker


def test_reporting_note_calls_it_internal_prototype():
    text = NOTE.read_text(encoding="utf-8")
    assert "**internal MROD prototype.**" in text
    assert "Compatibility fallbacks remain a separate operational layer" in text
    assert "Budget is deliberately not a candidate-information label" in text


def test_prototype_is_not_public_or_submission_evidence():
    public_text = PUBLIC_INIT.read_text(encoding="utf-8")
    assert "limitation_action_report" not in public_text
    assert "build_limitation_action_report" not in public_text

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    flattened = json.dumps(manifest, sort_keys=True)
    assert MODULE not in flattened

    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    assert "limitation_action_report" not in manuscript
    assert "partial_prediction_limited" not in manuscript
