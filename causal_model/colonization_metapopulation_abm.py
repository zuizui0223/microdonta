"""Colonization metapopulation ABM — a *establishment-mediated* third backend.

A third mechanistically INDEPENDENT generative model, to take the cross-system
generality test from N=2 to N=3 structurally different ecosystems.

Here the focal trait is **dispersal investment**. Its reward is neither fecundity
(pollination backend) nor survival (defense backend) but **offspring
establishment**: a disperser escapes local competition by settling in another
patch, but only while dispersal corridors exist. The reward is therefore gated by
**connectivity** (the relationship). Dispersal is a *committed* investment — a
high-trait parent allocates offspring to dispersal — so when connectivity is lost
those dispersing offspring die in transit, and high dispersal becomes pure cost
plus offspring loss (the island-syndrome selection against dispersal).

Relationship-change intervention: **connectivity loss** (corridors cut). It feeds
the same ``d(P_sim,P_obs) <= epsilon -> robust/fragile -> rule-transition invariant``
pipeline, so a combined sweep over {pollination, defense, colonization} yields a
cross-system invariant over three structurally different ecosystems.
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

_CHAIN_MOTIFS: frozenset = frozenset(
    {"relation_change", "constraint_reconfiguration", "trait_space_reconfiguration"}
)


@dataclass(frozen=True)
class ColonizationParameters:
    """Physical constraints/trade-offs for one colonization ecosystem.

    The trait is dispersal investment, rewarded through escaping local competition
    (establishment in another patch) and paid through a fecundity cost.
    """

    dispersal_cost: float           # > 0: fecundity cost per unit dispersal investment
    fecundity: float                # baseline reproductive probability scale
    extinction_rate: float          # per-patch local extinction probability per step
    density_threshold: float
    mutation_rate: float
    mutation_std: float
    distance_decay: float
    resource_replenishment: float
    base_survival: float = 0.9
    max_age: int = 8
    benefit_saturation: float = 0.0


@dataclass(frozen=True)
class ColonizationRegime:
    """Connectivity (the relationship) and any alternative compensation."""

    connectivity_present: float = 1.0   # 1 = corridors intact, 0 = isolated
    repro_baseline: float = 0.0


@dataclass(frozen=True)
class ColonizationIntervention:
    name: str
    before: ColonizationRegime
    after: ColonizationRegime
    channel_motif: str


def make_colonization_intervention(loss_level: float = 0.0, compensation: float = 0.06) -> ColonizationIntervention:
    return ColonizationIntervention(
        name="connectivity_loss_colonization",
        before=ColonizationRegime(connectivity_present=1.0),
        after=ColonizationRegime(connectivity_present=loss_level, repro_baseline=compensation),
        channel_motif="dispersal_corridor_relationship_loss",
    )


def _colonization_step(
    individuals: list[Individual],
    patches: dict,
    patch_states: dict,
    params: ColonizationParameters,
    rng: Random,
    regime: ColonizationRegime,
    *,
    mutation_override: float | None = None,
) -> list[Individual]:
    """One IBM step. Dispersers escape local competition (establish elsewhere) only
    while connectivity holds; otherwise they die in transit. Non-dispersers face
    local logistic competition. Dispersal investment carries a fecundity cost.
    """
    mutation_rate = params.mutation_rate if mutation_override is None else mutation_override
    n_per_patch: dict = {}
    for ind in individuals:
        n_per_patch[ind.patch_id] = n_per_patch.get(ind.patch_id, 0) + 1
    # patch density at the start of the step (used for establishment success): a
    # freshly emptied patch is a colonisation opportunity for dispersers.
    patch_density = {pid: n_per_patch.get(pid, 0) / max(patches[pid].carrying_capacity, 1) for pid in patches}
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
        local_room = max(0.0, 1.0 - density)

        for ind in local:
            age_term = (ind.age / max(params.max_age, 1)) ** 2
            survival_p = _clip(params.base_survival * (1.0 - 0.6 * age_term))
            if ind.age >= params.max_age or rng.random() > survival_p:
                continue
            survivors.append(replace(ind, age=ind.age + 1))

            mate = _mate_success(ind, local, params, rng)
            conceive_p = _clip(
                params.fecundity
                + 0.20 * mate
                + 0.30 * ps.resources
                + regime.repro_baseline
                - params.dispersal_cost * ind.trait
            )
            if rng.random() >= conceive_p:
                continue
            new_trait = ind.trait
            new_geno = ind.genotype
            if rng.random() < mutation_rate:
                new_trait = _clip(new_trait + rng.gauss(0.0, params.mutation_std))
                new_geno = _clip(new_geno + rng.gauss(0.0, params.mutation_std * 0.5))

            disperse_p = benefit_shape(ind.trait, params.benefit_saturation)  # committed investment
            if rng.random() < disperse_p:
                # disperser: reaches a patch only if a corridor exists, then
                # establishes with success set by the TARGET's available room (an
                # emptied patch is easy to colonise — the rescue/colonisation reward).
                if rng.random() < regime.connectivity_present and patch.connectivity:
                    target = rng.choice(list(patch.connectivity))
                    if rng.random() < max(0.0, 1.0 - patch_density.get(target, 1.0)):
                        offspring.append(Individual(new_trait, new_geno, 0, target,
                                                    (rng.random(), rng.random()), ind.lineage))
                # else: dispersed into the void / failed to establish -> dies
            else:
                # non-disperser: subject to local competition (logistic)
                if rng.random() < local_room:
                    offspring.append(Individual(new_trait, new_geno, 0, pid,
                                                (rng.random(), rng.random()), ind.lineage))

    next_gen = survivors + offspring
    # local extinction: each patch is wiped with probability extinction_rate,
    # creating empty patches that only dispersers (with connectivity) can recolonise.
    if params.extinction_rate > 0.0 and next_gen:
        doomed = {pid for pid in patches if rng.random() < params.extinction_rate}
        if doomed:
            next_gen = [i for i in next_gen if i.patch_id not in doomed]
    return next_gen


def advance_colonization(individuals, patches, patch_states, params, rng,
                         regime: ColonizationRegime = ColonizationRegime(), *,
                         steps: int = 1, mutation_override: float | None = None):
    for _ in range(steps):
        if not individuals:
            break
        individuals = _colonization_step(individuals, patches, patch_states, params, rng, regime,
                                         mutation_override=mutation_override)
    return individuals


def equilibrate_colonization(patches, params, *, steps=40, seed=0,
                             regime: ColonizationRegime = ColonizationRegime(), record_window=10):
    rng = Random(seed)
    individuals = seed_population(patches, params, rng)
    patch_states = init_patch_states(patches, rng)
    n_patches = len(patches)
    n_s=[]; mt_s=[]; occ_s=[]; var_s=[]
    for step in range(steps):
        individuals = advance_colonization(individuals, patches, patch_states, params, rng, regime, steps=1)
        if step >= steps - record_window - 1:
            n, mt, occ, var = _series_summary(individuals, n_patches)
            n_s.append(n); mt_s.append(mt); occ_s.append(occ); var_s.append(var)
        if not individuals:
            n_s.append(0); mt_s.append(0.0); occ_s.append(0); var_s.append(0.0); break
    report = assess_stationarity(n_s, mt_s, occ_s, var_s, window=record_window)
    state = PopulationState(tuple(individuals), {pid: ps.resources for pid, ps in patch_states.items()})
    return state, patch_states, report


def _log_growth(counts):
    import math
    if not counts or counts[0] == 0:
        return 0.0
    if counts[-1] == 0:
        return -5.0
    steps = len(counts) - 1
    return (math.log(counts[-1]) - math.log(counts[0])) / steps if steps else 0.0


def colonization_invasion_growth_rate(resident, resident_states, patches, params, regime,
                                      z_prime, *, steps=6, cohort=12, seed=0):
    rng = Random(seed)
    individuals = [replace(i, lineage=0) for i in resident.individuals]
    occupied = sorted(resident.occupied_patches()) or list(patches)
    for _ in range(cohort):
        pid = rng.choice(occupied)
        individuals.append(Individual(_clip(z_prime), _clip(z_prime), 0, pid,
                                      (rng.random(), rng.random()), 1))
    states = {pid: PatchState(ps.resources) for pid, ps in resident_states.items()}
    counts = [sum(1 for i in individuals if i.lineage == 1)]
    for _ in range(steps):
        individuals = _colonization_step(individuals, patches, states, params, rng, regime, mutation_override=0.0)
        c = sum(1 for i in individuals if i.lineage == 1)
        counts.append(c)
        if c == 0:
            break
    return _log_growth(counts)


def estimate_colonization_omega_inv(resident, resident_states, patches, params, regime, *,
                                    grid_points=9, invasion_steps=6, cohort=12, replicates=2,
                                    threshold=0.0, seed=0):
    grid = tuple(i / (grid_points - 1) for i in range(grid_points))
    mask=[]; rates=[]
    for gi, z in enumerate(grid):
        lam = 0.0
        for r in range(replicates):
            lam += colonization_invasion_growth_rate(resident, resident_states, patches, params, regime, z,
                                                     steps=invasion_steps, cohort=cohort, seed=seed*1000+gi*17+r)
        lam /= max(replicates, 1)
        rates.append(lam); mask.append(lam > threshold)
    return ViableTraitSet(grid=grid, mask=tuple(mask), growth_rates=tuple(rates))


def _mean_colonization_interaction(state: PopulationState, params: ColonizationParameters, connectivity: float) -> float:
    if not state.individuals:
        return 0.0
    vals = [connectivity * benefit_shape(i.trait, params.benefit_saturation) for i in state.individuals]
    return sum(vals) / len(vals)


def colonization_observed_pattern() -> dict[str, str]:
    """Focal P_obs for connectivity loss: dispersal-establishment interaction
    collapses, isolated patches lose recruitment (occupancy/persistence fall), and
    the viable set is reconfigured toward low dispersal."""
    return {
        "interaction_network": "decrease",
        "patch_occupancy": "decrease",   # isolated patches not recolonised
        "persistence_ne": "decrease",
        "trait_moments": "stable",
        "omega_inv_state": "shifted",
    }


def extract_colonization_pom(before, after, patches, params, ts, *,
                             connectivity_before, connectivity_after,
                             tolerance=0.05, interaction_tolerance=0.02):
    ic_b = _mean_colonization_interaction(before, params, connectivity_before)
    ic_a = _mean_colonization_interaction(after, params, connectivity_after)
    n_patches = max(len(patches), 1)
    occ_b = len(before.occupied_patches()) / n_patches
    occ_a = len(after.occupied_patches()) / n_patches
    ne_b, ne_a = _ne_proxy(before), _ne_proxy(after)
    ne_scale = max(ne_b, ne_a, 1.0)
    tm_b, tm_a = _trait_moments(before), _trait_moments(after)
    return {
        "interaction_network": _ordinal(ic_a - ic_b, interaction_tolerance),
        "patch_occupancy": _ordinal(occ_a - occ_b, tolerance),
        "persistence_ne": _ordinal((ne_a - ne_b) / ne_scale, tolerance),
        "trait_moments": _ordinal(tm_a - tm_b, tolerance),
        "omega_inv_state": _OMEGA_STATE.get(ts.primary, "conserved"),
    }


@dataclass(frozen=True)
class ColonizationResult:
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


def run_colonization_intervention(params, patches, intervention, *, observed_pattern=None,
                                  epsilon=DEFAULT_EPSILON, equilibration_steps=40, outcome_steps=12,
                                  grid_points=9, invasion_steps=6, invasion_cohort=12,
                                  invasion_replicates=2, seed=0) -> ColonizationResult:
    observed = observed_pattern if observed_pattern is not None else colonization_observed_pattern()
    resident, states, report = equilibrate_colonization(
        patches, params, steps=equilibration_steps, seed=seed, regime=intervention.before)
    base_motifs = {"relation_change", intervention.channel_motif, "finite_resources",
                   "finite_patches", "local_interaction", "positive_trait_cost"}
    if report.status != "stationary":
        empty = ViableTraitSet((), (), ())
        ts = classify_trait_space_change(ViableTraitSet((0.0,), (False,), (0.0,)),
                                         ViableTraitSet((0.0,), (False,), (0.0,)))
        return ColonizationResult(intervention.name, report.status, empty, empty, ts, {},
                                  dict(observed), 1.0, False,
                                  frozenset(base_motifs | {f"resident_{report.status}"}),
                                  {"stationarity": report.status})
    omega_seed = seed * 5 + 3
    ob = estimate_colonization_omega_inv(resident, states, patches, params, intervention.before,
        grid_points=grid_points, invasion_steps=invasion_steps, cohort=invasion_cohort,
        replicates=invasion_replicates, seed=omega_seed)
    oa = estimate_colonization_omega_inv(resident, states, patches, params, intervention.after,
        grid_points=grid_points, invasion_steps=invasion_steps, cohort=invasion_cohort,
        replicates=invasion_replicates, seed=omega_seed)
    ts = classify_trait_space_change(ob, oa)

    def _outcome(regime, bseed):
        rng = Random(bseed)
        inds = [replace(i) for i in resident.individuals]
        st = {pid: PatchState(ps.resources) for pid, ps in states.items()}
        inds = advance_colonization(inds, patches, st, params, rng, regime, steps=outcome_steps)
        return PopulationState(tuple(inds), {pid: ps.resources for pid, ps in st.items()})

    out_b = _outcome(intervention.before, seed * 7 + 1)
    out_a = _outcome(intervention.after, seed * 7 + 2)
    p_sim = extract_colonization_pom(out_b, out_a, patches, params, ts,
        connectivity_before=intervention.before.connectivity_present,
        connectivity_after=intervention.after.connectivity_present)
    distance = pom_distance(p_sim, observed)
    reconfigured = ts.primary in {"shift", "contraction", "fragmentation", "collapse"}
    accepted = accepted_by_epsilon(distance, epsilon) and reconfigured
    motifs = set(base_motifs); motifs.add("incomplete_compensation")
    if ts.contracted: motifs.add("trait_space_contraction")
    if ts.fragmented: motifs.add("trait_space_fragmentation")
    if ts.shifted: motifs.add("trait_space_shift")
    return ColonizationResult(intervention.name, report.status, ob, oa, ts, p_sim, dict(observed),
                              distance, accepted, frozenset(motifs),
                              {"stationarity": report.status, "primary": ts.primary,
                               "omega_measure_before": round(ob.measure, 4),
                               "omega_measure_after": round(oa.measure, 4)})


def _build_patches(n, capacity, *, connectivity, rng):
    patches = {}
    for pid in range(n):
        conn = {o: connectivity for o in range(n) if o != pid}
        patches[pid] = Patch(pid, rng.uniform(0.8, 1.2), capacity, conn)
    return patches


def sample_constrained_colonization(rng):
    """Crowded, well-structured habitat where dispersal genuinely buys escape from
    local competition, and is costly."""
    params = ColonizationParameters(
        dispersal_cost=rng.uniform(0.20, 0.40),
        fecundity=rng.uniform(0.55, 0.75),       # high fecundity -> patches crowd -> dispersal pays
        extinction_rate=rng.uniform(0.04, 0.10),  # turnover creates empties to colonise
        density_threshold=rng.uniform(0.6, 0.95),
        mutation_rate=rng.uniform(0.05, 0.40),
        mutation_std=rng.uniform(0.03, 0.12),
        distance_decay=rng.uniform(0.7, 1.6),
        resource_replenishment=rng.uniform(0.30, 0.45),
        base_survival=rng.uniform(0.86, 0.94),
        max_age=rng.randint(5, 9),
    )
    return params, _build_patches(rng.randint(3, 4), rng.randint(18, 28), connectivity=0.5, rng=rng)


def sample_compensated_colonization(rng):
    """Counterexample: low cost, low crowding, ample compensation -> connectivity
    loss barely matters."""
    params = ColonizationParameters(
        dispersal_cost=rng.uniform(0.03, 0.12),
        fecundity=rng.uniform(0.40, 0.55),
        extinction_rate=rng.uniform(0.02, 0.08),   # little turnover -> dispersal barely matters
        density_threshold=rng.uniform(0.7, 1.0),
        mutation_rate=rng.uniform(0.05, 0.40),
        mutation_std=rng.uniform(0.03, 0.12),
        distance_decay=rng.uniform(0.3, 0.8),
        resource_replenishment=rng.uniform(0.34, 0.48),
        base_survival=rng.uniform(0.9, 0.97),
        max_age=rng.randint(6, 10),
    )
    return params, _build_patches(rng.randint(4, 6), rng.randint(45, 65), connectivity=0.9, rng=rng)


def colonization_program_motifs(intervention: ColonizationIntervention) -> frozenset:
    """Asserts trait_space_contraction (its characteristic geometry).

    Connectivity loss makes committed dispersal lethal (offspring die in transit),
    so high dispersal becomes non-viable and the viable set's upper edge collapses
    — a contraction, like the fecundity-gated pollination model and unlike the
    survival-gated defense model (which shifts). The shared cross-system motifs are
    the chain and physical constraints, not this geometry.
    """
    return _CHAIN_MOTIFS | {
        intervention.channel_motif,
        "finite_resources", "finite_patches", "local_interaction",
        "positive_trait_cost", "incomplete_compensation", "trait_space_contraction",
    }


def generate_colonization_sweep_records(intervention, *, program_id, program_motifs,
                                        ecosystem_sampler, n_regions=6, seeds=(0, 1),
                                        epsilon=DEFAULT_EPSILON, base_seed=0, **experiment_kwargs):
    records = []
    for region in range(n_regions):
        params, patches = ecosystem_sampler(Random(base_seed * 9973 + region))
        region_id = f"eco_{region}"
        for s in seeds:
            res = run_colonization_intervention(params, patches, intervention, epsilon=epsilon,
                seed=base_seed * 9973 + region * 31 + s, **experiment_kwargs)
            records.append(SweepRecord(
                scenario=intervention.name, program_id=program_id, motifs=program_motifs,
                pattern_matched=res.accepted,
                parameters={"dispersal_cost": params.dispersal_cost, "fecundity": params.fecundity},
                initial_state={"omega_measure_before": res.diagnostics.get("omega_measure_before", 0.0)},
                metadata={"region_id": region_id, "P_sim": res.p_sim, "P_obs": res.p_obs,
                          "abc_distance": round(res.distance, 4), "epsilon": epsilon,
                          "accepted": res.accepted, "trait_space_primary": res.trait_space_change.primary},
                region_id=region_id, seed=s, fragile_flags=frozenset()))
    return tuple(records)


@dataclass(frozen=True)
class ColonizationSummary:
    n_runs: int
    n_stationary: int
    n_accepted: int
    accept_fraction: float
    primary_counts: dict = field(default_factory=dict)


def verify_colonization_reconfiguration(intervention, *, ecosystem_sampler=None, n_draws=14,
                                        base_seed=0, **experiment_kwargs) -> ColonizationSummary:
    sampler = ecosystem_sampler or sample_constrained_colonization
    n_stat = 0; n_acc = 0; primary = {}
    for i in range(n_draws):
        params, patches = sampler(Random(base_seed * 1213 + i))
        res = run_colonization_intervention(params, patches, intervention, seed=base_seed * 1213 + i, **experiment_kwargs)
        if res.stationarity != "stationary":
            continue
        n_stat += 1
        primary[res.trait_space_change.primary] = primary.get(res.trait_space_change.primary, 0) + 1
        n_acc += int(res.accepted)
    return ColonizationSummary(n_draws, n_stat, n_acc, n_acc / n_stat if n_stat else 0.0, primary)
