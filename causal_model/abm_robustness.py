"""DEPRECATED shim — moved to :mod:`causal_model.abm_family_adapter`.

The parameter-cell recurrence classifier now lives in ``abm_family_adapter`` so
that a single module is the sole entry point for turning ABM-family sweeps into
robust/fragile ``ProgramRun`` records. This module re-exports the old names for
backward compatibility; import from ``abm_family_adapter`` in new code.
"""
from __future__ import annotations

from causal_model.abm_family_adapter import (
    CellSweepRecord as SweepRecord,
    CellRobustnessPolicy as RobustnessPolicy,
    ProgramRobustnessSummary,
    program_runs_from_cell_sweep as program_runs_from_sweep,
    summarise_sweep_records,
)

__all__ = [
    "SweepRecord",
    "RobustnessPolicy",
    "ProgramRobustnessSummary",
    "program_runs_from_sweep",
    "summarise_sweep_records",
]
