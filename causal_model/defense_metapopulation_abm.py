"""Defense metapopulation ABM — survival-mediated trait rewards.

The standard intervention path evaluates Omega_inv at two resident equilibria:
the pre-loss resident and a post-loss resident re-equilibrated after the
intervention. This avoids treating instantaneous invasibility against the old
resident as the post-intervention evolutionary endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from random import Random
from typing import Callable, Iterable

from causal_model.abc_distance import accepted_by_epsilon
from causal_model.abm_family_adapter import SweepRecord
from causal_model.spatial_metapopulation_abm import (
    DEFAULT_EPSILON,
    Individual,
    Patch,
    PatchState,
    PopulationState,
    TraitSpaceChange,
    ViableTraitSet,
    _clip,
    _mate_success,
    _ne_proxy,
    _ordinal,
    _series_summary,
    _trait_moments,
    assess_stationarity,
    benefit_shape,
    classify_trait_space_change,
    init_patch_states,
    pom_distance,
    seed_population,
)
from causal_model.spatial_metapopulation_abm import _OMEGA_STATE

_CHAIN_MOTIFS: frozenset[str] = frozenset(
    {"relation_change", "constraint_reconfiguration", "trait_space_reconfiguration"}
)


@dataclass(frozen=True)
class DefenseParameters:
    """Constraints for an anti-predator defense trait.

    Defense is rewarded through survival only while predators are present and is
    paid for through fecundity. The model does not impose a trait direction.
    """

    predator_pressure: float
    defense_effectiveness: float
    defense_cost: float
    fecundity_floor: float
    density_threshold: float
    mutation_rate: float
    mutation_std: float
    dispersal_base: float
    distance_decay: float
    resource_replenishment: float
    base_survival: float = 0.92
    max_age: int = 8
    benefit_saturation: float = 0.0


@dataclass(frozen=True)
class DefenseRegime:
    """Predator presence, dispersal and non-channel compensation."""

    predator_present: float = 1.0
    dispersal_scale: float = 1.0
    repro_baseline: float = 0.0


@dataclass(frozen=True)
class DefenseIntervention:
    name: str
    before: DefenseRegime
    after: DefenseRegime
    channel_motif: str


def make_defense_intervention(
    loss_level: float = 0.0,
    compensation: float = 0.08,
) -> DefenseIntervention:
    """Remove only the predator-defense relationship; compensation is separate."""
    return DefenseIntervention(
        name="predator_loss_defense",
        before=DefenseRegime(predator_present=1.0),
        after=DefenseRegime(predator_present=loss_level, repro_baseline=compensation),
        channel_motif="antipredator_relationship_loss",
    )


def _defense_step(
    individuals: list[Individual],
    patches: dict,
    patch_states: dict,
    params: DefenseParameters,
    rng: Random,
    regime: DefenseRegime,
    *,
    mutation_override: float | None = None,
) -> list[Individual]:
    """One individual-based step with survival-mediated trait reward."""
    mutation_rate = params.mutation_rate if mutation_override is None else mutation_override
    n_per_patch: dict = {}
    for ind in individuals:
        n_per_patch[ind.patch_id] = n_per_patch.get(ind.patch_id, 0) + 1
    for pid, ps in patch_states.items():
        n = n_per_patch.get(pid, 0)
        patch = patches[pid]
        consumption = n * 0.08 / max(patch.area * patch.carrying_capacity, 1)
        ps.resources = _clip(ps.resources + params.resource_replenishment - consumption)

    by_patch: dict = {}
    for ind in individuals:
        by_patch.setdefault(ind.patch_id, []).append(ind)

    survivors: list[Individual] = []
    offspring: list[Individual] = []
    for pid, local in by_patch.items():
        patch = patches[pid]
        ps = patch_states[pid]
        density = len(local) / max(patch.carrying_capacity, 1)
        logistic = max(0.0, 1.0 - density)
        for ind in local:
            age_term = (ind.age / max(params.max_age, 1)) ** 2
            protection = params.defense_effectiveness * benefit_shape(
                ind.trait, params.benefit_saturation
            )
            predation_mortality = (
                regime.predator_present * params.predator_pressure * (1.0 - protection)
            )
            survival_p = _clip(
                params.base_survival * (1.0 - 0.6 * age_term) - predation_mortality
            )
            if ind.age >= params.max_age or rng.random() > survival_p:
                continue
            survivors.append(replace(ind, age=ind.age + 1))

            mate = _mate_success(ind, local, params, rng)
            repro_p = _clip(
                params.fecundity_floor
                + 0.20 * mate
                + 0.30 * ps.resources
                + regime.repro_baseline
                - params.defense_cost * ind.trait
            ) * logistic
            if rng.random() >= repro_p:
                continue
            new_trait, new_geno = ind.trait, ind.genotype
            if rng.random() < mutation_rate:
                new_trait = _clip(new_trait + rng.gauss(0.0, params.mutation_std))
                new_geno = _clip(new_geno + rng.gauss(0.0, params.mutation_std * 0.5))
            target_pid = pid
            if rng.random() < params.dispersal_base * regime.dispersal_scale and patch.connectivity:
                neighbors = list(patch.connectivity.items())
                total_weight = sum(weight for _, weight in neighbors)
                if total_weight > 0:
                    draw = rng.random() * total_weight
                    cumulative = 0.0
                    for neighbor, weight in neighbors:
                        cumulative += weight
                        if draw <= cumulative:
                            target_pid = neighbor
                            break
            offspring.append(
                Individual(
                    trait=new_trait,
                    genotype=new_geno,
                    age=0,
                    patch_id=target_pid,
                    location=(rng.random(), rng.random()),
                    lineage=ind.lineage,
                )
            )
    return survivors + offspring


def advance_defense(
    individuals: list[Individual],
    patches: dict,
    patch_states: dict,
    params: DefenseParameters,
    rng: Random,
    regime: DefenseRegime = DefenseRegime(),
    *,
    steps: int = 1,
    mutation_override: float | None = None,
) -> list[Individual]:
    for _ in range(steps):
        if not individuals:
            break
        individuals = _defense_step(
            individuals,
            patches,
            patch_states,
            params,
            rng,
            regime,
            mutation_override=mutation_override,
        )
    return individuals


def _stationarity_series(
    individuals: list[Individual],
    patches: dict,
    patch_states: dict,
    params: DefenseParameters,
    rng: Random,
    regime: DefenseRegime,
    *,
    steps: int,
    record_window: int,
    stationarity_tol: float | None = None,
) -> tuple[PopulationState, dict, object]:
    """Advance an existing resident and report its terminal quasi-stationarity."""
    n_patches = len(patches)
    n_s: list[int] = []
    mt_s: list[float] = []
    occ_s: list[int] = []
    var_s: list[float] = []
    for step in range(steps):
        individuals = advance_defense(
            individuals, patches, patch_states, params, rng, regime, steps=1
        )
        if step >= steps - record_window - 1:
            n, mt, occ, var = _series_summary(individuals, n_patches)
            n_s.append(n)
            mt_s.append(mt)
            occ_s.append(occ)
            var_s.append(var)
        if not individuals:
            n_s.append(0)
            mt_s.append(0.0)
            occ_s.append(0)
            var_s.append(0.0)
            break
    if stationarity_tol is None:
        report = assess_stationarity(n_s, mt_s, occ_s, var_s, window=record_window)
    else:
        report = assess_stationarity(
            n_s, mt_s, occ_s, var_s, window=record_window, tol=stationarity_tol
        )
    state = PopulationState(
        tuple(individuals),
        {pid: ps.resources for pid, ps in patch_states.items()},
    )
    return state, patch_states, report


def equilibrate_defense(
    patches: dict,
    params: DefenseParameters,
    *,
    steps: int = 40,
    seed: int = 0,
    regime: DefenseRegime = DefenseRegime(),
    record_window: int = 10,
):
    """Grow a resident from the seed population to quasi-stationarity."""
    rng = Random(seed)
    return _stationarity_series(
        seed_population(patches, params, rng),
        patches,
        init_patch_states(patches, rng),
        params,
        rng,
        regime,
        steps=steps,
        record_window=record_window,
    )


def reequilibrate_defense(
    resident: PopulationState,
    resident_states: dict,
    patches: dict,
    params: DefenseParameters,
    regime: DefenseRegime,
    *,
    steps: int = 40,
    seed: int = 0,
    record_window: int = 12,
    stationarity_tol: float = 0.14,
):
    """Re-equilibrate a shared resident after a regime switch.

    This function starts from the BEFORE resident rather than a fresh seed
    population. It is the required counterpart to ``equilibrate_defense`` for
    post-intervention Omega_inv estimation.
    """
    rng = Random(seed)
    return _stationarity_series(
        [replace(ind) for ind in resident.individuals],
        patches,
        {pid: PatchState(ps.resources) for pid, ps in resident_states.items()},
        params,
        rng,
        regime,
        steps=steps,
        record_window=record_window,
        stationarity_tol=stationarity_tol,
    )


def _log_growth(counts: list[int]) -> float:
    import math

    if not counts or counts[0] == 0:
        return 0.0
    if counts[-1] == 0:
        return -5.0
    n_steps = len(counts) - 1
    return (math.log(counts[-1]) - math.log(counts[0])) / n_steps if n_steps else 0.0


def defense_invasion_growth_rate(
    resident: PopulationState,
    resident_states: dict,
    patches: dict,
    params: DefenseParameters,
    regime: DefenseRegime,
    z_prime: float,
    *,
    steps: int = 6,
    cohort: int = 12,
    seed: int = 0,
) -> float:
    rng = Random(seed)
    individuals = [replace(ind, lineage=0) for ind in resident.individuals]
    occupied = sorted(resident.occupied_patches()) or list(patches)
    for _ in range(cohort):
        pid = rng.choice(occupied)
        individuals.append(
            Individual(
                trait=_clip(z_prime),
                genotype=_clip(z_prime),
                age=0,
                patch_id=pid,
                location=(rng.random(), rng.random()),
                lineage=1,
            )
        )
    states = {pid: PatchState(ps.resources) for pid, ps in resident_states.items()}
    counts = [sum(ind.lineage == 1 for ind in individuals)]
    for _ in range(steps):
        individuals = _defense_step(
            individuals, patches, states, params, rng, regime, mutation_override=0.0
        )
        count = sum(ind.lineage == 1 for ind in individuals)
        counts.append(count)
        if count == 0:
            break
    return _log_growth(counts)


def estimate_defense_omega_inv(
    resident: PopulationState,
    resident_states: dict,
    patches: dict,
    params: DefenseParameters,
    regime: DefenseRegime,
    *,
    grid_points: int = 9,
    invasion_steps: int = 6,
    cohort: int = 12,
    replicates: int = 2,
    threshold: float = 0.0,
    seed: int = 0,
) -> ViableTraitSet:
    if grid_points < 2:
        raise ValueError("grid_points must be >= 2")
    grid = tuple(i / (grid_points - 1) for i in range(grid_points))
    mask: list[bool] = []
    rates: list[float] = []
    for grid_index, trait in enumerate(grid):
        rate = 0.0
        for replicate in range(replicates):
            rate += defense_invasion_growth_rate(
                resident,
                resident_states,
                patches,
                params,
                regime,
                trait,
                steps=invasion_steps,
                cohort=cohort,
                seed=seed * 1000 + grid_index * 17 + replicate,
            )
        rate /= max(replicates, 1)
        rates.append(rate)
        mask.append(rate > threshold)
    return ViableTraitSet(grid, tuple(mask), tuple(rates))


def _mean_predation_interaction(
    state: PopulationState,
    params: DefenseParameters,
    predator_present: float,
) -> float:
    if not state.individuals:
        return 0.0
    return sum(
        predator_present
        * params.defense_effectiveness
        * benefit_shape(ind.trait, params.benefit_saturation)
        for ind in state.individuals
    ) / len(state.individuals)


def extract_defense_pom(
    before: PopulationState,
    after: PopulationState,
    patches: dict,
    params: DefenseParameters,
    ts: TraitSpaceChange,
    *,
    predator_before: float,
    predator_after: float,
    tolerance: float = 0.05,
    interaction_tolerance: float = 0.02,
) -> dict[str, str]:
    interaction_before = _mean_predation_interaction(
        before, params, predator_before
    )
    interaction_after = _mean_predation_interaction(after, params, predator_after)
    n_patches = max(len(patches), 1)
    occupancy_before = len(before.occupied_patches()) / n_patches
    occupancy_after = len(after.occupied_patches()) / n_patches
    ne_before, ne_after = _ne_proxy(before), _ne_proxy(after)
    ne_scale = max(ne_before, ne_after, 1.0)
    moments_before, moments_after = _trait_moments(before), _trait_moments(after)
    return {
        "interaction_network": _ordinal(
            interaction_after - interaction_before, interaction_tolerance
        ),
        "patch_occupancy": _ordinal(occupancy_after - occupancy_before, tolerance),
        "persistence_ne": _ordinal((ne_after - ne_before) / ne_scale, tolerance),
        "trait_moments": _ordinal(moments_after - moments_before, tolerance),
        "omega_inv_state": _OMEGA_STATE.get(ts.primary, "conserved"),
    }


@dataclass(frozen=True)
class DefenseResult:
    intervention: str
    stationarity: str
    omega_before: ViableTraitSet
    omega_after: ViableTraitSet
    trait_space_change: TraitSpaceChange
    p_sim: dict
    p_obs: dict
    distance: float
    accepted: bool
    motifs: frozenset
    diagnostics: dict


def defense_observed_pattern() -> dict[str, str]:
    """Predator loss removes the interaction and shifts viability toward low defense."""
    return {
        "interaction_network": "decrease",
        "patch_occupancy": "stable",
        "persistence_ne": "increase",
        "trait_moments": "stable",
        "omega_inv_state": "shifted",
    }


def _empty_viable() -> ViableTraitSet:
    return ViableTraitSet((), (), ())


def _empty_change() -> TraitSpaceChange:
    return classify_trait_space_change(
        ViableTraitSet((0.0,), (False,), (0.0,)),
        ViableTraitSet((0.0,), (False,), (0.0,)),
    )


def run_defense_intervention(
    params: DefenseParameters,
    patches: dict,
    intervention: DefenseIntervention,
    *,
    observed_pattern: dict | None = None,
    epsilon: float = DEFAULT_EPSILON,
    equilibration_steps: int = 40,
    outcome_steps: int = 12,
    reequilibration_steps: int | None = None,
    grid_points: int = 9,
    invasion_steps: int = 6,
    invasion_cohort: int = 12,
    invasion_replicates: int = 2,
    seed: int = 0,
) -> DefenseResult:
    """Evaluate Omega_inv before and after post-loss resident re-equilibration.

    ``outcome_steps`` is retained only as a backwards-compatible parameter. Standard
    results now use the resident endpoints, not a transient short branch, for both
    POM and post-loss invasion fitness.
    """
    observed = observed_pattern if observed_pattern is not None else defense_observed_pattern()
    resident_before, states_before, before_report = equilibrate_defense(
        patches,
        params,
        steps=equilibration_steps,
        seed=seed,
        regime=intervention.before,
    )
    base_motifs = {
        "relation_change",
        intervention.channel_motif,
        "finite_resources",
        "finite_patches",
        "local_interaction",
        "positive_trait_cost",
        "incomplete_compensation",
    }
    if before_report.status != "stationary" or resident_before.n_total == 0:
        return DefenseResult(
            intervention.name,
            before_report.status,
            _empty_viable(),
            _empty_viable(),
            _empty_change(),
            {},
            dict(observed),
            1.0,
            False,
            frozenset(base_motifs | {f"resident_before_{before_report.status}"}),
            {
                "stationarity_before": before_report.status,
                "stationarity_after": "not_run",
                "omega_after_resident": "not_run",
            },
        )

    omega_seed = seed * 5 + 3
    omega_before = estimate_defense_omega_inv(
        resident_before,
        states_before,
        patches,
        params,
        intervention.before,
        grid_points=grid_points,
        invasion_steps=invasion_steps,
        cohort=invasion_cohort,
        replicates=invasion_replicates,
        seed=omega_seed,
    )

    after_steps = reequilibration_steps if reequilibration_steps is not None else equilibration_steps
    resident_after, states_after, after_report = reequilibrate_defense(
        resident_before,
        states_before,
        patches,
        params,
        intervention.after,
        steps=max(after_steps, 4),
        seed=seed * 9 + 7,
    )
    if after_report.status != "stationary" or resident_after.n_total == 0:
        return DefenseResult(
            intervention.name,
            after_report.status,
            omega_before,
            _empty_viable(),
            _empty_change(),
            {},
            dict(observed),
            1.0,
            False,
            frozenset(base_motifs | {f"resident_after_{after_report.status}"}),
            {
                "stationarity_before": before_report.status,
                "stationarity_after": after_report.status,
                "n_resident_before": resident_before.n_total,
                "n_resident_after": resident_after.n_total,
                "omega_measure_before": round(omega_before.measure, 4),
                "omega_after_resident": "not_stationary",
                "reequilibration_steps": after_steps,
            },
        )

    omega_after = estimate_defense_omega_inv(
        resident_after,
        states_after,
        patches,
        params,
        intervention.after,
        grid_points=grid_points,
        invasion_steps=invasion_steps,
        cohort=invasion_cohort,
        replicates=invasion_replicates,
        seed=omega_seed + 1,
    )
    trait_space_change = classify_trait_space_change(omega_before, omega_after)
    p_sim = extract_defense_pom(
        resident_before,
        resident_after,
        patches,
        params,
        trait_space_change,
        predator_before=intervention.before.predator_present,
        predator_after=intervention.after.predator_present,
    )
    distance = pom_distance(p_sim, observed)
    reconfigured = trait_space_change.primary in {
        "shift",
        "contraction",
        "fragmentation",
        "collapse",
    }
    accepted = (
        after_report.status == "stationary"
        and accepted_by_epsilon(distance, epsilon)
        and reconfigured
    )
    return DefenseResult(
        intervention.name,
        "stationary",
        omega_before,
        omega_after,
        trait_space_change,
        p_sim,
        dict(observed),
        distance,
        accepted,
        frozenset(base_motifs),
        {
            "stationarity_before": before_report.status,
            "stationarity_after": after_report.status,
            "n_resident_before": resident_before.n_total,
            "n_resident_after": resident_after.n_total,
            "omega_measure_before": round(omega_before.measure, 4),
            "omega_measure_after": round(omega_after.measure, 4),
            "omega_components_before": omega_before.n_components,
            "omega_components_after": omega_after.n_components,
            "primary": trait_space_change.primary,
            "omega_after_resident": "post_intervention_reequilibrated",
            "reequilibration_steps": after_steps,
            "outcome_steps_deprecated": outcome_steps,
        },
    )


def _build_patches(n: int, capacity: int, *, connectivity: float, rng: Random) -> dict:
    return {
        pid: Patch(
            pid,
            rng.uniform(0.8, 1.2),
            capacity,
            {other: connectivity for other in range(n) if other != pid},
        )
        for pid in range(n)
    }


def sample_constrained_defense(rng: Random) -> tuple[DefenseParameters, dict]:
    params = DefenseParameters(
        predator_pressure=rng.uniform(0.22, 0.40),
        defense_effectiveness=rng.uniform(0.75, 1.0),
        defense_cost=rng.uniform(0.22, 0.42),
        fecundity_floor=rng.uniform(0.45, 0.58),
        density_threshold=rng.uniform(0.6, 0.95),
        mutation_rate=rng.uniform(0.05, 0.40),
        mutation_std=rng.uniform(0.03, 0.12),
        dispersal_base=rng.uniform(0.0, 0.18),
        distance_decay=rng.uniform(0.7, 1.6),
        resource_replenishment=rng.uniform(0.28, 0.42),
        base_survival=rng.uniform(0.93, 0.98),
        max_age=rng.randint(5, 9),
    )
    return params, _build_patches(
        rng.randint(3, 4),
        rng.randint(20, 30),
        connectivity=0.4,
        rng=rng,
    )


def sample_compensated_defense(rng: Random) -> tuple[DefenseParameters, dict]:
    params = DefenseParameters(
        predator_pressure=rng.uniform(0.05, 0.15),
        defense_effectiveness=rng.uniform(0.7, 1.0),
        defense_cost=rng.uniform(0.03, 0.12),
        fecundity_floor=rng.uniform(0.40, 0.55),
        density_threshold=rng.uniform(0.7, 1.0),
        mutation_rate=rng.uniform(0.05, 0.40),
        mutation_std=rng.uniform(0.03, 0.12),
        dispersal_base=rng.uniform(0.45, 0.70),
        distance_decay=rng.uniform(0.3, 0.8),
        resource_replenishment=rng.uniform(0.30, 0.45),
        base_survival=rng.uniform(0.92, 0.98),
        max_age=rng.randint(6, 10),
    )
    return params, _build_patches(
        rng.randint(4, 6),
        rng.randint(40, 60),
        connectivity=0.9,
        rng=rng,
    )


def defense_program_motifs(intervention: DefenseIntervention) -> frozenset[str]:
    """Legacy program assumptions; outcome labels are ignored by hardened analysis."""
    return _CHAIN_MOTIFS | {
        intervention.channel_motif,
        "finite_resources",
        "finite_patches",
        "local_interaction",
        "positive_trait_cost",
        "incomplete_compensation",
        "trait_space_shift",
    }


def generate_defense_sweep_records(
    intervention: DefenseIntervention,
    *,
    program_id: str,
    program_motifs: frozenset,
    ecosystem_sampler: Callable[[Random], tuple[DefenseParameters, dict]],
    n_regions: int = 6,
    seeds: Iterable[int] = (0, 1),
    epsilon: float = DEFAULT_EPSILON,
    base_seed: int = 0,
    **experiment_kwargs,
) -> tuple[SweepRecord, ...]:
    records: list[SweepRecord] = []
    for region in range(n_regions):
        params, patches = ecosystem_sampler(Random(base_seed * 9973 + region))
        region_id = f"eco_{region}"
        for replicate_seed in seeds:
            result = run_defense_intervention(
                params,
                patches,
                intervention,
                epsilon=epsilon,
                seed=base_seed * 9973 + region * 31 + replicate_seed,
                **experiment_kwargs,
            )
            records.append(
                SweepRecord(
                    scenario=intervention.name,
                    program_id=program_id,
                    motifs=program_motifs,
                    pattern_matched=result.accepted,
                    parameters={
                        "predator_pressure": params.predator_pressure,
                        "defense_cost": params.defense_cost,
                        "dispersal_base": params.dispersal_base,
                    },
                    initial_state={
                        "omega_measure_before": result.diagnostics.get(
                            "omega_measure_before", 0.0
                        )
                    },
                    metadata={
                        "region_id": region_id,
                        "P_sim": result.p_sim,
                        "P_obs": result.p_obs,
                        "abc_distance": round(result.distance, 4),
                        "epsilon": epsilon,
                        "accepted": result.accepted,
                        "trait_space_primary": result.trait_space_change.primary,
                        "stationarity_before": result.diagnostics.get("stationarity_before"),
                        "stationarity_after": result.diagnostics.get("stationarity_after"),
                        "omega_after_resident": result.diagnostics.get(
                            "omega_after_resident"
                        ),
                    },
                    region_id=region_id,
                    seed=replicate_seed,
                    fragile_flags=frozenset(),
                )
            )
    return tuple(records)


@dataclass(frozen=True)
class DefenseContractionSummary:
    n_runs: int
    n_stationary: int
    n_contracted: int
    contraction_fraction: float
    classification: str
    primary_counts: dict = field(default_factory=dict)


def verify_defense_contraction(
    intervention: DefenseIntervention,
    *,
    ecosystem_sampler: Callable[[Random], tuple[DefenseParameters, dict]] | None = None,
    n_draws: int = 14,
    base_seed: int = 0,
    robust_fraction: float = 0.6,
    **experiment_kwargs,
) -> DefenseContractionSummary:
    sampler = ecosystem_sampler or sample_constrained_defense
    n_stationary = 0
    n_contracted = 0
    primary_counts: dict[str, int] = {}
    for index in range(n_draws):
        params, patches = sampler(Random(base_seed * 1213 + index))
        result = run_defense_intervention(
            params,
            patches,
            intervention,
            seed=base_seed * 1213 + index,
            **experiment_kwargs,
        )
        if result.stationarity != "stationary":
            continue
        n_stationary += 1
        primary = result.trait_space_change.primary
        primary_counts[primary] = primary_counts.get(primary, 0) + 1
        n_contracted += int(result.trait_space_change.contracted)
    fraction = n_contracted / n_stationary if n_stationary else 0.0
    classification = (
        "insufficient"
        if n_stationary < 4
        else ("robust" if fraction >= robust_fraction else "fragile")
    )
    return DefenseContractionSummary(
        n_draws,
        n_stationary,
        n_contracted,
        fraction,
        classification,
        primary_counts,
    )
