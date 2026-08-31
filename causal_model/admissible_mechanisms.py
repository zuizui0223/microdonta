"""Descriptive public interface for admissible mechanism-region inference.

The scientific object is the full parameter–mechanism region compatible with a
predeclared model family, biological constraints and observed targets. The
interface deliberately uses role names rather than a method acronym.
"""
from __future__ import annotations

from . import causal_admissibility as _backend

CandidateObservation = _backend.CandidateObservation
CandidateOutcome = _backend.CandidateOutcome
CausalAdmissibilityResult = _backend.CausalAdmissibilityResult
ObservationContribution = _backend.ObservationContribution
CandidateInformationValueResult = _backend.NextObservationValueResult
MechanismResolutionSummary = _backend.RACHSummary

compute_admissible_mechanisms = _backend.causal_admissibility
mechanism_entropy = _backend.causal_degeneracy
mechanism_resolvability = _backend.causal_resolvability
observation_contribution = _backend.observation_contribution
mechanism_resolution_summary = _backend.rach_summary

# The older heuristic is retained only as an explicitly labelled compatibility
# calculation. Publication-level candidate value is defined in observation_value.
heuristic_observation_value = _backend.next_observation_value

__all__ = [
    "CandidateInformationValueResult",
    "CandidateObservation",
    "CandidateOutcome",
    "CausalAdmissibilityResult",
    "MechanismResolutionSummary",
    "ObservationContribution",
    "compute_admissible_mechanisms",
    "heuristic_observation_value",
    "mechanism_entropy",
    "mechanism_resolvability",
    "mechanism_resolution_summary",
    "observation_contribution",
]
