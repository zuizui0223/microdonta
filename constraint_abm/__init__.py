"""CAPOM: Constraint-aware pattern-oriented modelling tools.

Uses observable field patterns to constrain latent ecological trade-offs
that are difficult to measure directly.

Biological model layer: see `attraction_trait_model`.
Causal structure framework: see `causal_model`.
System-specific examples: see `examples/`.
"""

from .constraints import Constraint
from .latent import LatentParameter
from .matching import PatternMatchResult, compare_patterns, rank_scenarios
from .patterns import ObservablePattern
from .scenarios import Scenario
from .abm_core import simulate, simulate_multi_seed
from .inference import (
    InferenceResult,
    abc_rejection,
    abc_cross_population,
    posterior_summary,
    credible_interval,
)

__all__ = [
    # evaluation layer
    "Constraint",
    "LatentParameter",
    "ObservablePattern",
    "Scenario",
    "PatternMatchResult",
    "compare_patterns",
    "rank_scenarios",
    # simulation runner
    "simulate",
    "simulate_multi_seed",
    # inference
    "InferenceResult",
    "abc_rejection",
    "abc_cross_population",
    "posterior_summary",
    "credible_interval",
]
