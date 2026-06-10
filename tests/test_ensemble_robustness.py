"""Tests for ensemble robust/sensitive classification and NOV linkage.

Covers:
* ``classify_switch_robustness`` — robust vs prior/ε-sensitive verdict per switch
  with the ON / OFF / indeterminate directional call.
* ``sensitive_switches`` — names of the switches flagged for additional
  observation.
* ``next_observation_value(..., sensitive_switches=...)`` — candidates that
  target a sensitive switch are marked and sorted ahead of equal-gain
  candidates that only target already-robust switches.
"""
from __future__ import annotations

import sys
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from causal_model.ensemble import (
    EnsembleResult,
    classify_switch_robustness,
    sensitive_switches,
    select_best_ensemble_setting,
    best_config,
)
from causal_model.causal_admissibility import (
    next_observation_value,
    CandidateObservation,
)
from causal_model.switch_inference import BiologicalSwitch


def _ensemble():
    # S1: robust ON (high CA_j, tiny swing)
    # S2: prior/ε sensitive (CA_j swings across configs)
    # S3: robust OFF (low CA_j, tiny swing)
    return [
        EnsembleResult("p1", "r1", 0.8, 30, 100, 0.5, 0.60,
                       {"S1": 0.95, "S2": 0.20, "S3": 0.05}, 3),
        EnsembleResult("p1", "r2", 0.7, 40, 100, 0.4, 0.70,
                       {"S1": 0.92, "S2": 0.75, "S3": 0.08}, 3),
        EnsembleResult("p2", "r1", 0.8, 25, 100, 0.5, 0.55,
                       {"S1": 0.90, "S2": 0.55, "S3": 0.04}, 3),
    ]


def test_classify_switch_robustness_calls():
    rob = {r.switch: r for r in classify_switch_robustness(_ensemble())}

    assert rob["S1"].is_robust and rob["S1"].call == "ON"
    assert rob["S3"].is_robust and rob["S3"].call == "OFF"
    assert not rob["S2"].is_robust          # sensitivity_range >= 0.20
    assert "sensitive" in rob["S2"].verdict


def test_classify_switch_robustness_sorted_sensitive_first():
    rob = classify_switch_robustness(_ensemble())
    # Most-sensitive switch sorts first so it surfaces as the NOV target.
    assert rob[0].switch == "S2"


def test_sensitive_switches_returns_only_sensitive():
    assert sensitive_switches(_ensemble()) == ["S2"]


def test_select_best_ensemble_setting_is_best_config_alias():
    assert select_best_ensemble_setting is best_config
    best = select_best_ensemble_setting(_ensemble(), min_accepted=20)
    assert best is not None
    assert best.R_RACH == max(r.R_RACH for r in _ensemble())


def test_empty_ensemble_is_safe():
    assert classify_switch_robustness([]) == []
    assert sensitive_switches([]) == []


# ---------------------------------------------------------------------------
# NOV ↔ sensitive switch linkage
# ---------------------------------------------------------------------------

def _switches():
    return [
        BiologicalSwitch(name="S1", pathway_key="S1", description="",
                         biological_question="", prior_on_prob=0.5),
        BiologicalSwitch(name="S2", pathway_key="S2", description="",
                         biological_question="", prior_on_prob=0.5),
    ]


def _rows():
    return [
        {"S1": True,  "S2": True},
        {"S1": True,  "S2": False},
        {"S1": False, "S2": True},
        {"S1": False, "S2": False},
    ]


def _candidates():
    return [
        CandidateObservation(name="measure_S1", description="d",
                             target_switches=["S1"], rationale="r1"),
        CandidateObservation(name="measure_S2", description="d",
                             target_switches=["S2"], rationale="r2"),
    ]


def test_nov_marks_sensitive_targets():
    res = next_observation_value(_rows(), _switches(),
                                 candidates=_candidates(),
                                 sensitive_switches=["S2"])
    by_name = {r.candidate: r for r in res}
    assert by_name["measure_S2"].targets_sensitive_switch is True
    assert by_name["measure_S2"].sensitive_targets == ["S2"]
    assert by_name["measure_S1"].targets_sensitive_switch is False
    assert by_name["measure_S1"].sensitive_targets == []


def test_nov_sorts_sensitive_target_first_on_tie():
    res = next_observation_value(_rows(), _switches(),
                                 candidates=_candidates(),
                                 sensitive_switches=["S2"])
    # Equal gain → the sensitive-targeting candidate must come first.
    assert res[0].candidate == "measure_S2"


def test_nov_without_sensitive_arg_unchanged():
    res = next_observation_value(_rows(), _switches(), candidates=_candidates())
    for r in res:
        assert r.targets_sensitive_switch is False
        assert r.sensitive_targets == []
