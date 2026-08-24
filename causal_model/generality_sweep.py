"""Compatibility entry point for the publication RACH-SEQ generality benchmark.

The implementation lives in :mod:`causal_model.generality_sweep_core`.  It keeps
candidate ranking independent of hidden benchmark truth; truth is materialised
only after an observation has been selected.
"""
from causal_model.generality_sweep_core import (
    BudgetSummary,
    SweepResult,
    SystemRecord,
    _abc_accept,
    _candidates_for_system,
    _make_random_system,
    _truth_magnitude,
    main,
    make_figure,
    print_budget_table,
    print_report,
    run_budget_sweep,
    run_generality_sweep,
    save_budget_table,
)

__all__ = [
    "BudgetSummary",
    "SweepResult",
    "SystemRecord",
    "_abc_accept",
    "_candidates_for_system",
    "_make_random_system",
    "_truth_magnitude",
    "main",
    "make_figure",
    "print_budget_table",
    "print_report",
    "run_budget_sweep",
    "run_generality_sweep",
    "save_budget_table",
]

if __name__ == "__main__":
    raise SystemExit(main())
