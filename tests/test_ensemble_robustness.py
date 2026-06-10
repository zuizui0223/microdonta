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


def test_acceptance_rate_property():
    r = EnsembleResult("p", "r", 0.8, 5, 200, 0.5, 0.6, {"S1": 0.9}, 1)
    assert r.acceptance_rate == 5 / 200
    r0 = EnsembleResult("p", "r", 0.8, 0, 0, 0.5, 0.6, {"S1": 0.9}, 1)
    assert r0.acceptance_rate == 0.0


def test_min_acceptance_rate_rejects_strict_artifact():
    # Config A: high R_RACH but only 3/300 accepted (rate 0.01) -> artefact.
    # Config B: lower R_RACH, 40/200 accepted (rate 0.20) -> stable.
    res = [
        EnsembleResult("strict", "r", 0.95, 3, 300, 0.2, 0.95, {"S1": 1.0}, 1),
        EnsembleResult("stable", "r", 0.70, 40, 200, 0.4, 0.70, {"S1": 0.8}, 1),
    ]
    sel = select_best_ensemble_setting(res, min_accepted=20, min_acceptance_rate=0.02)
    assert sel.passed_filters
    assert sel.best.preset_name == "stable"   # strict config filtered out


def test_max_acceptance_rate_rejects_too_lax():
    res = [
        EnsembleResult("lax", "r", 0.3, 190, 200, 0.1, 0.9, {"S1": 0.9}, 1),
        EnsembleResult("mid", "r", 0.6, 60, 200, 0.3, 0.7, {"S1": 0.8}, 1),
    ]
    sel = select_best_ensemble_setting(res, min_accepted=20,
                                       min_acceptance_rate=0.02,
                                       max_acceptance_rate=0.5)
    assert sel.best.preset_name == "mid"      # lax config (rate 0.95) filtered out


def test_fallback_when_no_config_passes():
    # Both configs have tiny accepted samples below min_accepted.
    res = [
        EnsembleResult("a", "r", 0.9, 3, 100, 0.2, 0.9, {"S1": 1.0}, 1),
        EnsembleResult("b", "r", 0.8, 8, 100, 0.3, 0.8, {"S1": 0.9}, 1),
    ]
    sel = select_best_ensemble_setting(res, min_accepted=20, min_acceptance_rate=0.02)
    assert not sel.passed_filters
    assert sel.best.preset_name == "b"        # least-bad by n_accepted
    assert "least-bad" in sel.rationale
    assert sel.n_eligible == 0


def test_mode_max_accepted():
    res = [
        EnsembleResult("a", "r", 0.9, 30, 200, 0.2, 0.95, {"S1": 1.0}, 1),
        EnsembleResult("b", "r", 0.8, 80, 200, 0.3, 0.80, {"S1": 0.9}, 1),
    ]
    sel = select_best_ensemble_setting(res, min_accepted=20, min_acceptance_rate=0.02,
                                       mode="max_accepted")
    assert sel.best.preset_name == "b"        # largest accepted sample
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


def test_select_best_ensemble_setting_max_R():
    sel = select_best_ensemble_setting(_ensemble(), min_accepted=20,
                                       min_acceptance_rate=0.0)
    assert sel.best is not None
    assert sel.passed_filters
    assert sel.best.R_RACH == max(r.R_RACH for r in _ensemble())
    assert "highest R_RACH" in sel.rationale


def test_best_config_returns_result_only():
    best = best_config(_ensemble(), min_accepted=20)
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
