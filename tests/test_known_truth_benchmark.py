"""Lightweight tests for the known-truth recovery benchmark.

These tests use minimal settings (2 cases, 1 noise level, 50 draws) to keep
CI fast.  They verify structural correctness, not ecological performance.

EPISTEMIC NOTE: The benchmark is a specified-simulator recovery test.
A passing test only confirms self-consistency of RACH ABC under synthetic
data — it does NOT verify causal truth about real ecological mechanisms.
"""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

import pytest

from causal_model.known_truth_benchmark import (
    BenchmarkCase,
    BenchmarkResult,
    SwitchRecovery,
    TRUE_SWITCH_STATES,
    compute_case_metrics,
    generate_synthetic_patterns,
    run_benchmark,
    save_outputs,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_STATES = TRUE_SWITCH_STATES[:2]   # all_off, S1_only


@pytest.fixture(scope="module")
def minimal_result() -> BenchmarkResult:
    """Run benchmark with 2 cases, noise 0.0 only, 50 draws."""
    return run_benchmark(
        true_states=MINIMAL_STATES,
        noise_rates=[0.0],
        n_attempts=50,
        preset_name="literature_grounded",
        acceptance_rule="weighted_lax",
        seed=0,
        verbose=False,
    )


# ---------------------------------------------------------------------------
# Synthetic pattern generation
# ---------------------------------------------------------------------------

class TestGenerateSyntheticPatterns:
    def test_returns_nonempty_list(self):
        state = {"guide_attracts_bombus": True, "selfing_syndrome_active": False,
                 "island_isolation_common_cause": False, "small_pollinator_substitution": False}
        patterns = generate_synthetic_patterns(state, noise_rate=0.0, seed=0)
        assert len(patterns) >= 1

    def test_pattern_schema(self):
        state = {"guide_attracts_bombus": False, "selfing_syndrome_active": True,
                 "island_isolation_common_cause": False, "small_pollinator_substitution": False}
        patterns = generate_synthetic_patterns(state, noise_rate=0.0, seed=0)
        required_keys = {"pattern", "type", "variable", "left_population",
                         "right_population", "relation", "weight", "role"}
        for p in patterns:
            assert required_keys.issubset(p.keys()), f"Missing keys in {p}"
            assert p["role"] == "observed_target"
            assert p["type"] == "pairwise_relation"
            assert p["left_population"] == "Oshima"
            assert p["right_population"] == "Hachijo"

    def test_relation_format(self):
        state = {"guide_attracts_bombus": True, "selfing_syndrome_active": False,
                 "island_isolation_common_cause": False, "small_pollinator_substitution": False}
        patterns = generate_synthetic_patterns(state, noise_rate=0.0, seed=0)
        for p in patterns:
            rel = p["relation"]
            assert any(op in rel for op in (">", "<", "~=")), \
                f"Bad relation format: {rel}"

    def test_noise_injects_variation(self):
        state = {"guide_attracts_bombus": True, "selfing_syndrome_active": True,
                 "island_isolation_common_cause": True, "small_pollinator_substitution": False}
        clean   = generate_synthetic_patterns(state, noise_rate=0.0, seed=0)
        noisy   = generate_synthetic_patterns(state, noise_rate=1.0, seed=0)
        # With noise_rate=1.0 all relations must be flipped
        clean_rels = {p["variable"]: p["relation"] for p in clean}
        noisy_rels = {p["variable"]: p["relation"] for p in noisy}
        # At least one variable should differ (unless all were already ~= which is rare)
        assert any(clean_rels[v] != noisy_rels[v] for v in clean_rels if v in noisy_rels), \
            "noise_rate=1.0 should flip at least one relation"

    def test_noise_seed_reproducibility(self):
        state = {"guide_attracts_bombus": True, "selfing_syndrome_active": False,
                 "island_isolation_common_cause": False, "small_pollinator_substitution": False}
        a = generate_synthetic_patterns(state, noise_rate=0.5, seed=99)
        b = generate_synthetic_patterns(state, noise_rate=0.5, seed=99)
        assert [p["relation"] for p in a] == [p["relation"] for p in b]


# ---------------------------------------------------------------------------
# Compute metrics
# ---------------------------------------------------------------------------

class TestComputeCaseMetrics:
    def test_empty_accepted_returns_nan(self):
        from causal_model.switch_inference import CAMPANULA_SWITCHES
        true_state = {sw.name: False for sw in CAMPANULA_SWITCHES}
        per, agg = compute_case_metrics([], true_state, CAMPANULA_SWITCHES)
        assert all(math.isnan(s.ca_j) for s in per)
        assert math.isnan(agg["accuracy"])

    def test_all_on_accepted(self):
        from causal_model.switch_inference import CAMPANULA_SWITCHES
        # Accepted row: all switches ON
        accepted = [
            {sw.name: True for sw in CAMPANULA_SWITCHES}
        ]
        true_state = {sw.name: True for sw in CAMPANULA_SWITCHES}
        per, agg = compute_case_metrics(accepted, true_state, CAMPANULA_SWITCHES)
        # All CA_j should be 1.0 (only 1 accepted row, all switches ON)
        for s in per:
            assert s.ca_j == 1.0
            assert s.predicted_on is True
            assert s.correct is True
        assert agg["accuracy"] == 1.0
        assert agg["f1"] == 1.0

    def test_ca_j_range(self):
        from causal_model.switch_inference import CAMPANULA_SWITCHES
        rows = [
            {sw.name: (i % 2 == 0) for sw in CAMPANULA_SWITCHES}
            for i in range(10)
        ]
        true_state = {sw.name: True for sw in CAMPANULA_SWITCHES}
        per, agg = compute_case_metrics(rows, true_state, CAMPANULA_SWITCHES)
        for s in per:
            assert 0.0 <= s.ca_j <= 1.0, f"CA_j out of range: {s.ca_j}"

    def test_predicted_on_is_bool(self):
        from causal_model.switch_inference import CAMPANULA_SWITCHES
        rows = [{sw.name: True for sw in CAMPANULA_SWITCHES}]
        true_state = {sw.name: False for sw in CAMPANULA_SWITCHES}
        per, _ = compute_case_metrics(rows, true_state, CAMPANULA_SWITCHES)
        for s in per:
            assert isinstance(s.predicted_on, bool), \
                f"predicted_on must be bool, got {type(s.predicted_on)}"


# ---------------------------------------------------------------------------
# BenchmarkResult / run_benchmark
# ---------------------------------------------------------------------------

class TestRunBenchmark:
    def test_returns_correct_number_of_cases(self, minimal_result):
        expected = len(MINIMAL_STATES) * 1   # 1 noise level
        assert len(minimal_result.cases) == expected

    def test_ca_j_in_range(self, minimal_result):
        for case in minimal_result.cases:
            for sw in case.per_switch:
                if not math.isnan(sw.ca_j):
                    assert 0.0 <= sw.ca_j <= 1.0, \
                        f"CA_j out of [0,1]: switch={sw.switch_name} ca_j={sw.ca_j}"

    def test_predicted_on_is_bool(self, minimal_result):
        for case in minimal_result.cases:
            for sw in case.per_switch:
                assert isinstance(sw.predicted_on, bool), \
                    f"predicted_on is not bool: {type(sw.predicted_on)}"

    def test_metrics_numerically_valid(self, minimal_result):
        for case in minimal_result.cases:
            if case.n_accepted == 0:
                continue
            for metric in ("accuracy", "precision", "recall", "f1"):
                val = getattr(case, metric)
                if not math.isnan(val):
                    assert 0.0 <= val <= 1.0, \
                        f"{metric}={val} out of [0,1] for {case.true_state_label}"
            if not math.isnan(case.mean_abs_ca_error):
                assert 0.0 <= case.mean_abs_ca_error <= 1.0

    def test_n_accepted_nonneg(self, minimal_result):
        for case in minimal_result.cases:
            assert case.n_accepted >= 0
            assert case.n_evaluated >= 0

    def test_true_state_labels(self, minimal_result):
        expected_labels = {lbl for lbl, _ in MINIMAL_STATES}
        actual_labels   = {c.true_state_label for c in minimal_result.cases}
        assert actual_labels == expected_labels


# ---------------------------------------------------------------------------
# save_outputs / CSV files
# ---------------------------------------------------------------------------

class TestSaveOutputs:
    def test_all_csvs_created(self, minimal_result, tmp_path):
        written = save_outputs(minimal_result, tmp_path)
        expected = {
            "known_truth_cases.csv",
            "known_truth_summary.csv",
            "recovery_by_noise.csv",
            "recovery_by_n_attempts.csv",
            "recovery_by_backend_pair.csv",
        }
        assert set(written.keys()) == expected
        for name, path in written.items():
            assert path.exists(), f"{name} not found at {path}"
            assert path.stat().st_size > 0, f"{name} is empty"

    def test_cases_csv_has_header_and_rows(self, minimal_result, tmp_path):
        import csv
        written = save_outputs(minimal_result, tmp_path)
        cases_path = written["known_truth_cases.csv"]
        with cases_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) > 0, "known_truth_cases.csv is empty"
        # Check required columns
        for col in ("run_id", "true_state_label", "noise_rate", "switch_name",
                    "true_on", "ca_j", "predicted_on"):
            assert col in rows[0], f"Missing column: {col}"

    def test_summary_csv_has_header_and_rows(self, minimal_result, tmp_path):
        import csv
        written = save_outputs(minimal_result, tmp_path)
        with written["known_truth_summary.csv"].open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == len(minimal_result.cases)

    def test_recovery_by_noise_has_noise_column(self, minimal_result, tmp_path):
        import csv
        written = save_outputs(minimal_result, tmp_path)
        with written["recovery_by_noise.csv"].open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) >= 1
        assert "noise_rate" in rows[0]
