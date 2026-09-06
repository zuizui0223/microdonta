"""Public API for Mechanism-Resolving Observation Design.

Publication-facing vocabulary is deliberately descriptive:

    admissible mechanism region
    -> mechanism entropy / resolvability / replaceability
    -> observation information value
    -> sequential observation design

The validated MROD publication score remains mechanism information
``I(S;Q|A_epsilon)/K``.  A separate target-aware surface is exported for
prospective analyses that predeclare a target ``T``.  Target information is not
silently substituted for mechanism information, and neither quantity by itself
licenses a scientific report.

Historical import paths are mapped privately to descriptive backend modules so
frozen validation code remains reproducible without keeping retired filenames.
They do not define the advertised API.
"""
from __future__ import annotations

import sys

# Descriptive backend modules are canonical.  Private aliases preserve imports
# embedded in frozen validation/support code while retired source filenames are
# removed from the repository.
from . import mechanism_region as _mechanism_region_backend
sys.modules.setdefault(__name__ + ".causal_admissibility", _mechanism_region_backend)

from . import mechanism_replaceability_core as _replaceability_backend
sys.modules.setdefault(__name__ + ".causal_replaceability", _replaceability_backend)

from . import sequential_observation as _sequential_backend
sys.modules.setdefault(__name__ + ".rach_seq", _sequential_backend)

from . import observation_information as _information_backend
sys.modules.setdefault(__name__ + ".nov_evsi", _information_backend)

from . import information_value_calibration_core as _calibration_backend
sys.modules.setdefault(__name__ + ".nov_calibration", _calibration_backend)

from . import joint_observation_set as _joint_set_backend
sys.modules.setdefault(__name__ + ".rach_set", _joint_set_backend)

from . import replaceability_observation_value as _replaceability_value_backend
sys.modules.setdefault(__name__ + ".replaceability_nov", _replaceability_value_backend)

from .admissible_mechanisms import (
    CandidateInformationValueResult,
    CandidateObservation,
    CandidateOutcome,
    MechanismAdmissibilityResult,
    MechanismResolutionSummary,
    ObservationContribution,
    compute_admissible_mechanisms,
    heuristic_observation_value,
    mechanism_entropy,
    mechanism_resolvability,
    mechanism_resolution_summary,
    observation_contribution,
)
from .observation_value import (
    InformationValueResult,
    candidate_mutual_information_bits,
    observation_information_value,
)
from .target_observation_value import (
    TargetInformationValueResult,
    candidate_target_mutual_information_bits,
    target_entropy_bits,
    target_observation_information_value,
)
from .sequential_design import (
    PredictiveOutcomeDistribution,
    SequentialDesignResult,
    SequentialDesignStep,
    expected_edge_cuts,
    filter_by_outcome,
    predictive_outcome_distribution,
    sequential_candidate_value,
    sequential_observation_design,
    validated_information_value,
)
from .mechanism_replaceability import (
    ReplaceabilityResult,
    mechanism_replaceability_cost,
    mechanism_replaceability_cost_full,
    mechanism_replaceability_profile,
    mechanism_replaceability_profile_full,
)
from .mechanism_equivalence import mechanism_equivalence_structure

# General simulator/application schemas retained for compatibility, but not part
# of the publication-facing scientific surface below.
from .latent_parameters import LatentParameter
from .pattern_targets import PatternTarget
from .scoring import (
    expected_pattern_relations,
    score_causal_structure,
    score_pattern_match,
    score_simulated_relations,
    summarize_structure_support,
)
from .structures import CausalEdge, CausalStructure
from .switches import PathwaySwitches, switches_for_structure, switches_to_dict
from .generator_bridge import (
    GeneratorBridgeInput,
    apply_latent_overrides,
    bridge_inputs_for_structure,
)
from .rule_transition_protocol import install_rule_transition_contracts
install_rule_transition_contracts()

__all__ = [
    "CandidateInformationValueResult",
    "CandidateObservation",
    "CandidateOutcome",
    "InformationValueResult",
    "MechanismAdmissibilityResult",
    "MechanismResolutionSummary",
    "ObservationContribution",
    "PredictiveOutcomeDistribution",
    "ReplaceabilityResult",
    "SequentialDesignResult",
    "SequentialDesignStep",
    "TargetInformationValueResult",
    "candidate_mutual_information_bits",
    "candidate_target_mutual_information_bits",
    "compute_admissible_mechanisms",
    "expected_edge_cuts",
    "filter_by_outcome",
    "heuristic_observation_value",
    "mechanism_entropy",
    "mechanism_equivalence_structure",
    "mechanism_replaceability_cost",
    "mechanism_replaceability_cost_full",
    "mechanism_replaceability_profile",
    "mechanism_replaceability_profile_full",
    "mechanism_resolvability",
    "mechanism_resolution_summary",
    "observation_contribution",
    "observation_information_value",
    "predictive_outcome_distribution",
    "sequential_candidate_value",
    "sequential_observation_design",
    "target_entropy_bits",
    "target_observation_information_value",
    "validated_information_value",
]
