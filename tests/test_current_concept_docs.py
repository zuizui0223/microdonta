"""Keep current conceptual documentation aligned with the publication surface."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    ROOT / "docs" / "conceptual_scope_mechanism_ambiguity.md",
    ROOT / "docs" / "boundary_mrod_bridge.md",
    ROOT / "docs" / "literature_comparison.md",
)


def test_current_concept_documents_exist_and_use_mrod_frame():
    for path in DOCS:
        assert path.exists(), path
        text = path.read_text(encoding="utf-8")
        assert "MROD" in text or "Mechanism-Resolving Observation Design" in text, path


def test_current_concept_documents_do_not_restore_retired_publication_branding():
    forbidden = (
        "# Literature comparison and novelty of RACH",
        "Restricted Admissible Causal Hypotheses",
        "RACH-SEQ",
        "NOV(Q)",
        "D_RACH",
        "R_RACH",
    )
    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name}: {token}"


def test_literature_comparison_keeps_claim_ceiling():
    text = (ROOT / "docs" / "literature_comparison.md").read_text(encoding="utf-8")
    for marker in (
        "not that MROD invented EVSI or mutual information",
        "rank gain with positive MROD value",
        "More data never help",
        "Adaptive recomputation always outperforms",
        "management action table or external reward function",
        "Multiple working hypotheses and pre-data hypothesis vetting",
        "Betini et al. (2017)",
        "Yanco et al. (2020)",
        "post-data admissible region",
        "closed-loop connection",
        "MROD invented multiple working hypotheses",
    ):
        assert marker in text, marker


def test_literature_comparison_does_not_claim_ecology_lacked_ambiguity_design_methods():
    text = (ROOT / "docs" / "literature_comparison.md").read_text(encoding="utf-8").lower()
    forbidden = (
        "ecology has no procedure",
        "ecology lacked a procedure",
        "no method for turning ambiguity into design",
        "first method to use multiple working hypotheses",
    )
    for marker in forbidden:
        assert marker not in text, marker
