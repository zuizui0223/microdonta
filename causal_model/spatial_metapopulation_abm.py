"""Spatial individual- and patch-based metapopulation ABM for rule-transition RACH.

This is the *primary* generative backend for the rule-transition framework. The
abstract :mod:`causal_model.ecological_rule_abm` remains as a fast demo; this
module is a genuine individual-based, patch-based simulation in which the trait
distribution is an **emergent** outcome — no trait-evolution direction is ever
specified, only physical constraints and trade-offs.

What is modelled
----------------
* **Individual**: ``trait`` (focal investment), ``genotype`` (heritable basis),
  ``age``, ``patch_id``, within-patch ``location``, and a ``lineage`` tag used
  for invasion-fitness measurement.
* **Patch**: ``area``, ``carrying_capacity``, ``connectivity`` to other patches;
  a mutable ``PatchState`` carries the local ``resources``.
* **Interaction / reproduction / mortality / dispersal** all emerge from
  inter-individual distance, trait match, local density, resource constraint, and
  explicit life-history trade-offs (a costly trait reduces both fecundity and
  survival). Reproduction is logistic in local density (finite resources); there
  is no hard birth cap, so rare invaders always have demographic room.

The four invariant physical constraints (never violated by the ensemble):
finite resources, **positive** trait cost, finite patches, local interaction,
bounded traits in ``[0, 1]``. The trait *direction* is never an input.

Causal interventions ("relationship changes")
----------------------------------------------
A :class:`Regime` scales three mechanism channels. An :class:`Intervention`
pairs a *before* and *after* regime that share the identical pre-change resident
community and RNG structure, so the before/after comparison is controlled:

* ``pollination_loss``  — the interaction (mutualistic) relationship collapses
  (``interaction_scale`` 1→0) with only incomplete alternative compensation.
* ``predation_loss``    — top-down density-dependent mortality is removed
  (``predation_scale`` 1→0), intensifying resource competition.
* ``dispersal_loss``    — dispersal pathways are cut (``dispersal_scale`` 1→0),
  isolating patches.

Viable trait set ``Omega_inv`` (invasion fitness)
-------------------------------------------------
Trait space is summarised not by a mean but by the **viable set**
``Omega_inv = {z' : lambda(z' | Z*) > 0}``, where ``lambda`` is the long-term
growth rate of a rare monomorphic mutant ``z'`` introduced into the
quasi-stationary resident community ``Z*`` and bred true (mutation off) in the
full spatial dynamics. Comparing ``Omega_inv`` before vs after an intervention
detects trait-space **contraction**, **fragmentation**, or **shift**.

Connection to the rule-transition pipeline
------------------------------------------
:func:`generate_sweep_records` returns
:class:`causal_model.abm_family_adapter.SweepRecord` tuples that feed directly
into :func:`causal_model.rule_transition_pipeline.analyse_rule_transitions`
(robust/fragile classification → cross-system rule-transition invariants).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from random import Random
from typing import Callable, Iterable

from causal_model.abc_distance import accepted_by_epsilon, pattern_distance
from causal_model.abm_family_adapter import SweepRecord


# ---------------------------------------------------------------------------
# Core dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Individual:
    """One individual in the IBM."""

    trait: float                    # focal trait investment in [0, 1]
    genotype: float                 # heritable genetic basis in [0, 1]
    age: int
    patch_id: int
    location: tuple[float, float]   # (x, y) within-patch location in [0, 1]^2
    lineage: int = 0                # 0 = resident, 1 = introduced invader cohort


@dataclass(frozen=True)
class Patch:
    """One discrete habitat patch."""

    patch_id: int
    area: float
    carrying_capacity: int
    connectivity: dict              # {neighbor_patch_id: float} dispersal weight


@dataclass
class PatchState:
    """Mutable per-patch resource state during simulation."""

    resources: float


@dataclass(frozen=True)
class MetapopParameters:
    """Physical constraints and trade-offs for one ecosystem draw.

    None of these specify a trait *direction*: they are costs, benefits, and
    physical limits. The emergent trait distribution is read off the simulation.
    """

    interaction_benefit: float      # reproductive gain from a matched interaction
    investment_reward: float        # extra interaction gain that scales with trait
    trait_cost: float               # > 0: fecundity cost per unit trait (trade-off)
    survival_tradeoff: float        # >= 0: survival cost per unit trait (trade-off)
    density_threshold: float        # local density at which interaction saturates
    mutation_rate: float
    mutation_std: float
    dispersal_base: float
    distance_decay: float           # > 0: interaction is local in space
    resource_replenishment: float   # finite-resource recovery per step
    predation_pressure: float       # density-dependent top-down mortality
    base_survival: float = 0.85
    max_age: int = 8
    benefit_saturation: float = 0.0  # 0 = benefit linear in trait; >0 = saturating
                                     # (half-saturation constant; smaller = saturates earlier)


@dataclass(frozen=True)
class Regime:
    """Scales the three intervention channels (1.0 = channel intact)."""

    interaction_scale: float = 1.0
    predation_scale: float = 1.0
    dispersal_scale: float = 1.0
    repro_baseline: float = 0.0     # flat alternative-route compensation


@dataclass(frozen=True)
class PopulationState:
    """Snapshot of the metapopulation."""

    individuals: tuple[Individual, ...]
    patch_resources: dict

    @property
    def n_total(self) -> int:
        return len(self.individuals)

    def n_per_patch(self) -> dict:
        counts: dict = {}
        for ind in self.individuals:
            counts[ind.patch_id] = counts.get(ind.patch_id, 0) + 1
        return counts

    def trait_values(self) -> tuple[float, ...]:
        return tuple(i.trait for i in self.individuals)

    def mean_trait(self) -> float:
        v = self.trait_values()
        return sum(v) / len(v) if v else 0.0

    def trait_variance(self) -> float:
        v = self.trait_values()
        if len(v) < 2:
            return 0.0
        m = sum(v) / len(v)
        return sum((x - m) ** 2 for x in v) / len(v)

    def trait_genotype_cov(self) -> float:
        inds = self.individuals
        n = len(inds)
        if n < 2:
            return 0.0
        mt = sum(i.trait for i in inds) / n
        mg = sum(i.genotype for i in inds) / n
        return sum((i.trait - mt) * (i.genotype - mg) for i in inds) / n

    def occupied_patches(self) -> frozenset:
        return frozenset(i.patch_id for i in self.individuals)


# ---------------------------------------------------------------------------
# Simulation internals
# ---------------------------------------------------------------------------

def _clip(v: float) -> float:
    return max(0.0, min(1.0, v))


def benefit_shape(trait: float, saturation: float) -> float:
    """Benefit-vs-investment response B(z)/b, normalised so B(1)=1 in both forms.

    ``saturation <= 0`` is the linear response ``z``. ``saturation > 0`` is a
    saturating (Holling-II-like) response ``z*(1+h)/(h+z)`` with half-saturation
    ``h``: steep early, flat for large ``z`` — so high investment buys little extra
    benefit. Smaller ``h`` saturates earlier (weaker support for large traits).
    """
    if saturation <= 0.0:
        return trait
    return trait * (1.0 + saturation) / (saturation + trait)


def _relationship_service(
    ind: Individual,
    density: float,
    params: MetapopParameters,
    interaction_scale: float,
) -> float:
    """Reproductive benefit the *interaction relationship* confers on this individual.

    The service (e.g. pollinator visitation) rewards the individual's own trait
    **investment** through :func:`benefit_shape` (linear or saturating), moderated
    mildly by local density (a shared, locally limited service that never falls
    below a floor). It is gated by ``interaction_scale``: when the relationship is
    lost the whole term vanishes, so the costly trait loses its support. This is
    the load-bearing channel whose loss contracts trait space.
    """
    local_availability = max(0.55, 1.0 - 0.5 * density / max(params.density_threshold, 1e-6))
    shaped = benefit_shape(ind.trait, params.benefit_saturation)
    return interaction_scale * params.interaction_benefit * shaped * local_availability


def _mate_success(
    ind: Individual,
    local: list[Individual],
    params: MetapopParameters,
    rng: Random,
) -> float:
    """Mate-finding success: needs a trait-compatible, spatially close partner.

    Depends on inter-individual distance and trait match (this is the assortative,
    spatially local component the relationship-service term does not capture).
    """
    candidates = [o for o in local if o is not ind]
    if not candidates:
        return 0.0
    partner = rng.choice(candidates)
    trait_match = 1.0 - abs(ind.trait - partner.trait)
    dx = ind.location[0] - partner.location[0]
    dy = ind.location[1] - partner.location[1]
    dist = math.sqrt(dx * dx + dy * dy)
    dist_factor = math.exp(-params.distance_decay * dist)
    return trait_match * dist_factor


def _simulate_step(
    individuals: list[Individual],
    patches: dict,
    patch_states: dict,
    params: MetapopParameters,
    rng: Random,
    regime: Regime,
    *,
    mutation_override: float | None = None,
) -> list[Individual]:
    """One IBM step. Reproduction is logistic in local density (finite resources).

    ``regime`` scales the interaction, predation, and dispersal channels and adds
    any flat compensation. ``mutation_override`` (used by invasion probes) forces
    a mutation rate, e.g. 0.0 to breed an invader true.
    """
    mutation_rate = params.mutation_rate if mutation_override is None else mutation_override

    n_per_patch: dict = {}
    for ind in individuals:
        n_per_patch[ind.patch_id] = n_per_patch.get(ind.patch_id, 0) + 1

    # finite resources: replenishment minus per-capita consumption
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
        logistic = max(0.0, 1.0 - density)          # soft density dependence

        for ind in local:
            # survival: age + trait survival trade-off + density-dependent predation
            age_term = (ind.age / max(params.max_age, 1)) ** 2
            predation = params.predation_pressure * regime.predation_scale * density
            survival_p = _clip(
                params.base_survival * (1.0 - 0.6 * age_term)
                - params.survival_tradeoff * ind.trait
                - predation
            )
            if ind.age >= params.max_age or rng.random() > survival_p:
                continue
            survivors.append(replace(ind, age=ind.age + 1))

            service = _relationship_service(ind, density, params, regime.interaction_scale)
            mate = _mate_success(ind, local, params, rng)
            resource = ps.resources
            cost = ind.trait * params.trait_cost
            repro_p = _clip(
                0.22                                   # trait-independent fecundity floor
                + params.investment_reward * service   # load-bearing relationship
                + 0.20 * mate                          # compatible nearby partner
                + 0.30 * resource                      # finite resources
                + regime.repro_baseline                # alternative-route compensation
                - cost                                 # trait cost (trade-off)
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


# ---------------------------------------------------------------------------
# Reusable primitives
# ---------------------------------------------------------------------------

def seed_population(
    patches: dict,
    params: MetapopParameters,
    rng: Random,
    *,
    initial_fraction: float = 0.3,
    trait_mean: float = 0.5,
    trait_std: float = 0.18,
) -> list[Individual]:
    """Seed an initial population across patches with diffuse traits."""
    individuals: list[Individual] = []
    for pid, patch in patches.items():
        n_init = max(1, int(patch.carrying_capacity * initial_fraction))
        for _ in range(n_init):
            individuals.append(Individual(
                trait=_clip(rng.gauss(trait_mean, trait_std)),
                genotype=_clip(rng.gauss(trait_mean, trait_std)),
                age=rng.randint(0, max(1, params.max_age // 2)),
                patch_id=pid,
                location=(rng.random(), rng.random()),
            ))
    return individuals


def init_patch_states(patches: dict, rng: Random) -> dict:
    return {pid: PatchState(resources=0.7 + rng.uniform(-0.1, 0.1)) for pid in patches}


def advance(
    individuals: list[Individual],
    patches: dict,
    patch_states: dict,
    params: MetapopParameters,
    rng: Random,
    regime: Regime = Regime(),
    *,
    steps: int = 1,
    mutation_override: float | None = None,
) -> list[Individual]:
    """Advance ``steps`` IBM steps; mutates ``patch_states``."""
    for _ in range(steps):
        if not individuals:
            break
        individuals = _simulate_step(
            individuals, patches, patch_states, params, rng, regime,
            mutation_override=mutation_override,
        )
    return individuals


# ---------------------------------------------------------------------------
# Stationarity detection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StationarityReport:
    """Quasi-stationarity verdict over the tail of an equilibration run."""

    status: str                     # stationary | not_converged | extinct | oscillating
    n_series: tuple[int, ...]
    mean_trait_series: tuple[float, ...]
    occupancy_series: tuple[int, ...]
    variance_series: tuple[float, ...]

    @property
    def is_stationary(self) -> bool:
        return self.status == "stationary"


def _series_summary(individuals: list[Individual], n_patches: int) -> tuple[int, float, int, float]:
    n = len(individuals)
    if n == 0:
        return 0, 0.0, 0, 0.0
    mean_t = sum(i.trait for i in individuals) / n
    occ = len({i.patch_id for i in individuals})
    var = sum((i.trait - mean_t) ** 2 for i in individuals) / n if n > 1 else 0.0
    return n, mean_t, occ, var


def _relative_change(series: tuple[float, ...]) -> float:
    if len(series) < 2:
        return 0.0
    lo, hi = min(series), max(series)
    scale = max(abs(hi), abs(lo), 1e-9)
    return (hi - lo) / scale


def _is_oscillating(series: tuple[float, ...]) -> bool:
    """Detect an alternating up/down pattern over the window."""
    if len(series) < 4:
        return False
    deltas = [b - a for a, b in zip(series, series[1:])]
    signs = [1 if d > 1e-9 else (-1 if d < -1e-9 else 0) for d in deltas]
    nz = [s for s in signs if s != 0]
    if len(nz) < 3:
        return False
    alternations = sum(1 for a, b in zip(nz, nz[1:]) if a != b)
    return alternations >= len(nz) - 1 and _relative_change(series) > 0.25


def _half_window_trend(series: tuple[float, ...]) -> float:
    """Relative drift between the first and second half of the window.

    Trend (systematic drift) signals non-stationarity; symmetric demographic
    noise averages out across each half, so this is robust to stochastic jitter.
    """
    if len(series) < 4:
        return 0.0
    mid = len(series) // 2
    first = series[:mid]
    second = series[mid:]
    m1 = sum(first) / len(first)
    m2 = sum(second) / len(second)
    scale = max(abs(m1), abs(m2), 1e-9)
    return abs(m2 - m1) / scale


def assess_stationarity(
    n_series: list[int],
    mean_trait_series: list[float],
    occupancy_series: list[int],
    variance_series: list[float],
    *,
    window: int = 10,
    tol: float = 0.10,
) -> StationarityReport:
    """Classify the tail window as stationary / not_converged / extinct / oscillating.

    Stationarity is judged by *trend* (first-half vs second-half mean), not raw
    range, so demographic stochasticity does not masquerade as non-convergence.
    """
    n_s = tuple(n_series)
    mt_s = tuple(mean_trait_series)
    occ_s = tuple(occupancy_series)
    var_s = tuple(variance_series)

    if n_s and n_s[-1] == 0:
        status = "extinct"
    else:
        w = max(4, min(window, len(n_s)))
        n_tail = tuple(float(x) for x in n_s[-w:])
        mt_tail = mt_s[-w:]
        occ_tail = tuple(float(x) for x in occ_s[-w:])
        var_tail = var_s[-w:]
        if any(_is_oscillating(s) for s in (n_tail, mt_tail, var_tail)):
            status = "oscillating"
        elif all(
            _half_window_trend(s) <= tol_s
            for s, tol_s in (
                (n_tail, 0.45),          # population size: very noisy, loose band
                (mt_tail, tol),          # mean trait must not drift (the key signal)
                (occ_tail, 0.10),        # occupancy roughly flat
            )
        ):
            status = "stationary"
        else:
            status = "not_converged"

    return StationarityReport(
        status=status,
        n_series=n_s,
        mean_trait_series=mt_s,
        occupancy_series=occ_s,
        variance_series=var_s,
    )


def equilibrate(
    patches: dict,
    params: MetapopParameters,
    *,
    steps: int = 32,
    seed: int = 0,
    regime: Regime = Regime(),
    record_window: int = 10,
) -> tuple[PopulationState, dict, StationarityReport]:
    """Grow a resident community to quasi-stationarity and report its status."""
    rng = Random(seed)
    individuals = seed_population(patches, params, rng)
    patch_states = init_patch_states(patches, rng)
    n_patches = len(patches)

    n_series: list[int] = []
    mt_series: list[float] = []
    occ_series: list[int] = []
    var_series: list[float] = []

    for step in range(steps):
        individuals = advance(individuals, patches, patch_states, params, rng, regime, steps=1)
        if step >= steps - record_window - 1:
            n, mt, occ, var = _series_summary(individuals, n_patches)
            n_series.append(n)
            mt_series.append(mt)
            occ_series.append(occ)
            var_series.append(var)
        if not individuals:
            n_series.append(0); mt_series.append(0.0); occ_series.append(0); var_series.append(0.0)
            break

    report = assess_stationarity(n_series, mt_series, occ_series, var_series, window=record_window)
    state = PopulationState(
        individuals=tuple(individuals),
        patch_resources={pid: ps.resources for pid, ps in patch_states.items()},
    )
    return state, patch_states, report


# ---------------------------------------------------------------------------
# Invasion fitness and the viable trait set Omega_inv
# ---------------------------------------------------------------------------

def _log_growth_rate(counts: list[int]) -> float:
    """Per-step log growth rate of an invader lineage; -inf-ish if it dies out."""
    if not counts or counts[0] == 0:
        return 0.0
    if counts[-1] == 0:
        return -5.0
    steps = len(counts) - 1
    if steps <= 0:
        return 0.0
    return (math.log(counts[-1]) - math.log(counts[0])) / steps


def invasion_growth_rate(
    resident: PopulationState,
    resident_patch_states: dict,
    patches: dict,
    params: MetapopParameters,
    regime: Regime,
    z_prime: float,
    *,
    steps: int = 6,
    cohort: int = 10,
    seed: int = 0,
) -> float:
    """Long-term growth rate lambda(z'|Z*) of a rare bred-true mutant z'.

    A small monomorphic cohort at trait ``z_prime`` (``lineage=1``) is introduced
    into the resident community and run forward in the full spatial dynamics with
    mutation off; the per-step log growth rate of the invader lineage is returned.
    ``lambda > 0`` means ``z_prime`` can invade and persist.
    """
    rng = Random(seed)
    individuals = [replace(i, lineage=0) for i in resident.individuals]
    occupied = sorted(resident.occupied_patches()) or list(patches)
    for _ in range(cohort):
        pid = rng.choice(occupied)
        individuals.append(Individual(
            trait=_clip(z_prime), genotype=_clip(z_prime), age=0,
            patch_id=pid, location=(rng.random(), rng.random()), lineage=1,
        ))
    patch_states = {pid: PatchState(ps.resources) for pid, ps in resident_patch_states.items()}

    counts = [sum(1 for i in individuals if i.lineage == 1)]
    for _ in range(steps):
        individuals = _simulate_step(
            individuals, patches, patch_states, params, rng, regime, mutation_override=0.0,
        )
        c = sum(1 for i in individuals if i.lineage == 1)
        counts.append(c)
        if c == 0:
            break
    return _log_growth_rate(counts)


@dataclass(frozen=True)
class ViableTraitSet:
    """Estimated ``Omega_inv`` over a candidate trait grid."""

    grid: tuple[float, ...]
    mask: tuple[bool, ...]
    growth_rates: tuple[float, ...]

    @property
    def viable_values(self) -> tuple[float, ...]:
        return tuple(t for t, m in zip(self.grid, self.mask) if m)

    @property
    def measure(self) -> float:
        return sum(1 for m in self.mask if m) / len(self.mask) if self.mask else 0.0

    @property
    def n_components(self) -> int:
        count = 0
        prev = False
        for m in self.mask:
            if m and not prev:
                count += 1
            prev = m
        return count

    @property
    def centroid(self) -> float | None:
        vals = self.viable_values
        return sum(vals) / len(vals) if vals else None


def estimate_omega_inv(
    resident: PopulationState,
    resident_patch_states: dict,
    patches: dict,
    params: MetapopParameters,
    regime: Regime,
    *,
    grid_points: int = 9,
    invasion_steps: int = 6,
    cohort: int = 10,
    replicates: int = 2,
    threshold: float = 0.0,
    seed: int = 0,
) -> ViableTraitSet:
    """Estimate ``Omega_inv = {z' : lambda(z'|Z*) > threshold}`` over a trait grid.

    For each candidate trait the invasion growth rate is averaged over
    ``replicates`` seeds to reduce stochastic noise.
    """
    if grid_points < 2:
        raise ValueError("grid_points must be >= 2")
    grid = tuple(i / (grid_points - 1) for i in range(grid_points))
    mask: list[bool] = []
    rates: list[float] = []
    for gi, z in enumerate(grid):
        lam = 0.0
        for r in range(replicates):
            lam += invasion_growth_rate(
                resident, resident_patch_states, patches, params, regime, z,
                steps=invasion_steps, cohort=cohort, seed=seed * 1000 + gi * 17 + r,
            )
        lam /= max(replicates, 1)
        rates.append(lam)
        mask.append(lam > threshold)
    return ViableTraitSet(grid=grid, mask=tuple(mask), growth_rates=tuple(rates))


# ---------------------------------------------------------------------------
# Trait-space change classification
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TraitSpaceChange:
    measure_before: float
    measure_after: float
    n_components_before: int
    n_components_after: int
    centroid_before: float | None
    centroid_after: float | None
    contracted: bool
    fragmented: bool
    shifted: bool
    collapsed: bool
    expanded: bool
    primary: str  # contraction|fragmentation|shift|collapse|expansion|conserved


def classify_trait_space_change(
    before: ViableTraitSet,
    after: ViableTraitSet,
    *,
    contraction_rel_tol: float = 0.15,
    shift_tol: float = 0.12,
) -> TraitSpaceChange:
    mb, ma = before.measure, after.measure
    nb, na = before.n_components, after.n_components
    cb, ca = before.centroid, after.centroid

    collapsed = ma == 0.0 and mb > 0.0
    contracted = (ma < mb * (1.0 - contraction_rel_tol)) and not collapsed
    expanded = ma > mb * (1.0 + contraction_rel_tol)
    fragmented = na > nb
    shifted = cb is not None and ca is not None and abs(ca - cb) > shift_tol

    if collapsed:
        primary = "collapse"
    elif contracted:
        primary = "contraction"
    elif fragmented:
        primary = "fragmentation"
    elif shifted:
        primary = "shift"
    elif expanded:
        primary = "expansion"
    else:
        primary = "conserved"

    return TraitSpaceChange(
        measure_before=mb, measure_after=ma,
        n_components_before=nb, n_components_after=na,
        centroid_before=cb, centroid_after=ca,
        contracted=contracted or collapsed,
        fragmented=fragmented, shifted=shifted,
        collapsed=collapsed, expanded=expanded, primary=primary,
    )


# ---------------------------------------------------------------------------
# POM extraction (real spatial-ABM output -> 5-component ordinal P_sim)
# ---------------------------------------------------------------------------

POM_PATTERN_NAMES: tuple[str, ...] = (
    "interaction_network",   # realised interaction connectivity (relationship-gated)
    "patch_occupancy",       # fraction of patches occupied / local extinction
    "persistence_ne",        # census x diversity (Ne / persistence proxy)
    "trait_moments",         # trait variance + |cov(trait, genotype)|
    "omega_inv_state",       # qualitative Omega_inv verdict (contracted/...)
)

_OMEGA_STATE: dict[str, str] = {
    "collapse": "contracted",
    "contraction": "contracted",
    "fragmentation": "fragmented",
    "shift": "shifted",
    "expansion": "expanded",
    "conserved": "conserved",
}


def _mean_interaction_rate(state: PopulationState, patches: dict, params: MetapopParameters) -> float:
    """Mean realised relationship service across the population (interaction network).

    This is the per-capita relationship-service term (own trait x local
    availability); it collapses when the relationship is lost, so the
    ``interaction_network`` POM component registers the loss directly.
    """
    rates: list[float] = []
    by_patch: dict = {}
    for ind in state.individuals:
        by_patch.setdefault(ind.patch_id, []).append(ind)
    for pid, local in by_patch.items():
        n = len(local)
        density = n / max(patches[pid].carrying_capacity, 1)
        availability = max(0.55, 1.0 - 0.5 * density / max(params.density_threshold, 1e-6))
        for ind in local:
            rates.append(params.interaction_benefit * ind.trait * availability)
    return sum(rates) / len(rates) if rates else 0.0


def _ne_proxy(state: PopulationState) -> float:
    """Census size weighted by standing genetic dispersion (Ne/diversity proxy)."""
    return state.n_total * (1.0 + state.trait_variance() + abs(state.trait_genotype_cov()))


def _trait_moments(state: PopulationState) -> float:
    return state.trait_variance() + abs(state.trait_genotype_cov())


def _ordinal(delta: float, tol: float) -> str:
    if delta > tol:
        return "increase"
    if delta < -tol:
        return "decrease"
    return "stable"


def extract_pom_pattern(
    outcome_before: PopulationState,
    outcome_after: PopulationState,
    patches: dict,
    params: MetapopParameters,
    trait_space_change: TraitSpaceChange,
    *,
    interaction_scale_before: float,
    interaction_scale_after: float,
    tolerance: float = 0.05,
    interaction_tolerance: float = 0.02,
) -> dict[str, str]:
    """Extract the 5-component POM ``P_sim`` from realised before/after outcomes."""
    ic_b = _mean_interaction_rate(outcome_before, patches, params) * interaction_scale_before
    ic_a = _mean_interaction_rate(outcome_after, patches, params) * interaction_scale_after

    n_patches = max(len(patches), 1)
    occ_b = len(outcome_before.occupied_patches()) / n_patches
    occ_a = len(outcome_after.occupied_patches()) / n_patches

    ne_b = _ne_proxy(outcome_before)
    ne_a = _ne_proxy(outcome_after)
    ne_scale = max(ne_b, ne_a, 1.0)

    tm_b = _trait_moments(outcome_before)
    tm_a = _trait_moments(outcome_after)

    return {
        "interaction_network": _ordinal(ic_a - ic_b, interaction_tolerance),
        "patch_occupancy": _ordinal(occ_a - occ_b, tolerance),
        "persistence_ne": _ordinal((ne_a - ne_b) / ne_scale, tolerance),
        "trait_moments": _ordinal(tm_a - tm_b, tolerance),
        "omega_inv_state": _OMEGA_STATE.get(trait_space_change.primary, "conserved"),
    }


def default_observed_pattern() -> dict[str, str]:
    """Focal ``P_obs``: the signature of a relationship loss that contracts trait space."""
    return {
        "interaction_network": "decrease",
        "patch_occupancy": "stable",
        "persistence_ne": "decrease",
        "trait_moments": "stable",
        "omega_inv_state": "contracted",
    }


DEFAULT_EPSILON: float = 0.2  # at most one of five POM components may mismatch


def pom_distance(simulated: dict[str, str], observed: dict[str, str]) -> float:
    total = len(observed)
    matches = sum(1 for k, rel in observed.items() if simulated.get(k) == rel)
    return pattern_distance(matches, total)


# ---------------------------------------------------------------------------
# Interventions and ensembles
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Intervention:
    """A relationship-change intervention as a paired (before, after) regime."""

    name: str
    before: Regime
    after: Regime
    channel_motif: str             # the rule-transition relation-change motif


def make_interventions(loss_level: float = 0.0, compensation: float = 0.08) -> dict[str, Intervention]:
    """The three canonical interventions, each a controlled before/after regime.

    The focal trait is a *relationship-dependent investment*: every intervention
    removes the ecological relationship that makes the costly trait worthwhile
    (``interaction_scale`` 1->loss, with only incomplete ``repro_baseline``
    compensation), and adds its characteristic *secondary* disturbance:

    * ``pollination_loss`` — the mutualistic service collapses (no secondary toggle).
    * ``predation_loss``   — top-down mortality is also relaxed
      (``predation_scale`` 1->0), so local density rises.
    * ``dispersal_loss``   — dispersal pathways are also cut
      (``dispersal_scale`` 1->0), isolating patches (drives fragmentation).
    """
    return {
        "pollination_loss": Intervention(
            "pollination_loss",
            before=Regime(interaction_scale=1.0),
            after=Regime(interaction_scale=loss_level, repro_baseline=compensation),
            channel_motif="interaction_relationship_loss",
        ),
        "predation_loss": Intervention(
            "predation_loss",
            before=Regime(interaction_scale=1.0, predation_scale=1.0),
            after=Regime(interaction_scale=loss_level, predation_scale=0.0, repro_baseline=compensation),
            channel_motif="topdown_control_loss",
        ),
        "dispersal_loss": Intervention(
            "dispersal_loss",
            before=Regime(interaction_scale=1.0, dispersal_scale=1.0),
            after=Regime(interaction_scale=loss_level, dispersal_scale=0.0, repro_baseline=compensation),
            channel_motif="dispersal_pathway_loss",
        ),
    }


def sample_constrained_ecosystem(rng: Random) -> tuple[MetapopParameters, dict]:
    """Random ecosystem honouring the invariant physical constraints.

    Randomises interaction strength, trade-offs, resources, mutation, dispersal,
    patch sizes and connectivity. Always keeps: finite resources, **positive**
    trait cost, finite patches, local interaction, bounded traits. The trait
    direction is never set.
    """
    params = MetapopParameters(
        interaction_benefit=rng.uniform(0.55, 1.0),
        investment_reward=rng.uniform(0.9, 1.5),
        trait_cost=rng.uniform(0.25, 0.50),          # strictly positive, moderate
        survival_tradeoff=rng.uniform(0.0, 0.06),
        density_threshold=rng.uniform(0.6, 0.95),
        mutation_rate=rng.uniform(0.05, 0.40),
        mutation_std=rng.uniform(0.03, 0.12),
        dispersal_base=rng.uniform(0.0, 0.18),       # limited dispersal
        distance_decay=rng.uniform(0.7, 1.6),        # genuinely local interaction
        resource_replenishment=rng.uniform(0.24, 0.38),
        predation_pressure=rng.uniform(0.04, 0.14),  # real top-down control
        base_survival=rng.uniform(0.88, 0.95),
        max_age=rng.randint(5, 9),
    )
    n_patches = rng.randint(3, 4)
    capacity = rng.randint(20, 30)
    patches = _build_patches(n_patches, capacity, connectivity=0.4, rng=rng)
    return params, patches


def sample_compensated_ecosystem(rng: Random) -> tuple[MetapopParameters, dict]:
    """Counterexample ensemble: ample dispersal, large well-connected patches,
    low trait cost, strong compensation — trait-space contraction should NOT occur.
    """
    params = MetapopParameters(
        interaction_benefit=rng.uniform(0.45, 1.0),
        investment_reward=rng.uniform(0.7, 1.2),
        trait_cost=rng.uniform(0.05, 0.20),          # low cost: trait barely penalised
        survival_tradeoff=rng.uniform(0.0, 0.03),
        density_threshold=rng.uniform(0.7, 1.0),
        mutation_rate=rng.uniform(0.05, 0.40),
        mutation_std=rng.uniform(0.03, 0.12),
        dispersal_base=rng.uniform(0.45, 0.7),       # high dispersal
        distance_decay=rng.uniform(0.3, 0.8),        # broader interaction
        resource_replenishment=rng.uniform(0.30, 0.45),
        predation_pressure=rng.uniform(0.0, 0.08),
        base_survival=rng.uniform(0.85, 0.95),
        max_age=rng.randint(6, 10),
    )
    n_patches = rng.randint(4, 6)
    capacity = rng.randint(40, 60)                    # large patches
    patches = _build_patches(n_patches, capacity, connectivity=0.9, rng=rng)
    return params, patches


def _build_patches(n: int, capacity: int, *, connectivity: float, rng: Random) -> dict:
    patches: dict = {}
    for pid in range(n):
        conn = {other: connectivity for other in range(n) if other != pid}
        patches[pid] = Patch(
            patch_id=pid,
            area=rng.uniform(0.8, 1.2),
            carrying_capacity=capacity,
            connectivity=conn,
        )
    return patches


def default_patches(n: int = 3, capacity: int = 20) -> dict:
    rng = Random(0)
    return _build_patches(n, capacity, connectivity=0.5, rng=rng)


# ---------------------------------------------------------------------------
# One intervention experiment
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InterventionResult:
    intervention: str
    stationarity: str
    omega_before: ViableTraitSet
    omega_after: ViableTraitSet
    trait_space_change: TraitSpaceChange
    p_sim: dict[str, str]
    p_obs: dict[str, str]
    distance: float
    accepted: bool
    motifs: frozenset
    diagnostics: dict


def run_intervention_experiment(
    params: MetapopParameters,
    patches: dict,
    intervention: Intervention,
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
) -> InterventionResult:
    """Run one controlled before/after intervention from a shared resident community."""
    observed = observed_pattern if observed_pattern is not None else default_observed_pattern()

    # shared resident equilibrium under the BEFORE regime (same initial conditions)
    resident, resident_states, report = equilibrate(
        patches, params, steps=equilibration_steps, seed=seed, regime=intervention.before,
    )

    base_motifs = {
        "relation_change", intervention.channel_motif,
        "finite_resources", "finite_patches", "local_interaction",
    }
    if params.trait_cost > 0.0:
        base_motifs.add("positive_trait_cost")

    if report.status != "stationary":
        # non-stationary residents are recorded but never accepted
        empty = ViableTraitSet(grid=(), mask=(), growth_rates=())
        ts = classify_trait_space_change(
            ViableTraitSet((0.0,), (False,), (0.0,)),
            ViableTraitSet((0.0,), (False,), (0.0,)),
        )
        return InterventionResult(
            intervention=intervention.name,
            stationarity=report.status,
            omega_before=empty, omega_after=empty,
            trait_space_change=ts,
            p_sim={}, p_obs=dict(observed), distance=1.0, accepted=False,
            motifs=frozenset(base_motifs | {f"resident_{report.status}"}),
            diagnostics={"stationarity": report.status, "n_final": report.n_series[-1] if report.n_series else 0},
        )

    # Omega_inv before vs after, evaluated against the SAME resident Z* with the
    # SAME invasion seed so the comparison is paired: the invader cohorts are
    # placed identically and the only difference is the intervened regime. This
    # removes the dominant source of stochastic noise from the contrast.
    omega_seed = seed * 5 + 3
    omega_before = estimate_omega_inv(
        resident, resident_states, patches, params, intervention.before,
        grid_points=grid_points, invasion_steps=invasion_steps,
        cohort=invasion_cohort, replicates=invasion_replicates, seed=omega_seed,
    )
    omega_after = estimate_omega_inv(
        resident, resident_states, patches, params, intervention.after,
        grid_points=grid_points, invasion_steps=invasion_steps,
        cohort=invasion_cohort, replicates=invasion_replicates, seed=omega_seed,
    )
    ts_change = classify_trait_space_change(omega_before, omega_after)

    # realised dynamic outcomes from the SAME resident under each regime
    def _outcome(regime: Regime, branch_seed: int) -> PopulationState:
        rng = Random(branch_seed)
        inds = [replace(i) for i in resident.individuals]
        states = {pid: PatchState(ps.resources) for pid, ps in resident_states.items()}
        inds = advance(inds, patches, states, params, rng, regime, steps=outcome_steps)
        return PopulationState(tuple(inds), {pid: ps.resources for pid, ps in states.items()})

    outcome_before = _outcome(intervention.before, seed * 7 + 1)
    outcome_after = _outcome(intervention.after, seed * 7 + 2)

    p_sim = extract_pom_pattern(
        outcome_before, outcome_after, patches, params, ts_change,
        interaction_scale_before=intervention.before.interaction_scale,
        interaction_scale_after=intervention.after.interaction_scale,
    )
    distance = pom_distance(p_sim, observed)
    # The focal qualitative pattern is trait-space *contraction*: a run is admitted
    # only if its POM is within epsilon AND its viable set actually contracted.
    # (Without the contraction gate, runs that merely shift/expand Omega could pass
    # on the other, often-stable POM components.)
    contracted_signature = p_sim.get("omega_inv_state") == "contracted"
    accepted = accepted_by_epsilon(distance, epsilon) and contracted_signature

    motifs = set(base_motifs)
    motifs.add("incomplete_compensation")  # compensation never fully restores the channel here
    if ts_change.contracted:
        motifs.add("trait_space_contraction")
    if ts_change.fragmented:
        motifs.add("trait_space_fragmentation")
    if ts_change.shifted:
        motifs.add("trait_space_shift")

    diagnostics = {
        "stationarity": report.status,
        "omega_measure_before": round(omega_before.measure, 4),
        "omega_measure_after": round(omega_after.measure, 4),
        "omega_components_before": omega_before.n_components,
        "omega_components_after": omega_after.n_components,
        "centroid_before": omega_before.centroid,
        "centroid_after": omega_after.centroid,
        "primary": ts_change.primary,
        "n_before": outcome_before.n_total,
        "n_after": outcome_after.n_total,
    }
    return InterventionResult(
        intervention=intervention.name,
        stationarity=report.status,
        omega_before=omega_before, omega_after=omega_after,
        trait_space_change=ts_change,
        p_sim=p_sim, p_obs=dict(observed), distance=distance, accepted=accepted,
        motifs=frozenset(motifs), diagnostics=diagnostics,
    )


# ---------------------------------------------------------------------------
# Resident re-equilibration: does the trait-space change PERSIST after re-evolution?
# ---------------------------------------------------------------------------

def _trait_quantile(values: tuple[float, ...], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[idx]


@dataclass(frozen=True)
class ReequilibrationResult:
    """Before vs *re-equilibrated*-after comparison (eco-evolutionary endpoint).

    Unlike :class:`InterventionResult` (instantaneous invasibility against the
    *same* resident), this lets the resident re-evolve under the post-loss regime
    to a new quasi-stationary state and asks whether the trait-space change
    persists. ``persistent_contraction`` requires the post-loss system to be
    stationary again AND its realised occupied trait set (and viable set) to remain
    contracted relative to before.
    """

    intervention: str
    stationarity_before: str
    stationarity_after: str
    # realised occupied trait set (the population itself, not invasion)
    upper_edge_before: float           # 90th percentile trait before loss
    upper_edge_after: float            # 90th percentile trait at the new equilibrium
    breadth_before: float              # q90 - q10
    breadth_after: float
    mean_before: float
    mean_after: float
    # invasion-based viable set Omega_inv at EACH regime's OWN re-equilibrated resident
    omega_measure_before: float
    omega_measure_after: float
    omega_upper_before: float
    omega_upper_after: float
    persistent_contraction: bool
    diagnostics: dict


def run_reequilibration_experiment(
    params: MetapopParameters,
    patches: dict,
    intervention: Intervention,
    *,
    equilibration_steps: int = 40,
    reequilibration_steps: int = 60,
    grid_points: int = 9,
    invasion_steps: int = 6,
    invasion_cohort: int = 12,
    invasion_replicates: int = 2,
    upper_quantile: float = 0.9,
    lower_quantile: float = 0.1,
    contraction_tol: float = 0.06,
    seed: int = 0,
) -> ReequilibrationResult:
    """Run a before / re-equilibrated-after intervention from one shared seed.

    1. Equilibrate the resident under the BEFORE regime (must be stationary).
    2. From that identical community, switch to the AFTER regime and run a long
       re-equilibration, checking it reaches a new quasi-stationary state.
    3. Compare the realised occupied trait set and the invasion-based Omega_inv,
       each evaluated at its OWN re-equilibrated resident — the eco-evolutionary
       endpoint, not transient invasibility.
    """
    resident_b, states_b, report_b = equilibrate(
        patches, params, steps=equilibration_steps, seed=seed, regime=intervention.before,
    )

    def _metrics(state: PopulationState) -> tuple[float, float, float, float]:
        vals = state.trait_values()
        ue = _trait_quantile(vals, upper_quantile)
        le = _trait_quantile(vals, lower_quantile)
        return ue, ue - le, state.mean_trait(), state.n_total

    ue_b, br_b, mean_b, n_b = _metrics(resident_b)

    if report_b.status != "stationary" or resident_b.n_total == 0:
        return ReequilibrationResult(
            intervention=intervention.name,
            stationarity_before=report_b.status, stationarity_after="not_run",
            upper_edge_before=ue_b, upper_edge_after=0.0,
            breadth_before=br_b, breadth_after=0.0,
            mean_before=mean_b, mean_after=0.0,
            omega_measure_before=0.0, omega_measure_after=0.0,
            omega_upper_before=0.0, omega_upper_after=0.0,
            persistent_contraction=False,
            diagnostics={"reason": f"resident_before_{report_b.status}"},
        )

    omega_b = estimate_omega_inv(
        resident_b, states_b, patches, params, intervention.before,
        grid_points=grid_points, invasion_steps=invasion_steps,
        cohort=invasion_cohort, replicates=invasion_replicates, seed=seed * 5 + 3,
    )

    # --- re-equilibrate under the AFTER regime from the SAME community ---
    rng = Random(seed * 9 + 7)
    inds = [replace(i) for i in resident_b.individuals]
    states_a = {pid: PatchState(ps.resources) for pid, ps in states_b.items()}
    n_patches = len(patches)
    n_series: list[int] = []
    mt_series: list[float] = []
    occ_series: list[int] = []
    var_series: list[float] = []
    rec_window = 12
    for step in range(reequilibration_steps):
        inds = advance(inds, patches, states_a, params, rng, intervention.after, steps=1)
        if step >= reequilibration_steps - rec_window - 1:
            n, mt, occ, var = _series_summary(inds, n_patches)
            n_series.append(n); mt_series.append(mt); occ_series.append(occ); var_series.append(var)
        if not inds:
            n_series.append(0); mt_series.append(0.0); occ_series.append(0); var_series.append(0.0)
            break
    # a post-perturbation system settles more slowly than a virgin one, so the
    # re-equilibration phase gets a slightly more permissive stationarity tolerance.
    report_a = assess_stationarity(n_series, mt_series, occ_series, var_series, window=rec_window, tol=0.14)
    resident_a = PopulationState(tuple(inds), {pid: ps.resources for pid, ps in states_a.items()})
    ue_a, br_a, mean_a, n_a = _metrics(resident_a)

    if resident_a.n_total > 0 and report_a.status == "stationary":
        omega_a = estimate_omega_inv(
            resident_a, states_a, patches, params, intervention.after,
            grid_points=grid_points, invasion_steps=invasion_steps,
            cohort=invasion_cohort, replicates=invasion_replicates, seed=seed * 5 + 4,
        )
        om_meas_a, om_up_a = omega_a.measure, (max(omega_a.viable_values) if omega_a.viable_values else 0.0)
    else:
        om_meas_a, om_up_a = 0.0, 0.0

    om_up_b = max(omega_b.viable_values) if omega_b.viable_values else 0.0

    # persistent contraction: the post-loss system is stationary again AND the
    # realised occupied upper edge receded and stayed receded.
    persistent = (
        report_a.status == "stationary"
        and resident_a.n_total > 0
        and ue_a < ue_b - contraction_tol
    )

    return ReequilibrationResult(
        intervention=intervention.name,
        stationarity_before=report_b.status, stationarity_after=report_a.status,
        upper_edge_before=ue_b, upper_edge_after=ue_a,
        breadth_before=br_b, breadth_after=br_a,
        mean_before=mean_b, mean_after=mean_a,
        omega_measure_before=omega_b.measure, omega_measure_after=om_meas_a,
        omega_upper_before=om_up_b, omega_upper_after=om_up_a,
        persistent_contraction=persistent,
        diagnostics={
            "n_before": n_b, "n_after": n_a,
            "upper_edge_delta": round(ue_a - ue_b, 4),
            "mean_delta": round(mean_a - mean_b, 4),
        },
    )


# ---------------------------------------------------------------------------
# Sweep-record generation for the rule-transition pipeline
# ---------------------------------------------------------------------------

#: The canonical rule-transition chain motifs (shared framework vocabulary).
_CHAIN_MOTIFS: frozenset = frozenset(
    {"relation_change", "constraint_reconfiguration", "trait_space_reconfiguration"}
)


def constraint_program_motifs(intervention: Intervention) -> frozenset:
    """Deterministic structural motifs of the physical-constraint program.

    These describe the *program* (its rule-transition structure and the physical
    constraints it asserts), not the stochastic outcome of any one run — so all
    replicates group together and the invariant layer reports them as necessary.
    """
    return _CHAIN_MOTIFS | {
        intervention.channel_motif,
        "finite_resources", "finite_patches", "local_interaction",
        "positive_trait_cost", "incomplete_compensation",
        "trait_space_contraction",
    }


def compensated_program_motifs(intervention: Intervention) -> frozenset:
    """Deterministic structural motifs of the compensated counterexample program."""
    return _CHAIN_MOTIFS | {
        intervention.channel_motif,
        "ample_dispersal", "large_patches", "low_trait_cost", "sufficient_compensation",
    }


def generate_sweep_records(
    intervention: Intervention,
    *,
    program_id: str,
    program_motifs: frozenset,
    ecosystem_sampler: Callable[[Random], tuple[MetapopParameters, dict]],
    n_regions: int = 6,
    seeds: Iterable[int] = (0, 1),
    observed_pattern: dict | None = None,
    epsilon: float = DEFAULT_EPSILON,
    base_seed: int = 0,
    **experiment_kwargs,
) -> tuple[SweepRecord, ...]:
    """Run a spatial-ABM sweep and return ``SweepRecord``s for the pipeline.

    Each ecosystem draw is a declared *region*; each seed is a replicate. The
    scenario is the intervention name and ``program_motifs`` are the program's
    fixed structural motifs, so the records plug straight into
    :func:`causal_model.rule_transition_pipeline.analyse_rule_transitions`.
    ``pattern_matched`` is whether that run reproduced trait-space contraction.
    """
    records: list[SweepRecord] = []
    seed_list = tuple(seeds)
    for region in range(n_regions):
        eco_rng = Random(base_seed * 9973 + region)
        params, patches = ecosystem_sampler(eco_rng)
        region_id = f"eco_{region}"
        for s in seed_list:
            result = run_intervention_experiment(
                params, patches, intervention,
                observed_pattern=observed_pattern, epsilon=epsilon,
                seed=base_seed * 9973 + region * 31 + s, **experiment_kwargs,
            )
            records.append(SweepRecord(
                scenario=intervention.name,
                program_id=program_id,
                motifs=program_motifs,
                pattern_matched=result.accepted,
                parameters={
                    "interaction_benefit": params.interaction_benefit,
                    "trait_cost": params.trait_cost,
                    "dispersal_base": params.dispersal_base,
                    "predation_pressure": params.predation_pressure,
                    "distance_decay": params.distance_decay,
                    "resource_replenishment": params.resource_replenishment,
                },
                initial_state={"omega_measure_before": result.diagnostics.get("omega_measure_before", 0.0)},
                metadata={
                    "region_id": region_id,
                    "P_sim": result.p_sim,
                    "P_obs": result.p_obs,
                    "abc_distance": round(result.distance, 4),
                    "epsilon": epsilon,
                    "accepted": result.accepted,
                    "stationarity": result.stationarity,
                    "trait_space_primary": result.trait_space_change.primary,
                    "omega_measure_before": result.diagnostics.get("omega_measure_before"),
                    "omega_measure_after": result.diagnostics.get("omega_measure_after"),
                },
                region_id=region_id,
                seed=s,
                fragile_flags=frozenset(),
            ))
    return tuple(records)


@dataclass(frozen=True)
class ContractionRobustness:
    n_runs: int
    n_contracted: int
    contraction_fraction: float
    n_accepted: int
    acceptance_fraction: float
    stationarity_counts: dict
    primary_counts: dict
    classification: str             # robust | fragile | insufficient


def verify_contraction_robustness(
    intervention: Intervention,
    *,
    ecosystem_sampler: Callable[[Random], tuple[MetapopParameters, dict]] | None = None,
    n_draws: int = 12,
    base_seed: int = 0,
    robust_fraction: float = 0.6,
    **experiment_kwargs,
) -> ContractionRobustness:
    """Verify whether trait-space contraction robustly follows an intervention.

    Draws ``n_draws`` random ecosystems and reports the fraction whose
    ``Omega_inv`` contracts, the acceptance fraction, the stationarity mix, and a
    robust/fragile/insufficient verdict (stationary runs only count toward the
    fraction).
    """
    sampler = ecosystem_sampler or sample_constrained_ecosystem
    primary_counts: dict = {}
    stationarity_counts: dict = {}
    n_contracted = 0
    n_accepted = 0
    n_stationary = 0
    for i in range(n_draws):
        rng = Random(base_seed * 1213 + i)
        params, patches = sampler(rng)
        result = run_intervention_experiment(
            params, patches, intervention, seed=base_seed * 1213 + i, **experiment_kwargs,
        )
        stationarity_counts[result.stationarity] = stationarity_counts.get(result.stationarity, 0) + 1
        primary_counts[result.trait_space_change.primary] = (
            primary_counts.get(result.trait_space_change.primary, 0) + 1
        )
        if result.stationarity == "stationary":
            n_stationary += 1
            if result.trait_space_change.contracted:
                n_contracted += 1
            if result.accepted:
                n_accepted += 1

    contraction_fraction = n_contracted / n_stationary if n_stationary else 0.0
    acceptance_fraction = n_accepted / n_stationary if n_stationary else 0.0
    if n_stationary < 4:
        classification = "insufficient"
    elif contraction_fraction >= robust_fraction:
        classification = "robust"
    else:
        classification = "fragile"

    return ContractionRobustness(
        n_runs=n_draws,
        n_contracted=n_contracted,
        contraction_fraction=contraction_fraction,
        n_accepted=n_accepted,
        acceptance_fraction=acceptance_fraction,
        stationarity_counts=stationarity_counts,
        primary_counts=primary_counts,
        classification=classification,
    )
