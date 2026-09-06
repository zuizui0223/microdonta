from pathlib import Path


def test_question_relative_target_summary_keeps_core_witness_visible():
    text = (Path(__file__).resolve().parents[1] / "docs" / "question_relative_target_summary.md").read_text(encoding="utf-8")
    for marker in ("S=(T,U1,U2)", "I(S;Q)=2 bits", "I(T;Q)=0 bits", "H(S)=2", "active MEE estimand"):
        assert marker in text, marker
