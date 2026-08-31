"""Public API for Mechanism-Resolving Observation Design.

Publication-facing vocabulary is deliberately descriptive:

    admissible mechanism region
    -> mechanism entropy / resolvability / replaceability
    -> observation information value
    -> sequential observation design

Historical implementation modules remain compatibility backends for frozen
validation provenance, but they do not define the advertised API.
"""

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
    "candidate_mutual_information_bits",
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
    "validated_information_value",
]
