"""Endpoint sensitivity runners for mechanistically distinct ABM backends.

The spatial runner lives in :mod:`causal_model.rule_transition_diagnostics`.
This module adds the corresponding defense endpoint runner while preserving the
same declared settings, region/seed replication design, and uncertainty summary.
"""
from __future__ import annotations

from dataclasses import asdict
from random import Random
from typing import Callable, Iterable, Mapping

from causal_model.abc_distance import accepted_by_epsilon
from causal_model.abm_family_adapter import SweepRecord
from causal_model.defense_metapopulation_abm import (
    DEFAULT_EPSILON,
    DefenseIntervention,
    DefenseParameters,
    defense_observed_pattern,
    equilibrate_defense,
    estimate_defense_omega_inv,
    extract_defense_pom,
    reequilibrate_defense,
)
from causal_model.rule_transition_diagnostics import (
    EndpointSensitivitySettings,
    SensitivityCellResult,
    summarise_match_uncertainty,
)
from causal_model.spatial_metapopulation_abm import classify_trait_space_change, pom_distance


DefenseSampler = Callable[[Random], tuple[DefenseParameters, dict]]


def evaluate_defense_endpoint(
    params: DefenseParameters,
    patches: dict,
    intervention: DefenseIntervention,
    settings: EndpointSensitivitySettings,
    *,
    seed: int,
    observed_pattern: Mapping[str, str] | None = None,
    epsilon: float = DEFAULT_EPSILON,
) -> tuple[bool, dict[str, object]]:
    """Evaluate one defense endpoint under an explicit sensitivity setting.

    Both invasion sets are measured against their own stationary residents. A
    non-stationary or extinct post-loss resident is retained as a rejected record,
    not converted into an artificial empty invasion set.
    """
    observed = dict(observed_pattern or defense_observed_pattern())
    resident_before, states_before, report_before = equilibrate_defense(
        patches,
        params,
        steps=settings.equilibration_steps,
        seed=seed,
        regime=intervention.before,
        record_window=settings.stationarity_window,
    )
    diagnostics: dict[str, object] = {
        "endpoint_protocol": "reequilibrated_resident",
        "stationarity_before": report_before.status,
        "stationarity_after": "not_run",
        "sensitivity_settings": asdict(settings),
    }
    if report_before.status != "stationary" or resident_before.n_total == 0:
        return False, diagnostics

    omega_before = estimate_defense_omega_inv(
        resident_before,
        states_before,
        patches,
        params,
        intervention.before,
        grid_points=settings.grid_points,
        invasion_steps=settings.invasion_steps,
        cohort=settings.invasion_cohort,
        replicates=settings.invasion_replicates,
        threshold=settings.invasion_threshold,
        seed=seed * 1000 + 3,
    )
    resident_after, states_after, report_after = reequilibrate_defense(
        resident_before,
        states_before,
        patches,
        params,
        intervention.after,
        steps=settings.reequilibration_steps,
        seed=seed * 1000 + 7,
        record_window=settings.stationarity_window,
        stationarity_tol=settings.stationarity_tolerance,
    )
    diagnostics.update({
        "stationarity_after": report_after.status,
        "n_resident_before": resident_before.n_total,
        "n_resident_after": resident_after.n_total,
        "omega_measure_before": omega_before.measure,
    })
    if report_after.status != "stationary" or resident_after.n_total == 0:
        diagnostics["omega_after_resident"] = "not_stationary"
        return False, diagnostics

    omega_after = estimate_defense_omega_inv(
        resident_after,
        states_after,
        patches,
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
    p_sim = extract_defense_pom(
        resident_before,
        resident_after,
        patches,
        params,
        change,
        predator_before=intervention.before.predator_present,
        predator_after=intervention.after.predator_present,
    )
    distance = pom_distance(p_sim, observed)
    reconfigured = change.primary in {"contraction", "fragmentation", "shift", "collapse"}
    accepted = accepted_by_epsilon(distance, epsilon) and reconfigured
    diagnostics.update({
        "omega_after_resident": "post_intervention_reequilibrated",
        "omega_measure_after": omega_after.measure,
        "trait_space_primary": change.primary,
        "P_sim": p_sim,
        "P_obs": observed,
        "abc_distance": distance,
        "epsilon": epsilon,
    })
    return accepted, diagnostics


def run_defense_endpoint_sensitivity(
    intervention: DefenseIntervention,
    *,
    program_id: str,
    program_motifs: frozenset[str],
    ecosystem_sampler: DefenseSampler,
    settings: Iterable[EndpointSensitivitySettings],
    observed_pattern: Mapping[str, str] | None = None,
    n_regions: int = 6,
    seeds: Iterable[int] = (0, 1),
    epsilon: float = DEFAULT_EPSILON,
    base_seed: int = 0,
) -> tuple[SensitivityCellResult, ...]:
    """Run declared defense endpoint sensitivity cells with region/seed provenance."""
    rows: list[SensitivityCellResult] = []
    for setting_index, setting in enumerate(settings):
        records: list[SweepRecord] = []
        for region in range(n_regions):
            params, patches = ecosystem_sampler(Random(base_seed * 9973 + region))
            region_id = f"eco_{region}"
            for replicate_seed in seeds:
                effective_seed = (
                    base_seed * 100000
                    + setting_index * 1000
                    + region * 31
                    + replicate_seed
                )
                matched, diagnostics = evaluate_defense_endpoint(
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
                        "predator_pressure": params.predator_pressure,
                        "defense_cost": params.defense_cost,
                        "dispersal_base": params.dispersal_base,
                    },
                    initial_state={
                        "omega_measure_before": float(
                            diagnostics.get("omega_measure_before", 0.0)
                        ),
                    },
                    metadata=diagnostics,
                    region_id=region_id,
                    seed=replicate_seed,
                    fragile_flags=frozenset(),
                ))
        rows.append(SensitivityCellResult(
            settings=setting,
            records=tuple(records),
            uncertainty=summarise_match_uncertainty(records),
        ))
    return tuple(rows)
