"""Submission guards for current resolvability versus evidence gain."""
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
README = ROOT / "README.md"
PUBLIC_API = ROOT / "causal_model" / "admissible_mechanisms.py"
WITNESS = "causal_model/prior_evidence_separation_witness.py"


def test_manuscript_separates_current_state_from_evidence_attribution():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    for marker in (
        "A separate distinction concerns **attribution**",
        "positive `R` is therefore not, by itself, the amount of information supplied by the observations",
        "refer to `R` as **current resolvability**",
        "candidate `V(Q)` is already an **incremental** information quantity",
        "prior-concentrated current region can have `R>0` while a mechanism-independent candidate has `V(Q)=0`",
        "Current resolvability and evidence gain are likewise distinct",
    ):
        assert marker in text, marker


def test_foundations_state_baseline_relative_information_identity():
    text = FOUNDATIONS.read_text(encoding="utf-8")
    for marker in (
        "## Proposition 9 — current resolvability is not evidence attribution",
        "R_{B,o} is an **absolute current-state concentration measure",
        "Delta_R(o)",
        "E_O[Delta_R(O)]",
        "I(S;O|B)/K",
        "Prior sensitivity of candidate ranking",
        "Use `R` to describe **how concentrated the current declared mechanism distribution is**",
    ):
        assert marker in text, marker


def test_si_reports_prior_evidence_audit_and_claim_guard():
    text = SI.read_text(encoding="utf-8")
    for marker in (
        "### S4.5 Current resolvability versus evidence-gain audit",
        "R=1-H_2(0.9)=0.5310.",
        "direct observation of `S` | 0.468996 bit | 0.4690 | 1.0000",
        "mechanism-independent noise | 0.000000 bit | 0.0000 | 0.5310",
        "Under `P(A=1)=0.5, P(B=1)=0.9`, `observe_A` ranks first",
        "after swapping these prior concentrations, `observe_B` ranks first",
        "not part of frozen G2 performance evidence",
    ):
        assert marker in text, marker


def test_readme_separates_current_resolvability_from_incremental_information():
    text = README.read_text(encoding="utf-8")
    for marker in (
        "`R` summarizes the concentration of the current declared mechanism distribution",
        "does not by itself attribute that concentration to the observations",
        "`V(Q)` is incremental conditional information",
    ):
        assert marker in text, marker


def test_public_api_docstring_does_not_call_R_data_information_gain():
    text = PUBLIC_API.read_text(encoding="utf-8")
    for marker in (
        "Return current normalized mechanism concentration",
        "must not be interpreted by itself as",
        "Evidence attribution requires an",
        "Candidate observation value is",
        "incremental conditional mutual information",
    ):
        assert marker in text, marker


def test_reviewer_objection_blocks_prior_as_evidence_overclaim():
    text = REVIEWER.read_text(encoding="utf-8")
    for marker in (
        "Could I get high R just by choosing a strong prior?",
        "Positive `R` describes concentration of the **current declared mechanism distribution**",
        "positive baseline `R` is prior concentration, not data evidence",
        "Candidate rankings can also be prior-sensitive",
        "do not label it “information gained from data” without a baseline contrast",
    ):
        assert marker in text, marker


def test_submission_manifest_classifies_prior_witness_as_validation_not_frozen_result():
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


def test_reviewer_bundle_contains_and_executes_prior_evidence_witness():
    text = BUNDLE.read_text(encoding="utf-8")
    assert f'"{WITNESS}"' in text
    assert "from causal_model.prior_evidence_separation_witness import (" in text
    assert "def test_prior_evidence_separation_witness():" in text
    assert "result.baseline_resolvability == 0.531" in text
    assert "result.signal_information_bits == 0.468996" in text
    assert "result.noise_value == 0.0" in text
    assert "def test_prior_ranking_sensitivity_witness():" in text
    assert 'result.first_best == "observe_A"' in text
    assert 'result.second_best == "observe_B"' in text
