"""Claim guards for specification-sensitivity reporting versus robust design."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / "docs" / "tolerance_and_specification_robustness.md"
REVIEWER = ROOT / "paper" / "reviewer_objections.md"


def test_scope_note_concedes_robust_design_prior_art():
    text = NOTE.read_text(encoding="utf-8")
    for marker in (
        "Robust experimental design is not new",
        "Go & Isaac (2022)",
        "Robust Expected Information Gain",
        "does **not** claim to invent robust experimental design",
        "sensitivity-reporting diagnostic, not a new decision-theory optimum",
        "does not silently choose a maximin, averaged, regret-minimizing or robust-EIG replacement",
        "share the **same declared mechanism target `S` and the same candidate-observation vocabulary**",
        "common-best comparisons remain interpretable when the mechanism target or candidate vocabulary itself changes",
    ):
        assert marker in text, marker


def test_reviewer_audit_blocks_robust_design_novelty_overclaim():
    text = REVIEWER.read_text(encoding="utf-8")
    for marker in (
        "Is your specification-robust recommendation just robust Bayesian experimental design?",
        "No new robust-design objective is claimed",
        "Go & Isaac (2022)",
        "B_common = intersection_lambda B_lambda",
        "It does not silently replace the criterion with maximin, model averaging, minimax regret or robust EIG",
        "do not present the common-best set as a new robust optimal-design solution",
        "MROD invented multiple working hypotheses",
        "robust experimental design",
    ):
        assert marker in text, marker
