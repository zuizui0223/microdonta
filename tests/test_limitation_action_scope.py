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
SYNERGY_MODULE = "causal_model/zero_singleton_synergy_witness.py"


def test_limitation_action_theory_preserves_key_distinctions():
    text = THEORY.read_text(encoding="utf-8")
    for marker in (
        "Proposition L1 — complete singleton coverage gives a one-step dichotomy",
        "Proposition L2 — incomplete predictive coverage blocks global singleton claims",
        "Proposition L4 — budget limitation is orthogonal to epistemic recommendation",
        "Proposition L5 — declared target resolution is weaker than full mechanism resolution",
        "Proposition L7 — zero singleton information does not imply zero sequence information",
        "Proposition L8 — joint zero information licenses a sequence-level information limit",
        "a non-estimable candidate has zero information",
        "zero singleton values imply sequence-level information impossibility",
        "make the logical status of `limitations -> next action` explicit",
    ):
        assert marker in text, marker


def test_reporting_note_calls_it_internal_prototype_and_limits_greedy_claims():
    text = NOTE.read_text(encoding="utf-8")
    for marker in (
        "**internal MROD prototype.**",
        "Compatibility fallbacks remain a separate operational layer",
        "Budget is deliberately not a candidate-information label",
        "one-step/myopic stop only",
        "sequence-information limit for the declared candidate vector",
        "I(S;Q1,Q2)=1 bit",
        "positive joint information identifies the best acquisition order",
    ):
        assert marker in text, marker


def test_prototype_is_not_public_or_submission_evidence():
    public_text = PUBLIC_INIT.read_text(encoding="utf-8")
    assert "limitation_action_report" not in public_text
    assert "build_limitation_action_report" not in public_text
    assert "zero_singleton_synergy_witness" not in public_text

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    flattened = json.dumps(manifest, sort_keys=True)
    assert MODULE not in flattened
    assert SYNERGY_MODULE not in flattened

    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    assert "limitation_action_report" not in manuscript
    assert "partial_prediction_limited" not in manuscript
    assert "zero_singleton_synergy_witness" not in manuscript
