"""Canonical admissible-mechanism region backend.

This module is the descriptive entry point for Mechanism-Resolving Observation
Design. The implementation is retained in a private compatibility module so that
historical support code can continue to resolve old symbol names while new code
uses the method vocabulary below.
"""
from __future__ import annotations

from . import _compat_mechanism_region as _impl

CandidateObservation = _impl.CandidateObservation
CandidateOutcome = _impl.CandidateOutcome
MechanismAdmissibilityResult = _impl.CausalAdmissibilityResult
MechanismResolutionSummary = _impl.RACHSummary
ObservationContribution = _impl.ObservationContribution
CandidateInformationValueResult = _impl.NextObservationValueResult

compute_admissible_mechanisms = _impl.causal_admissibility
mechanism_entropy = _impl.causal_degeneracy
mechanism_resolvability = _impl.causal_resolvability
observation_contribution = _impl.observation_contribution
mechanism_resolution_summary = _impl.rach_summary
heuristic_observation_value = _impl.next_observation_value


def __getattr__(name: str):
    """Delegate historical support symbols to the private compatibility backend."""
    return getattr(_impl, name)


__all__ = [
    "CandidateInformationValueResult",
    "CandidateObservation",
    "CandidateOutcome",
    "MechanismAdmissibilityResult",
    "MechanismResolutionSummary",
    "ObservationContribution",
    "compute_admissible_mechanisms",
    "heuristic_observation_value",
    "mechanism_entropy",
    "mechanism_resolvability",
    "mechanism_resolution_summary",
    "observation_contribution",
]
