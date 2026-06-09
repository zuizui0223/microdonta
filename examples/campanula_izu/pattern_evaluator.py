"""Pattern evaluator for ecological gradient pattern targets.

Supports four pattern types defined in observed_patterns.csv:

pairwise_relation
    Ordinal comparison between two populations, e.g. "Oshima > Hachijo".
    Match: simulated relation string == observed relation string.

gradient_slope
    The sign of the linear regression slope of a simulated variable
    across a population gradient (e.g. distance_from_mainland).
    Match: sign(simulated_slope) == expected_direction.

rank_order
    The rank order of simulated variable values across populations
    matches an expected ordering (increasing or decreasing).
    Match: Kendall's tau > 0 (correct monotone order).

trait_correlation
    Pearson correlation (slope sign) between two variables across all
    simulated populations.  The ``variable`` column is the response (y)
    and the ``predictor`` column is the explanatory variable (x).
    Predictors can be either a field on PopulationProxyOutput OR a
    column in the env_table (env_table lookup is used as fallback).
    Match: sign(Pearson r) == expected_direction (positive / negative).

Role filtering (Issue #7)
--------------------------
``evaluate_patterns()`` automatically skips rows with
``role == "input_context"``.  Predictor variables (e.g.
``primary_pollinator_frequency``) are injected from ecological_context, not
simulated, so including them in the acceptance criterion would be circular.
Only ``role == "response_target"`` rows count toward ``weighted_match_rate``.

Pass ``response_target_patterns()`` from ``observed_data`` to ensure only
the correct rows reach this function; the role guard here is a defensive
second check.

Entry points
------------
evaluate_patterns(simulated_outputs, observed_rows, env_table)
    Evaluate all response_target pattern rows. Returns EvaluationResult.

weighted_pattern_distance(eval_result)
    Compute ABC distance in [0, 1] from EvaluationResult.

match_pairwise(simulated_relations, pattern_row)
    Evaluate a single pairwise_relation row.

match_gradient_slope(simulated_outputs, env_table, pattern_row)
    Evaluate a single gradient_slope row.

match_rank_order(simulated_outputs, pattern_row)
    Evaluate a single rank_order row.
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
    detail: str  # human-readable explanation


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
        """Fraction of patterns matched (unweighted)."""
        if self.n_total == 0:
            return 0.0
        return self.n_matched / self.n_total

    @property
    def weighted_match_rate(self) -> float:
        """Fraction of weight matched."""
        if self.total_weight == 0.0:
            return 0.0
        return self.matched_weight / self.total_weight

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
    simulated_outputs: list,            # list[PopulationProxyOutput]
    observed_rows: list[dict],          # from response_target_patterns() or load_observed_pattern_table()
    env_table: dict[str, dict],         # from load_ecological_context()
    pairwise_left: str = "Oshima",
    pairwise_right: str = "Hachijo",
) -> EvaluationResult:
    """Evaluate response_target pattern rows against simulated outputs.

    Rows with ``role == "input_context"`` are silently skipped — predictor
    variables are injected from ecological_context, not simulated, so they
    must not count toward ABC acceptance (circular logic prevention).

    Parameters
    ----------
    simulated_outputs:
        List of PopulationProxyOutput objects (one per population).
    observed_rows:
        Pattern rows.  Prefer passing ``response_target_patterns()`` from
        ``observed_data``; this function also guards against input_context rows
        appearing in the list.
    env_table:
        Ecological context dict from ``load_ecological_context()``.
    pairwise_left / pairwise_right:
        Default populations for pairwise comparison when the pattern row
        itself does not specify left/right_population.

    Returns
    -------
    EvaluationResult
    """
    # Build lookup by population name
    by_pop = {o.population: o for o in simulated_outputs}

    # Pre-compute simulated pairwise relations (lazy, for pairwise_relation rows)
    _sim_pairwise_cache: dict[tuple, dict] = {}

    def _get_pairwise_relations(left: str, right: str) -> dict[str, str]:
        key = (left, right)
        if key not in _sim_pairwise_cache:
            from causal_model.simulation import relations_from_outputs
            _sim_pairwise_cache[key] = relations_from_outputs(
                simulated_outputs, left=left, right=right
            )
        return _sim_pairwise_cache[key]

    result = EvaluationResult()
    for row in observed_rows:
        # Defensive role guard: skip input_context rows regardless of how the
        # list was assembled.  Predictor variables must not count toward ABC.
        if row.get("role", "response_target") == "input_context":
            continue
        ptype = row.get("type", "pairwise_relation")
        weight = float(row.get("weight", 1.0))
        variable = row.get("variable", row.get("pattern", ""))
        pattern_id = row.get("pattern", variable)

        if ptype == "pairwise_relation":
            left  = row.get("left_population", pairwise_left) or pairwise_left
            right = row.get("right_population", pairwise_right) or pairwise_right
            sim_relations = _get_pairwise_relations(left, right)
            match = match_pairwise(sim_relations, row)

        elif ptype == "gradient_slope":
            match = match_gradient_slope(by_pop, env_table, row)

        elif ptype == "rank_order":
            match = match_rank_order(by_pop, row)

        elif ptype == "trait_correlation":
            match = match_trait_correlation(by_pop, env_table, row)

        else:
            # Unknown type: skip with a non-match so it counts against acceptance
            match = PatternMatch(
                pattern=pattern_id,
                pattern_type=ptype,
                variable=variable,
                weight=weight,
                matched=False,
                detail=f"Unknown pattern type '{ptype}'",
            )

        result.matches.append(match)

    return result


def weighted_pattern_distance(eval_result: EvaluationResult) -> float:
    """Compute ABC distance = 1 - weighted_match_rate.

    Returns a value in [0, 1] where 0 = perfect match, 1 = no match.
    """
    return 1.0 - eval_result.weighted_match_rate


# ---------------------------------------------------------------------------
# Per-type evaluators
# ---------------------------------------------------------------------------

def match_pairwise(
    simulated_relations: dict[str, str],
    pattern_row: dict,
) -> PatternMatch:
    """Evaluate a pairwise_relation pattern row.

    Parameters
    ----------
    simulated_relations:
        Output of relations_from_outputs(), keyed by variable name.
    pattern_row:
        One row from observed_patterns.csv with type == 'pairwise_relation'.
    """
    variable   = pattern_row.get("variable", pattern_row.get("pattern", ""))
    pattern_id = pattern_row.get("pattern", variable)
    weight     = float(pattern_row.get("weight", 1.0))
    expected   = pattern_row.get("relation", "")

    simulated = simulated_relations.get(variable, "")
    matched = simulated == expected and bool(expected)

    detail = f"sim={simulated!r} expected={expected!r}"
    return PatternMatch(
        pattern=pattern_id,
        pattern_type="pairwise_relation",
        variable=variable,
        weight=weight,
        matched=matched,
        detail=detail,
    )


def match_gradient_slope(
    by_pop: dict,         # {pop_name: PopulationProxyOutput}
    env_table: dict,      # {pop_name: {col: val}}
    pattern_row: dict,
) -> PatternMatch:
    """Evaluate a gradient_slope pattern row.

    Fits a simple linear regression (OLS, no intercept needed) of
    ``variable ~ predictor`` across the specified populations and checks
    whether the slope sign matches expected_direction.

    Parameters
    ----------
    by_pop:
        Dict mapping population name to PopulationProxyOutput.
    env_table:
        Dict mapping population name to environment row (numeric floats).
    pattern_row:
        One CSV row with type == 'gradient_slope'.
    """
    variable   = pattern_row.get("variable", "")
    pattern_id = pattern_row.get("pattern", variable)
    weight     = float(pattern_row.get("weight", 1.0))
    predictor  = pattern_row.get("predictor", "distance_from_mainland")
    expected_dir = pattern_row.get("expected_direction", "").strip().lower()

    raw_pops = pattern_row.get("populations", "")
    pop_list = [p.strip() for p in raw_pops.split(";") if p.strip()]
    # Empty populations field → use ALL simulated populations,
    # sorted by predictor value so the gradient direction is meaningful.
    if not pop_list:
        pop_list = sorted(
            by_pop.keys(),
            key=lambda p: float((env_table.get(p) or {}).get(predictor) or 0),
        )

    if len(pop_list) < 2:
        return PatternMatch(
            pattern=pattern_id, pattern_type="gradient_slope",
            variable=variable, weight=weight, matched=False,
            detail="fewer than 2 populations available",
        )

    xs, ys = [], []
    missing = []
    for pop in pop_list:
        env_row = env_table.get(pop)
        out     = by_pop.get(pop)
        if env_row is None or out is None:
            missing.append(pop)
            continue
        x_val = env_row.get(predictor)
        y_val = getattr(out, variable, None)
        if x_val is None or y_val is None:
            missing.append(pop)
            continue
        xs.append(float(x_val))
        ys.append(float(y_val))

    if len(xs) < 2:
        return PatternMatch(
            pattern=pattern_id, pattern_type="gradient_slope",
            variable=variable, weight=weight, matched=False,
            detail=f"insufficient data (missing populations: {missing})",
        )

    slope = _ols_slope(xs, ys)
    if expected_dir == "negative":
        matched = slope < 0.0
    elif expected_dir == "positive":
        matched = slope > 0.0
    else:
        matched = False

    detail = (
        f"slope={slope:.4f} expected={expected_dir} "
        f"n={len(xs)} pops={pop_list}"
    )
    return PatternMatch(
        pattern=pattern_id, pattern_type="gradient_slope",
        variable=variable, weight=weight, matched=matched, detail=detail,
    )


def match_trait_correlation(
    by_pop: dict,       # {pop_name: PopulationProxyOutput}
    env_table: dict,    # {pop_name: {col: val}}
    pattern_row: dict,
) -> PatternMatch:
    """Evaluate a trait_correlation pattern row.

    Computes the Pearson correlation (via OLS slope sign) between response
    variable y and predictor x across all simulated populations.

    Predictor lookup order:
    1. ``getattr(output, predictor)`` — field on PopulationProxyOutput
    2. ``env_table[pop].get(predictor)`` — environmental column (fallback)

    Parameters
    ----------
    by_pop:
        Dict mapping population name to PopulationProxyOutput.
    env_table:
        Dict mapping population name to environment row.
    pattern_row:
        One CSV row with type == 'trait_correlation'.
        Required fields: variable (y), predictor (x), expected_direction.
    """
    variable     = pattern_row.get("variable", "")
    predictor    = pattern_row.get("predictor", "")
    pattern_id   = pattern_row.get("pattern", variable)
    weight       = float(pattern_row.get("weight", 1.0))
    expected_dir = pattern_row.get("expected_direction", "").strip().lower()

    if not variable or not predictor:
        return PatternMatch(
            pattern=pattern_id, pattern_type="trait_correlation",
            variable=variable, weight=weight, matched=False,
            detail="missing variable or predictor field",
        )

    xs, ys, missing = [], [], []
    for pop, out in by_pop.items():
        y_val = getattr(out, variable, None)
        # Predictor: try output attribute first, then env_table
        x_val = getattr(out, predictor, None)
        if x_val is None:
            env_row = env_table.get(pop, {})
            x_val = env_row.get(predictor)
        if x_val is None or y_val is None:
            missing.append(pop)
            continue
        xs.append(float(x_val))
        ys.append(float(y_val))

    if len(xs) < 3:
        return PatternMatch(
            pattern=pattern_id, pattern_type="trait_correlation",
            variable=variable, weight=weight, matched=False,
            detail=f"insufficient data (n={len(xs)}, missing={missing})",
        )

    slope = _ols_slope(xs, ys)
    # Pearson r has the same sign as OLS slope for the same data
    if expected_dir == "positive":
        matched = slope > 0.0
    elif expected_dir == "negative":
        matched = slope < 0.0
    else:
        matched = False

    detail = (
        f"corr_slope={slope:.4f} expected={expected_dir} "
        f"n={len(xs)} y={variable} x={predictor}"
    )
    return PatternMatch(
        pattern=pattern_id, pattern_type="trait_correlation",
        variable=variable, weight=weight, matched=matched, detail=detail,
    )


def match_rank_order(
    by_pop: dict,  # {pop_name: PopulationProxyOutput}
    pattern_row: dict,
) -> PatternMatch:
    """Evaluate a rank_order pattern row.

    Checks whether the simulated variable values follow the expected
    monotone order (increasing or decreasing) across populations.
    Uses Kendall's tau sign: tau > 0 = correct direction.

    Parameters
    ----------
    by_pop:
        Dict mapping population name to PopulationProxyOutput.
    pattern_row:
        One CSV row with type == 'rank_order'.
    """
    variable   = pattern_row.get("variable", "")
    pattern_id = pattern_row.get("pattern", variable)
    weight     = float(pattern_row.get("weight", 1.0))
    expected_dir = pattern_row.get("expected_direction", "").strip().lower()

    raw_pops = pattern_row.get("populations", "")
    pop_list = [p.strip() for p in raw_pops.split(";") if p.strip()]
    # Empty populations field → use ALL simulated populations in dict order
    # (caller should ensure by_pop is ordered by isolation distance).
    if not pop_list:
        pop_list = list(by_pop.keys())

    if len(pop_list) < 2:
        return PatternMatch(
            pattern=pattern_id, pattern_type="rank_order",
            variable=variable, weight=weight, matched=False,
            detail="fewer than 2 populations specified",
        )

    values, available = [], []
    for pop in pop_list:
        out = by_pop.get(pop)
        if out is None:
            continue
        val = getattr(out, variable, None)
        if val is None:
            continue
        values.append(float(val))
        available.append(pop)

    if len(values) < 2:
        return PatternMatch(
            pattern=pattern_id, pattern_type="rank_order",
            variable=variable, weight=weight, matched=False,
            detail=f"insufficient data for populations {pop_list}",
        )

    tau = _kendall_tau(values)
    if expected_dir == "increasing":
        matched = tau > 0.0
    elif expected_dir == "decreasing":
        matched = tau < 0.0
    else:
        matched = False

    detail = (
        f"tau={tau:.4f} expected={expected_dir} "
        f"values={[round(v, 3) for v in values]} pops={available}"
    )
    return PatternMatch(
        pattern=pattern_id, pattern_type="rank_order",
        variable=variable, weight=weight, matched=matched, detail=detail,
    )


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------

def _ols_slope(xs: list[float], ys: list[float]) -> float:
    """Compute OLS slope of y ~ x without external dependencies."""
    n = len(xs)
    if n < 2:
        return 0.0
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    den = sum((x - x_mean) ** 2 for x in xs)
    if den == 0.0:
        return 0.0
    return num / den


class ABMPopulationProxy:
    """Thin wrapper around ABM final-generation averages for pattern evaluation.

    Mimics the attribute interface of PopulationProxyOutput so that
    evaluate_patterns() can be called with ABM outputs.
    primary_pollinator_frequency is injected from ecological_context, not from ABM.
    """

    # ABM key → PopulationProxyOutput attribute
    _KEY_MAP = {
        "nectar_guide":  "mean_nectar_guide",
        "selfing_rate":  "selfing_rate",
        "herkogamy":     "mean_herkogamy",
        "flower_size":   "mean_flower_size",
        "Fis":           "Fis_proxy",
    }

    def __init__(
        self,
        population: str,
        final_dict: dict,
        env_row: dict | None = None,
    ) -> None:
        self.population = population
        self.nectar_guide  = float(final_dict.get("mean_nectar_guide", 0.5))
        self.selfing_rate  = float(final_dict.get("selfing_rate",      0.5))
        self.herkogamy     = float(final_dict.get("mean_herkogamy",    0.5))
        self.flower_size   = float(final_dict.get("mean_flower_size",  0.5))
        self.Fis           = float(final_dict.get("Fis_proxy",         0.5))
        self.primary_pollinator_frequency = (
            float(env_row.get("primary_pollinator_frequency", 0.0)) if env_row else 0.0
        )
        self.outcrossing_opportunity = max(0.0, 1.0 - self.selfing_rate)
        # ABM tracks mean_neutral_diversity when available; fall back to 0.5
        self.neutral_diversity = float(final_dict.get("mean_neutral_diversity", 0.5))


def _kendall_tau(values: list[float]) -> float:
    """Compute Kendall's tau for a sequence vs its natural index order.

    Positive tau = values increase along the sequence.
    Negative tau = values decrease along the sequence.
    Uses simple concordant/discordant pair counting (O(n^2)).
    """
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
    if total == 0:
        return 0.0
    return (concordant - discordant) / total
