"""Declared multi-patch simulator for eco-genetic criticality hypotheses.

This is intentionally a *simulation layer*. Its equations are documented in
``docs/multipatch_criticality_dynamics_contract.md`` and should not be read as a
proof of the general theorem layer. It exposes every life-cycle assumption needed
to examine H_critical, H_genetic_lag, and H_fragmentation under finite populations.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp
from random import Random
from typing import Sequence


@dataclass(frozen=True)
class DynamicsParameters:
    patch_areas: tuple[float, ...]
    generations: int = 30
    initial_population: tuple[int, ...] = ()
    initial_interaction: tuple[float, ...] = ()
    initial_high_allele_frequency: tuple[float, ...] = ()
    density_capacity: float = 40.0
    area_reference: float = 1.0
    interaction_feedback: float = 6.0
    interaction_memory_weight: float = 0.6
    interaction_barrier: float = 0.5
    low_base: float = 1.1
    low_cost: float = 0.8
    high_base: float = 0.2
    high_interaction_benefit: float = 0.8
    high_peak_width: float = 0.15
    viability_threshold: float = 1.0
    trait_grid_size: int = 101
    high_trait_cutoff: float = 0.7
    selection_strength: float = 0.5
    baseline_growth: float = 0.3
    interaction_growth: float = 0.4
    high_allele_growth: float = 0.1
    effective_fraction: float = 0.6
    skew_penalty: float = 0.0
    migration_rate: float = 0.0
    random_seed: int = 1

    def __post_init__(self) -> None:
        if not self.patch_areas or any(area <= 0.0 for area in self.patch_areas):
            raise ValueError("patch_areas must be nonempty and positive")
        n = len(self.patch_areas)
        if self.generations < 1:
            raise ValueError("generations must be positive")
        for values, label, lower, upper in (
            (self.initial_population, "initial_population", 1, None),
            (self.initial_interaction, "initial_interaction", 0.0, 1.0),
            (self.initial_high_allele_frequency, "initial_high_allele_frequency", 0.0, 1.0),
        ):
            if values and len(values) != n:
                raise ValueError(f"{label} must be empty or match patch count")
            if upper is None:
                if values and any(value < lower for value in values):
                    raise ValueError(f"{label} has values below {lower}")
            elif values and any(value < lower or value > upper for value in values):
                raise ValueError(f"{label} must lie in [{lower}, {upper}]")
        if self.density_capacity <= 0.0 or self.area_reference <= 0.0:
            raise ValueError("density_capacity and area_reference must be positive")
        if self.interaction_feedback <= 0.0:
            raise ValueError("interaction_feedback must be positive")
        if not 0.0 <= self.interaction_memory_weight <= 1.0:
            raise ValueError("interaction_memory_weight must lie in [0, 1]")
        if self.high_peak_width <= 0.0:
            raise ValueError("high_peak_width must be positive")
        if self.trait_grid_size < 3:
            raise ValueError("trait_grid_size must be at least 3")
        if not 0.0 <= self.high_trait_cutoff <= 1.0:
            raise ValueError("high_trait_cutoff must lie in [0, 1]")
        if not 0.0 < self.effective_fraction <= 1.0:
            raise ValueError("effective_fraction must lie in (0, 1]")
        if not 0.0 <= self.skew_penalty < 1.0:
            raise ValueError("skew_penalty must lie in [0, 1)")
        if not 0.0 <= self.migration_rate <= 1.0:
            raise ValueError("migration_rate must lie in [0, 1]")


@dataclass(frozen=True)
class TraitSpaceSummary:
    viable_components: int
    high_trait_component_present: bool
    high_trait_margin: float


@dataclass(frozen=True)
class SimulationSnapshot:
    generation: int
    interaction: tuple[float, ...]
    population: tuple[int, ...]
    effective_size: tuple[float, ...]
    high_allele_frequency: tuple[float, ...]
    trait_space: tuple[TraitSpaceSummary, ...]
    h_alpha: float
    h_gamma: float
    fst: float | None


@dataclass(frozen=True)
class SimulationResult:
    parameters: DynamicsParameters
    snapshots: tuple[SimulationSnapshot, ...]


def sigmoid(value: float) -> float:
    if value >= 0.0:
        inverse = exp(-value)
        return 1.0 / (1.0 + inverse)
    inverse = exp(value)
    return inverse / (1.0 + inverse)


def trait_fitness(z: float, interaction: float, parameters: DynamicsParameters) -> float:
    """Declared continuous trait-performance surface W(z;q)."""
    if not 0.0 <= z <= 1.0 or not 0.0 <= interaction <= 1.0:
        raise ValueError("z and interaction must lie in [0, 1]")
    low_route = parameters.low_base - parameters.low_cost * z * z
    peak = parameters.high_base + parameters.high_interaction_benefit * interaction
    high_route = peak * exp(-((z - 1.0) / parameters.high_peak_width) ** 2)
    return low_route + high_route


def trait_space_summary(interaction: float, parameters: DynamicsParameters) -> TraitSpaceSummary:
    """Summarise viable-grid topology and high-investment component presence."""
    grid = tuple(index / (parameters.trait_grid_size - 1) for index in range(parameters.trait_grid_size))
    viable = tuple(trait_fitness(z, interaction, parameters) >= parameters.viability_threshold for z in grid)
    components = 0
    in_component = False
    high_present = False
    for z, is_viable in zip(grid, viable):
        if is_viable and not in_component:
            components += 1
            in_component = True
        if not is_viable:
            in_component = False
        if is_viable and z >= parameters.high_trait_cutoff:
            high_present = True
    margin = max(
        trait_fitness(z, interaction, parameters) - parameters.viability_threshold
        for z in grid
        if z >= parameters.high_trait_cutoff
    )
    return TraitSpaceSummary(components, high_present, margin)


def _heterozygosity(p: float) -> float:
    return 2.0 * p * (1.0 - p)


def _diversity(frequencies: Sequence[float], weights: Sequence[float]) -> tuple[float, float, float | None]:
    total = sum(weights)
    normalised = tuple(weight / total for weight in weights)
    p_bar = sum(weight * p for weight, p in zip(normalised, frequencies))
    h_alpha = sum(weight * _heterozygosity(p) for weight, p in zip(normalised, frequencies))
    h_gamma = _heterozygosity(p_bar)
    fst = None if h_gamma <= 0.0 else 1.0 - h_alpha / h_gamma
    return h_alpha, h_gamma, fst


def _binomial(rng: Random, trials: int, probability: float) -> int:
    probability = min(1.0, max(0.0, probability))
    return sum(rng.random() < probability for _ in range(trials))


def _initial_values(parameters: DynamicsParameters) -> tuple[tuple[int, ...], tuple[float, ...], tuple[float, ...]]:
    n = len(parameters.patch_areas)
    population = parameters.initial_population or tuple(
        max(1, round(parameters.density_capacity * area * 0.6)) for area in parameters.patch_areas
    )
    interaction = parameters.initial_interaction or tuple(0.5 for _ in range(n))
    frequency = parameters.initial_high_allele_frequency or tuple(0.5 for _ in range(n))
    return tuple(population), tuple(interaction), tuple(frequency)


def _effective_size(population: int, interaction: float, parameters: DynamicsParameters) -> float:
    # Interaction may increase demographic support but can also increase skew.
    return max(1.0, parameters.effective_fraction * population * (1.0 - parameters.skew_penalty * interaction))


def _snapshot(
    generation: int,
    population: tuple[int, ...],
    interaction: tuple[float, ...],
    frequency: tuple[float, ...],
    parameters: DynamicsParameters,
) -> SimulationSnapshot:
    effective = tuple(_effective_size(n, q, parameters) for n, q in zip(population, interaction))
    trait_spaces = tuple(trait_space_summary(q, parameters) for q in interaction)
    h_alpha, h_gamma, fst = _diversity(frequency, tuple(float(n) for n in population))
    return SimulationSnapshot(generation, interaction, population, effective, frequency, trait_spaces, h_alpha, h_gamma, fst)


def simulate(parameters: DynamicsParameters) -> SimulationResult:
    """Run the declared finite-population multi-patch life cycle."""
    rng = Random(parameters.random_seed)
    population, interaction, frequency = _initial_values(parameters)
    snapshots = [_snapshot(0, population, interaction, frequency, parameters)]

    for generation in range(1, parameters.generations + 1):
        carrying = tuple(parameters.density_capacity * area for area in parameters.patch_areas)
        density = tuple(min(1.0, n / k) for n, k in zip(population, carrying))
        q_next = tuple(
            sigmoid(
                parameters.interaction_feedback
                * (
                    (area / parameters.area_reference)
                    * dens
                    * (parameters.interaction_memory_weight * q + (1.0 - parameters.interaction_memory_weight) * p)
                    - parameters.interaction_barrier
                )
            )
            for area, dens, q, p in zip(parameters.patch_areas, density, interaction, frequency)
        )

        selected: list[float] = []
        for q, p in zip(q_next, frequency):
            high_margin = trait_fitness(1.0, q, parameters) - parameters.viability_threshold
            high_fitness = max(1e-12, 1.0 + parameters.selection_strength * high_margin)
            mean_fitness = p * high_fitness + (1.0 - p)
            selected.append(p * high_fitness / mean_fitness)

        weights = tuple(float(n) for n in population)
        total_weight = sum(weights)
        selected_mean = sum(weight * p for weight, p in zip(weights, selected)) / total_weight
        migrated = tuple(
            (1.0 - parameters.migration_rate) * p + parameters.migration_rate * selected_mean
            for p in selected
        )

        next_population: list[int] = []
        for n, k, q, p in zip(population, carrying, q_next, selected):
            exponent = parameters.baseline_growth + parameters.interaction_growth * q + parameters.high_allele_growth * p - n / k
            next_population.append(max(1, round(n * exp(exponent))))

        next_frequency: list[float] = []
        for n, q, p in zip(next_population, q_next, migrated):
            n_eff = _effective_size(n, q, parameters)
            gene_copies = max(2, round(2.0 * n_eff))
            next_frequency.append(_binomial(rng, gene_copies, p) / gene_copies)

        population = tuple(next_population)
        interaction = q_next
        frequency = tuple(next_frequency)
        snapshots.append(_snapshot(generation, population, interaction, frequency, parameters))

    return SimulationResult(parameters, tuple(snapshots))


def first_high_trait_absence(result: SimulationResult) -> int | None:
    """Return first generation without high-trait viability in any patch."""
    for snapshot in result.snapshots:
        if not any(summary.high_trait_component_present for summary in snapshot.trait_space):
            return snapshot.generation
    return None


def first_alpha_warning(result: SimulationResult, warning_threshold: float) -> int | None:
    """Return first generation where H_alpha is at or below a predeclared boundary."""
    if not 0.0 <= warning_threshold <= 1.0:
        raise ValueError("warning_threshold must lie in [0, 1]")
    for snapshot in result.snapshots:
        if snapshot.h_alpha <= warning_threshold:
            return snapshot.generation
    return None
