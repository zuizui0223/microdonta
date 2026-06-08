"""CAPOM: Constraint-aware pattern-oriented modelling tools.

Uses observable field patterns to constrain latent ecological trade-offs
that are difficult to measure directly.
"""

from .constraints import Constraint
from .latent import LatentParameter
from .matching import PatternMatchResult, compare_patterns, rank_scenarios
from .patterns import ObservablePattern
from .scenarios import Scenario
from .abm_core import Plant, evaluate_population, simulate, simulate_multi_seed
from .inference import (
    InferenceResult,
    abc_rejection,
    abc_cross_population,
    posterior_summary,
    credible_interval,
)

__all__ = [
    # existing
    "Constraint",
    "LatentParameter",
    "ObservablePattern",
    "Scenario",
    "PatternMatchResult",
    "compare_patterns",
    "rank_scenarios",
    # new: simulation core
    "Plant",
    "evaluate_population",
    "simulate",
    "simulate_multi_seed",
    # new: inference
    "InferenceResult",
    "abc_rejection",
    "abc_cross_population",
    "posterior_summary",
    "credible_interval",
]
