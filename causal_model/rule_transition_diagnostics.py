"""Uncertainty, sensitivity, and benchmark reporting for rule-transition RACH.

This module deliberately works from ``SweepRecord`` objects so every reported
interval remains tied to declared region and seed replicates.  The spatial
sensitivity runner evaluates Omega_inv at re-equilibrated before/after residents;
it never substitutes an instantaneous invasion contrast for an endpoint result.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from itertools import product
from random import Random
from statistics import NormalDist
from typing import Iterable, Mapping, Sequence

from causal_model.abc_distance import accepted_by_epsilon
from causal_model.abm_family_adapter import RobustnessPolicy, SweepRecord, summarise_sweep
from causal_model.rule_transition_hardened import program_runs_from_observed_sweep
from causal_model.rule_transition_invariants import explain_result, infer_rule_transition_invariants
from causal_model.spatial_metapopulation_abm import (
    DEFAULT_EPSILON,
    Intervention,
    MetapopParameters,
    PatchState,
    PopulationState,
    StationarityReport,
    advance,
    assess_stationarity,
    classify_trait_space_change,
    equilibrate,
    estimate_omega_inv,
    extract_pom_pattern,
    pom_distance,
    _series_summary,
)


@dataclass(frozen=True)
class ProportionInterval:
    """Wilson confidence interval for a binomial match fraction."""

    estimate: float
    lower: float
    upper: float
    confidence: float


@dataclass(frozen=True)
class GroupMatchSummary:
    scenario: str
    program_id: str
    motifs: frozenset[str]
    group_kind: str
    group_id: str
    n_replicates: int
    n_matches: int
    interval: ProportionInterval


@dataclass(frozen=True)
class ProgramUncertaintySummary:
    scenario: str
    program_id: str
    motifs: frozenset[str]
    n_replicates: int
    n_matches: int
    interval: ProportionInterval
    by_region: tuple[GroupMatchSummary, ...]
    by_seed: tuple[GroupMatchSummary, ...]


@dataclass(frozen=True)
class EndpointSensitivitySettings:
    """One fully declared endpoint-sensitivity setting."""

    grid_points: int = 9
    invasion_steps: int = 6
    invasion_replicates: int = 2
    invasion_threshold: float = 0.0
    stationarity_window: int = 12
    equilibration_steps: int = 40
    reequilibration_steps: int = 60
    invasion_cohort: int = 12
    stationarity_tolerance: float = 0.14

    def __post_init__(self) -> None:
        if self.grid_points < 2:
            raise ValueError("grid_points must be at least 2")
        if self.invasion_steps < 1 or self.invasion_replicates < 1:
            raise ValueError("invasion steps and replicates must be positive")
        if self.stationarity_window < 4:
            raise ValueError("stationarity_window must be at least 4")
        if self.equilibration_steps < self.stationarity_window:
            raise ValueError("equilibration_steps must cover the stationarity window")
        if self.reequilibration_steps < self.stationarity_window:
            raise ValueError("reequilibration_steps must cover the stationarity window")


@dataclass(frozen=True)
class SensitivityCellResult:
    settings: EndpointSensitivitySettings
    records: tuple[SweepRecord, ...]
    uncertainty: tuple[ProgramUncertaintySummary, ...]


def wilson_interval(
    n_matches: int,
    n_replicates: int,
    *,
    confidence: float = 0.95,
) -> ProportionInterval:
    """Return a Wilson interval without relying on an optional statistics package."""
    if n_replicates < 1:
        return ProportionInterval(0.0, 0.0, 1.0, confidence)
    if not 0 <= n_matches <= n_replicates:
        raise ValueError("n_matches must lie between 0 and n_replicates")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between 0 and 1")
    estimate = n_matches / n_replicates
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    denominator = 1.0 + z * z / n_replicates
    center = (estimate + z * z / (2.0 * n_replicates)) / denominator
    half_width = z * (
        (estimate * (1.0 - estimate) / n_replicates + z * z / (4.0 * n_replicates ** 2))
        ** 0.5
    ) / denominator
    return ProportionInterval(
        estimate=estimate,
        lower=max(0.0, center - half_width),
        upper=min(1.0, center + half_width),
        confidence=confidence,
    )


def _program_key(record: SweepRecord) -> tuple[str, str, frozenset[str]]:
    return record.scenario, record.program_id, frozenset(record.motifs)


def _group_summary(
    scenario: str,
    program_id: str,
    motifs: frozenset[str],
    group_kind: str,
    group_id: object,
    records: Sequence[SweepRecord],
    confidence: float,
) -> GroupMatchSummary:
    matches = sum(record.pattern_matched for record in records)
    return GroupMatchSummary(
        scenario=scenario,
        program_id=program_id,
        motifs=motifs,
        group_kind=group_kind,
        group_id=str(group_id),
        n_replicates=len(records),
        n_matches=matches,
        interval=wilson_interval(matches, len(records), confidence=confidence),
    )


def summarise_match_uncertainty(
    records: Iterable[SweepRecord],
    *,
    confidence: float = 0.95,
) -> tuple[ProgramUncertaintySummary, ...]:
    """Summarise matching support overall and separately by declared region and seed."""
    grouped: dict[tuple[str, str, frozenset[str]], list[SweepRecord]] = {}
    for record in records:
        grouped.setdefault(_program_key(record), []).append(record)

    summaries: list[ProgramUncertaintySummary] = []
    for (scenario, program_id, motifs), rows in sorted(grouped.items()):
        n_matches = sum(row.pattern_matched for row in rows)
        regions: dict[object, list[SweepRecord]] = {}
        seeds: dict[object, list[SweepRecord]] = {}
        for row in rows:
            if row.region_id is not None:
                regions.setdefault(row.region_id, []).append(row)
            if row.seed is not None:
                seeds.setdefault(row.seed, []).append(row)
        summaries.append(
            ProgramUncertaintySummary(
                scenario=scenario,
                program_id=program_id,
                motifs=motifs,
                n_replicates=len(rows),
                n_matches=n_matches,
                interval=wilson_interval(n_matches, len(rows), confidence=confidence),
                by_region=tuple(
                    _group_summary(scenario, program_id, motifs, "region", group_id, group, confidence)
                    for group_id, group in sorted(regions.items(), key=lambda item: str(item[0]))
                ),
                by_seed=tuple(
                    _group_summary(scenario, program_id, motifs, "seed", group_id, group, confidence)
                    for group_id, group in sorted(seeds.items(), key=lambda item: str(item[0]))
                ),
            )
        )
    return tuple(summaries)


def endpoint_sensitivity_grid(
    *,
    grid_points: Sequence[int] = (7, 9, 13),
    invasion_steps: Sequence[int] = (4, 6, 10),
    invasion_replicates: Sequence[int] = (1, 2, 4),
    invasion_thresholds: Sequence[float] = (-0.02, 0.0, 0.02),
    stationarity_windows: Sequence[int] = (8, 12),
    equilibration_steps: int = 40,
    reequilibration_steps: int = 60,
    invasion_cohort: int = 12,
    stationarity_tolerance: float = 0.14,
) -> tuple[EndpointSensitivitySettings, ...]:
    """Return the explicit Cartesian grid required for endpoint sensitivity checks."""
    return tuple(
        EndpointSensitivitySettings(
            grid_points=grid,
            invasion_steps=steps,
            invasion_replicates=replicates,
            invasion_threshold=threshold,
            stationarity_window=window,
            equilibration_steps=equilibration_steps,
            reequilibration_steps=reequilibration_steps,
            invasion_cohort=invasion_cohort,
            stationarity_tolerance=stationarity_tolerance,
        )
        for grid, steps, replicates, threshold, window in product(
            grid_points,
            invasion_steps,
            invasion_replicates,
            invasion_thresholds,
            stationarity_windows,
        )
    )


def _reequilibrate_spatial(
    resident: PopulationState,
    resident_states: Mapping[int, PatchState],
    patches: Mapping[int, object],
    params: MetapopParameters,
    intervention: Intervention,
    settings: EndpointSensitivitySettings,
    *,
    seed: int,
) -> tuple[PopulationState, dict, StationarityReport]:
    rng = Random(seed)
    individuals = [replace(individual) for individual in resident.individuals]
    patch_states = {patch_id: PatchState(state.resources) for patch_id, state in resident_states.items()}
    n_series: list[int] = []
    mean_series: list[float] = []
    occupancy_series: list[int] = []
    variance_series: list[float] = []
    n_patches = len(patches)
    for step in range(settings.reequilibration_steps):
        individuals = advance(
            individuals,
            dict(patches),
            patch_states,
            params,
            rng,
            intervention.after,
            steps=1,
        )
        if step >= settings.reequilibration_steps - settings.stationarity_window:
            n, mean, occupied, variance = _series_summary(individuals, n_patches)
            n_series.append(n)
            mean_series.append(mean)
            occupancy_series.append(occupied)
            variance_series.append(variance)
        if not individuals:
            break
    report = assess_stationarity(
        n_series,
        mean_series,
        occupancy_series,
        variance_series,
        window=settings.stationarity_window,
        tol=settings.stationarity_tolerance,
    )
    return (
        PopulationState(
            tuple(individuals),
            {patch_id: state.resources for patch_id, state in patch_states.items()},
        ),
        patch_states,
        report,
    )


def evaluate_spatial_endpoint(
    params: MetapopParameters,
    patches: Mapping[int, object],
    intervention: Intervention,
    settings: EndpointSensitivitySettings,
    *,
    seed: int,
    observed_pattern: Mapping[str, str],
    epsilon: float = DEFAULT_EPSILON,
) -> tuple[bool, dict[str, object]]:
    """Evaluate one before/after endpoint under an explicit sensitivity setting."""
    resident_before, states_before, before_report = equilibrate(
        dict(patches),
        params,
        steps=settings.equilibration_steps,
        seed=seed,
        regime=intervention.before,
        record_window=settings.stationarity_window,
    )
    diagnostics: dict[str, object] = {
        "stationarity_before": before_report.status,
        "stationarity_after": "not_run",
        "sensitivity_settings": asdict(settings),
        "endpoint_protocol": "reequilibrated_resident",
    }
    if before_report.status != "stationary" or resident_before.n_total == 0:
        return False, diagnostics

    omega_before = estimate_omega_inv(
        resident_before,
        states_before,
        dict(patches),
        params,
        intervention.before,
        grid_points=settings.grid_points,
        invasion_steps=settings.invasion_steps,
        cohort=settings.invasion_cohort,
        replicates=settings.invasion_replicates,
        threshold=settings.invasion_threshold,
        seed=seed * 1000 + 3,
    )
    resident_after, states_after, after_report = _reequilibrate_spatial(
        resident_before,
        states_before,
        patches,
        params,
        intervention,
        settings,
        seed=seed * 1000 + 7,
    )
    diagnostics["stationarity_after"] = after_report.status
    diagnostics["n_resident_before"] = resident_before.n_total
    diagnostics["n_resident_after"] = resident_after.n_total
    diagnostics["omega_measure_before"] = omega_before.measure
    if after_report.status != "stationary" or resident_after.n_total == 0:
        diagnostics["omega_after_resident"] = "not_stationary"
        return False, diagnostics

    omega_after = estimate_omega_inv(
        resident_after,
        states_after,
        dict(patches),
        params,
        intervention.after,
        grid_points=settings.grid_points,
        invasion_steps=settings.invasion_steps,
        cohort=settings.invasion_cohort,
        replicates=settings.invasion_replicates,
        threshold=settings.invasion_threshold,
        seed=seed * 1000 + 4,
    )
    change = classify_trait_space_change(omega_before, omega_after)
    p_sim = extract_pom_pattern(
        resident_before,
        resident_after,
        dict(patches),
        params,
        change,
        interaction_scale_before=intervention.before.interaction_scale,
        interaction_scale_after=intervention.after.interaction_scale,
    )
    distance = pom_distance(p_sim, dict(observed_pattern))
    diagnostics.update({
        "omega_after_resident": "post_intervention_reequilibrated",
        "omega_measure_after": omega_after.measure,
        "trait_space_primary": change.primary,
        "P_sim": p_sim,
        "P_obs": dict(observed_pattern),
        "abc_distance": distance,
        "epsilon": epsilon,
    })
    return accepted_by_epsilon(distance, epsilon), diagnostics


def run_spatial_endpoint_sensitivity(
    intervention: Intervention,
    *,
    program_id: str,
    program_motifs: frozenset[str],
    ecosystem_sampler: object,
    settings: Iterable[EndpointSensitivitySettings],
    observed_pattern: Mapping[str, str],
    n_regions: int = 6,
    seeds: Iterable[int] = (0, 1),
    epsilon: float = DEFAULT_EPSILON,
    base_seed: int = 0,
) -> tuple[SensitivityCellResult, ...]:
    """Run declared spatial endpoint sensitivity cells and retain every record."""
    sampler = ecosystem_sampler
    if not callable(sampler):
        raise TypeError("ecosystem_sampler must be callable")
    cells: list[SensitivityCellResult] = []
    for setting_index, setting in enumerate(settings):
        records: list[SweepRecord] = []
        for region in range(n_regions):
            params, patches = sampler(Random(base_seed * 9973 + region))
            region_id = f"eco_{region}"
            for replicate_seed in seeds:
                effective_seed = base_seed * 100000 + setting_index * 1000 + region * 31 + replicate_seed
                matched, diagnostics = evaluate_spatial_endpoint(
                    params,
                    patches,
                    intervention,
                    setting,
                    seed=effective_seed,
                    observed_pattern=observed_pattern,
                    epsilon=epsilon,
                )
                records.append(SweepRecord(
                    scenario=intervention.name,
                    program_id=program_id,
                    motifs=program_motifs,
                    pattern_matched=matched,
                    parameters={
                        "interaction_benefit": params.interaction_benefit,
                        "trait_cost": params.trait_cost,
                        "predation_pressure": params.predation_pressure,
                    },
                    initial_state={},
                    metadata=diagnostics,
                    region_id=region_id,
                    seed=replicate_seed,
                    fragile_flags=frozenset(),
                ))
        cells.append(SensitivityCellResult(
            settings=setting,
            records=tuple(records),
            uncertainty=summarise_match_uncertainty(records),
        ))
    return tuple(cells)


def build_benchmark_report(
    records: Iterable[SweepRecord],
    *,
    policy: RobustnessPolicy = RobustnessPolicy(),
    unresolved_limitations: Sequence[str] = (),
) -> dict[str, object]:
    """Build the compact report required by the hardened rule-transition workflow."""
    rows = tuple(records)
    observed = program_runs_from_observed_sweep(rows, policy)
    invariant = infer_rule_transition_invariants(observed.program_runs)
    outcomes = {
        f"{run.scenario}:{run.program_id}": {
            "outcome_motifs": sorted(run.outcome_motifs),
            "outcome_provenance": run.metadata.get("outcome_provenance"),
            "observed_primary_counts": run.metadata.get("observed_primary_counts", {}),
        }
        for run in observed.program_runs
    }
    assumptions = {
        f"{run.scenario}:{run.program_id}": sorted(run.motifs)
        for run in observed.program_runs
    }
    counterexamples = [
        {
            "scenario": summary.scenario,
            "program_id": summary.program_id,
            "classification": summary.classification,
            "match_fraction": summary.match_fraction,
            "fragility_reasons": sorted(summary.fragility_reasons),
        }
        for summary in summarise_sweep(rows, policy)
        if summary.classification != "robust"
    ]
    return {
        "assumptions": assumptions,
        "observed_outcomes": outcomes,
        "conditional_necessity": explain_result(invariant),
        "counterexamples": counterexamples,
        "uncertainty": [
            {
                "scenario": summary.scenario,
                "program_id": summary.program_id,
                "n_replicates": summary.n_replicates,
                "n_matches": summary.n_matches,
                "wilson_interval": asdict(summary.interval),
                "by_region": [
                    {
                        "region_id": group.group_id,
                        "n_replicates": group.n_replicates,
                        "n_matches": group.n_matches,
                        "wilson_interval": asdict(group.interval),
                    }
                    for group in summary.by_region
                ],
                "by_seed": [
                    {
                        "seed": group.group_id,
                        "n_replicates": group.n_replicates,
                        "n_matches": group.n_matches,
                        "wilson_interval": asdict(group.interval),
                    }
                    for group in summary.by_seed
                ],
            }
            for summary in summarise_match_uncertainty(rows)
        ],
        "unresolved_limitations": list(unresolved_limitations),
    }
