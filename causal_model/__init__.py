"""Public API for microdonta's mechanism-resolving observation design.

Publication-facing vocabulary is deliberately descriptive:

    admissible mechanism region
    -> mechanism entropy / resolvability / replaceability
    -> observation information value
    -> sequential observation design

Historical implementation modules remain internal compatibility backends for the
frozen validation record, but they do not define the advertised API.
"""

from .admissible_mechanisms import (
    CandidateInformationValueResult,
    CandidateObservation,
    CandidateOutcome,
    CausalAdmissibilityResult,
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
from .causal_replaceability import (
    CRCResult,
    causal_replaceability_cost,
    causal_replaceability_cost_full,
    crc_profile,
    crc_profile_full,
)
from .mechanism_equivalence import mechanism_equivalence_structure

# General-purpose support schemas retained for simulator/application compatibility.
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
    "CausalAdmissibilityResult",
    "CRCResult",
    "InformationValueResult",
    "MechanismResolutionSummary",
    "ObservationContribution",
    "PredictiveOutcomeDistribution",
    "SequentialDesignResult",
    "SequentialDesignStep",
    "candidate_mutual_information_bits",
    "causal_replaceability_cost",
    "causal_replaceability_cost_full",
    "compute_admissible_mechanisms",
    "crc_profile",
    "crc_profile_full",
    "expected_edge_cuts",
    "filter_by_outcome",
    "heuristic_observation_value",
    "mechanism_entropy",
    "mechanism_equivalence_structure",
    "mechanism_resolvability",
    "mechanism_resolution_summary",
    "observation_contribution",
    "observation_information_value",
    "predictive_outcome_distribution",
    "sequential_candidate_value",
    "sequential_observation_design",
    "validated_information_value",
]
