"""Utility helpers for deriving symbolic relations from simulation summaries.

These functions convert numeric population means into the symbolic relation
strings (``<``, ``>``, ``~=``) used by the pattern-matching scorer.
"""

from __future__ import annotations


def relation_from_values(
    left_name: str,
    left_value: float,
    right_name: str,
    right_value: float,
    tolerance: float = 0.05,
) -> str:
    """Return a symbolic relation string comparing *left_value* to *right_value*.

    Parameters
    ----------
    left_name:
        Label for the left population (e.g. ``"Oshima"``).
    left_value:
        Numeric mean for the variable in the left population.
    right_name:
        Label for the right population (e.g. ``"Hachijo"``).
    right_value:
        Numeric mean for the variable in the right population.
    tolerance:
        Absolute difference below which the two values are considered equal.
        Defaults to 0.05.

    Returns
    -------
    str
        One of:

        * ``"{left_name} ~= {right_name}"`` when the difference is within
          *tolerance*,
        * ``"{left_name} > {right_name}"`` when *left_value* is clearly higher,
        * ``"{left_name} < {right_name}"`` otherwise.
    """
    diff = left_value - right_value
    if abs(diff) <= tolerance:
        return f"{left_name} ~= {right_name}"
    elif diff > 0:
        return f"{left_name} > {right_name}"
    else:
        return f"{left_name} < {right_name}"


def relations_from_final_summaries(
    left_summary: dict,
    right_summary: dict,
    variables: list[str],
    tolerance: float = 0.05,
) -> dict[str, str]:
    """Derive per-variable symbolic relations from two population summaries.

    Parameters
    ----------
    left_summary:
        Summary dict for the left / reference population (e.g. Oshima).
        Typically the last row returned by :func:`simulate_population`.
    right_summary:
        Summary dict for the right / comparison population (e.g. Hachijo).
    variables:
        Variable keys to compare.  Only keys present in both summaries are
        compared; missing keys are silently skipped.
    tolerance:
        Forwarded to :func:`relation_from_values`.

    Returns
    -------
    dict[str, str]
        Mapping from each variable name to its symbolic relation string.
    """
    left_name = left_summary.get("population_name", "Left")
    right_name = right_summary.get("population_name", "Right")

    result: dict[str, str] = {}
    for var in variables:
        if var not in left_summary or var not in right_summary:
            continue
        result[var] = relation_from_values(
            left_name,
            float(left_summary[var]),
            right_name,
            float(right_summary[var]),
            tolerance=tolerance,
        )
    return result
