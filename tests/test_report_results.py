"""Tests for the report generator (issue #26).

Exercises the pure summarisation / markdown functions against small synthetic
CSV fixtures and reconstructed ensemble results — no ABC runs required.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from causal_model.report_results import (
    summarize_benchmark,
    benchmark_summary_md,
    summarize_ensemble,
    ensemble_summary_md,
    results_summary_md,
    _rows_to_ensemble_results,
    EPISTEMIC_CAUTION,
)
from causal_model.ensemble import EnsembleResult


def _write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _make_benchmark_dir(tmp: Path) -> Path:
    d = tmp / "bench"
    _write_csv(d / "known_truth_summary.csv", [
        {"run_id": "a", "true_state_label": "all_off", "noise_rate": 0.0,
         "n_attempts": 100, "accuracy": 0.75, "precision": 0.5, "recall": 1.0,
         "f1": 0.667, "mean_abs_ca_error": 0.2, "R_RACH": 0.6, "D_RACH": 1.6},
        {"run_id": "b", "true_state_label": "S1_only", "noise_rate": 0.1,
         "n_attempts": 100, "accuracy": 0.5, "precision": 0.4, "recall": 0.9,
         "f1": 0.55, "mean_abs_ca_error": 0.3, "R_RACH": 0.7, "D_RACH": 1.2},
    ])
    _write_csv(d / "known_truth_cases.csv", [
        {"switch_name": "S1", "correct": "True", "abs_ca_error": 0.1},
        {"switch_name": "S1", "correct": "True", "abs_ca_error": 0.2},
        {"switch_name": "S2", "correct": "False", "abs_ca_error": 0.6},
        {"switch_name": "S2", "correct": "True", "abs_ca_error": 0.3},
    ])
    _write_csv(d / "recovery_by_noise.csv", [
        {"noise_rate": 0.0, "n_cases": 1, "mean_accuracy": 0.75,
         "mean_precision": 0.5, "mean_recall": 1.0, "mean_f1": 0.667, "mean_R_RACH": 0.6},
        {"noise_rate": 0.1, "n_cases": 1, "mean_accuracy": 0.5,
         "mean_precision": 0.4, "mean_recall": 0.9, "mean_f1": 0.55, "mean_R_RACH": 0.7},
    ])
    return d


def test_summarize_benchmark_overall_and_weakest(tmp_path):
    bench = summarize_benchmark(_make_benchmark_dir(tmp_path))
    assert bench["available"]
    assert bench["n_cases"] == 2
    # mean accuracy of 0.75 and 0.5
    assert abs(bench["overall"]["accuracy"] - 0.625) < 1e-6
    # S2 has lower correct rate than S1 -> weakest first
    assert bench["switch_quality"][0]["switch"] == "S2"


def test_benchmark_summary_md_has_caution(tmp_path):
    bench = summarize_benchmark(_make_benchmark_dir(tmp_path))
    md = benchmark_summary_md(bench)
    assert EPISTEMIC_CAUTION in md
    assert "Overall recovery metrics" in md
    assert "Weakest-recovered switches" in md


def test_summarize_benchmark_missing_dir(tmp_path):
    bench = summarize_benchmark(tmp_path / "does_not_exist")
    assert bench["available"] is False
    md = benchmark_summary_md(bench)
    assert EPISTEMIC_CAUTION in md


def _ensemble():
    return [
        EnsembleResult("p1", "lax", 0.6, 30, 100, 0.5, 0.60,
                       {"S1": 0.95, "S2": 0.20}, 2),
        EnsembleResult("p1", "strict", 0.9, 40, 100, 0.4, 0.70,
                       {"S1": 0.92, "S2": 0.75}, 2),
    ]


def test_summarize_ensemble_and_md():
    ens = summarize_ensemble(_ensemble(), ["S1", "S2"])
    assert ens["available"]
    assert ens["selection"].best is not None
    assert "S1" in ens["robust_switches"]      # tiny CA_j swing
    assert "S2" in ens["sensitive_switches"]   # large CA_j swing
    md = ensemble_summary_md(ens)
    assert "Best (ensemble-selected) setting" in md
    assert "Robust vs prior/ε-sensitive switches" in md


def test_results_summary_md_separates_claims():
    bench = {"available": False, "switch_quality": []}
    ens = summarize_ensemble(_ensemble(), ["S1", "S2"])
    md = results_summary_md(bench, ens)
    assert "Synthetic known-truth recovery" in md
    assert "Empirical ensemble inference" in md
    # Manuscript safety: must not claim truth/identification.
    assert "admissibility is not identification" in md


def test_rows_to_ensemble_results_roundtrip():
    rows = [{
        "preset_name": "p1", "acceptance_rule": "lax", "threshold": "0.6",
        "n_accepted": "30", "n_evaluated": "100", "D_RACH": "0.5", "R_RACH": "0.6",
        "K": "2", "CA_S1": "0.9", "CA_S2": "0.2",
    }]
    res = _rows_to_ensemble_results(rows)
    assert len(res) == 1
    assert res[0].preset_name == "p1"
    assert res[0].n_accepted == 30
    assert res[0].ca_j == {"S1": 0.9, "S2": 0.2}
    assert abs(res[0].acceptance_rate - 0.30) < 1e-9
