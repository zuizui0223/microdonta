"""Submission guards for mechanism-vocabulary normalization and reporting."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper" / "manuscript.md"
SI = ROOT / "paper" / "supporting_information.md"
REVIEWER = ROOT / "paper" / "reviewer_objections.md"
FOUNDATIONS = ROOT / "docs" / "observation_information_foundations.md"
MANIFEST = ROOT / "paper" / "submission_manifest.json"
BUNDLE = ROOT / "paper" / "build_reviewer_bundle.py"
WITNESS = "causal_model/vocabulary_normalization_witness.py"


def test_manuscript_reports_vocabulary_internal_normalization():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    for marker in (
        "The normalization is conditional on the declared mechanism vocabulary",
        "report residual entropy `D` in bits together with `K`",
        "deterministic redundancy cannot change candidate ordering or zero-value status",
        "implementation therefore exposes `mutual_information_bits` alongside normalized `V(Q)`",
        "The `K` normalization is deliberately a bounded reporting scale",
    ):
        assert marker in text, marker


def test_foundations_state_raw_invariance_and_normalized_sensitivity():
    text = FOUNDATIONS.read_text(encoding="utf-8")
    for marker in (
        "## Proposition 8 — vocabulary recoding, redundant coordinates and K-normalization",
        "H(S,U|A)",
        "I((S,U);Q|A)",
        "Normalized magnitudes are vocabulary-internal",
        "Candidate selection is preserved under deterministic redundancy",
        "Do not compare absolute `R` or normalized `V` values across differently encoded mechanism vocabularies",
    ):
        assert marker in text, marker


def test_si_reports_executable_representation_audit():
    text = SI.read_text(encoding="utf-8")
    for marker in (
        "### S4.4 Mechanism-vocabulary normalization audit",
        "raw entropy `H(S)` | 2.0000 bit | 2.0000 bit",
        "normalized `R` | 0.0000 | 0.3333",
        "raw MI `observe_A` | 1.000000 bit | 1.000000 bit",
        "normalized `V(observe_A)` | 0.5000 | 0.3333",
        "candidate ranking | `observe_A` > `observe_A_and_B` | unchanged",
        "not part of frozen G2 performance evidence",
    ):
        assert marker in text, marker


def test_reviewer_objection_blocks_normalized_score_gaming_claims():
    text = REVIEWER.read_text(encoding="utf-8")
    for marker in (
        "Could I inflate resolvability by duplicating a switch?",
        "A duplicate therefore creates neither raw residual mechanism entropy nor raw mechanism–observation information",
        "candidate ranking, zero-value status and positive-value status are preserved",
        "report raw `I(S;Q|A_epsilon)` in bits alongside normalized `V(Q)`",
    ):
        assert marker in text, marker


def test_submission_manifest_classifies_vocabulary_witness_as_validation_not_frozen_result():
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


def test_reviewer_bundle_contains_and_executes_vocabulary_witness():
    text = BUNDLE.read_text(encoding="utf-8")
    assert f'"{WITNESS}"' in text
    assert "from causal_model.vocabulary_normalization_witness import evaluate_vocabulary_normalization" in text
    assert "def test_vocabulary_normalization_witness():" in text
    assert "result.original_entropy_bits == 2.0" in text
    assert "result.redundant_entropy_bits == 2.0" in text
    assert "result.redundant_resolvability == 0.3333" in text
    assert "result.original_information_bits == result.redundant_information_bits" in text
    assert "result.original_ranking == result.redundant_ranking" in text
