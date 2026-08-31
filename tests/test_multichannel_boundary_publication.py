from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str):
    spec = spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_multichannel_anchor_figure_writes_png(tmp_path):
    module = _load_module(
        ROOT / "paper" / "make_multichannel_anchor_figure.py",
        "multichannel_anchor_figure",
    )
    output = tmp_path / "multichannel_anchor_dimension.png"
    written = module.build_figure(output)
    assert written == output
    assert output.exists()
    assert output.stat().st_size > 0


def test_submission_manuscript_contains_conceptual_and_quantitative_spine():
    text = (ROOT / "paper" / "boundary_manuscript_submission.md").read_text(encoding="utf-8")
    assert "Mechanistic evidence should be classified by what it identifies" in text
    assert "biological measurement level or proximity" in text
    assert "identification strength" in text
    assert "Theorem N1-k" in text
    assert "k - 1 - r" in text
    assert "S_m = V_m E_m" in text
    assert "sum_m V_mE_m" in text
    assert "Channel anchors" in text
    assert "Calibration anchors" in text


def test_mechanistic_evidence_governance_keeps_two_axes_and_scope_guard():
    text = (ROOT / "paper" / "mechanistic_evidence_identification_axis.md").read_text(
        encoding="utf-8"
    )
    assert "mechanistic proximity" in text
    assert "identification strength" in text
    assert "molecular and genomic measurements can provide mechanistic proximity" in text
    assert "field observations need not remain merely descriptive" in text
    assert "Do not write:" in text


def test_two_paper_governance_routes_izu_core_questions_separately():
    text = (ROOT / "paper" / "TWO_PAPER_STRATEGY.md").read_text(encoding="utf-8")
    assert "signed functional starting position" in text
    assert "pollination motivation belongs in Paper A" in text
    assert "Channel anchors" in text
    assert "Calibration anchors" in text


def test_ecology_letters_proposal_stays_within_300_words_and_keeps_two_axes():
    text = (ROOT / "paper" / "ecology_letters_perspective_proposal.md").read_text(
        encoding="utf-8"
    )
    proposal = text.split("## Proposal", 1)[1].split("## Venue-fit notes", 1)[0].strip()
    words = proposal.split()
    assert len(words) <= 300
    assert "proximity to biological machinery" in proposal
    assert "identification among competing mechanisms" in proposal
    assert "k-1-r" in proposal
    assert "Gamma" in proposal
    assert "seed dispersal" in proposal
    assert "two axes" in proposal
