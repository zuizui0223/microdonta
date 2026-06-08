"""Plotting adapters.

The package core intentionally avoids a plotting dependency. Functions here
return tidy records that Streamlit, matplotlib, seaborn, or plotnine can consume.
"""

from __future__ import annotations

from .matching import PatternMatchResult


def scenario_score_records(results: list[PatternMatchResult]) -> list[dict[str, float | str]]:
    """Convert pattern-matching results into tidy plotting records."""

    return [
        {"scenario": result.scenario, "total_distance": result.total_distance}
        for result in results
    ]
