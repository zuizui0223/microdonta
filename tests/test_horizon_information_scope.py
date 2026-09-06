"""Scope guards for the internal horizon-information diagnostic."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "horizon_information_profile.md"
PUBLIC_INIT = ROOT / "causal_model" / "__init__.py"
MANIFEST = ROOT / "paper" / "submission_manifest.json"
MANUSCRIPT = ROOT / "paper" / "manuscript.md"
MODULE = "causal_model/horizon_information_profile.py"


def test_horizon_note_preserves_internal_claim_ceiling():
    text = DOC.read_text(encoding="utf-8")
    for marker in (
        "Status: **internal audit only**",
        "fixed-bundle horizon",
        "J_1=0",
        "J_2=1",
        "J_|C|=0",
        "first positive bundle size",
        "not the minimum number of steps required by an adaptive policy",
        "controlled claim-ceiling diagnostic",
        "not the publication method",
    ):
        assert marker in text, marker


def test_horizon_audit_is_not_public_or_submission_evidence():
    public_text = PUBLIC_INIT.read_text(encoding="utf-8")
    assert "horizon_information_profile" not in public_text
    assert "HorizonInformationProfile" not in public_text

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert MODULE not in json.dumps(manifest, sort_keys=True)

    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    assert "horizon_information_profile" not in manuscript
    assert "first positive bundle size" not in manuscript
