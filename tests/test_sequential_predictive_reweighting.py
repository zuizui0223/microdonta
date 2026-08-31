"""Tests for current-A_epsilon predictive reweighting in RACH-SEQ."""
import random

from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome
from causal_model.rach_seq import (
    _materialize_and_filter,
    filter_by_outcome,
    predictive_outcome_distribution,
)


def _two_band_candidate(prior_high=0.1, prior_low=0.9):
    return CandidateObservation(
        name="measure_trait",
        description="measure a two-band trait",
        target_switches=["A"],
        rationale="test current-region predictive weighting",
        outcomes=[
            CandidateOutcome(
                name="high",
                description="high band",
                prior_probability=prior_high,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "trait",
                    "population": "pop",
                    "observed_value": "0.75",
                    "scale": "0.05",
                }],
            ),
            CandidateOutcome(
                name="low",
                description="low band",
                prior_probability=prior_low,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "trait",
                    "population": "pop",
                    "observed_value": "0.25",
                    "scale": "0.05",
                }],
            ),
        ],
    )


def test_verified_partition_overrides_stale_declared_prior():
    rows = [{"pop_trait": 0.75}] * 8 + [{"pop_trait": 0.25}] * 2
    candidate = _two_band_candidate(prior_high=0.1, prior_low=0.9)
    distribution = predictive_outcome_distribution(candidate, rows)
    assert distribution.source == "current_admissible_region"
    assert distribution.partition_verified
    assert distribution.probabilities == {"high": 0.8, "low": 0.2}


def test_reweighting_changes_after_conditioning_current_region():
    rows = [
        {"pop_trait": 0.75, "gate_trait": 0.75},
        {"pop_trait": 0.75, "gate_trait": 0.75},
        {"pop_trait": 0.25, "gate_trait": 0.75},
        {"pop_trait": 0.25, "gate_trait": 0.25},
    ] * 5
    candidate = _two_band_candidate(prior_high=0.5, prior_low=0.5)
    before = predictive_outcome_distribution(candidate, rows)
    assert before.probabilities == {"high": 0.5, "low": 0.5}

    conditioned = filter_by_outcome(rows, [{
        "type": "absolute_summary",
        "variable": "trait",
        "population": "gate",
        "observed_value": "0.75",
        "scale": "0.05",
    }])
    after = predictive_outcome_distribution(candidate, conditioned)
    assert after.source == "current_admissible_region"
    assert after.probabilities["high"] == 2 / 3
    assert after.probabilities["low"] == 1 / 3


def test_overlap_or_missing_columns_falls_back_to_declared_prior():
    rows = [{"unrelated": i} for i in range(10)]
    candidate = _two_band_candidate(prior_high=0.2, prior_low=0.8)
    distribution = predictive_outcome_distribution(candidate, rows)
    # Missing pop_trait makes both outcome filters conservatively match every row,
    # so the partition cannot be verified and current-row frequencies are unsafe.
    assert distribution.source == "declared_prior"
    assert not distribution.partition_verified
    assert distribution.probabilities == {"high": 0.2, "low": 0.8}


def test_materialisation_samples_from_current_region_not_stale_prior():
    rows = [{"pop_trait": 0.75} for _ in range(12)]
    candidate = _two_band_candidate(prior_high=0.0, prior_low=1.0)
    outcome, filtered = _materialize_and_filter(
        candidate,
        rows,
        random.Random(0),
        min_sub_size=5,
    )
    assert outcome == "high"
    assert filtered == rows
