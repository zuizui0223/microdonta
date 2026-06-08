"""Loader for Campanula Izu empirical observed patterns.

Provides two loaders:

load_observed_patterns()
    Returns ``{pattern_name: relation_string}`` suitable for direct comparison
    with simulated relations.

load_observed_pattern_table()
    Returns the full table as a list of dicts, including left/right population
    values, weights, source citations, and notes.

Default data file
-----------------
``examples/campanula_izu/data/observed_patterns.csv``

The file can be replaced by any CSV with the same columns.  Pass a custom
``path`` argument to either loader to override the default.

Column specification
--------------------
pattern             str   pattern variable name matching simulation output keys
left_population     str   reference population (e.g. Oshima)
right_population    str   comparison population (e.g. Hachijo)
left_value          float provisional quantitative field estimate [0, 1]
right_value         float provisional quantitative field estimate [0, 1]
relation            str   ordinal relation string, e.g. "Oshima > Hachijo"
weight              float importance weight for weighted ABC distance [0, 1+]
source              str   data source / literature citation shorthand
notes               str   free-text annotation
"""

from __future__ import annotations

import csv
from pathlib import Path

_DEFAULT_CSV = Path(__file__).parent / "data" / "observed_patterns.csv"

# Hard-coded fallback if the CSV file is missing (should not happen in production)
_FALLBACK: list[dict] = [
    {"pattern": "nectar_guide",    "left_population": "Oshima", "right_population": "Hachijo",
     "left_value": "0.72", "right_value": "0.31", "relation": "Oshima > Hachijo",
     "weight": "1.0", "source": "field/Inoue1986", "notes": "fallback"},
    {"pattern": "selfing_rate",    "left_population": "Oshima", "right_population": "Hachijo",
     "left_value": "0.18", "right_value": "0.64", "relation": "Oshima < Hachijo",
     "weight": "1.0", "source": "field/Inoue1986", "notes": "fallback"},
    {"pattern": "herkogamy",       "left_population": "Oshima", "right_population": "Hachijo",
     "left_value": "0.70", "right_value": "0.35", "relation": "Oshima > Hachijo",
     "weight": "0.8", "source": "field", "notes": "fallback"},
    {"pattern": "flower_size",     "left_population": "Oshima", "right_population": "Hachijo",
     "left_value": "0.75", "right_value": "0.48", "relation": "Oshima > Hachijo",
     "weight": "0.8", "source": "field/Inoue1986", "notes": "fallback"},
    {"pattern": "Fis",             "left_population": "Oshima", "right_population": "Hachijo",
     "left_value": "0.08", "right_value": "0.35", "relation": "Oshima < Hachijo",
     "weight": "1.0", "source": "genetic", "notes": "fallback"},
    {"pattern": "Bombus_frequency","left_population": "Oshima", "right_population": "Hachijo",
     "left_value": "0.35", "right_value": "0.00", "relation": "Oshima > Hachijo",
     "weight": "1.0", "source": "field/literature", "notes": "fallback"},
]


def load_observed_pattern_table(path: str | Path | None = None) -> list[dict]:
    """Load the observed pattern table from CSV.

    Parameters
    ----------
    path:
        Path to a CSV file.  Defaults to
        ``examples/campanula_izu/data/observed_patterns.csv``.

    Returns
    -------
    list of dict
        One dict per pattern row.  Numeric columns (``left_value``,
        ``right_value``, ``weight``) are returned as-is (strings); callers
        that need floats should cast explicitly.
    """

    p = Path(path) if path else _DEFAULT_CSV
    try:
        with p.open(encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return list(_FALLBACK)


def load_observed_patterns(path: str | Path | None = None) -> dict[str, str]:
    """Return ``{pattern_name: relation_string}`` from the observed data CSV.

    Parameters
    ----------
    path:
        Path to a CSV file.  Defaults to
        ``examples/campanula_izu/data/observed_patterns.csv``.

    Returns
    -------
    dict
        Mapping from pattern variable name to observed ordinal relation string,
        e.g. ``{"nectar_guide": "Oshima > Hachijo", ...}``.
    """

    return {row["pattern"]: row["relation"] for row in load_observed_pattern_table(path)}


def load_pattern_weights(path: str | Path | None = None) -> dict[str, float]:
    """Return ``{pattern_name: weight}`` from the observed data CSV.

    Parameters
    ----------
    path:
        Path to a CSV file.  Defaults to
        ``examples/campanula_izu/data/observed_patterns.csv``.

    Returns
    -------
    dict
        Mapping from pattern variable name to importance weight.
    """

    return {
        row["pattern"]: float(row.get("weight", 1.0))
        for row in load_observed_pattern_table(path)
    }
