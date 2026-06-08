"""Loader for Campanula Izu empirical observed patterns and population environments.

Loaders
-------
load_observed_pattern_table()
    Full table as list of dicts supporting three pattern types:
    - pairwise_relation : ordinal left vs right comparison
    - gradient_slope    : expected sign of regression slope across gradient
    - rank_order        : expected rank ordering of populations

load_observed_patterns()
    Returns pairwise patterns as ``{pattern_name: relation_string}`` (backward compat).

observed_pairwise_relations()
    Returns only pairwise_relation rows as ``{variable: relation_string}``.

observed_gradient_patterns()
    Returns gradient_slope and rank_order rows as list of dicts.

load_population_env()
    Returns population environment table from population_env.csv as
    ``{population_name: dict}`` with numeric fields already cast to float.

Default data files
------------------
``examples/campanula_izu/data/observed_patterns.csv``
``examples/campanula_izu/data/population_env.csv``

observed_patterns.csv column specification
------------------------------------------
pattern             str   unique pattern identifier
type                str   pairwise_relation | gradient_slope | rank_order
variable            str   trait variable name (matches simulation output keys)
left_population     str   reference population (pairwise only)
right_population    str   comparison population (pairwise only)
populations         str   semicolon-separated ordered list (gradient/rank only)
predictor           str   gradient axis variable name (gradient_slope only)
expected_direction  str   positive | negative (gradient_slope only)
relation            str   ordinal relation string e.g. "Oshima > Hachijo" (pairwise only)
weight              float importance weight for weighted ABC distance [0, 1+]
source              str   data source / literature citation shorthand
notes               str   free-text annotation

population_env.csv column specification
----------------------------------------
population                    str
distance_from_mainland        float  km
island_area_km2               float
Bombus_frequency              float  [0,1]
small_pollinator_frequency    float  [0,1]
effective_population_size_proxy float [0,1]
isolation                     float  [0,1]
pollinator_environment        float  [0,1]
migration_rate                float  [0,1]
"""

from __future__ import annotations

import csv
from pathlib import Path

_DEFAULT_PATTERNS_CSV = Path(__file__).parent / "data" / "observed_patterns.csv"
_DEFAULT_ENV_CSV      = Path(__file__).parent / "data" / "population_env.csv"

# Hard-coded fallback pairwise patterns (used only if CSV is missing)
_FALLBACK_PAIRWISE: list[dict] = [
    {"pattern": "nectar_guide_pairwise",    "type": "pairwise_relation", "variable": "nectar_guide",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima > Hachijo", "weight": "1.0",
     "source": "field/Inoue1986", "notes": "fallback"},
    {"pattern": "selfing_rate_pairwise",    "type": "pairwise_relation", "variable": "selfing_rate",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima < Hachijo", "weight": "1.0",
     "source": "field/Inoue1986", "notes": "fallback"},
    {"pattern": "herkogamy_pairwise",       "type": "pairwise_relation", "variable": "herkogamy",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima > Hachijo", "weight": "0.8",
     "source": "field", "notes": "fallback"},
    {"pattern": "flower_size_pairwise",     "type": "pairwise_relation", "variable": "flower_size",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima > Hachijo", "weight": "0.8",
     "source": "field/Inoue1986", "notes": "fallback"},
    {"pattern": "Fis_pairwise",             "type": "pairwise_relation", "variable": "Fis",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima < Hachijo", "weight": "1.0",
     "source": "genetic", "notes": "fallback"},
    {"pattern": "Bombus_frequency_pairwise","type": "pairwise_relation", "variable": "Bombus_frequency",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima > Hachijo", "weight": "1.0",
     "source": "field/literature", "notes": "fallback"},
]

_ENV_NUMERIC_COLS = (
    "distance_from_mainland",
    "island_area_km2",
    "Bombus_frequency",
    "small_pollinator_frequency",
    "effective_population_size_proxy",
    "isolation",
    "pollinator_environment",
    "migration_rate",
)


# ---------------------------------------------------------------------------
# Pattern loaders
# ---------------------------------------------------------------------------

def load_observed_pattern_table(path: str | Path | None = None) -> list[dict]:
    """Load the full observed pattern table from CSV.

    Returns
    -------
    list of dict
        One dict per pattern row.  All values are strings; callers that need
        floats for weight etc. should cast explicitly.
    """
    p = Path(path) if path else _DEFAULT_PATTERNS_CSV
    try:
        with p.open(encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return list(_FALLBACK_PAIRWISE)


def load_observed_patterns(path: str | Path | None = None) -> dict[str, str]:
    """Return pairwise patterns as ``{variable_name: relation_string}`` (backward compat).

    Only rows with type == 'pairwise_relation' are included.
    The key is the ``variable`` column (e.g. 'nectar_guide'), matching
    the keys returned by simulate_campanula_with_switches / relations_from_outputs.
    """
    return {
        row["variable"]: row["relation"]
        for row in load_observed_pattern_table(path)
        if row.get("type", "pairwise_relation") == "pairwise_relation"
    }


def observed_pairwise_relations(path: str | Path | None = None) -> dict[str, str]:
    """Return pairwise patterns keyed by *variable* name.

    Returns
    -------
    dict
        ``{variable_name: relation_string}`` e.g.
        ``{"nectar_guide": "Oshima > Hachijo", ...}``
    """
    return {
        row["variable"]: row["relation"]
        for row in load_observed_pattern_table(path)
        if row.get("type", "pairwise_relation") == "pairwise_relation"
    }


def observed_gradient_patterns(path: str | Path | None = None) -> list[dict]:
    """Return gradient_slope and rank_order pattern rows.

    These are the gradient POM: abstract directional expectations that do NOT
    name specific population pairs, only the direction of change along the
    isolation gradient (e.g. "nectar_guide decreases with distance").

    Returns
    -------
    list of dict
        Rows with type in {'gradient_slope', 'rank_order'}, with
        ``weight`` cast to float and ``populations`` split to a list.
    """
    rows = []
    for row in load_observed_pattern_table(path):
        ptype = row.get("type", "")
        if ptype not in ("gradient_slope", "rank_order"):
            continue
        out = dict(row)
        out["weight"] = float(row.get("weight", 1.0))
        raw_pops = row.get("populations", "")
        out["populations"] = [p.strip() for p in raw_pops.split(";") if p.strip()]
        rows.append(out)
    return rows


def observed_gradient_only_patterns(path: str | Path | None = None) -> list[dict]:
    """Return ONLY gradient_slope and rank_order rows as raw dicts (unprocessed).

    Unlike observed_gradient_patterns(), this returns the raw CSV rows
    (suitable for passing to evaluate_patterns() directly), without splitting
    the populations field — evaluate_patterns() handles that internally.

    Use this when you want purely gradient-based POM with no population-specific
    pairwise comparisons.
    """
    return [
        row for row in load_observed_pattern_table(path)
        if row.get("type", "") in ("gradient_slope", "rank_order")
    ]


def load_pattern_weights(path: str | Path | None = None) -> dict[str, float]:
    """Return ``{variable_name: weight}`` for pairwise pattern rows.

    Keyed by ``variable`` (e.g. 'nectar_guide') to match simulation output keys.
    Only pairwise_relation rows are included (gradient/rank rows are evaluated
    separately via pattern_evaluator, not via compute_run_distances).
    """
    return {
        row["variable"]: float(row.get("weight", 1.0))
        for row in load_observed_pattern_table(path)
        if row.get("type", "pairwise_relation") == "pairwise_relation"
    }


# ---------------------------------------------------------------------------
# Population environment loader
# ---------------------------------------------------------------------------

def load_population_env(path: str | Path | None = None) -> dict[str, dict]:
    """Load population environment data from CSV.

    Parameters
    ----------
    path:
        Path to population_env.csv.  Defaults to
        ``examples/campanula_izu/data/population_env.csv``.

    Returns
    -------
    dict
        ``{population_name: {column: value}}`` where numeric columns are
        cast to float.  Order reflects CSV row order.

    Examples
    --------
    >>> env = load_population_env()
    >>> env["Oshima"]["Bombus_frequency"]
    0.45
    >>> env["Hachijo"]["isolation"]
    0.85
    """
    p = Path(path) if path else _DEFAULT_ENV_CSV
    result: dict[str, dict] = {}
    try:
        with p.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row["population"]
                entry: dict = {}
                for col, val in row.items():
                    if col == "population":
                        entry[col] = val
                    elif col in _ENV_NUMERIC_COLS:
                        try:
                            entry[col] = float(val)
                        except (ValueError, TypeError):
                            entry[col] = val
                    else:
                        entry[col] = val
                result[name] = entry
    except FileNotFoundError:
        # Minimal fallback for two-population pairwise use
        result = {
            "Oshima": {
                "population": "Oshima",
                "distance_from_mainland": 120.0,
                "island_area_km2": 91.0,
                "Bombus_frequency": 0.45,
                "small_pollinator_frequency": 0.50,
                "effective_population_size_proxy": 0.75,
                "isolation": 0.35,
                "pollinator_environment": 0.62,
                "migration_rate": 0.05,
            },
            "Hachijo": {
                "population": "Hachijo",
                "distance_from_mainland": 290.0,
                "island_area_km2": 69.0,
                "Bombus_frequency": 0.00,
                "small_pollinator_frequency": 0.60,
                "effective_population_size_proxy": 0.35,
                "isolation": 0.85,
                "pollinator_environment": 0.34,
                "migration_rate": 0.01,
            },
        }
    return result


def ordered_populations(path: str | Path | None = None) -> list[str]:
    """Return population names in CSV row order (mainland to most isolated)."""
    return list(load_population_env(path).keys())
