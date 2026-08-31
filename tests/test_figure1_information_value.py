from pathlib import Path

from causal_model.confound_demo import _binary_threshold_information_value


def test_binary_threshold_information_value_is_exact_for_a_partition():
    rows = [
        {"A": False, "pop_trait": 0.1},
        {"A": False, "pop_trait": 0.2},
        {"A": True, "pop_trait": 0.8},
        {"A": True, "pop_trait": 0.9},
    ]
    value, probability_low, reason = _binary_threshold_information_value(
        rows, ["A"], "pop_trait", 0.5
    )
    assert reason == ""
    assert probability_low == 0.5
    assert value == 1.0


def test_binary_threshold_information_value_fails_closed_on_missing_prediction():
    rows = [
        {"A": False, "pop_trait": 0.1},
        {"A": True},
    ]
    value, probability_low, reason = _binary_threshold_information_value(
        rows, ["A"], "pop_trait", 0.5
    )
    assert value is None
    assert probability_low is None
    assert "missing numeric prediction" in reason


def test_figure1_generator_has_no_retired_display_vocabulary_or_heuristic_score():
    text = Path("causal_model/confound_demo.py").read_text(encoding="utf-8")
    assert "next_observation_value" not in text
    assert "RACH degeneracy" not in text
    assert "expected ΔR (NOV)" not in text
    assert "V(Q)=I(S;Q | A_epsilon)/K" in text
    assert "pre-outcome threshold" in text
