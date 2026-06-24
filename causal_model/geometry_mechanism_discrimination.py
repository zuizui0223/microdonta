"""Competing-mechanism test for the information in trait-space geometry.

This is a deliberately adversarial *theory* experiment.  Several ecological
mechanism families are constructed to reproduce the same coarse pattern-oriented
summary:

    * the realised mean trait declines; and
    * a viable resident population persists.

The coarse POM therefore leaves all mechanisms admissible.  The experiment then
adds the geometry of the viable trait support -- its lower and upper edges,
breadth, and number of connected components -- and asks which candidates remain.

The point is not that any signature is universally diagnostic.  In particular,
``upper_edge_contraction`` is intentionally shared by relationship-benefit loss
and a directional connectivity filter.  A result that keeps both is reported as
ambiguous, not silently promoted to a causal identification.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp
from random import Random
from typing import Callable, Iterable, Literal, Mapping

from causal_model.abm_family_adapter import (
    ProgramSweepSummary,
    RobustnessPolicy,
    SweepRecord,
    summarise_sweep,
)

GeometryLabel = Literal[
    "upper_edge_contraction",
    "shift",
    "fragmentation",
    "conserved",
    "other",
]


@dataclass(frozen=True)
class CoarsePOM:
    """Low-resolution summary intentionally excluding trait-space geometry."""

    mean_before: float
    mean_after: float
    persistent_after: bool

    @property
    def mean_delta(self) -> float:
        return self.mean_after - self.mean_before


@dataclass(frozen=True)
class CoarsePOMTarget:
    """Declared coarse pattern shared by the competing mechanism models.

    This target represents a common empirical situation where mean phenotype and
    persistence are observed, but the occupied/viable support is not.
    """

    after_mean_min: float = 0.24
    after_mean_max: float = 0.43
    min_mean_decline: float = 0.09
    require_persistence: bool = True

    def matches(self, pom: CoarsePOM) -> bool:
        return (
            self.after_mean_min <= pom.mean_after <= self.after_mean_max
            and pom.mean_delta <= -self.min_mean_decline
            and (pom.persistent_after or not self.require_persistence)
        )


@dataclass(frozen=True)
class TraitGeometry:
    """Support geometry of a viable trait set on a fixed trait grid."""

    lower_edge: float
    upper_edge: float
    breadth: float
    n_components: int


@dataclass(frozen=True)
class GeometryChange:
    """Before/after support geometry and its qualitative signature."""

    before: TraitGeometry
    after: TraitGeometry
    label: GeometryLabel


@dataclass(frozen=True)
class MechanismTrial:
    """One parameter-region draw from one competing mechanism family."""

    mechanism_id: str
    motifs: frozenset[str]
    parameters: Mapping[str, float]
    before_mask: tuple[bool, ...]
    after_mask: tuple[bool, ...]
    coarse_pom: CoarsePOM
    geometry: GeometryChange
    region_id: str
    seed: int


@dataclass(frozen=True)
class GeometryResolution:
    """Candidate mechanisms surviving after a stated geometry observation."""

    observed_geometry: GeometryLabel
    survivors: tuple[str, ...]
    eliminated: tuple[str, ...]
    status: Literal["unique", "ambiguous", "unsupported"]


@dataclass(frozen=True)
class GeometryDiscriminationReport:
    """Auditable output of the competing-mechanism discrimination experiment."""

    target: CoarsePOMTarget
    policy: RobustnessPolicy
    trials: tuple[MechanismTrial, ...]
    coarse_summaries: tuple[ProgramSweepSummary, ...]
    geometry_summaries: Mapping[GeometryLabel, tuple[ProgramSweepSummary, ...]]
    resolutions: tuple[GeometryResolution, ...]

    @property
    def coarse_survivors(self) -> tuple[str, ...]:
        return tuple(
            summary.program_id
            for summary in self.coarse_summaries
            if summary.classification == "robust"
        )

    def resolution_for(self, label: GeometryLabel) -> GeometryResolution:
        for resolution in self.resolutions:
            if resolution.observed_geometry == label:
                return resolution
        raise KeyError(label)


# ---------------------------------------------------------------------------
# Trait-support arithmetic
# ---------------------------------------------------------------------------


def _grid(n: int) -> tuple[float, ...]:
    if n < 9:
        raise ValueError("grid_points must be >= 9")
    return tuple(i / (n - 1) for i in range(n))


def _interval_mask(grid: tuple[float, ...], low: float, high: float) -> tuple[bool, ...]:
    return tuple(low - 1e-12 <= z <= high + 1e-12 for z in grid)


def _union_mask(
    grid: tuple[float, ...], intervals: Iterable[tuple[float, float]]
) -> tuple[bool, ...]:
    intervals = tuple(intervals)
    return tuple(
        any(low - 1e-12 <= z <= high + 1e-12 for low, high in intervals)
        for z in grid
    )


def _n_components(mask: tuple[bool, ...]) -> int:
    components = 0
    previous = False
    for value in mask:
        if value and not previous:
            components += 1
        previous = value
    return components


def _geometry(grid: tuple[float, ...], mask: tuple[bool, ...]) -> TraitGeometry:
    values = [z for z, viable in zip(grid, mask) if viable]
    if not values:
        return TraitGeometry(lower_edge=float("nan"), upper_edge=float("nan"), breadth=0.0, n_components=0)
    return TraitGeometry(
        lower_edge=min(values),
        upper_edge=max(values),
        breadth=max(values) - min(values),
        n_components=_n_components(mask),
    )


def _weighted_mean(grid: tuple[float, ...], mask: tuple[bool, ...], tilt: float = 0.0) -> float:
    """Mean realised trait inside viable support under an exponential frequency tilt.

    The tilt is a nuisance frequency process (e.g. mating, density dependence, or
    non-limiting compensation).  It affects the observed *mean* but never changes
    which traits remain viable; that distinction is precisely why geometry can add
    information beyond a coarse mean-trait POM.
    """
    weights = [exp(tilt * (z - 0.5)) if viable else 0.0 for z, viable in zip(grid, mask)]
    total = sum(weights)
    if total <= 0:
        return float("nan")
    return sum(z * w for z, w in zip(grid, weights)) / total


def _classify_geometry(before: TraitGeometry, after: TraitGeometry, *, tol: float) -> GeometryLabel:
    if after.n_components == 0:
        return "other"
    if after.n_components > before.n_components:
        return "fragmentation"
    lower_change = after.lower_edge - before.lower_edge
    upper_change = after.upper_edge - before.upper_edge
    breadth_change = after.breadth - before.breadth
    if (
        abs(lower_change) <= tol
        and upper_change < -tol
        and breadth_change < -tol
    ):
        return "upper_edge_contraction"
    if (
        abs(upper_change - lower_change) <= tol
        and abs(breadth_change) <= tol
        and abs(lower_change) > tol
    ):
        return "shift"
    if (
        abs(lower_change) <= tol
        and abs(upper_change) <= tol
        and abs(breadth_change) <= tol
        and after.n_components == before.n_components
    ):
        return "conserved"
    return "other"


def _trial(
    *,
    mechanism_id: str,
    motifs: frozenset[str],
    parameters: Mapping[str, float],
    grid: tuple[float, ...],
    before_mask: tuple[bool, ...],
    after_mask: tuple[bool, ...],
    before_tilt: float,
    after_tilt: float,
    region_id: str,
    seed: int,
) -> MechanismTrial:
    before = _geometry(grid, before_mask)
    after = _geometry(grid, after_mask)
    geometry = GeometryChange(
        before=before,
        after=after,
        label=_classify_geometry(before, after, tol=2.0 / max(len(grid) - 1, 1)),
    )
    return MechanismTrial(
        mechanism_id=mechanism_id,
        motifs=motifs,
        parameters=dict(parameters),
        before_mask=before_mask,
        after_mask=after_mask,
        coarse_pom=CoarsePOM(
            mean_before=_weighted_mean(grid, before_mask, before_tilt),
            mean_after=_weighted_mean(grid, after_mask, after_tilt),
            persistent_after=any(after_mask),
        ),
        geometry=geometry,
        region_id=region_id,
        seed=seed,
    )


# ---------------------------------------------------------------------------
# Competing mechanism families
# ---------------------------------------------------------------------------


def _relationship_benefit_loss(rng: Random, grid: tuple[float, ...], region_id: str, seed: int) -> MechanismTrial:
    """Loss of a high-trait relationship reward removes the upper viable edge."""
    after_upper = rng.uniform(0.56, 0.70)
    before_upper = min(0.98, after_upper + rng.uniform(0.20, 0.28))
    return _trial(
        mechanism_id="relationship_benefit_loss",
        motifs=frozenset({
            "relation_change",
            "benefit_gated_by_interaction",
            "positive_trait_cost",
            "incomplete_compensation",
        }),
        parameters={"before_upper": before_upper, "after_upper": after_upper},
        grid=grid,
        before_mask=_interval_mask(grid, 0.0, before_upper),
        after_mask=_interval_mask(grid, 0.0, after_upper),
        before_tilt=0.0,
        after_tilt=0.0,
        region_id=region_id,
        seed=seed,
    )


def _optimum_displacement(rng: Random, grid: tuple[float, ...], region_id: str, seed: int) -> MechanismTrial:
    """A moving fitness optimum shifts an otherwise connected viable support."""
    width = rng.uniform(0.52, 0.60)
    after_lower = rng.uniform(0.05, 0.12)
    shift = rng.uniform(0.15, 0.21)
    before_lower = after_lower + shift
    return _trial(
        mechanism_id="optimum_displacement",
        motifs=frozenset({
            "abiotic_or_enemy_regime_change",
            "stabilising_selection",
            "constant_viability_width",
        }),
        parameters={"width": width, "before_lower": before_lower, "after_lower": after_lower},
        grid=grid,
        before_mask=_interval_mask(grid, before_lower, before_lower + width),
        after_mask=_interval_mask(grid, after_lower, after_lower + width),
        before_tilt=0.0,
        after_tilt=0.0,
        region_id=region_id,
        seed=seed,
    )


def _connectivity_fragmentation(rng: Random, grid: tuple[float, ...], region_id: str, seed: int) -> MechanismTrial:
    """Patchy reachability splits realised trait support into disconnected islands."""
    before_lower = rng.uniform(0.08, 0.12)
    before_upper = rng.uniform(0.86, 0.92)
    left_low = rng.uniform(0.04, 0.07)
    left_high = rng.uniform(0.18, 0.24)
    right_low = rng.uniform(0.33, 0.39)
    right_high = rng.uniform(0.52, 0.60)
    return _trial(
        mechanism_id="connectivity_fragmentation",
        motifs=frozenset({
            "connectivity_loss",
            "patchy_trait_suitability",
            "reachability_constraint",
        }),
        parameters={
            "before_lower": before_lower,
            "before_upper": before_upper,
            "left_low": left_low,
            "left_high": left_high,
            "right_low": right_low,
            "right_high": right_high,
        },
        grid=grid,
        before_mask=_interval_mask(grid, before_lower, before_upper),
        after_mask=_union_mask(grid, ((left_low, left_high), (right_low, right_high))),
        before_tilt=0.0,
        after_tilt=0.0,
        region_id=region_id,
        seed=seed,
    )


def _directional_connectivity_pruning(rng: Random, grid: tuple[float, ...], region_id: str, seed: int) -> MechanismTrial:
    """A spatial confound that removes high-trait suitable patches without splitting support."""
    after_upper = rng.uniform(0.56, 0.70)
    before_upper = min(0.98, after_upper + rng.uniform(0.20, 0.28))
    return _trial(
        mechanism_id="directional_connectivity_pruning",
        motifs=frozenset({
            "connectivity_loss",
            "trait_correlated_patch_loss",
            "reachability_constraint",
        }),
        parameters={"before_upper": before_upper, "after_upper": after_upper},
        grid=grid,
        before_mask=_interval_mask(grid, 0.0, before_upper),
        after_mask=_interval_mask(grid, 0.0, after_upper),
        before_tilt=0.0,
        after_tilt=0.0,
        region_id=region_id,
        seed=seed,
    )


def _compensated_frequency_reweighting(rng: Random, grid: tuple[float, ...], region_id: str, seed: int) -> MechanismTrial:
    """Mean-trait decline with unchanged viable support via frequency reweighting.

    This is a deliberate counterexample to treating an observed mean decline as
    evidence that the viable trait support contracted.  Compensation preserves the
    support, while unobserved frequency processes change the realised mean.
    """
    upper = rng.uniform(0.82, 0.88)
    before_tilt = rng.uniform(1.8, 2.4)
    after_tilt = rng.uniform(-2.0, -1.5)
    mask = _interval_mask(grid, 0.0, upper)
    return _trial(
        mechanism_id="compensated_frequency_reweighting",
        motifs=frozenset({
            "relation_change",
            "sufficient_compensation",
            "frequency_reweighting",
            "unchanged_viability_support",
        }),
        parameters={"upper": upper, "before_tilt": before_tilt, "after_tilt": after_tilt},
        grid=grid,
        before_mask=mask,
        after_mask=mask,
        before_tilt=before_tilt,
        after_tilt=after_tilt,
        region_id=region_id,
        seed=seed,
    )


_MECHANISM_BUILDERS: dict[str, Callable[[Random, tuple[float, ...], str, int], MechanismTrial]] = {
    "relationship_benefit_loss": _relationship_benefit_loss,
    "optimum_displacement": _optimum_displacement,
    "connectivity_fragmentation": _connectivity_fragmentation,
    "directional_connectivity_pruning": _directional_connectivity_pruning,
    "compensated_frequency_reweighting": _compensated_frequency_reweighting,
}


# ---------------------------------------------------------------------------
# RACH-facing comparison
# ---------------------------------------------------------------------------


def _record(trial: MechanismTrial, target: CoarsePOMTarget, geometry: GeometryLabel | None) -> SweepRecord:
    coarse_match = target.matches(trial.coarse_pom)
    matched = coarse_match if geometry is None else coarse_match and trial.geometry.label == geometry
    return SweepRecord(
        scenario="coarse_pom" if geometry is None else f"coarse_pom_plus_{geometry}",
        program_id=trial.mechanism_id,
        motifs=trial.motifs,
        pattern_matched=matched,
        parameters=trial.parameters,
        initial_state={"mean_before": trial.coarse_pom.mean_before},
        metadata={
            "coarse_pom": {
                "mean_before": round(trial.coarse_pom.mean_before, 6),
                "mean_after": round(trial.coarse_pom.mean_after, 6),
                "mean_delta": round(trial.coarse_pom.mean_delta, 6),
                "persistent_after": trial.coarse_pom.persistent_after,
            },
            "geometry": {
                "label": trial.geometry.label,
                "before": trial.geometry.before,
                "after": trial.geometry.after,
            },
            "coarse_match": coarse_match,
        },
        region_id=trial.region_id,
        seed=trial.seed,
    )


def run_geometry_mechanism_discrimination(
    *,
    target: CoarsePOMTarget = CoarsePOMTarget(),
    policy: RobustnessPolicy = RobustnessPolicy(
        min_replicates=20,
        min_match_fraction=0.80,
        fragile_max_fraction=0.10,
    ),
    n_regions: int = 12,
    seeds: Iterable[int] = (0, 1),
    grid_points: int = 101,
    base_seed: int = 20260624,
) -> GeometryDiscriminationReport:
    """Compare competing mechanisms before and after adding trait geometry.

    ``n_regions`` represents predeclared broad parameter regions.  The same region
    and seed design is run for every mechanism; a geometry label is informative only
    when a mechanism reproduces it robustly *after* already matching the coarse POM.
    """
    if n_regions < 1:
        raise ValueError("n_regions must be >= 1")
    seed_values = tuple(seeds)
    if not seed_values:
        raise ValueError("at least one stochastic seed is required")
    grid = _grid(grid_points)
    trials: list[MechanismTrial] = []
    for mechanism_index, builder in enumerate(_MECHANISM_BUILDERS.values()):
        for region_index in range(n_regions):
            region_id = f"region_{region_index}"
            for seed in seed_values:
                rng = Random(
                    base_seed * 1000003
                    + mechanism_index * 10007
                    + region_index * 101
                    + seed
                )
                trials.append(builder(rng, grid, region_id, seed))

    coarse_summaries = summarise_sweep(
        (_record(trial, target, geometry=None) for trial in trials), policy
    )
    geometry_labels: tuple[GeometryLabel, ...] = (
        "upper_edge_contraction",
        "shift",
        "fragmentation",
        "conserved",
    )
    geometry_summaries = {
        label: summarise_sweep(
            (_record(trial, target, geometry=label) for trial in trials), policy
        )
        for label in geometry_labels
    }
    coarse_survivors = {
        summary.program_id
        for summary in coarse_summaries
        if summary.classification == "robust"
    }
    resolutions: list[GeometryResolution] = []
    for label in geometry_labels:
        surviving = tuple(
            summary.program_id
            for summary in geometry_summaries[label]
            if summary.classification == "robust"
        )
        eliminated = tuple(sorted(coarse_survivors - set(surviving)))
        if len(surviving) == 1:
            status: Literal["unique", "ambiguous", "unsupported"] = "unique"
        elif len(surviving) > 1:
            status = "ambiguous"
        else:
            status = "unsupported"
        resolutions.append(
            GeometryResolution(
                observed_geometry=label,
                survivors=surviving,
                eliminated=eliminated,
                status=status,
            )
        )
    return GeometryDiscriminationReport(
        target=target,
        policy=policy,
        trials=tuple(trials),
        coarse_summaries=coarse_summaries,
        geometry_summaries=geometry_summaries,
        resolutions=tuple(resolutions),
    )
