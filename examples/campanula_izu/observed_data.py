"""Loaders for Campanula / Izu RACH data roles.

RACH separates epistemic roles by inference function, not by data type:

- input_context: fixed empirical context x_obs used by f(x_obs; theta, s).
- observed_target: independent empirical y_obs used for ABC/RACH acceptance.
- hypothesis_prediction: theory-derived or posterior-predictive expectations.
- diagnostic_only: circular/internal checks excluded from acceptance.
- excluded_from_ABC: rows with provenance gaps or pending field validation.
- future_observation: planned measurements tracked as NOV/design candidates.

`response_target` and `planned_observation` are accepted as legacy aliases.
"""

from __future__ import annotations

import csv
from pathlib import Path

_DEFAULT_PATTERNS_CSV = Path(__file__).parent / "data" / "observed_patterns.csv"
_DEFAULT_CONTEXT_CSV = Path(__file__).parent / "data" / "ecological_context.csv"
_DEFAULT_INDEPENDENT_OBS_CSV = Path(__file__).parent / "data" / "independent_observations.csv"
_DEFAULT_FUTURE_OBS_CSV = Path(__file__).parent / "data" / "future_observations.csv"
_DEFAULT_ABSOLUTE_OBS_CSV = Path(__file__).parent / "data" / "absolute_observations.csv"
_DEFAULT_ENV_CSV = _DEFAULT_CONTEXT_CSV

ABC_TARGET_ROLES = {"observed_target", "response_target"}
EXCLUDED_ROLES = {
    "input_context",
    "hypothesis_prediction",
    "excluded_from_ABC",
    "diagnostic_only",
    "planned_observation",
    "future_observation",
}
FUTURE_ROLES = {"future_observation", "planned_observation"}
PENDING_STATUSES = {
    "pending_pdf_check",
    "pending_field_validation",
    "pending_independent_genetic_validation",
}

_FALLBACK_PAIRWISE: list[dict] = [
    {"pattern": "nectar_guide_pairwise", "type": "pairwise_relation", "variable": "nectar_guide", "left_population": "Oshima", "right_population": "Hachijo", "populations": "", "predictor": "", "expected_direction": "", "relation": "Oshima > Hachijo", "weight": "1.0", "source": "future_field_validation", "notes": "fallback; planned own field data, not an Inoue measurement; NOV candidate for S1", "role": "excluded_from_ABC", "epistemic_status": "pending_field_validation"},
    {"pattern": "selfing_distance", "type": "gradient_slope", "variable": "selfing_rate", "left_population": "", "right_population": "", "populations": "", "predictor": "distance_from_mainland", "expected_direction": "positive", "relation": "", "weight": "1.0", "source": "field/Inoue1990", "notes": "fallback canonical y_obs", "role": "observed_target", "epistemic_status": "field_derived"},
    {"pattern": "flower_size_distance", "type": "gradient_slope", "variable": "flower_size", "left_population": "", "right_population": "", "populations": "", "predictor": "distance_from_mainland", "expected_direction": "negative", "relation": "", "weight": "0.8", "source": "field/InoueAmano1986", "notes": "fallback canonical y_obs", "role": "observed_target", "epistemic_status": "field_derived"},
    {"pattern": "herkogamy_pairwise", "type": "pairwise_relation", "variable": "herkogamy", "left_population": "Oshima", "right_population": "Hachijo", "populations": "", "predictor": "", "expected_direction": "", "relation": "Oshima > Hachijo", "weight": "0.8", "source": "theoretical", "notes": "fallback; latent dichogamy/delayed-selfing, not an Inoue field measurement", "role": "excluded_from_ABC", "epistemic_status": "theoretical_design"},
    {"pattern": "Bombus_frequency_pairwise", "type": "pairwise_relation", "variable": "primary_pollinator_frequency", "left_population": "Oshima", "right_population": "Hachijo", "populations": "", "predictor": "", "expected_direction": "", "relation": "Oshima > Hachijo", "weight": "1.0", "source": "Inoue1986", "notes": "fallback; pollinator assemblage is excluded input context", "role": "input_context", "epistemic_status": "field_derived"},
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


def _to_optional_float(value):
    val = str(value or "").strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def load_ecological_context(path: str | Path | None = None) -> dict[str, dict]:
    """Load fixed empirical context x_obs from ecological_context.csv."""
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
                parsed = _to_optional_float(val)
                entry[col] = parsed if parsed is not None else val
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
    """Return independent ABC/RACH y_obs target rows only."""
    return [
        row for row in load_observed_pattern_table(path)
        if row.get("role", "observed_target") in ABC_TARGET_ROLES
    ]


def response_target_patterns(path: str | Path | None = None) -> list[dict]:
    """Backward-compatible alias for observed_target_patterns()."""
    return observed_target_patterns(path)


def excluded_patterns(path: str | Path | None = None) -> list[dict]:
    """Return input_context, hypothesis_prediction, diagnostics, and excluded rows."""
    return [
        row for row in load_observed_pattern_table(path)
        if row.get("role", "observed_target") in EXCLUDED_ROLES
    ]


def hypothesis_prediction_patterns(path: str | Path | None = None) -> list[dict]:
    """Return hypothesis-derived predictions for posterior checks only."""
    return [row for row in load_observed_pattern_table(path) if row.get("role") == "hypothesis_prediction"]


def diagnostic_only_patterns(path: str | Path | None = None) -> list[dict]:
    """Return circular/internal diagnostic patterns excluded from ABC."""
    return [row for row in load_observed_pattern_table(path) if row.get("role") == "diagnostic_only"]


def planned_observation_patterns(path: str | Path | None = None) -> list[dict]:
    """Return not-yet-collected observed_patterns rows tracked as NOV candidates."""
    return [
        row for row in load_observed_pattern_table(path)
        if row.get("role") in FUTURE_ROLES
        or (
            row.get("role") == "excluded_from_ABC"
            and row.get("epistemic_status") in {"planned", "pending_field_validation"}
        )
    ]


def observed_gradient_only_patterns(path: str | Path | None = None) -> list[dict]:
    """Return observed_target rows usable as pattern targets."""
    accepted_types = {
        "pairwise_relation",
        "gradient_slope",
        "numeric_gradient",
        "rank_order",
        "categorical_transition",
        "trait_correlation",
    }
    return [row for row in observed_target_patterns(path) if row.get("type", "") in accepted_types]


def observed_gradient_patterns(path: str | Path | None = None) -> list[dict]:
    """Processed observed_target pattern rows with numeric weights."""
    rows = []
    for row in observed_gradient_only_patterns(path):
        out = dict(row)
        parsed_weight = _to_optional_float(row.get("weight", 1.0))
        out["weight"] = parsed_weight if parsed_weight is not None else 1.0
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
            parsed_weight = _to_optional_float(row.get("weight", 1.0))
            out[row["variable"]] = parsed_weight if parsed_weight is not None else 1.0
    return out


def load_independent_observations(path: str | Path | None = None) -> list[dict]:
    """Load independent_observations.csv and parse numeric fields."""
    p = Path(path) if path else _DEFAULT_INDEPENDENT_OBS_CSV
    try:
        rows = _read_csv_rows(p)
    except FileNotFoundError:
        return []
    for row in rows:
        for col in ("observed_value", "se"):
            row[col] = _to_optional_float(row.get(col))
    return rows


def load_future_observations(path: str | Path | None = None) -> list[dict]:
    """Load planned future observations for NOV / study-design prioritisation.

    These rows are not ABC targets until measured and promoted to observed_target
    in observed_patterns.csv or independent_observations.csv.
    """
    p = Path(path) if path else _DEFAULT_FUTURE_OBS_CSV
    try:
        rows = _read_csv_rows(p)
    except FileNotFoundError:
        return []
    for row in rows:
        for col in ("expected_weight", "cost", "feasibility", "priority"):
            row[col] = _to_optional_float(row.get(col))
    return rows


def load_absolute_observations(path: str | Path | None = None) -> list[dict]:
    """Load absolute numeric observations and parse numeric fields.

    Empty values and pending rows are deliberately preserved outside acceptance.
    A row can become an acceptance target only when ``role == observed_target``,
    ``observed_value`` is numeric, and ``epistemic_status`` is not pending.
    """
    p = Path(path) if path else _DEFAULT_ABSOLUTE_OBS_CSV
    try:
        rows = _read_csv_rows(p)
    except FileNotFoundError:
        return []
    for row in rows:
        for col in ("observed_value", "se", "scale", "weight"):
            row[col] = _to_optional_float(row.get(col))
        if row.get("weight") is None:
            row["weight"] = 1.0
    return rows


def observed_absolute_targets(path: str | Path | None = None) -> list[dict]:
    """Return measured absolute observations eligible for acceptance."""
    return [
        row for row in load_absolute_observations(path)
        if row.get("role") in ABC_TARGET_ROLES
        and row.get("observed_value") is not None
        and row.get("epistemic_status") not in PENDING_STATUSES
    ]


def future_absolute_observations(path: str | Path | None = None) -> list[dict]:
    """Return future or pending absolute observations for NOV/study design."""
    return [
        row for row in load_absolute_observations(path)
        if row.get("role") in FUTURE_ROLES
        or row.get("epistemic_status") in PENDING_STATUSES
    ]


def future_observation_patterns(path: str | Path | None = None) -> list[dict]:
    """Return planned future observations tracked as NOV/design candidates."""
    return load_future_observations(path)


def nov_candidate_observations(path: str | Path | None = None) -> list[dict]:
    """Alias for future_observation_patterns()."""
    return future_observation_patterns(path)
