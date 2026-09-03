from pathlib import Path

from causal_model.causal_admissibility import causal_resolvability
from causal_model.information_value_calibration_core import evsi_resolvability


class _Switch:
    def __init__(self, name: str):
        self.name = name


def test_quantitative_information_value_is_exact_for_a_verified_partition():
    rows = [
        {"A": False, "test_trait": 0.1},
        {"A": False, "test_trait": 0.2},
        {"A": True, "test_trait": 0.8},
        {"A": True, "test_trait": 0.9},
    ]
    switches = [_Switch("A")]
    r0 = causal_resolvability(rows, switches)

    # Two quantitative bins split the four current admissible rows exactly by A.
    # The observation therefore removes the full one bit of residual mechanism
    # entropy and has normalized information value 1.
    value = evsi_resolvability(
        rows,
        switches,
        "test",
        "trait",
        r0,
        n_bins=2,
    )
    assert r0 == 0.0
    assert value == 1.0


def test_constant_quantitative_candidate_has_zero_information_value():
    rows = [
        {"A": False, "test_trait": 0.5},
        {"A": True, "test_trait": 0.5},
    ]
    switches = [_Switch("A")]
    r0 = causal_resolvability(rows, switches)
    value = evsi_resolvability(rows, switches, "test", "trait", r0, n_bins=2)
    assert value == 0.0


def test_figure1_generator_uses_canonical_module_and_no_retired_vocabulary():
    text = Path("causal_model/controlled_confounding_demo.py").read_text(encoding="utf-8")
    assert "causal_model.confound_demo" not in text
    assert "next_observation_value" not in text
    assert "RACH degeneracy" not in text
    assert "expected ΔR (NOV)" not in text
    assert "V(Q)=I(S;Q|A_epsilon)/K" in text
    assert "six-bin" in text
