"""Canonical sequential observation-design backend.

The public method repeatedly scores available observations using the current
admissible mechanism region, selects before revealing the realised outcome,
conditions on that outcome, and recomputes all remaining values. Verified
candidates use ``V(Q)=I(S;Q|A_epsilon)/K``; explicitly labelled structural
fallbacks remain available when a predictive outcome partition is not identified.

Historical implementation symbols are isolated in a private compatibility module
and remain reachable only for support/provenance code.
"""
from __future__ import annotations

import causal_model._compat_sequential_observation as _impl

PredictiveOutcomeDistribution = _impl.PredictiveOutcomeDistribution
SequentialDesignStep = _impl.SeqStep
SequentialDesignResult = _impl.SeqResult

filter_by_outcome = _impl.filter_by_outcome
predictive_outcome_distribution = _impl.predictive_outcome_distribution
candidate_mutual_information_bits = _impl.candidate_mutual_information_bits
validated_information_value = _impl.validated_nov_value
expected_edge_cuts = _impl.expected_edge_cuts
sequential_candidate_value = _impl.sequential_candidate_value
sequential_observation_design = _impl.rach_seq


def __getattr__(name: str):
    """Delegate historical support symbols to the private compatibility backend."""
    return getattr(_impl, name)


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
