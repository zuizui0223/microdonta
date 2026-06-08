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
    summarize_structure_support,
)
from .structures import CausalEdge, CausalStructure

__all__ = [
    "CausalEdge",
    "CausalStructure",
    "LatentParameter",
    "PatternTarget",
    "expected_pattern_relations",
    "score_causal_structure",
    "score_pattern_match",
    "summarize_structure_support",
]
