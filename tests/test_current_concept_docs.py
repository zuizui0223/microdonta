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
        "MROD did not invent",
        "rank gain with positive MROD value",
        "More data never help",
        "Adaptive recomputation always outperforms",
        "management action table or external reward function",
    ):
        assert marker in text, marker
