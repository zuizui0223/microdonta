"""Public API for RACH: Restricted Admissible Causal Hypotheses.

The package-level surface follows the publication mainline:

    admissible causal region -> CA / D / R / replaceability
    -> mechanism equivalence -> validated NOV/EVSI -> RACH-SEQ

Package-level callable names deliberately avoid colliding with submodule names.
For example, ``compute_causal_admissibility`` is the root-level callable while
``causal_model.causal_admissibility`` remains the importable module; likewise
``run_rach_seq`` leaves ``causal_model.rach_seq`` intact.

The publication-level next-observation quantity is ``next_observation_evsi``.
Older heuristics, structural scoring helpers, and edge-cut/filter utilities remain
available as explicitly named compatibility attributes or through their canonical
submodules, but they are not advertised in ``__all__`` and therefore do not
define the scientific package surface.
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
observation_contribution = causal_admissibility.observation_contribution
rach_summary = causal_admissibility.rach_summary

# Compatibility attributes: importable by explicit name but not primary API.
heuristic_next_observation_value = causal_admissibility.next_observation_value
SeqResult = rach_seq.SeqResult
SeqStep = rach_seq.SeqStep
expected_edge_cuts = rach_seq.expected_edge_cuts
filter_by_outcome = rach_seq.filter_by_outcome
run_rach_seq = rach_seq.rach_seq

from .nov_evsi import EVSIResult, next_observation_evsi
from .causal_replaceability import (
    CRCResult,
    causal_replaceability_cost,
    causal_replaceability_cost_full,
    crc_profile,
    crc_profile_full,
)
from .mechanism_equivalence import mechanism_equivalence_structure

# General-purpose support schemas retained as explicit compatibility attributes.
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
    "CandidateObservation",
    "CandidateOutcome",
    "CausalAdmissibilityResult",
    "CRCResult",
    "EVSIResult",
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
    "mechanism_equivalence_structure",
    "next_observation_evsi",
    "observation_contribution",
    "run_rach_seq",
    "rach_summary",
]
