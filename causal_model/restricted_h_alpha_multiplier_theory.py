"""Restricted expected H-alpha multiplier theorem for the finite-bin simulator.

A universal H-alpha contraction theorem is false: migration can increase local
heterozygosity by mixing patches, and selection can move frequencies toward one
half. This module proves a one-step conditional upper multiplier on a specified
high-allele interval.

If every patch frequency lies in [p_min, p_max] with p_min >= 1/2, high-allele
selection has a uniform fitness advantage f_min > 1, and census size is bounded
above, then selection moves every patch above s_min. Census-weighted migration
preserves that lower bound. Heterozygosity is decreasing on [1/2, 1], so the
post-migration local H-alpha is at most H(s_min), while current H-alpha is at
least H(p_max). Wright--Fisher sampling adds the exact factor 1-1/M.

The resulting multiplier can be >=1. A contraction certificate is issued only
when its computed upper bound is strictly below one.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import floor

from causal_model.multipatch_criticality_dynamics import DynamicsParameters, trait_fitness


@dataclass(frozen=True)
class RestrictedHAlphaMultiplier:
    """Conditional one-step upper multiplier for expected local H-alpha."""

    allele_lower_bound: float
    allele_upper_bound: float
    interaction_lower_bound: float
    population_upper_bound: int
    high_allele_fitness_lower_bound: float
    selected_allele_lower_bound: float
    heterozygosity_current_lower_bound: float
    heterozygosity_post_migration_upper_bound: float
    gene_copy_upper_bound: int
    sampling_multiplier_upper_bound: float
    expected_h_alpha_multiplier_upper_bound: float
    contraction_certified: bool


def heterozygosity(frequency: float) -> float:
    """Return diploid biallelic heterozygosity H(p)=2p(1-p)."""
    if not 0.0 <= frequency <= 1.0:
        raise ValueError("frequency must lie in [0, 1]")
    return 2.0 * frequency * (1.0 - frequency)


def _validate_interval(lower: float, upper: float) -> tuple[float, float]:
    lower = float(lower)
    upper = float(upper)
    if not 0.5 <= lower <= upper < 1.0:
        raise ValueError("allele interval must satisfy 1/2 <= lower <= upper < 1")
    return lower, upper


def _require_monotone_selection(parameters: DynamicsParameters) -> None:
    if parameters.high_interaction_benefit < 0.0:
        raise ValueError("theorem requires non-negative high_interaction_benefit")
    if parameters.selection_strength < 0.0:
        raise ValueError("theorem requires non-negative selection_strength")
    if parameters.skew_penalty < 0.0:
        raise ValueError("theorem requires non-negative skew_penalty")


def high_allele_fitness_lower_bound(
    interaction_lower_bound: float,
    parameters: DynamicsParameters,
) -> float:
    """Return the uniform high-allele fitness lower bound in the stated region."""
    _require_monotone_selection(parameters)
    if not 0.0 <= interaction_lower_bound <= 1.0:
        raise ValueError("interaction_lower_bound must lie in [0, 1]")
    margin = trait_fitness(1.0, interaction_lower_bound, parameters) - parameters.viability_threshold
    return max(1e-12, 1.0 + parameters.selection_strength * margin)


def selected_frequency(
    frequency: float,
    high_allele_fitness: float,
) -> float:
    """Return the simulator's deterministic one-allele selection map."""
    if not 0.0 <= frequency <= 1.0:
        raise ValueError("frequency must lie in [0, 1]")
    if high_allele_fitness <= 0.0:
        raise ValueError("high_allele_fitness must be positive")
    return frequency * high_allele_fitness / (
        frequency * high_allele_fitness + (1.0 - frequency)
    )


def gene_copy_upper_bound(
    population_upper_bound: int,
    parameters: DynamicsParameters,
) -> int:
    """Safely upper-bound simulator gene copies from a census upper bound."""
    _require_monotone_selection(parameters)
    if population_upper_bound < 1:
        raise ValueError("population_upper_bound must be at least one")
    # n_eff=N*effective_fraction*(1-skew*q) <= N_max*effective_fraction.
    effective_upper = max(1.0, parameters.effective_fraction * population_upper_bound)
    # floor(x+1/2) is a safe upper envelope for Python half-even round(x).
    return max(2, floor(2.0 * effective_upper + 0.5))


def restricted_h_alpha_multiplier(
    parameters: DynamicsParameters,
    allele_lower_bound: float,
    allele_upper_bound: float,
    interaction_lower_bound: float,
    population_upper_bound: int,
) -> RestrictedHAlphaMultiplier:
    """Bound E[H_alpha,next] / H_alpha,current on a high-allele interval.

    Assumptions are that every patch currently has p_j in [p_min, p_max],
    q_j >= q_min, and next census size at most N_max. Under f_min>1:

      H_alpha,current >= H(p_max)
      E[H_alpha,next] <= (1-1/M_max) H(s(p_min, f_min)).

    Their ratio is the returned upper multiplier. The migration rate may take
    any legal value because convex-combination migration cannot lower a common
    post-selection lower bound.
    """
    p_min, p_max = _validate_interval(allele_lower_bound, allele_upper_bound)
    f_min = high_allele_fitness_lower_bound(interaction_lower_bound, parameters)
    if f_min <= 1.0:
        raise ValueError("theorem requires a strict high-allele fitness advantage f_min > 1")
    selected_min = selected_frequency(p_min, f_min)
    h_current_lower = heterozygosity(p_max)
    h_post_upper = heterozygosity(selected_min)
    copies_upper = gene_copy_upper_bound(population_upper_bound, parameters)
    sampling_upper = 1.0 - 1.0 / copies_upper
    multiplier = sampling_upper * h_post_upper / h_current_lower
    return RestrictedHAlphaMultiplier(
        allele_lower_bound=p_min,
        allele_upper_bound=p_max,
        interaction_lower_bound=float(interaction_lower_bound),
        population_upper_bound=int(population_upper_bound),
        high_allele_fitness_lower_bound=f_min,
        selected_allele_lower_bound=selected_min,
        heterozygosity_current_lower_bound=h_current_lower,
        heterozygosity_post_migration_upper_bound=h_post_upper,
        gene_copy_upper_bound=copies_upper,
        sampling_multiplier_upper_bound=sampling_upper,
        expected_h_alpha_multiplier_upper_bound=multiplier,
        contraction_certified=multiplier < 1.0,
    )
