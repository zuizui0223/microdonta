"""Defense metapopulation ABM — a *survival-mediated* second backend.

This is a mechanistically INDEPENDENT generative model used to test whether the
rule-transition invariant found with the pollination backend
(:mod:`causal_model.spatial_metapopulation_abm`) is an artefact of that model or a
genuine cross-ecosystem regularity.

Where the pollination model rewards the focal trait through **fecundity** (a
relationship *service* added to reproduction), this model rewards it through
**survival**: the trait is an anti-predator *defense* that reduces predation
mortality **only while the predator is present**, and is paid for by a fecundity
trade-off. The reward therefore lives in a different vital rate and a different
equation; the two backends share only the neutral scaffolding (data classes, viable-
set geometry, stationarity test, POM ordinals), never the reward dynamics.

Relationship-change intervention: **predator loss** (``predator_present`` 1 -> 0).
When the predator disappears, the defense confers no survival advantage and only
its fecundity cost remains, so high-defense phenotypes lose support and the viable
trait set contracts — exactly the same rule transition as pollinator loss, reached
through a different mechanism.

The POM output feeds the *same*
``d(P_sim, P_obs) <= epsilon -> robust/fragile -> rule-transition invariant``
pipeline, so a combined sweep over {pollination backend, defense backend} yields a
cross-system invariant across two structurally different ecosystems.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from random import Random
from typing import Callable, Iterable

from causal_model.abc_distance import accepted_by_epsilon
from causal_model.abm_family_adapter import SweepRecord
from causal_model.spatial_metapopulation_abm import (
    DEFAULT_EPSILON,
    POM_PATTERN_NAMES,
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
    default_observed_pattern,
    init_patch_states,
    pom_distance,
    seed_population,
)

_CHAIN_MOTIFS: frozenset = frozenset(
    {"relation_change", "constraint_reconfiguration", "trait_space_reconfiguration"}
)


# ---------------------------------------------------------------------------
# Parameters and regime
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DefenseParameters:
    """Physical constraints and trade-offs for one defense ecosystem.

    The trait is an anti-predator defense rewarded through *survival* and paid for
    through *fecundity*. No trait direction is specified.
    """

    predator_pressure: float        # baseline predation mortality on an undefended prey
    defense_effectiveness: float    # in (0,1]: fraction of predation a full defense removes
    defense_cost: float             # > 0: fecundity cost per unit defense (trade-off)
    fecundity_floor: float          # trait-independent baseline fecundity
    density_threshold: float
    mutation_rate: float
    mutation_std: float
    dispersal_base: float
    distance_decay: float
    resource_replenishment: float
    base_survival: float = 0.92
    max_age: int = 8
    benefit_saturation: float = 0.0  # shape of defense effectiveness vs investment


@dataclass(frozen=True)
class DefenseRegime:
    """Predator presence (the relationship) and any alternative compensation."""

    predator_present: float = 1.0    # 1 = predator present, 0 = predator lost
    dispersal_scale: float = 1.0
    repro_baseline: float = 0.0      # flat alternative-route compensation after loss


@dataclass(frozen=True)
class DefenseIntervention:
    name: str
    before: DefenseRegime
    after: DefenseRegime
    channel_motif: str


def make_defense_intervention(loss_level: float = 0.0, compensation: float = 0.08) -> DefenseIntervention:
    """Predator-loss intervention: the survival-rewarding relationship is removed."""
    return DefenseIntervention(
        name="predator_loss_defense",
        before=DefenseRegime(predator_present=1.0),
        after=DefenseRegime(predator_present=loss_level, repro_baseline=compensation),
        channel_motif="antipredator_relationship_loss",
    )


# ---------------------------------------------------------------------------
# Simulation step (survival-mediated reward — the independent mechanism)
# ---------------------------------------------------------------------------

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
    """One IBM step. Defense reduces predation mortality (gated by the predator);
    reproduction carries the fecundity cost of defense and is logistic in density.
    """
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
        n = len(local)
        k = max(patch.carrying_capacity, 1)
        density = n / k
        logistic = max(0.0, 1.0 - density)

        for ind in local:
            age_term = (ind.age / max(params.max_age, 1)) ** 2
            # SURVIVAL reward: defense removes predation mortality, gated by predator.
            protection = params.defense_effectiveness * benefit_shape(ind.trait, params.benefit_saturation)
            predation_mortality = regime.predator_present * params.predator_pressure * (1.0 - protection)
            survival_p = _clip(params.base_survival * (1.0 - 0.6 * age_term) - predation_mortality)
            if ind.age >= params.max_age or rng.random() > survival_p:
                continue
            survivors.append(replace(ind, age=ind.age + 1))

            # FECUNDITY carries the cost of defense; no relationship term here.
            mate = _mate_success(ind, local, params, rng)
            repro_p = _clip(
                params.fecundity_floor
                + 0.20 * mate
                + 0.30 * ps.resources
                + regime.repro_baseline
                - params.defense_cost * ind.trait
            ) * logistic
            if rng.random() < repro_p:
                new_trait = ind.trait
                new_geno = ind.genotype
                if rng.random() < mutation_rate:
                    new_trait = _clip(new_trait + rng.gauss(0.0, params.mutation_std))
                    new_geno = _clip(new_geno + rng.gauss(0.0, params.mutation_std * 0.5))
                target_pid = pid
                if rng.random() < params.dispersal_base * regime.dispersal_scale and patch.connectivity:
                    neighbors = list(patch.connectivity.items())
                    total_w = sum(w for _, w in neighbors)
                    if total_w > 0:
                        r = rng.random() * total_w
                        cumw = 0.0
                        for npid, w in neighbors:
                            cumw += w
                            if r <= cumw:
                                target_pid = npid
                                break
                offspring.append(Individual(
                    trait=new_trait, genotype=new_geno, age=0,
                    patch_id=target_pid, location=(rng.random(), rng.random()),
                    lineage=ind.lineage,
                ))
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
            individuals, patches, patch_states, params, rng, regime,
            mutation_override=mutation_override,
        )
    return individuals


def equilibrate_defense(
    patches: dict,
    params: DefenseParameters,
    *,
    steps: int = 40,
    seed: int = 0,
    regime: DefenseRegime = DefenseRegime(),
    record_window: int = 10,
):
    rng = Random(seed)
    individuals = seed_population(patches, params, rng)
    patch_states = init_patch_states(patches, rng)
    n_patches = len(patches)
    n_s: list[int] = []; mt_s: list[float] = []; occ_s: list[int] = []; var_s: list[float] = []
    for step in range(steps):
        individuals = advance_defense(individuals, patches, patch_states, params, rng, regime, steps=1)
        if step >= steps - record_window - 1:
            n, mt, occ, var = _series_summary(individuals, n_patches)
            n_s.append(n); mt_s.append(mt); occ_s.append(occ); var_s.append(var)
        if not individuals:
            n_s.append(0); mt_s.append(0.0); occ_s.append(0); var_s.append(0.0)
            break
    report = assess_stationarity(n_s, mt_s, occ_s, var_s, window=record_window)
    state = PopulationState(tuple(individuals), {pid: ps.resources for pid, ps in patch_states.items()})
    return state, patch_states, report


# ---------------------------------------------------------------------------
# Invasion fitness and Omega_inv (survival-mediated)
# ---------------------------------------------------------------------------

def _log_growth(counts: list[int]) -> float:
    import math
    if not counts or counts[0] == 0:
        return 0.0
    if counts[-1] == 0:
        return -5.0
    steps = len(counts) - 1
    return (math.log(counts[-1]) - math.log(counts[0])) / steps if steps else 0.0


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
    individuals = [replace(i, lineage=0) for i in resident.individuals]
    occupied = sorted(resident.occupied_patches()) or list(patches)
    for _ in range(cohort):
        pid = rng.choice(occupied)
        individuals.append(Individual(
            trait=_clip(z_prime), genotype=_clip(z_prime), age=0,
            patch_id=pid, location=(rng.random(), rng.random()), lineage=1,
        ))
    states = {pid: PatchState(ps.resources) for pid, ps in resident_states.items()}
    counts = [sum(1 for i in individuals if i.lineage == 1)]
    for _ in range(steps):
        individuals = _defense_step(individuals, patches, states, params, rng, regime, mutation_override=0.0)
        c = sum(1 for i in individuals if i.lineage == 1)
        counts.append(c)
        if c == 0:
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
    grid = tuple(i / (grid_points - 1) for i in range(grid_points))
    mask: list[bool] = []
    rates: list[float] = []
    for gi, z in enumerate(grid):
        lam = 0.0
        for r in range(replicates):
            lam += defense_invasion_growth_rate(
                resident, resident_states, patches, params, regime, z,
                steps=invasion_steps, cohort=cohort, seed=seed * 1000 + gi * 17 + r,
            )
        lam /= max(replicates, 1)
        rates.append(lam)
        mask.append(lam > threshold)
    return ViableTraitSet(grid=grid, mask=tuple(mask), growth_rates=tuple(rates))


# ---------------------------------------------------------------------------
# POM (defense-specific interaction term) and one intervention experiment
# ---------------------------------------------------------------------------

def _mean_predation_interaction(state: PopulationState, params: DefenseParameters, predator_present: float) -> float:
    """Realised predator-defense interaction: collapses when the predator is lost."""
    if not state.individuals:
        return 0.0
    vals = [
        predator_present * params.defense_effectiveness * benefit_shape(i.trait, params.benefit_saturation)
        for i in state.individuals
    ]
    return sum(vals) / len(vals)


def extract_defense_pom(
    before: PopulationState, after: PopulationState,
    patches: dict, params: DefenseParameters, ts: TraitSpaceChange,
    *, predator_before: float, predator_after: float,
    tolerance: float = 0.05, interaction_tolerance: float = 0.02,
) -> dict[str, str]:
    ic_b = _mean_predation_interaction(before, params, predator_before)
    ic_a = _mean_predation_interaction(after, params, predator_after)
    n_patches = max(len(patches), 1)
    occ_b = len(before.occupied_patches()) / n_patches
    occ_a = len(after.occupied_patches()) / n_patches
    ne_b, ne_a = _ne_proxy(before), _ne_proxy(after)
    ne_scale = max(ne_b, ne_a, 1.0)
    tm_b, tm_a = _trait_moments(before), _trait_moments(after)
    from causal_model.spatial_metapopulation_abm import _OMEGA_STATE
    return {
        "interaction_network": _ordinal(ic_a - ic_b, interaction_tolerance),
        "patch_occupancy": _ordinal(occ_a - occ_b, tolerance),
        "persistence_ne": _ordinal((ne_a - ne_b) / ne_scale, tolerance),
        "trait_moments": _ordinal(tm_a - tm_b, tolerance),
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
    """Focal ``P_obs`` for predator loss: the survival-mediated signature.

    Unlike pollinator loss (persistence falls, viable set CONTRACTS), losing a
    predator lets the population grow and shifts the viable set toward low defense:
    the relationship loss *reconfigures* trait space, but as a SHIFT, not a
    contraction.
    """
    return {
        "interaction_network": "decrease",   # predator-defense interaction collapses
        "patch_occupancy": "stable",
        "persistence_ne": "increase",        # predation removed -> population grows
        "trait_moments": "stable",
        "omega_inv_state": "shifted",        # viable set shifts toward low defense
    }


def run_defense_intervention(
    params: DefenseParameters,
    patches: dict,
    intervention: DefenseIntervention,
    *,
    observed_pattern: dict | None = None,
    epsilon: float = DEFAULT_EPSILON,
    equilibration_steps: int = 40,
    outcome_steps: int = 12,
    grid_points: int = 9,
    invasion_steps: int = 6,
    invasion_cohort: int = 12,
    invasion_replicates: int = 2,
    seed: int = 0,
) -> DefenseResult:
    observed = observed_pattern if observed_pattern is not None else defense_observed_pattern()
    resident, states, report = equilibrate_defense(
        patches, params, steps=equilibration_steps, seed=seed, regime=intervention.before,
    )
    base_motifs = {
        "relation_change", intervention.channel_motif,
        "finite_resources", "finite_patches", "local_interaction", "positive_trait_cost",
    }
    if report.status != "stationary":
        empty = ViableTraitSet((), (), ())
        ts = classify_trait_space_change(ViableTraitSet((0.0,), (False,), (0.0,)),
                                         ViableTraitSet((0.0,), (False,), (0.0,)))
        return DefenseResult(
            intervention.name, report.status, empty, empty, ts, {}, dict(observed), 1.0, False,
            frozenset(base_motifs | {f"resident_{report.status}"}), {"stationarity": report.status},
        )

    omega_seed = seed * 5 + 3
    omega_before = estimate_defense_omega_inv(
        resident, states, patches, params, intervention.before,
        grid_points=grid_points, invasion_steps=invasion_steps,
        cohort=invasion_cohort, replicates=invasion_replicates, seed=omega_seed)
    omega_after = estimate_defense_omega_inv(
        resident, states, patches, params, intervention.after,
        grid_points=grid_points, invasion_steps=invasion_steps,
        cohort=invasion_cohort, replicates=invasion_replicates, seed=omega_seed)
    ts = classify_trait_space_change(omega_before, omega_after)

    def _outcome(regime: DefenseRegime, bseed: int) -> PopulationState:
        rng = Random(bseed)
        inds = [replace(i) for i in resident.individuals]
        st = {pid: PatchState(ps.resources) for pid, ps in states.items()}
        inds = advance_defense(inds, patches, st, params, rng, regime, steps=outcome_steps)
        return PopulationState(tuple(inds), {pid: ps.resources for pid, ps in st.items()})

    out_b = _outcome(intervention.before, seed * 7 + 1)
    out_a = _outcome(intervention.after, seed * 7 + 2)
    p_sim = extract_defense_pom(
        out_b, out_a, patches, params, ts,
        predator_before=intervention.before.predator_present,
        predator_after=intervention.after.predator_present)
    distance = pom_distance(p_sim, observed)
    # The focal pattern is *loss-direction* trait-space reconfiguration (a shift
    # toward low defense, possibly with fragmentation/contraction) — NOT expansion
    # (which sufficient compensation produces) and NOT conserved. A run is admitted
    # iff its POM is within epsilon AND the viable set was reconfigured downward.
    reconfigured = ts.primary in {"shift", "contraction", "fragmentation", "collapse"}
    accepted = accepted_by_epsilon(distance, epsilon) and reconfigured

    motifs = set(base_motifs)
    motifs.add("incomplete_compensation")
    if ts.contracted:
        motifs.add("trait_space_contraction")
    if ts.fragmented:
        motifs.add("trait_space_fragmentation")
    if ts.shifted:
        motifs.add("trait_space_shift")

    return DefenseResult(
        intervention.name, report.status, omega_before, omega_after, ts,
        p_sim, dict(observed), distance, accepted, frozenset(motifs),
        {"stationarity": report.status,
         "omega_measure_before": round(omega_before.measure, 4),
         "omega_measure_after": round(omega_after.measure, 4),
         "primary": ts.primary},
    )


# ---------------------------------------------------------------------------
# Random ecosystems (constrained vs compensated counterexample)
# ---------------------------------------------------------------------------

def _build_patches(n: int, capacity: int, *, connectivity: float, rng: Random) -> dict:
    patches: dict = {}
    for pid in range(n):
        conn = {o: connectivity for o in range(n) if o != pid}
        patches[pid] = Patch(pid, rng.uniform(0.8, 1.2), capacity, conn)
    return patches


def sample_constrained_defense(rng: Random) -> tuple[DefenseParameters, dict]:
    """A load-bearing predator: defense materially buys survival, and is costly."""
    params = DefenseParameters(
        predator_pressure=rng.uniform(0.22, 0.40),    # load-bearing but survivable predation
        defense_effectiveness=rng.uniform(0.75, 1.0),
        defense_cost=rng.uniform(0.22, 0.42),         # positive fecundity cost
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
    return params, _build_patches(rng.randint(3, 4), rng.randint(20, 30), connectivity=0.4, rng=rng)


def sample_compensated_defense(rng: Random) -> tuple[DefenseParameters, dict]:
    """Counterexample: weak predation, cheap defense, ample dispersal/large patches."""
    params = DefenseParameters(
        predator_pressure=rng.uniform(0.05, 0.15),    # predator barely matters
        defense_effectiveness=rng.uniform(0.7, 1.0),
        defense_cost=rng.uniform(0.03, 0.12),         # defense almost free
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
    return params, _build_patches(rng.randint(4, 6), rng.randint(40, 60), connectivity=0.9, rng=rng)


# ---------------------------------------------------------------------------
# Sweep records for the rule-transition pipeline
# ---------------------------------------------------------------------------

def defense_program_motifs(intervention: DefenseIntervention) -> frozenset:
    """Structural motifs of the defense program.

    Note this asserts ``trait_space_shift`` — the survival-mediated geometry — NOT
    ``trait_space_contraction``. The shared chain and physical-constraint motifs are
    what it has in common with the pollination program; the specific geometry is not
    shared, so the cross-system invariant correctly excludes contraction.
    """
    return _CHAIN_MOTIFS | {
        intervention.channel_motif,
        "finite_resources", "finite_patches", "local_interaction",
        "positive_trait_cost", "incomplete_compensation", "trait_space_shift",
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
        for s in seeds:
            res = run_defense_intervention(
                params, patches, intervention, epsilon=epsilon,
                seed=base_seed * 9973 + region * 31 + s, **experiment_kwargs)
            records.append(SweepRecord(
                scenario=intervention.name,
                program_id=program_id,
                motifs=program_motifs,
                pattern_matched=res.accepted,
                parameters={"predator_pressure": params.predator_pressure,
                            "defense_cost": params.defense_cost,
                            "dispersal_base": params.dispersal_base},
                initial_state={"omega_measure_before": res.diagnostics.get("omega_measure_before", 0.0)},
                metadata={"region_id": region_id, "P_sim": res.p_sim, "P_obs": res.p_obs,
                          "abc_distance": round(res.distance, 4), "epsilon": epsilon,
                          "accepted": res.accepted, "trait_space_primary": res.trait_space_change.primary},
                region_id=region_id, seed=s, fragile_flags=frozenset(),
            ))
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
    n_stat = 0; n_con = 0; primary: dict = {}
    for i in range(n_draws):
        params, patches = sampler(Random(base_seed * 1213 + i))
        res = run_defense_intervention(params, patches, intervention, seed=base_seed * 1213 + i, **experiment_kwargs)
        if res.stationarity != "stationary":
            continue
        n_stat += 1
        primary[res.trait_space_change.primary] = primary.get(res.trait_space_change.primary, 0) + 1
        if res.trait_space_change.contracted:
            n_con += 1
    frac = n_con / n_stat if n_stat else 0.0
    cls = "insufficient" if n_stat < 4 else ("robust" if frac >= robust_fraction else "fragile")
    return DefenseContractionSummary(n_draws, n_stat, n_con, frac, cls, primary)
