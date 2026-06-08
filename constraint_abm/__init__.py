"""Constraint-aware pattern-oriented modelling tools.

CAPOM uses observable field patterns to constrain latent ecological trade-offs
that are difficult to measure directly.
"""

from .constraints import Constraint
from .latent import LatentParameter
from .matching import PatternMatchResult, compare_patterns, rank_scenarios
from .patterns import ObservablePattern
from .scenarios import Scenario

__all__ = [
    "Constraint",
    "LatentParameter",
    "ObservablePattern",
    "PatternMatchResult",
    "Scenario",
    "compare_patterns",
    "rank_scenarios",
]
