"""Lightweight schemas for latent causal generative models.

General-purpose package. System-specific structures and defaults
live in examples/ (e.g., examples/campanula_izu/causal_structures.py).
"""

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

__all__ = [
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
