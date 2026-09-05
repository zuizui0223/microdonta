"""Sequential observation design for reducing residual mechanism ambiguity.

At each step, verified candidates are scored by the current normalized mechanism
information ``I(S;Q | A_t)/K``; the highest positive candidate is selected before
its realised outcome is revealed, the admissible region is conditioned on that
outcome, and all remaining candidate values are recomputed.
"""
from __future__ import annotations

from . import sequential_observation as _backend

PredictiveOutcomeDistribution = _backend.PredictiveOutcomeDistribution
SequentialDesignStep = _backend.SequentialDesignStep
SequentialDesignResult = _backend.SequentialDesignResult

filter_by_outcome = _backend.filter_by_outcome
predictive_outcome_distribution = _backend.predictive_outcome_distribution
candidate_mutual_information_bits = _backend.candidate_mutual_information_bits
validated_information_value = _backend.validated_information_value
expected_edge_cuts = _backend.expected_edge_cuts
sequential_candidate_value = _backend.sequential_candidate_value
sequential_observation_design = _backend.sequential_observation_design


__all__ = [
    "PredictiveOutcomeDistribution",
    "SequentialDesignResult",
    "SequentialDesignStep",
    "candidate_mutual_information_bits",
    "expected_edge_cuts",
    "filter_by_outcome",
    "predictive_outcome_distribution",
    "sequential_candidate_value",
    "sequential_observation_design",
    "validated_information_value",
]
