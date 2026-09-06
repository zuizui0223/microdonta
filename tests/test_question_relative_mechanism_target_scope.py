"""Scope guards for the question-relative mechanism-target audit."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "question_relative_mechanism_target.md"
PUBLIC_INIT = ROOT / "causal_model" / "__init__.py"
MANIFEST = ROOT / "paper" / "submission_manifest.json"
MANUSCRIPT = ROOT / "paper" / "manuscript.md"
WITNESS_MODULE = "question_relative_mechanism_target_witness"


def test_question_relative_target_note_contains_theorem_and_claim_ceiling():
    text = DOC.read_text(encoding="utf-8")
    for marker in (
        "T = tau(S)",
        "H(T|A) <= H(S|A)",
        "I(T;Q|A) <= I(S;Q|A)",
        "H(T)=0",
        "H(S)=2 bits",
        "Mechanistic depth is not question-relevant identifying power",
        "Target validity is not supplied by information theory",
        "internal theory / claim-ceiling audit",
    ):
        assert marker in text, marker


def test_question_relative_witness_is_internal_but_existing_target_api_remains_public():
    public_text = PUBLIC_INIT.read_text(encoding="utf-8")
    assert WITNESS_MODULE not in public_text
    # The target-aware layer already exists publicly; this audit must not pretend
    # to invent or remove it.
    assert "target_observation_information_value" in public_text
    assert "target_sequential_observation_design" in public_text

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert WITNESS_MODULE not in json.dumps(manifest, sort_keys=True)

    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    assert "question_relative_mechanism_target_witness" not in manuscript
    assert "T = tau(S)" not in manuscript
