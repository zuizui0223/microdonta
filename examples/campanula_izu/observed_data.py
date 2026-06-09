"""Loader for Campanula Izu observed patterns and ecological context data.

Design principle (Issue #7)
---------------------------
RACH separates two kinds of data:

``ecological_context.csv``  —  **input_context**
    Environmental predictors that *drive* the simulation: isolation distance,
    pollinator availability, effective population size, etc.  These are NOT
    response targets; using them as ABC acceptance criteria would be circular.

``observed_patterns.csv``   —  **response_target** rows
    Empirical or conceptual patterns that the simulation must *reproduce*:
    trait gradients (nectar guide, selfing rate, herkogamy, Fis).  Only rows
    with ``role == "response_target"`` count toward ABC acceptance.
    Rows with ``role == "input_context"`` are predictor variables and are
    excluded from the match calculation automatically.

Loaders
-------
load_ecological_context()
    Canonical loader.  Returns ``{population_name: dict}`` from
    ``ecological_context.csv``.

load_population_env()
    Backward-compatible alias for ``load_ecological_context()``.

load_observed_pattern_table()
    Full ``observed_patterns.csv`` as list of dicts (all roles).

response_target_patterns()
    ``observed_patterns.csv`` rows with ``role == "response_target"`` only.
    Use this as the canonical input to ``evaluate_patterns()``.

observed_gradient_only_patterns()
    ``response_target`` rows of type ``gradient_slope`` or ``rank_order``.
    The primary ABC acceptance criterion in Switch Posterior Inference.

observed_pairwise_relations()
    ``response_target`` pairwise rows as ``{variable: relation_string}``.

observed_gradient_patterns()
    Processed gradient rows (weight cast to float, populations split to list).

load_observed_patterns()
    Legacy: pairwise patterns as ``{variable: relation_string}``.

load_pattern_weights()
    ``{variable: weight}`` for pairwise response_target rows.

ordered_populations()
    Population names in CSV row order (mainland → most isolated).

Default data files
------------------
``examples/campanula_izu/data/ecological_context.csv``
``examples/campanula_izu/data/observed_patterns.csv``

ecological_context.csv column specification
-------------------------------------------
population                       str
distance_from_mainland           float  km
island_area_km2                  float
primary_pollinator_frequency     float  [0,1]  trait-responsive, high-efficiency guild
background_pollinator_frequency  float  [0,1]  trait-non-responsive guild
effective_population_size_proxy  float  [0,1]
isolation                        float  [0,1]
community_pollinator_abundance   float  [0,1]  overall pollinator activity scalar
migration_rate                   float  [0,1]

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
role                str   response_target | input_context
                          Only response_target rows count toward ABC acceptance.
                          input_context rows are predictor variables (e.g.
                          primary_pollinator_frequency) that are injected from
                          ecological_context.csv, not simulated — including them
                          in ABC would be circular.
"""

from __future__ import annotations

import csv
from pathlib import Path

_DEFAULT_PATTERNS_CSV  = Path(__file__).parent / "data" / "observed_patterns.csv"
_DEFAULT_CONTEXT_CSV   = Path(__file__).parent / "data" / "ecological_context.csv"

# Backward-compat alias (old name still works as a path constant)
_DEFAULT_ENV_CSV = _DEFAULT_CONTEXT_CSV

# Hard-coded fallback pairwise patterns (used only if CSV is missing)
_FALLBACK_PAIRWISE: list[dict] = [
    {"pattern": "nectar_guide_pairwise",    "type": "pairwise_relation", "variable": "nectar_guide",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima > Hachijo", "weight": "1.0",
     "source": "field/Inoue1986", "notes": "fallback", "role": "response_target"},
    {"pattern": "selfing_rate_pairwise",    "type": "pairwise_relation", "variable": "selfing_rate",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima < Hachijo", "weight": "1.0",
     "source": "field/Inoue1986", "notes": "fallback", "role": "response_target"},
    {"pattern": "herkogamy_pairwise",       "type": "pairwise_relation", "variable": "herkogamy",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima > Hachijo", "weight": "0.8",
     "source": "field", "notes": "fallback", "role": "response_target"},
    {"pattern": "flower_size_pairwise",     "type": "pairwise_relation", "variable": "flower_size",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima > Hachijo", "weight": "0.8",
     "source": "field/Inoue1986", "notes": "fallback", "role": "response_target"},
    {"pattern": "Fis_pairwise",             "type": "pairwise_relation", "variable": "Fis",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima < Hachijo", "weight": "1.0",
     "source": "genetic", "notes": "fallback", "role": "response_target"},
    {"pattern": "Bombus_frequency_pairwise", "type": "pairwise_relation",
     "variable": "primary_pollinator_frequency",
     "left_population": "Oshima", "right_population": "Hachijo",
     "populations": "", "predictor": "", "expected_direction": "",
     "relation": "Oshima > Hachijo", "weight": "1.0",
     "source": "field/literature", "notes": "fallback", "role": "input_context"},
]

_CONTEXT_NUMERIC_COLS = (
    "distance_from_mainland",
    "island_area_km2",
    "primary_pollinator_frequency",
    "background_pollinator_frequency",
    "effective_population_size_proxy",
    "isolation",
    "community_pollinator_abundance",
    "migration_rate",
)

# Backward-compat alias
_ENV_NUMERIC_COLS = _CONTEXT_NUMERIC_COLS


# ---------------------------------------------------------------------------
# Ecological context loader (input_context)
# ---------------------------------------------------------------------------

def load_ecological_context(path: str | Path | None = None) -> dict[str, dict]:
    """Load ecological context data (environmental predictors) from CSV.

    This is the canonical loader for ``ecological_context.csv``.  The returned
    dict drives simulation inputs — it is NOT an ABC acceptance criterion.
    Use ``response_target_patterns()`` / ``observed_gradient_only_patterns()``
    for the acceptance criterion.

    Parameters
    ----------
    path:
        Path to ecological_context.csv.  Defaults to
        ``examples/campanula_izu/data/ecological_context.csv``.

    Returns
    -------
    dict
        ``{population_name: {column: value}}`` where numeric columns are
        cast to float.  Order reflects CSV row order (mainland → most isolated).
    """
    p = Path(path) if path else _DEFAULT_CONTEXT_CSV
    result: dict[str, dict] = {}
    try:
        with p.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row["population"]
                entry: dict = {}
                for col, val in row.items():
                    if col == "population":
                        entry[col] = val
                    elif col in _CONTEXT_NUMERIC_COLS:
                        try:
                            entry[col] = float(val)
                        except (ValueError, TypeError):
                            entry[col] = val
                    else:
                        entry[col] = val
                result[name] = entry
    except FileNotFoundError:
        # Minimal fallback for two-population use
        result = {
            "Oshima": {
                "population": "Oshima",
                "distance_from_mainland": 120.0,
                "island_area_km2": 91.0,
                "primary_pollinator_frequency": 0.45,
                "background_pollinator_frequency": 0.50,
                "effective_population_size_proxy": 0.75,
                "isolation": 0.35,
                "community_pollinator_abundance": 0.62,
                "migration_rate": 0.05,
            },
            "Hachijo": {
                "population": "Hachijo",
                "distance_from_mainland": 290.0,
                "island_area_km2": 69.0,
                "primary_pollinator_frequency": 0.00,
                "background_pollinator_frequency": 0.60,
                "effective_population_size_proxy": 0.35,
                "isolation": 0.85,
                "community_pollinator_abundance": 0.34,
                "migration_rate": 0.01,
            },
        }
    return result


def load_population_env(path: str | Path | None = None) -> dict[str, dict]:
    """Backward-compatible alias for ``load_ecological_context()``.

    New code should call ``load_ecological_context()`` directly.
    This alias will remain available for compatibility with existing callers.
    """
    return load_ecological_context(path)


def ordered_populations(path: str | Path | None = None) -> list[str]:
    """Return population names in CSV row order (mainland to most isolated)."""
    return list(load_ecological_context(path).keys())


# ---------------------------------------------------------------------------
# Pattern loaders (response_target / input_context)
# ---------------------------------------------------------------------------

def load_observed_pattern_table(path: str | Path | None = None) -> list[dict]:
    """Load the full observed pattern table from CSV (all roles).

    Returns all rows regardless of ``role`` column.  Use
    ``response_target_patterns()`` to get only ABC-relevant rows.

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


def response_target_patterns(path: str | Path | None = None) -> list[dict]:
    """Return only ``role == "response_target"`` rows from observed_patterns.csv.

    These are the rows that count toward ABC acceptance.  Rows with
    ``role == "input_context"`` (predictor variables such as
    ``primary_pollinator_frequency``) are excluded to prevent circular logic:
    predictor variables are injected from ecological_context, not simulated,
    so they would always match regardless of switch state.

    This is the canonical pattern list to pass to ``evaluate_patterns()``.
    """
    return [
        row for row in load_observed_pattern_table(path)
        if row.get("role", "response_target") == "response_target"
    ]


def observed_gradient_only_patterns(path: str | Path | None = None) -> list[dict]:
    """Return ``response_target`` rows usable with the isolation gradient simulation.

    Includes: gradient_slope, rank_order, and trait_correlation patterns.
    Excludes: pairwise_relation (requires named populations Oshima/Hachijo).

    These are the directional patterns that work with any population set —
    they describe the *shape* of the gradient, not comparisons between named
    islands.  This is the primary acceptance criterion in Switch Posterior
    Inference (used by ``switch_inference.py`` and ``test_ecological_invariants.py``).

    Returns raw CSV dicts (suitable for ``evaluate_patterns()``).
    """
    return [
        row for row in response_target_patterns(path)
        if row.get("type", "") in ("gradient_slope", "rank_order", "trait_correlation")
    ]


def observed_gradient_patterns(path: str | Path | None = None) -> list[dict]:
    """Return gradient_slope and rank_order response_target rows, processed.

    Same as ``observed_gradient_only_patterns()`` but with ``weight`` cast to
    float and ``populations`` split to a list.
    """
    rows = []
    for row in observed_gradient_only_patterns(path):
        out = dict(row)
        out["weight"] = float(row.get("weight", 1.0))
        raw_pops = row.get("populations", "")
        out["populations"] = [p.strip() for p in raw_pops.split(";") if p.strip()]
        rows.append(out)
    return rows


def observed_pairwise_relations(path: str | Path | None = None) -> dict[str, str]:
    """Return ``response_target`` pairwise patterns as ``{variable: relation_string}``.

    Returns
    -------
    dict
        ``{variable_name: relation_string}`` e.g.
        ``{"nectar_guide": "Oshima > Hachijo", ...}``
        ``input_context`` rows (e.g. Bombus_frequency_pairwise) are excluded.
    """
    return {
        row["variable"]: row["relation"]
        for row in response_target_patterns(path)
        if row.get("type", "pairwise_relation") == "pairwise_relation"
    }


def load_observed_patterns(path: str | Path | None = None) -> dict[str, str]:
    """Legacy: return ``response_target`` pairwise patterns as ``{variable: relation}``.

    Equivalent to ``observed_pairwise_relations()``.
    New code should use ``observed_pairwise_relations()`` directly.
    """
    return observed_pairwise_relations(path)


def load_pattern_weights(path: str | Path | None = None) -> dict[str, float]:
    """Return ``{variable_name: weight}`` for ``response_target`` pairwise rows.

    Keyed by ``variable`` (e.g. 'nectar_guide') to match simulation output keys.
    Only ``response_target`` pairwise_relation rows are included.
    """
    return {
        row["variable"]: float(row.get("weight", 1.0))
        for row in response_target_patterns(path)
        if row.get("type", "pairwise_relation") == "pairwise_relation"
    }
