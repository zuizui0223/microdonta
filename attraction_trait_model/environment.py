"""Environment definitions for attraction-trait simulations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Environment:
    """Population or island environment used by the generative model.

    Values can start as ordinal or literature-derived proxies and later be
    replaced by field estimates. They are environmental conditions, not latent
    trade-off parameters.
    """

    name: str
    bombus_frequency: float
    small_pollinator_frequency: float
    pollinator_environment: float
    migration_rate: float
    effective_population_size: float
    island_distance: float = 0.0
