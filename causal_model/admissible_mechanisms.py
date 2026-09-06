"""Public interface for admissible mechanism-region inference.

The scientific object is the full parameter–mechanism region compatible with a
predeclared model family, biological constraints and observed targets. Public
names are descriptive rather than acronym-based.
"""
from __future__ import annotations

from . import mechanism_region as _backend

CandidateObservation = _backend.CandidateObservation
CandidateOutcome = _backend.CandidateOutcome
MechanismAdmissibilityResult = _backend.MechanismAdmissibilityResult
ObservationContribution = _backend.ObservationContribution
CandidateInformationValueResult = _backend.CandidateInformationValueResult
MechanismResolutionSummary = _backend.MechanismResolutionSummary

compute_admissible_mechanisms = _backend.compute_admissible_mechanisms
mechanism_entropy = _backend.mechanism_entropy


def mechanism_resolvability(accepted_rows, switches, bias_correction: str = "none"):
    """Return current normalized mechanism concentration ``1-H(S|A)/K``.

    This is a state summary of the declared current admissible mechanism
    distribution. It can reflect prior concentration and pre-data constraints as
    well as accepted observations, so it must not be interpreted by itself as
    information supplied by the observations. Evidence attribution requires an
    explicit pre-observation baseline contrast. Candidate observation value is
    separately reported as incremental conditional mutual information.
    """
    return _backend.mechanism_resolvability(
        accepted_rows,
        switches,
        bias_correction=bias_correction,
    )


observation_contribution = _backend.observation_contribution
mechanism_resolution_summary = _backend.mechanism_resolution_summary

# Explicit compatibility calculation. The publication-level candidate quantity
# is defined in observation_value.py.
heuristic_observation_value = _backend.heuristic_observation_value


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
