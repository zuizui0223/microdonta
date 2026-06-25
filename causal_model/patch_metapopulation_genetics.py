"""Metapopulation genetic diversity and exact equal-partition drift results.

This module sits above the one-patch Wright--Fisher moment theory in
:mod:`causal_model.patch_genetic_drift_theory`.

For biallelic patch frequencies p_j and weights w_j, it defines

    H_alpha = sum_j w_j 2 p_j (1-p_j)
    p_bar   = sum_j w_j p_j
    H_gamma = 2 p_bar (1-p_bar)
    F_ST    = 1 - H_alpha/H_gamma,  when H_gamma > 0.

The key exact partition result holds before migration, mutation, and
between-patch selection differences are introduced. If a total area T is split
into m equal isolated patches with the same interaction availability q and the
same density closure, each patch effective size is N_e/m. Hence the one-generation
within-patch drift coefficient 1/(2N_e) is multiplied exactly by m.

This is a statement about expected within-patch diversity erosion (alpha
heterozygosity), not about long-run gamma diversity or F_ST after migration and
selection are added.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from causal_model.patch_genetic_drift_theory import (
    drift_erosion_rate,
    effective_population_size,
    heterozygosity,
)


@dataclass(frozen=True)
class MetapopulationDiversity:
    """Biallelic alpha, gamma, and differentiation diversity components."""

    mean_allele_frequency: float
    alpha_heterozygosity: float
    gamma_heterozygosity: float
    fst: float | None


@dataclass(frozen=True)
class PartitionDriftContrast:
    """Exact within-patch drift contrast for one versus m equal isolated patches."""

    total_area: float
    patch_count: int
    interaction_availability: float
    single_patch_effective_size: float
    equal_patch_effective_size: float
    single_patch_erosion_rate: float
    equal_patch_erosion_rate: float
    erosion_rate_multiplier: float


def _weights(weights: Sequence[float], length: int) -> tuple[float, ...]:
    values = tuple(float(weight) for weight in weights)
    if len(values) != length:
        raise ValueError("weights must have the same length as frequencies")
    if any(weight < 0.0 for weight in values):
        raise ValueError("weights must be non-negative")
    total = sum(values)
    if total <= 0.0:
        raise ValueError("weights must have positive sum")
    return tuple(weight / total for weight in values)


def metapopulation_diversity(frequencies: Sequence[float], weights: Sequence[float]) -> MetapopulationDiversity:
    """Return H_alpha, H_gamma, and F_ST for a biallelic metapopulation."""
    p = tuple(float(value) for value in frequencies)
    if not p:
        raise ValueError("frequencies must be nonempty")
    if any(value < 0.0 or value > 1.0 for value in p):
        raise ValueError("frequencies must lie in [0, 1]")
    w = _weights(weights, len(p))
    mean = sum(weight * value for weight, value in zip(w, p))
    h_alpha = sum(weight * heterozygosity(value) for weight, value in zip(w, p))
    h_gamma = heterozygosity(mean)
    return MetapopulationDiversity(
        mean_allele_frequency=mean,
        alpha_heterozygosity=h_alpha,
        gamma_heterozygosity=h_gamma,
        fst=None if h_gamma == 0.0 else 1.0 - h_alpha / h_gamma,
    )


def equal_partition_drift_contrast(
    total_area: float,
    patch_count: int,
    interaction_availability: float,
    *,
    density_scale: float,
    baseline_density: float,
) -> PartitionDriftContrast:
    """Return the exact one-generation alpha-drift multiplier under equal isolation."""
    if total_area <= 0.0:
        raise ValueError("total_area must be positive")
    if patch_count < 1:
        raise ValueError("patch_count must be at least one")
    n_single = effective_population_size(
        total_area,
        interaction_availability,
        density_scale=density_scale,
        baseline_density=baseline_density,
    )
    n_equal = effective_population_size(
        total_area / patch_count,
        interaction_availability,
        density_scale=density_scale,
        baseline_density=baseline_density,
    )
    d_single = drift_erosion_rate(n_single)
    d_equal = drift_erosion_rate(n_equal)
    return PartitionDriftContrast(
        total_area=total_area,
        patch_count=patch_count,
        interaction_availability=interaction_availability,
        single_patch_effective_size=n_single,
        equal_patch_effective_size=n_equal,
        single_patch_erosion_rate=d_single,
        equal_patch_erosion_rate=d_equal,
        erosion_rate_multiplier=d_equal / d_single,
    )
