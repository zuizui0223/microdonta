"""Summaries for accepted latent parameter ranges.

Research-mode inference should report ranges of accepted latent parameters, not
one hand-tuned value. This module provides a small dependency-free helper for
min/quantile/median/max summaries.
"""

from __future__ import annotations

from typing import Iterable, Any


def _quantile(sorted_values: list[float], q: float) -> float:
    """Return a linear-interpolated quantile for sorted numeric values."""

    if not sorted_values:
        raise ValueError("cannot compute a quantile of an empty list")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


def summarize_parameter_ranges(
    rows: Iterable[dict[str, Any]],
    parameter_names: Iterable[str],
) -> list[dict[str, float | int | str]]:
    """Summarize accepted parameter ranges.

    Parameters
    ----------
    rows:
        Accepted run rows or accepted parameter-set rows.
    parameter_names:
        Numeric latent parameter names to summarize.

    Returns
    -------
    list of dict
        One row per parameter with min, q025, median, q975, max and n_accepted.
    """

    rows = list(rows)
    summaries: list[dict[str, float | int | str]] = []
    for param in parameter_names:
        values = sorted(
            float(row[param])
            for row in rows
            if isinstance(row.get(param), (int, float))
        )
        if not values:
            continue
        summaries.append(
            {
                "Parameter": param,
                "Min": round(values[0], 4),
                "q025": round(_quantile(values, 0.025), 4),
                "Median": round(_quantile(values, 0.50), 4),
                "q975": round(_quantile(values, 0.975), 4),
                "Max": round(values[-1], 4),
                "n_accepted": len(values),
            }
        )
    return summaries
