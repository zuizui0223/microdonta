"""Public API for RACH: Restricted Admissible Causal Hypotheses.

The package-level surface follows the publication mainline:

    admissible causal region -> CA / D / R / replaceability
    -> mechanism equivalence -> NOV / RACH-SEQ next observation

Package-level callable names deliberately avoid colliding with submodule names.
For example, ``compute_causal_admissibility`` is the root-level callable while
``causal_model.causal_admissibility`` remains the importable module; likewise
``run_rach_seq`` leaves ``causal_model.rach_seq`` intact.

Lower-level causal-structure schemas and rule-transition ABMs remain available
for compatibility and supplementary analyses, but they are not the package's
primary inferential interface.
"""

# Keep canonical submodules importable under their own names.
from . import causal_admissibility
from . import rach_seq

# RACH inferential core.
CandidateObservation = causal_admissibility.CandidateObservation
CandidateOutcome = causal_admissibility.CandidateOutcome
CausalAdmissibilityResult = causal_admissibility.CausalAdmissibilityResult
NextObservationValueResult = causal_admissibility.NextObservationValueResult
ObservationContribution = causal_admissibility.ObservationContribution
RACHSummary = causal_admissibility.RACHSummary
compute_causal_admissibility = causal_admissibility.causal_admissibility
causal_degeneracy = causal_admissibility.causal_degeneracy
causal_resolvability = causal_admissibility.causal_resolvability
next_observation_value = causal_admissibility.next_observation_value
observation_contribution = causal_admissibility.observation_contribution
rach_summary = causal_admissibility.rach_summary

SeqResult = rach_seq.SeqResult
SeqStep = rach_seq.SeqStep
expected_edge_cuts = rach_seq.expected_edge_cuts
filter_by_outcome = rach_seq.filter_by_outcome
run_rach_seq = rach_seq.rach_seq

from .causal_replaceability import (
    CRCResult,
    causal_replaceability_cost,
    causal_replaceability_cost_full,
    crc_profile,
    crc_profile_full,
)
from .mechanism_equivalence import mechanism_equivalence_structure

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

# Supplementary rule-transition compatibility. Existing ABM modules expose a
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
    "compute_causal_admissibility",
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
    "run_rach_seq",
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
