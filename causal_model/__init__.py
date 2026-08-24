"""Public API for RACH: Restricted Admissible Causal Hypotheses.

The package-level surface follows the publication mainline:

    admissible causal region -> CA / D / R / replaceability
    -> mechanism equivalence -> NOV / RACH-SEQ next observation

Lower-level causal-structure schemas and rule-transition ABMs remain available
for compatibility and supplementary analyses, but they are not the package's
primary inferential interface.
"""

# RACH inferential core.
from .causal_admissibility import (
    CandidateObservation,
    CandidateOutcome,
    CausalAdmissibilityResult,
    NextObservationValueResult,
    ObservationContribution,
    RACHSummary,
    causal_admissibility,
    causal_degeneracy,
    causal_resolvability,
    next_observation_value,
    observation_contribution,
    rach_summary,
)
from .causal_replaceability import (
    CRCResult,
    causal_replaceability_cost,
    causal_replaceability_cost_full,
    crc_profile,
    crc_profile_full,
)
from .mechanism_equivalence import mechanism_equivalence_structure
from .rach_seq import (
    SeqResult,
    SeqStep,
    expected_edge_cuts,
    filter_by_outcome,
    rach_seq,
)

# General-purpose support schemas retained for backward compatibility.
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

# Supplementary rule-transition compatibility.  Existing ABM modules expose a
# shared isolated-intervention contract; this is deliberately not part of
# ``__all__`` because it is not the RACH publication mainline.
from .rule_transition_protocol import install_rule_transition_contracts
install_rule_transition_contracts()


__all__ = [
    # Primary RACH interface.
    "CandidateObservation",
    "CandidateOutcome",
    "CausalAdmissibilityResult",
    "CRCResult",
    "NextObservationValueResult",
    "ObservationContribution",
    "RACHSummary",
    "SeqResult",
    "SeqStep",
    "causal_admissibility",
    "causal_degeneracy",
    "causal_replaceability_cost",
    "causal_replaceability_cost_full",
    "causal_resolvability",
    "crc_profile",
    "crc_profile_full",
    "expected_edge_cuts",
    "filter_by_outcome",
    "mechanism_equivalence_structure",
    "next_observation_value",
    "observation_contribution",
    "rach_seq",
    "rach_summary",
    # Compatibility support schemas.
    "CausalEdge",
    "CausalStructure",
    "GeneratorBridgeInput",
    "LatentParameter",
    "PatternTarget",
    "PathwaySwitches",
    "apply_latent_overrides",
    "bridge_inputs_for_structure",
    "expected_pattern_relations",
    "score_causal_structure",
    "score_pattern_match",
    "score_simulated_relations",
    "summarize_structure_support",
    "switches_for_structure",
    "switches_to_dict",
]
