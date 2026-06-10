"""Tests for cross-backend known-truth recovery (issue #24).

Covers the lightweight proxy->proxy self-consistency path end to end, the
generator-backend dispatch, and the backend metadata / recovery_by_backend_pair
output.  Heavy ABM inference paths are exercised only for dispatch wiring with
tiny settings.
"""
from __future__ import annotations

import sys
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from causal_model.known_truth_benchmark import (
    generate_synthetic_patterns,
    run_benchmark,
    save_outputs,
    BenchmarkCase,
    TRUE_SWITCH_STATES,
)

_S1_S2 = dict(TRUE_SWITCH_STATES[4][1])   # ("S1_S2", {...})


def test_backend_pair_property():
    c = BenchmarkCase(
        run_id="x", true_state_label="all_off", true_state={}, noise_rate=0.0,
        n_attempts=1, preset_name="literature_grounded", acceptance_rule="weighted_lax",
        seed=0, generator_backend="abm", inference_backend="proxy",
    )
    assert c.backend_pair == "abm->proxy"


def test_proxy_generator_returns_pairwise_rows():
    pats = generate_synthetic_patterns(_S1_S2, noise_rate=0.0, seed=1,
                                       generator_backend="proxy")
    assert pats, "proxy generator should return pattern rows"
    for p in pats:
        assert p["type"] == "pairwise_relation"
        assert p["left_population"] == "Oshima"
        assert p["right_population"] == "Hachijo"
        assert "Oshima" in p["relation"] and "Hachijo" in p["relation"]


def test_abm_generator_returns_valid_rows():
    # Tiny ABM settings — just verify it returns valid pairwise rows (or falls
    # back to proxy), never crashes.
    pats = generate_synthetic_patterns(
        _S1_S2, noise_rate=0.0, seed=2, generator_backend="abm",
        abm_generations=6, abm_population_size=30, abm_replicates=1,
    )
    assert pats
    for p in pats:
        assert p["type"] == "pairwise_relation"
        assert "Oshima" in p["relation"]


def test_run_benchmark_proxy_proxy_metadata(tmp_path):
    result = run_benchmark(
        true_states=[("all_off", dict(TRUE_SWITCH_STATES[0][1]))],
        noise_rates=(0.0,), n_attempts=20, seed=7,
        generator_backend="proxy", inference_backend="proxy", verbose=False,
    )
    assert result.cases
    c = result.cases[0]
    assert c.generator_backend == "proxy"
    assert c.inference_backend == "proxy"
    assert c.backend_pair == "proxy->proxy"

    written = save_outputs(result, tmp_path)
    assert "recovery_by_backend_pair.csv" in written
    bp_text = written["recovery_by_backend_pair.csv"].read_text(encoding="utf-8")
    assert "backend_pair" in bp_text
    assert "proxy->proxy" in bp_text

    # Backend metadata must appear in the per-case and summary CSVs too.
    cases_text = written["known_truth_cases.csv"].read_text(encoding="utf-8")
    assert "generator_backend" in cases_text and "inference_backend" in cases_text
    summary_text = written["known_truth_summary.csv"].read_text(encoding="utf-8")
    assert "backend_pair" in summary_text
