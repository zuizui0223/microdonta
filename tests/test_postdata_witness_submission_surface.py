"""Submission guards for the reviewer-visible post-data reprioritization witness."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SI = ROOT / "paper" / "supporting_information.md"
MANIFEST = ROOT / "paper" / "submission_manifest.json"
BUNDLE = ROOT / "paper" / "build_reviewer_bundle.py"
WITNESS = "causal_model/postdata_reprioritization_witness.py"


def test_si_reports_ranking_reversal_with_claim_guard():
    text = SI.read_text(encoding="utf-8")
    for marker in (
        "### S4.3 Post-data candidate reprioritization witness",
        "`observe_A` | 1.000000 | 0.000000 | 0.5000 | 0.0000",
        "`observe_B_when_A0` | 0.811278 | 1.000000 | 0.4056 | 0.5000",
        "existence witness only",
        "not part of the frozen G2 performance evidence",
    ):
        assert marker in text, marker


def test_submission_manifest_classifies_witness_as_validation_not_frozen_result():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert WITNESS in data["main_text"]["validation"]
    assert WITNESS not in data["supplementary"]["frozen_results"]
    assert data["claim_spine"] == [
        "admissible mechanism region and residual mechanism ambiguity",
        "observation information value equals normalized mechanism-observation mutual information",
        "sequential observation design recomputes and selects maximum current information value",
        "truth-peek-free G2 matched-policy selection validation",
        "reproducible software and reviewer evidence bundle",
    ]


def test_reviewer_bundle_contains_and_executes_witness():
    text = BUNDLE.read_text(encoding="utf-8")
    assert f'"{WITNESS}"' in text
    assert "from causal_model.postdata_reprioritization_witness import evaluate_reprioritization" in text
    assert "def test_postdata_reprioritization_witness():" in text
    assert 'result.prior_best == "observe_A"' in text
    assert 'result.current_best == "observe_B_when_A0"' in text
    assert 'result.prior_information_bits["observe_B_when_A0"] == 0.811278' in text
    assert 'result.current_information_bits["observe_B_when_A0"] == 1.0' in text
