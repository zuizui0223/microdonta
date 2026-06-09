"""Backward-compatibility shim — content moved to causal_model.phenomenological_model.

All content has moved to :mod:`causal_model.phenomenological_model`.
This module re-exports everything under the old names so that
existing callers continue to work without changes.
"""
from causal_model.phenomenological_model import (  # noqa: F401
    RELATION_TOLERANCE,
    PhenomenologicalOutput,
    PhenomenologicalOutput as PopulationProxyOutput,
    clamp01,
    predict_traits_phenomenological,
    predict_traits_phenomenological as simulate_population_proxy,
    relation_from_values,
    relations_from_outputs,
)

__all__ = [
    "RELATION_TOLERANCE",
    "PopulationProxyOutput",
    "PhenomenologicalOutput",
    "clamp01",
    "simulate_population_proxy",
    "predict_traits_phenomenological",
    "relation_from_values",
    "relations_from_outputs",
]
