"""Spatial metapopulation IBM backend for RACH rule-transition inference.

Individual-based, patch-based ABM where trait evolution is *emergent*: only
physical constraints and trade-offs are specified; no trait direction is given.

Biotic structure
----------------
- **Individual**: trait investment, genotype, age, patch residence, spatial
  location.
- **Patch**: area, carrying capacity, resource level, inter-patch connectivity.

Within each step:

1. Resources replenish at a fixed rate and are consumed per capita.
2. Every individual draws a local interaction partner; interaction success =
   trait-match × distance-decay × density-modulation.
3. Reproductive probability = f(interaction success, mate availability,
   resource level, trait cost).
4. Offspring inherit parents' trait + genotype with mutation.
5. Offspring may disperse to a neighbouring patch proportional to
   connectivity × distance-weight.
6. Individuals age and die with age-dependent probability.
7. Patches with zero individuals are flagged as locally extinct.

POM summary (5 components)
---------------------------
1. ``interaction_connectivity`` — ordinal change in mean pairwise interaction
   rate (average over all patches: matched pairs / all pairs per patch).
2. ``patch_persistence``        — ordinal change in fraction of occupied patches.
3. ``inbreeding_proxy``         — ordinal change in a within-patch kinship proxy
   (mean pairwise |trait_i − trait_j| within patch, inverted so ↑ = more
   inbreeding / less diversity; reported relative to initial diversity).
4. ``trait_investment``         — ordinal change in population-mean trait.
5. ``trait_space_state``        — ``"reconfigured"`` if trait variance changed by
   more than *tolerance*, else ``"conserved"``.

These are compared to ``P_obs`` via ``d(P_sim, P_obs) ≤ ε`` (``abc_distance``),
using the same ordinal-mismatch rule as every other RACH acceptance step.

Rule-transition compatibility
------------------------------
``generate_sweep_records`` returns tuples of ``SweepRecord`` (defined here) that
carry the same fields as the rule-transition layer's sweep records: scenario,
program_id, motifs, pattern_matched, parameters, initial_state, metadata
(P_sim / P_obs / abc_distance / epsilon / accepted), region_id, seed,
fragile_flags.  Any downstream invariant-extraction layer can consume them
directly.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from random import Random
from typing import Iterable

from causal_model.abc_distance import accepted_by_epsilon, pattern_distance


# ---------------------------------------------------------------------------
# Sweep record (compatible with rule-transition RACH layer)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SweepRecord:
    """One (program, parameter-draw, region, seed) run; carries POM acceptance."""

    scenario: str
    program_id: str
    motifs: frozenset[str]
    pattern_matched: bool
    parameters: dict
    initial_state: dict
    metadata: dict
    region_id: str
    seed: int
    fragile_flags: frozenset[str] = field(default_factory=frozenset)


# ---------------------------------------------------------------------------
# Core dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Individual:
    """One individual in the IBM."""

    trait: float         # focal trait investment in [0, 1]
    genotype: float      # heritable genetic basis in [0, 1]
    age: int             # integer timestep age
    patch_id: int        # resident patch
    location: tuple[float, float]  # (x, y) within-patch location in [0, 1]²


@dataclass(frozen=True)
class Patch:
    """One discrete habitat patch."""

    patch_id: int
    area: float               # relative size, affects carrying capacity scaling
    carrying_capacity: int    # maximum number of individuals
    connectivity: dict        # {neighbor_patch_id: float} dispersal weight


@dataclass
class PatchState:
    """Mutable per-patch resource state during simulation."""

    resources: float  # current resource level in [0, 1]


@dataclass(frozen=True)
class MetapopParameters:
    """All parameters for one spatial-metapopulation IBM run.

    No parameter directly specifies whether the trait *increases* or *decreases*.
    The emergent direction depends on the balance of costs and benefits.
    """

    trait_match_benefit: float    # max fitness gain from a perfectly matched pair
    trait_cost: float             # fitness cost per unit of trait investment
    density_threshold: float      # local density (fraction of K) above which
                                  # interactions become competitive
    mutation_rate: float          # per-offspring probability of a mutation
    mutation_std: float           # Gaussian mutation step size
    dispersal_base: float         # base per-offspring dispersal probability
    distance_decay: float         # spatial distance decay coefficient
    resource_replenishment: float # per-step fractional resource recovery
    max_age: int = 8              # maximum individual lifespan (steps)


@dataclass(frozen=True)
class PopulationState:
    """Snapshot of the entire metapopulation at one point in time."""

    individuals: tuple[Individual, ...]
    patch_resources: dict   # {patch_id: float}

    @property
    def n_total(self) -> int:
        return len(self.individuals)

    def n_per_patch(self) -> dict:
        counts: dict = {}
        for ind in self.individuals:
            counts[ind.patch_id] = counts.get(ind.patch_id, 0) + 1
        return counts

    def trait_values(self) -> tuple[float, ...]:
        return tuple(ind.trait for ind in self.individuals)

    def mean_trait(self) -> float:
        vals = self.trait_values()
        return sum(vals) / len(vals) if vals else 0.0

    def trait_variance(self) -> float:
        vals = self.trait_values()
        if len(vals) < 2:
            return 0.0
        m = sum(vals) / len(vals)
        return sum((v - m) ** 2 for v in vals) / len(vals)

    def occupied_patches(self) -> frozenset:
        return frozenset(ind.patch_id for ind in self.individuals)


# ---------------------------------------------------------------------------
# Simulation internals
# ---------------------------------------------------------------------------

def _clip(v: float) -> float:
    return max(0.0, min(1.0, v))


def _interaction_success(
    ind: Individual,
    local: list[Individual],
    density: float,
    params: MetapopParameters,
    rng: Random,
) -> float:
    """Per-individual interaction success in [0, 1]."""
    candidates = [o for o in local if o is not ind]
    if not candidates:
        return 0.0
    partner = rng.choice(candidates)
    trait_match = 1.0 - abs(ind.trait - partner.trait)
    dx = ind.location[0] - partner.location[0]
    dy = ind.location[1] - partner.location[1]
    dist = math.sqrt(dx * dx + dy * dy)
    dist_factor = math.exp(-params.distance_decay * dist)
    density_factor = max(0.0, 1.0 - density / max(params.density_threshold, 1e-6))
    return trait_match * dist_factor * density_factor


def _simulate_step(
    individuals: list[Individual],
    patches: dict,          # {patch_id: Patch}
    patch_states: dict,     # {patch_id: PatchState}
    params: MetapopParameters,
    rng: Random,
) -> list[Individual]:
    """One IBM step; returns the next generation of individuals."""

    # --- 1. update patch resources ---
    n_per_patch: dict = {}
    for ind in individuals:
        n_per_patch[ind.patch_id] = n_per_patch.get(ind.patch_id, 0) + 1

    for pid, ps in patch_states.items():
        n = n_per_patch.get(pid, 0)
        patch = patches[pid]
        consumption = n * 0.08 / max(patch.area * patch.carrying_capacity, 1)
        ps.resources = _clip(ps.resources + params.resource_replenishment - consumption)

    # --- 2. compute offspring and survivors ---
    survivors: list[Individual] = []
    offspring: list[Individual] = []

    # group individuals by patch for fast access
    by_patch: dict = {}
    for ind in individuals:
        by_patch.setdefault(ind.patch_id, []).append(ind)

    for pid, local in by_patch.items():
        patch = patches[pid]
        ps = patch_states[pid]
        n = len(local)
        density = n / max(patch.carrying_capacity, 1)
        k = patch.carrying_capacity

        for ind in local:
            # survival: age-dependent mortality
            survival_p = max(0.0, 1.0 - (ind.age / max(params.max_age, 1)) ** 2 * 0.6)
            if ind.age >= params.max_age or rng.random() > survival_p:
                continue
            survivors.append(Individual(ind.trait, ind.genotype, ind.age + 1, ind.patch_id, ind.location))

            # reproduction: only when patch is not at capacity
            current_n = n_per_patch.get(pid, 0)
            if current_n >= k:
                continue
            interaction = _interaction_success(ind, local, density, params, rng)
            mate_avail = min(1.0, (n - 1) / max(k * 0.15, 1.0))
            resource = ps.resources
            cost = ind.trait * params.trait_cost
            repro_p = _clip(
                interaction * params.trait_match_benefit
                + mate_avail * 0.25
                + resource * 0.25
                - cost
            )
            if rng.random() < repro_p:
                # mutate trait/genotype
                new_trait = ind.trait
                new_geno = ind.genotype
                if rng.random() < params.mutation_rate:
                    new_trait = _clip(new_trait + rng.gauss(0.0, params.mutation_std))
                    new_geno = _clip(new_geno + rng.gauss(0.0, params.mutation_std * 0.5))

                # dispersal target
                target_pid = pid
                if rng.random() < params.dispersal_base and patch.connectivity:
                    neighbors = [(npid, w) for npid, w in patch.connectivity.items()]
                    total_w = sum(w for _, w in neighbors)
                    if total_w > 0:
                        r = rng.random() * total_w
                        cumw = 0.0
                        for npid, w in neighbors:
                            cumw += w
                            if r <= cumw:
                                target_pid = npid
                                break

                child = Individual(
                    trait=new_trait,
                    genotype=new_geno,
                    age=0,
                    patch_id=target_pid,
                    location=(rng.random(), rng.random()),
                )
                offspring.append(child)
                n_per_patch[pid] = n_per_patch.get(pid, 0) + 1

    return survivors + offspring


def simulate_metapopulation(
    patches: dict,
    params: MetapopParameters,
    *,
    n_warmup: int = 5,
    steps: int = 30,
    seed: int = 0,
    initial_population_size: int | None = None,
) -> tuple[PopulationState, PopulationState, frozenset]:
    """Run the IBM and return (before_state, after_state, motifs).

    Parameters
    ----------
    patches:
        ``{patch_id: Patch}`` — the spatial layout.
    params:
        Parameters controlling interaction, reproduction, dispersal, mutation.
    n_warmup:
        Burn-in steps before recording ``before_state``.
    steps:
        Steps after the warm-up before recording ``after_state``.
    seed:
        RNG seed for reproducibility.
    initial_population_size:
        Individuals to seed per patch; defaults to 30% of carrying_capacity.

    Returns
    -------
    before_state, after_state:
        ``PopulationState`` snapshots before and after the main run.
    motifs:
        Structural motifs encoding which dynamic regimes were active: always
        includes ``"interaction_opportunity"`` and ``"trait_cost_pressure"``;
        adds ``"strong_selection"`` when trait_match_benefit > 0.5;
        ``"dispersal_gene_flow"`` when dispersal_base > 0.2;
        ``"mutation_drift"`` when mutation_rate > 0.3.
    """
    rng = Random(seed)

    # --- initialise individuals ---
    individuals: list[Individual] = []
    for pid, patch in patches.items():
        n_init = initial_population_size or max(1, int(patch.carrying_capacity * 0.3))
        for _ in range(n_init):
            individuals.append(Individual(
                trait=_clip(rng.gauss(0.5, 0.15)),
                genotype=_clip(rng.gauss(0.5, 0.15)),
                age=rng.randint(0, max(1, params.max_age // 2)),
                patch_id=pid,
                location=(rng.random(), rng.random()),
            ))

    patch_states = {pid: PatchState(resources=0.7 + rng.uniform(-0.1, 0.1)) for pid in patches}

    # --- warm-up ---
    for _ in range(n_warmup):
        if not individuals:
            break
        individuals = _simulate_step(individuals, patches, patch_states, params, rng)

    before_state = PopulationState(
        individuals=tuple(individuals),
        patch_resources={pid: ps.resources for pid, ps in patch_states.items()},
    )

    # --- main run ---
    for _ in range(steps):
        if not individuals:
            break
        individuals = _simulate_step(individuals, patches, patch_states, params, rng)

    after_state = PopulationState(
        individuals=tuple(individuals),
        patch_resources={pid: ps.resources for pid, ps in patch_states.items()},
    )

    # --- motifs ---
    motifs: set[str] = {"interaction_opportunity", "trait_cost_pressure"}
    if params.trait_match_benefit > 0.5:
        motifs.add("strong_selection")
    if params.dispersal_base > 0.2:
        motifs.add("dispersal_gene_flow")
    if params.mutation_rate > 0.3:
        motifs.add("mutation_drift")

    return before_state, after_state, frozenset(motifs)


# ---------------------------------------------------------------------------
# POM pattern extraction
# ---------------------------------------------------------------------------

#: Ordered POM component names for this ABM.
POM_PATTERN_NAMES: tuple[str, ...] = (
    "interaction_connectivity",  # pairwise interaction-rate trend
    "patch_persistence",         # fraction of patches remaining occupied
    "inbreeding_proxy",          # within-patch kinship / diversity proxy
    "trait_investment",          # population-mean trait trend
    "trait_space_state",         # qualitative state of trait-space occupation
)


def _mean_interaction_rate(state: PopulationState, patches: dict, params: MetapopParameters) -> float:
    """Mean pairwise within-patch interaction success (proxy for interaction_connectivity)."""
    rates: list[float] = []
    by_patch: dict = {}
    for ind in state.individuals:
        by_patch.setdefault(ind.patch_id, []).append(ind)
    for pid, local in by_patch.items():
        n = len(local)
        if n < 2:
            rates.append(0.0)
            continue
        patch = patches[pid]
        density = n / max(patch.carrying_capacity, 1)
        total = 0.0
        pairs = 0
        for i, a in enumerate(local):
            for b in local[i + 1:]:
                tm = 1.0 - abs(a.trait - b.trait)
                dx = a.location[0] - b.location[0]
                dy = a.location[1] - b.location[1]
                dist = math.sqrt(dx * dx + dy * dy)
                df = math.exp(-params.distance_decay * dist)
                densf = max(0.0, 1.0 - density / max(params.density_threshold, 1e-6))
                total += tm * df * densf
                pairs += 1
        rates.append(total / pairs if pairs else 0.0)
    return sum(rates) / len(rates) if rates else 0.0


def _within_patch_dissimilarity(state: PopulationState) -> float:
    """Mean within-patch pairwise |trait_i - trait_j|; higher = more diverse (lower inbreeding)."""
    diffs: list[float] = []
    by_patch: dict = {}
    for ind in state.individuals:
        by_patch.setdefault(ind.patch_id, []).append(ind)
    for local in by_patch.values():
        if len(local) < 2:
            continue
        for i, a in enumerate(local):
            for b in local[i + 1:]:
                diffs.append(abs(a.trait - b.trait))
    return sum(diffs) / len(diffs) if diffs else 0.0


def _ordinal(delta: float, tolerance: float) -> str:
    if delta > tolerance:
        return "increase"
    if delta < -tolerance:
        return "decrease"
    return "stable"


def extract_pom_pattern(
    before: PopulationState,
    after: PopulationState,
    patches: dict,
    params: MetapopParameters,
    *,
    tolerance: float = 0.08,
) -> dict[str, str]:
    """Extract the 5-component POM summary statistic P_sim from a simulation run.

    Returns ordinal directions for interaction connectivity, patch persistence,
    inbreeding proxy, and trait investment, plus the qualitative trait-space state.
    """
    n_patches = len(patches)

    # 1. interaction connectivity
    ic_before = _mean_interaction_rate(before, patches, params)
    ic_after = _mean_interaction_rate(after, patches, params)
    interaction_connectivity = _ordinal(ic_after - ic_before, tolerance)

    # 2. patch persistence (fraction occupied)
    occ_before = len(before.occupied_patches()) / max(n_patches, 1)
    occ_after = len(after.occupied_patches()) / max(n_patches, 1)
    patch_persistence = _ordinal(occ_after - occ_before, tolerance)

    # 3. inbreeding proxy: within-patch dissimilarity (higher = less inbreeding)
    # We invert: inbreeding_proxy ordinal = "increase" means MORE inbreeding
    diss_before = _within_patch_dissimilarity(before)
    diss_after = _within_patch_dissimilarity(after)
    # lower dissimilarity = higher inbreeding proxy
    inbreeding_proxy = _ordinal(diss_before - diss_after, tolerance)

    # 4. trait investment
    trait_before = before.mean_trait()
    trait_after = after.mean_trait()
    trait_investment = _ordinal(trait_after - trait_before, tolerance)

    # 5. trait-space state
    var_before = before.trait_variance()
    var_after = after.trait_variance()
    trait_space_state = (
        "reconfigured"
        if abs(var_after - var_before) > tolerance or abs(trait_after - trait_before) > tolerance
        else "conserved"
    )

    return {
        "interaction_connectivity": interaction_connectivity,
        "patch_persistence": patch_persistence,
        "inbreeding_proxy": inbreeding_proxy,
        "trait_investment": trait_investment,
        "trait_space_state": trait_space_state,
    }


def default_observed_pattern() -> dict[str, str]:
    """Default focal P_obs: loss of interaction leads to trait decline with patch persistence.

    Focal signature: interaction connectivity decreases, patches remain occupied,
    inbreeding increases (gene flow lost), trait investment decreases, trait space
    is reconfigured.  This is the canonical rule-transition signature used when
    no empirical P_obs is supplied.
    """
    return {
        "interaction_connectivity": "decrease",
        "patch_persistence": "stable",
        "inbreeding_proxy": "increase",
        "trait_investment": "decrease",
        "trait_space_state": "reconfigured",
    }


#: Default ε: at most one of five POM components may mismatch (1/5 = 0.2).
DEFAULT_EPSILON: float = 0.2


def pom_distance(simulated: dict[str, str], observed: dict[str, str]) -> float:
    """ABC distance d(P_sim, P_obs): fraction of observed components unmatched."""
    total = len(observed)
    matches = sum(1 for name, rel in observed.items() if simulated.get(name) == rel)
    return pattern_distance(matches, total)


# ---------------------------------------------------------------------------
# Default patch layout and parameter presets
# ---------------------------------------------------------------------------

def default_patches(n: int = 3) -> dict:
    """Create ``n`` fully-connected patches with equal area and capacity."""
    patches = {}
    capacity = 20
    for pid in range(n):
        conn = {other: 0.5 for other in range(n) if other != pid}
        patches[pid] = Patch(
            patch_id=pid,
            area=1.0,
            carrying_capacity=capacity,
            connectivity=conn,
        )
    return patches


# Program-level fragility flags (programs whose match depends on exact cancellation).
_PROGRAM_FRAGILITY: dict[str, frozenset] = {
    "opposing_pathway_cancellation": frozenset({"exact_cancellation"}),
}


# ---------------------------------------------------------------------------
# Sweep-record generation (rule-transition layer interface)
# ---------------------------------------------------------------------------

def generate_sweep_records(
    scenario: str,
    program_parameter_draws: Iterable[tuple[str, MetapopParameters]],
    patches: dict | None = None,
    *,
    observed_pattern: dict | None = None,
    epsilon: float = DEFAULT_EPSILON,
    pom_tolerance: float = 0.08,
    seeds: Iterable[int] = (0,),
    region_prefix: str = "draw",
    n_warmup: int = 5,
    steps: int = 30,
) -> tuple[SweepRecord, ...]:
    """Generate RACH-compatible sweep records for the spatial metapopulation ABM.

    For every (program_id, parameter draw, seed) triplet:

    1. Run the IBM (warm-up + main).
    2. Extract the 5-component POM pattern P_sim.
    3. Compute d(P_sim, P_obs) and accept iff d ≤ ε.
    4. Return a ``SweepRecord`` carrying program motifs, pattern_matched flag, and
       all metadata needed by downstream invariant-extraction layers.

    Parameters
    ----------
    scenario:
        Scenario label (e.g. ``"pollinator_loss"``).
    program_parameter_draws:
        Iterable of ``(program_id, MetapopParameters)`` pairs, one per
        (program, parameter-draw) combination.  Multiple seeds are expanded
        internally.
    patches:
        Patch layout; defaults to ``default_patches(3)``.
    observed_pattern:
        P_obs; defaults to ``default_observed_pattern()``.
    epsilon:
        Acceptance threshold.
    pom_tolerance:
        Ordinal dead-band for POM component extraction.
    seeds:
        Seeds to use for each (program, draw) — each seed is a distinct replicate.
    region_prefix:
        Prefix for region_id strings.
    n_warmup:
        IBM warm-up steps before recording ``before_state``.
    steps:
        IBM main-run steps.
    """
    if patches is None:
        patches = default_patches(3)
    observed = observed_pattern if observed_pattern is not None else default_observed_pattern()
    records: list[SweepRecord] = []
    seed_list = tuple(seeds)
    draws = list(program_parameter_draws)

    for index, (program_id, params) in enumerate(draws):
        fragile_flags = _PROGRAM_FRAGILITY.get(program_id, frozenset())
        region_id = f"{region_prefix}_{index}"
        for seed in seed_list:
            before, after, motifs = simulate_metapopulation(
                patches, params, n_warmup=n_warmup, steps=steps, seed=seed,
            )
            p_sim = extract_pom_pattern(before, after, patches, params, tolerance=pom_tolerance)
            distance = pom_distance(p_sim, observed)
            acc = accepted_by_epsilon(distance, epsilon)
            records.append(SweepRecord(
                scenario=scenario,
                program_id=program_id,
                motifs=motifs | fragile_flags,
                pattern_matched=acc,
                parameters={
                    "trait_match_benefit": params.trait_match_benefit,
                    "trait_cost": params.trait_cost,
                    "density_threshold": params.density_threshold,
                    "mutation_rate": params.mutation_rate,
                    "mutation_std": params.mutation_std,
                    "dispersal_base": params.dispersal_base,
                    "distance_decay": params.distance_decay,
                    "resource_replenishment": params.resource_replenishment,
                    "max_age": params.max_age,
                },
                initial_state={
                    "n_individuals": before.n_total,
                    "mean_trait": round(before.mean_trait(), 4),
                    "trait_variance": round(before.trait_variance(), 4),
                    "n_patches_occupied": len(before.occupied_patches()),
                },
                metadata={
                    "region_id": region_id,
                    "P_sim": p_sim,
                    "P_obs": dict(observed),
                    "abc_distance": round(distance, 4),
                    "epsilon": epsilon,
                    "accepted": acc,
                    "n_individuals_before": before.n_total,
                    "n_individuals_after": after.n_total,
                    "patches_occupied_before": len(before.occupied_patches()),
                    "patches_occupied_after": len(after.occupied_patches()),
                    "mean_trait_before": round(before.mean_trait(), 4),
                    "mean_trait_after": round(after.mean_trait(), 4),
                },
                region_id=region_id,
                seed=seed,
                fragile_flags=fragile_flags,
            ))
    return tuple(records)
