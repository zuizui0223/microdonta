"""Backward-compatibility shim — content moved to campanula_phenomenological.py.

All content has moved to :mod:`examples.campanula_izu.campanula_phenomenological`.
This module re-exports everything under the old names so that
existing callers continue to work without changes.
"""
from examples.campanula_izu.campanula_phenomenological import (  # noqa: F401
    default_campanula_environments,
    default_campanula_environments as default_campanula_proxy_environments,
    default_campanula_gradient_environments,
    env_from_isolation,
    environments_from_population_env,
    simulate_campanula_causal_structure,
    simulate_campanula_gradient,
    simulate_campanula_isolation_gradient,
    simulate_campanula_with_switches,
)
