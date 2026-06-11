"""Pattern evaluator for ecological gradient pattern targets.

Supported pattern types
-----------------------
pairwise_relation
    Ordinal comparison between two populations, e.g. ``Oshima > Hachijo``.

gradient_slope
    Sign of a simulated variable along an environmental predictor.

numeric_gradient
    Numeric gradient target for PDF-transcribed or measured values.  It uses the
    same slope-sign logic as ``gradient_slope`` but can additionally check
    optional CSV columns such as ``min_slope`` / ``max_slope`` when present.

rank_order
    Monotone rank order across populations.

categorical_transition
    Ordered categorical sequence across populations, e.g.
    ``SI_outcrossing -> SC_mixed -> SC_selfing``.  This is intended for
    breeding-system transitions once category provenance is source-confirmed.

trait_correlation
    Sign of association between two simulated or contextual variables.

Role filtering
--------------
Only ``observed_target`` (and legacy ``response_target``) rows enter ABC/RACH
acceptance.  ``input_context`` is x_obs and is injected into the simulator;
``hypothesis_prediction``, ``diagnostic_only``, and ``excluded_from_ABC`` are
not used as acceptance targets.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PatternMatch:
    """Result of evaluating one pattern row."""

    pattern: str
    pattern_type: str
    variable: str
    weight: float
    matched: bool
    detail: str


@dataclass
class EvaluationResult:
    """Aggregate result of evaluating all patterns against simulated outputs."""

    matches: list[PatternMatch] = field(default_factory=list)

    @property
    def n_total(self) -> int:
        return len(self.matches)

    @property
    def n_matched(self) -> int:
        return sum(1 for m in self.matches if m.matched)

    @property
    def total_weight(self) -> float:
        return sum(m.weight for m in self.matches)

    @property
    def matched_weight(self) -> float:
        return sum(m.weight for m in self.matches if m.matched)

    @property
    def simple_match_rate(self) -> float:
        return self.n_matched / self.n_total if self.n_total else 0.0

    @property
    def weighted_match_rate(self) -> float:
        return self.matched_weight / self.total_weight if self.total_weight else 0.0

    def summary_dict(self) -> dict:
        return {
            "n_total": self.n_total,
            "n_matched": self.n_matched,
            "simple_match_rate": round(self.simple_match_rate, 4),
            "total_weight": round(self.total_weight, 4),
            "matched_weight": round(self.matched_weight, 4),
            "weighted_match_rate": round(self.weighted_match_rate, 4),
        }


# ---------------------------------------------------------------------------
# Top-level evaluator
# ---------------------------------------------------------------------------

def evaluate_patterns(
    simulated_outputs: list,
    observed_rows: list[dict],
    env_table: dict[str, dict],
    pairwise_left: str = "Oshima",
    pairwise_right: str = "Hachijo",
) -> EvaluationResult:
    """Evaluate observed_target rows against simulated outputs.

    Rows with roles other than ``observed_target`` / legacy ``response_target``
    are skipped so that x_obs, hypothesis predictions, diagnostics, and future
    observations do not enter ABC acceptance.
    """
    by_pop = {o.population: o for o in simulated_outputs}
    _sim_pairwise_cache: dict[tuple[str, str], dict[str, str]] = {}

    def _get_pairwise_relations(left: str, right: str) -> dict[str, str]:
        key = (left, right)
        if key not in _sim_pairwise_cache:
            from causal_model.phenomenological_model import relations_from_outputs
            _sim_pairwise_cache[key] = relations_from_outputs(
                simulated_outputs, left=left, right=right
            )
        return _sim_pairwise_cache[key]

    result = EvaluationResult()
    for row in observed_rows:
        role = row.get("role", "observed_target")
        if role not in ("observed_target", "response_target"):
            continue

        ptype = row.get("type", "pairwise_relation")
        weight = _to_float(row.get("weight", 1.0), 1.0)
        variable = row.get("variable", row.get("pattern", ""))
        pattern_id = row.get("pattern", variable)

        if ptype == "pairwise_relation":
            left = row.get("left_population", pairwise_left) or pairwise_left
            right = row.get("right_population", pairwise_right) or pairwise_right
            match = match_pairwise(_get_pairwise_relations(left, right), row)
        elif ptype == "gradient_slope":
            match = match_gradient_slope(by_pop, env_table, row)
        elif ptype == "numeric_gradient":
            match = match_numeric_gradient(by_pop, env_table, row)
        elif ptype == "rank_order":
            match = match_rank_order(by_pop, row)
        elif ptype == "categorical_transition":
            match = match_categorical_transition(by_pop, env_table, row)
        elif ptype == "trait_correlation":
            match = match_trait_correlation(by_pop, env_table, row)
        else:
            match = PatternMatch(
                pattern=pattern_id,
                pattern_type=ptype,
                variable=variable,
                weight=weight,
                matched=False,
                detail=f"Unknown pattern type {ptype!r}",
            )
        result.matches.append(match)
    return result


def weighted_pattern_distance(eval_result: EvaluationResult) -> float:
    """Compute ABC distance = 1 - weighted_match_rate."""
    return 1.0 - eval_result.weighted_match_rate


# ---------------------------------------------------------------------------
# Per-type evaluators
# ---------------------------------------------------------------------------

def match_pairwise(simulated_relations: dict[str, str], pattern_row: dict) -> PatternMatch:
    """Evaluate a pairwise_relation pattern row."""
    variable = pattern_row.get("variable", pattern_row.get("pattern", ""))
    pattern_id = pattern_row.get("pattern", variable)
    weight = _to_float(pattern_row.get("weight", 1.0), 1.0)
    expected = pattern_row.get("relation", "")
    simulated = simulated_relations.get(variable, "")
    return PatternMatch(
        pattern=pattern_id,
        pattern_type="pairwise_relation",
        variable=variable,
        weight=weight,
        matched=bool(expected) and simulated == expected,
        detail=f"sim={simulated!r} expected={expected!r}",
    )


def match_gradient_slope(by_pop: dict, env_table: dict, pattern_row: dict) -> PatternMatch:
    """Evaluate a gradient_slope pattern row by slope sign."""
    variable = pattern_row.get("variable", "")
    pattern_id = pattern_row.get("pattern", variable)
    weight = _to_float(pattern_row.get("weight", 1.0), 1.0)
    predictor = pattern_row.get("predictor", "distance_from_mainland") or "distance_from_mainland"
    expected_dir = pattern_row.get("expected_direction", "").strip().lower()

    points, missing = _collect_xy(by_pop, env_table, variable, predictor, pattern_row)
    if len(points) < 2:
        return PatternMatch(
            pattern=pattern_id,
            pattern_type="gradient_slope",
            variable=variable,
            weight=weight,
            matched=False,
            detail=f"insufficient data (n={len(points)}, missing={missing})",
        )
    xs = [p[1] for p in points]
    ys = [p[2] for p in points]
    slope = _ols_slope(xs, ys)
    matched = _direction_matches(slope, expected_dir)
    return PatternMatch(
        pattern=pattern_id,
        pattern_type="gradient_slope",
        variable=variable,
        weight=weight,
        matched=matched,
        detail=f"slope={slope:.4f} expected={expected_dir} n={len(points)} pops={[p[0] for p in points]}",
    )


def match_numeric_gradient(by_pop: dict, env_table: dict, pattern_row: dict) -> PatternMatch:
    """Evaluate a numeric_gradient row.

    The default check is the same as ``gradient_slope``.  If optional numeric
    bounds are present in the row, they are also enforced:

    - ``min_slope``: simulated slope must be >= this value
    - ``max_slope``: simulated slope must be <= this value
    - ``min_abs_slope``: abs(simulated slope) must be >= this value

    This lets future PDF-transcribed or field-measured gradients replace purely
    directional targets without changing the evaluator interface.
    """
    variable = pattern_row.get("variable", "")
    pattern_id = pattern_row.get("pattern", variable)
    weight = _to_float(pattern_row.get("weight", 1.0), 1.0)
    predictor = pattern_row.get("predictor", "distance_from_mainland") or "distance_from_mainland"
    expected_dir = pattern_row.get("expected_direction", "").strip().lower()

    points, missing = _collect_xy(by_pop, env_table, variable, predictor, pattern_row)
    if len(points) < 2:
        return PatternMatch(
            pattern=pattern_id,
            pattern_type="numeric_gradient",
            variable=variable,
            weight=weight,
            matched=False,
            detail=f"insufficient data (n={len(points)}, missing={missing})",
        )
    xs = [p[1] for p in points]
    ys = [p[2] for p in points]
    slope = _ols_slope(xs, ys)

    checks: list[bool] = []
    if expected_dir:
        checks.append(_direction_matches(slope, expected_dir))
    min_slope = _optional_float(pattern_row.get("min_slope"))
    max_slope = _optional_float(pattern_row.get("max_slope"))
    min_abs = _optional_float(pattern_row.get("min_abs_slope"))
    if min_slope is not None:
        checks.append(slope >= min_slope)
    if max_slope is not None:
        checks.append(slope <= max_slope)
    if min_abs is not None:
        checks.append(abs(slope) >= min_abs)
    if not checks:
        checks.append(True)

    matched = all(checks)
    detail = (
        f"numeric_slope={slope:.4f} expected={expected_dir or 'none'} "
        f"min_slope={min_slope} max_slope={max_slope} min_abs_slope={min_abs} "
        f"n={len(points)} pops={[p[0] for p in points]}"
    )
    return PatternMatch(
        pattern=pattern_id,
        pattern_type="numeric_gradient",
        variable=variable,
        weight=weight,
        matched=matched,
        detail=detail,
    )


def match_categorical_transition(by_pop: dict, env_table: dict, pattern_row: dict) -> PatternMatch:
    """Evaluate an ordered categorical transition across populations.

    The expected sequence is read from ``relation`` as ``A -> B -> C``.  If
    ``populations`` is empty, populations are sorted by ``predictor`` (default:
    distance_from_mainland).  Observed categories are obtained in this order:

    1. an output attribute matching ``variable`` if it is already a string;
    2. a context value in ``env_table``;
    3. derived categories for known continuous variables such as selfing_rate.

    This is mainly for source-confirmed transitions such as
    SI_outcrossing -> SC_mixed -> SC_selfing.
    """
    variable = pattern_row.get("variable", "")
    pattern_id = pattern_row.get("pattern", variable)
    weight = _to_float(pattern_row.get("weight", 1.0), 1.0)
    expected = _parse_transition(pattern_row.get("relation", ""))
    predictor = pattern_row.get("predictor", "distance_from_mainland") or "distance_from_mainland"
    pop_list = _population_list(by_pop, env_table, predictor, pattern_row)

    observed: list[str] = []
    missing: list[str] = []
    for pop in pop_list:
        out = by_pop.get(pop)
        env_row = env_table.get(pop, {})
        cat = _category_for(pop, out, env_row, variable)
        if cat is None:
            missing.append(pop)
        else:
            observed.append(cat)

    matched = bool(expected) and observed == expected
    detail = f"observed={' -> '.join(observed)} expected={' -> '.join(expected)} missing={missing} pops={pop_list}"
    return PatternMatch(
        pattern=pattern_id,
        pattern_type="categorical_transition",
        variable=variable,
        weight=weight,
        matched=matched,
        detail=detail,
    )


def match_trait_correlation(by_pop: dict, env_table: dict, pattern_row: dict) -> PatternMatch:
    """Evaluate a trait_correlation pattern row by OLS slope sign."""
    variable = pattern_row.get("variable", "")
    predictor = pattern_row.get("predictor", "")
    pattern_id = pattern_row.get("pattern", variable)
    weight = _to_float(pattern_row.get("weight", 1.0), 1.0)
    expected_dir = pattern_row.get("expected_direction", "").strip().lower()

    if not variable or not predictor:
        return PatternMatch(
            pattern=pattern_id,
            pattern_type="trait_correlation",
            variable=variable,
            weight=weight,
            matched=False,
            detail="missing variable or predictor field",
        )

    xs, ys, missing = [], [], []
    for pop, out in by_pop.items():
        y_val = _value_from_output_or_env(pop, out, env_table, variable)
        x_val = _value_from_output_or_env(pop, out, env_table, predictor)
        if x_val is None or y_val is None:
            missing.append(pop)
            continue
        xs.append(float(x_val))
        ys.append(float(y_val))

    if len(xs) < 3:
        return PatternMatch(
            pattern=pattern_id,
            pattern_type="trait_correlation",
            variable=variable,
            weight=weight,
            matched=False,
            detail=f"insufficient data (n={len(xs)}, missing={missing})",
        )

    slope = _ols_slope(xs, ys)
    matched = _direction_matches(slope, expected_dir)
    return PatternMatch(
        pattern=pattern_id,
        pattern_type="trait_correlation",
        variable=variable,
        weight=weight,
        matched=matched,
        detail=f"corr_slope={slope:.4f} expected={expected_dir} n={len(xs)} y={variable} x={predictor}",
    )


def match_rank_order(by_pop: dict, pattern_row: dict) -> PatternMatch:
    """Evaluate a rank_order pattern row."""
    variable = pattern_row.get("variable", "")
    pattern_id = pattern_row.get("pattern", variable)
    weight = _to_float(pattern_row.get("weight", 1.0), 1.0)
    expected_dir = pattern_row.get("expected_direction", "").strip().lower()

    raw_pops = pattern_row.get("populations", "")
    pop_list = [p.strip() for p in raw_pops.split(";") if p.strip()] or list(by_pop.keys())

    values, available = [], []
    for pop in pop_list:
        out = by_pop.get(pop)
        val = getattr(out, variable, None) if out is not None else None
        if val is None:
            continue
        values.append(float(val))
        available.append(pop)

    if len(values) < 2:
        return PatternMatch(
            pattern=pattern_id,
            pattern_type="rank_order",
            variable=variable,
            weight=weight,
            matched=False,
            detail=f"insufficient data for populations {pop_list}",
        )

    tau = _kendall_tau(values)
    if expected_dir == "increasing":
        matched = tau > 0.0
    elif expected_dir == "decreasing":
        matched = tau < 0.0
    else:
        matched = False
    return PatternMatch(
        pattern=pattern_id,
        pattern_type="rank_order",
        variable=variable,
        weight=weight,
        matched=matched,
        detail=f"tau={tau:.4f} expected={expected_dir} values={[round(v, 3) for v in values]} pops={available}",
    )


# ---------------------------------------------------------------------------
# Data extraction helpers
# ---------------------------------------------------------------------------

def _collect_xy(by_pop: dict, env_table: dict, variable: str, predictor: str, pattern_row: dict) -> tuple[list[tuple[str, float, float]], list[str]]:
    pop_list = _population_list(by_pop, env_table, predictor, pattern_row)
    points: list[tuple[str, float, float]] = []
    missing: list[str] = []
    for pop in pop_list:
        out = by_pop.get(pop)
        x_val = (env_table.get(pop) or {}).get(predictor)
        y_val = getattr(out, variable, None) if out is not None else None
        if x_val is None or y_val is None:
            missing.append(pop)
            continue
        points.append((pop, float(x_val), float(y_val)))
    return points, missing


def _population_list(by_pop: dict, env_table: dict, predictor: str, pattern_row: dict) -> list[str]:
    raw_pops = pattern_row.get("populations", "")
    pop_list = [p.strip() for p in raw_pops.split(";") if p.strip()]
    if pop_list:
        return pop_list
    return sorted(
        by_pop.keys(),
        key=lambda p: float((env_table.get(p) or {}).get(predictor) or 0.0),
    )


def _value_from_output_or_env(pop: str, out, env_table: dict, key: str):
    val = getattr(out, key, None) if out is not None else None
    if val is not None:
        return val
    return (env_table.get(pop) or {}).get(key)


def _category_for(pop: str, out, env_row: dict, variable: str) -> str | None:
    val = getattr(out, variable, None) if out is not None else None
    if isinstance(val, str):
        return val
    if val is None:
        val = env_row.get(variable)
    if isinstance(val, str):
        return val

    # Derived categories for common continuous variables in the Campanula example.
    if variable in {"selfing_rate", "breeding_system", "breeding_system_category"}:
        numeric = getattr(out, "selfing_rate", None) if out is not None else None
        if numeric is None:
            numeric = env_row.get("selfing_rate")
        if numeric is None:
            return None
        x = float(numeric)
        if x < 0.25:
            return "SI_outcrossing"
        if x < 0.65:
            return "SC_mixed"
        return "SC_selfing"
    return None


def _parse_transition(text: str) -> list[str]:
    if not text:
        return []
    return [part.strip() for part in text.split("->") if part.strip()]


def _direction_matches(value: float, expected_dir: str) -> bool:
    if expected_dir == "negative":
        return value < 0.0
    if expected_dir == "positive":
        return value > 0.0
    if expected_dir == "zero":
        return value == 0.0
    return False


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------

def _to_float(v, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _optional_float(v) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _ols_slope(xs: list[float], ys: list[float]) -> float:
    """Compute OLS slope of y ~ x without external dependencies."""
    n = len(xs)
    if n < 2:
        return 0.0
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    den = sum((x - x_mean) ** 2 for x in xs)
    return 0.0 if den == 0.0 else num / den


def _kendall_tau(values: list[float]) -> float:
    """Compute Kendall's tau for a sequence vs its natural index order."""
    n = len(values)
    if n < 2:
        return 0.0
    concordant = discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            diff = values[j] - values[i]
            if diff > 0:
                concordant += 1
            elif diff < 0:
                discordant += 1
    total = concordant + discordant
    return 0.0 if total == 0 else (concordant - discordant) / total


class ABMPopulationProxy:
    """Thin wrapper around ABM final-generation averages for pattern evaluation."""

    _KEY_MAP = {
        "nectar_guide": "mean_nectar_guide",
        "selfing_rate": "selfing_rate",
        "herkogamy": "mean_herkogamy",
        "flower_size": "mean_flower_size",
        "Fis": "Fis_proxy",
    }

    def __init__(self, population: str, final_dict: dict, env_row: dict | None = None) -> None:
        self.population = population
        self.nectar_guide = float(final_dict.get("mean_nectar_guide", 0.5))
        self.selfing_rate = float(final_dict.get("selfing_rate", 0.5))
        self.herkogamy = float(final_dict.get("mean_herkogamy", 0.5))
        self.flower_size = float(final_dict.get("mean_flower_size", 0.5))
        self.Fis = float(final_dict.get("Fis_proxy", 0.5))
        self.primary_pollinator_frequency = (
            float(env_row.get("primary_pollinator_frequency", 0.0)) if env_row else 0.0
        )
        self.outcrossing_opportunity = max(0.0, 1.0 - self.selfing_rate)
        self.neutral_diversity = float(final_dict.get("mean_neutral_diversity", 0.5))
