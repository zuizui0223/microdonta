"""Generative attraction-trait evolution model components.

This package is the biological model layer. CAPOM pattern matching and
inference remain in `constraint_abm`.
"""

from .agents import PlantAgent
from .diagnostics import guide_status, selfing_syndrome_score
from .environment import Environment
from .fitness import fitness, flower_cost_effect, guide_cost_effect, reproductive_output
from .inheritance import drift_strength, inherit_trait, selfing_syndrome_shift
from .parameters import ModelParameters
from .reproduction import (
    clamp,
    outcrossing_probability,
    selfing_probability,
    small_pollinator_access,
)

__all__ = [
    "Environment",
    "ModelParameters",
    "PlantAgent",
    "clamp",
    "drift_strength",
    "fitness",
    "flower_cost_effect",
    "guide_cost_effect",
    "guide_status",
    "inherit_trait",
    "outcrossing_probability",
    "reproductive_output",
    "selfing_probability",
    "selfing_syndrome_score",
    "selfing_syndrome_shift",
    "small_pollinator_access",
]
