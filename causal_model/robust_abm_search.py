"""DEPRECATED shim — moved to :mod:`causal_model.abm_family_adapter`.

The context-coverage ABM classifier now lives in ``abm_family_adapter`` so that a
single module is the sole entry point for turning ABM-family sweeps into
robust/fragile ``ProgramRun`` records. This module re-exports the old names for
backward compatibility; import from ``abm_family_adapter`` in new code.
"""
from __future__ import annotations

from causal_model.abm_family_adapter import (
    RobustnessSummary,
    SweepRun,
    classify_sweep_runs,
)

__all__ = ["RobustnessSummary", "SweepRun", "classify_sweep_runs"]
