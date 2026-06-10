"""Loaders for Campanula / Izu RACH data roles.

RACH separates several epistemic roles:

- input_context: fixed empirical context x_obs used by f(x_obs; theta, s), excluded from ABC.
- observed_target: independent empirical response observations used for ABC/RACH acceptance.
- hypothesis_prediction: theoretical or posterior-predictive expectations, excluded by default.
- diagnostic_only: circular/internal checks such as syndrome definitions, excluded by default.

`response_target` is accepted only as a backward-compatible alias for old data files.
"""

from __future__ import annotations

import csv
from pathlib import Path

_DEFAULT_PATTERNS_CSV = Path(__file__).parent / "data" / "observed_patterns.csv"
_DEFAULT_CONTEXT_CSV = Path(__file__).parent / "data" / "ecological_context.csv"
_DEFAULT_INDEPENDENT_OBS_CSV = Path(__file__).parent / "data" / "independent_observations.csv"
_DEFAULT_ENV_CSV = _DEFAULT_CONTEXT_CSV

ABC_TARGET_ROLES = {"observed_target", "response_target"}  # response_target is legacy
EXCLUDED_ROLES = {"input_context", "hypothesis_prediction", "diagnostic_only"}

_FALLBACK_PAIRWISE: list[dict] = [
    {"pattern": "nectar_guide_pairwise", "type": "pairwise_relation", "variable": "nectar_guide", "left_population": "Oshima", "right_population": "Hachijo", "populations": "", "predictor": "", "expected_direction": "", "relation": "Oshima > Hachijo", "weight": "1.0", "source": "field/Inoue1986", "notes": "fallback", "role": "observed_target"},
    {"pattern": "selfing_rate_pairwise", "type": "pairwise_relation", "variable": "selfing_rate", "left_population": "Oshima", "right_population": "Hachijo", "populations": "", "predictor": "", "expected_direction": "", "relation": "Oshima < Hachijo", "weight": "1.0", "source": "field/Inoue1986", "notes": "fallback", "role": "observed_target"},
    {"pattern": "herkogamy_pairwise", "type": "pairwise_relation", "variable": "herkogamy", "left_population": "Oshima", "right_population": "Hachijo", "populations": "", "predictor": "", "expected_direction": "", "relation": "Oshima > Hachijo", "weight": "0.8", "source": "field", "notes": "fallback", "role": "observed_target"},
    {"pattern": "flower_size_pairwise", "type": "pairwise_relation", "variable": "flower_size", "left_population": "Oshima", "right_population": "Hachijo", "populations": "", "predictor": "", "expected_direction": "", "relation": "Oshima > Hachijo", "weight": "0.8", "source": "field/Inoue1986", "notes": "fallback", "role": "observed_target"},
    {"pattern": "Fis_pairwise", "type": "pairwise_relation", "variable": "Fis", "left_population": "Oshima", "right_population": "Hachijo", "populations": "", "predictor": "", "expected_direction": "", "relation": "Oshima < Hachijo", "weight": "0.5", "source": "genetic", "notes": "fallback; down-weighted — Fis proxy derived from selfing_rate in model", "role": "observed_target"},
    {"pattern": "Bombus_frequency_pairwise", "type": "pairwise_relation", "variable": "primary_pollinator_frequency", "left_population": "Oshima", "right_population": "Hachijo", "populations": "", "predictor": "", "expected_direction": "", "relation": "Oshima > Hachijo", "weight": "1.0", "source": "field/literature", "notes": "fallback; excluded input context", "role": "input_context"},
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
_ENV_NUMERIC_COLS = _CONTEXT_NUMERIC_COLS


def _read_csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_ecological_context(path: str | Path | None = None) -> dict[str, dict]:
    """Load fixed empirical context x_obs from ecological_context.csv.

    These values drive simulations and are excluded from ABC target distance.
    """
    p = Path(path) if path else _DEFAULT_CONTEXT_CSV
    result: dict[str, dict] = {}
    try:
        rows = _read_csv_rows(p)
    except FileNotFoundError:
        rows = [
            {"population": "Oshima", "distance_from_mainland": "120", "island_area_km2": "91", "primary_pollinator_frequency": "0.45", "background_pollinator_frequency": "0.50", "effective_population_size_proxy": "0.75", "isolation": "0.35", "community_pollinator_abundance": "0.62", "migration_rate": "0.05"},
            {"population": "Hachijo", "distance_from_mainland": "290", "island_area_km2": "69", "primary_pollinator_frequency": "0.00", "background_pollinator_frequency": "0.60", "effective_population_size_proxy": "0.35", "isolation": "0.85", "community_pollinator_abundance": "0.34", "migration_rate": "0.01"},
        ]
    for row in rows:
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
    return result


def load_population_env(path: str | Path | None = None) -> dict[str, dict]:
    """Backward-compatible alias for load_ecological_context()."""
    return load_ecological_context(path)


def ordered_populations(path: str | Path | None = None) -> list[str]:
    """Return population names in CSV order."""
    return list(load_ecological_context(path).keys())


def load_observed_pattern_table(path: str | Path | None = None) -> list[dict]:
    """Load all observed_patterns.csv rows, including excluded roles."""
    p = Path(path) if path else _DEFAULT_PATTERNS_CSV
    try:
        return _read_csv_rows(p)
    except FileNotFoundError:
        return list(_FALLBACK_PAIRWISE)


def observed_target_patterns(path: str | Path | None = None) -> list[dict]:
    """Return independent ABC/RACH target rows only.

    Default strict RACH acceptance uses only role == observed_target.
    The legacy role response_target is also accepted for backward compatibility.
    """
    return [
        row for row in load_observed_pattern_table(path)
        if row.get("role", "observed_target") in ABC_TARGET_ROLES
    ]


def response_target_patterns(path: str | Path | None = None) -> list[dict]:
    """Backward-compatible alias for observed_target_patterns()."""
    return observed_target_patterns(path)


def excluded_patterns(path: str | Path | None = None) -> list[dict]:
    """Return input_context, hypothesis_prediction, and diagnostic_only rows."""
    return [
        row for row in load_observed_pattern_table(path)
        if row.get("role", "observed_target") in EXCLUDED_ROLES
    ]


def hypothesis_prediction_patterns(path: str | Path | None = None) -> list[dict]:
    """Return hypothesis-derived predictions for posterior checks only."""
    return [
        row for row in load_observed_pattern_table(path)
        if row.get("role") == "hypothesis_prediction"
    ]


def diagnostic_only_patterns(path: str | Path | None = None) -> list[dict]:
    """Return circular/internal diagnostic patterns excluded from ABC."""
    return [
        row for row in load_observed_pattern_table(path)
        if row.get("role") == "diagnostic_only"
    ]


def observed_gradient_only_patterns(path: str | Path | None = None) -> list[dict]:
    """Return observed_target rows usable as pattern targets.

    Historical name retained. Under strict RACH this may return pairwise endpoint
    targets if no independent observed gradient targets exist. Hypothesis-derived
    conceptual gradients are excluded.
    """
    return [
        row for row in observed_target_patterns(path)
        if row.get("type", "") in ("pairwise_relation", "gradient_slope", "rank_order", "trait_correlation")
    ]


def observed_gradient_patterns(path: str | Path | None = None) -> list[dict]:
    """Processed observed_target pattern rows with numeric weights."""
    rows = []
    for row in observed_gradient_only_patterns(path):
        out = dict(row)
        try:
            out["weight"] = float(row.get("weight", 1.0))
        except (ValueError, TypeError):
            out["weight"] = 1.0
        raw_pops = row.get("populations", "")
        out["populations"] = [p.strip() for p in raw_pops.split(";") if p.strip()]
        rows.append(out)
    return rows


def observed_pairwise_relations(path: str | Path | None = None) -> dict[str, str]:
    """Return observed_target pairwise patterns as {variable: relation}."""
    return {
        row["variable"]: row["relation"]
        for row in observed_target_patterns(path)
        if row.get("type", "pairwise_relation") == "pairwise_relation"
    }


def load_observed_patterns(path: str | Path | None = None) -> dict[str, str]:
    """Legacy alias for observed_pairwise_relations()."""
    return observed_pairwise_relations(path)


def load_pattern_weights(path: str | Path | None = None) -> dict[str, float]:
    """Return {variable: weight} for observed_target pairwise rows."""
    out: dict[str, float] = {}
    for row in observed_target_patterns(path):
        if row.get("type", "pairwise_relation") == "pairwise_relation":
            try:
                out[row["variable"]] = float(row.get("weight", 1.0))
            except (ValueError, TypeError):
                out[row["variable"]] = 1.0
    return out


def load_independent_observations(path: str | Path | None = None) -> list[dict]:
    """Load independent_observations.csv.

    Rows with role=observed_target are future numeric y_obs targets; rows with
    role=input_context are fixed x_obs context and excluded from target distance.
    Empty numeric fields are preserved as None.
    """
    p = Path(path) if path else _DEFAULT_INDEPENDENT_OBS_CSV
    try:
        rows = _read_csv_rows(p)
    except FileNotFoundError:
        return []
    for row in rows:
        for col in ("observed_value", "se"):
            val = str(row.get(col, "")).strip()
            if not val:
                row[col] = None
            else:
                try:
                    row[col] = float(val)
                except ValueError:
                    row[col] = None
    return rows
