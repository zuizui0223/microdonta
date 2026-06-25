"""Finite-population genetic drift coupled to patch interaction states.

This module adds the genetic layer to
:mod:`causal_model.patch_interaction_bifurcation_theory` without claiming that
alleles have already been measured in any real system.

One generation is explicitly ordered as:

    individual viability / fecundity selection
    -> finite gamete sampling (Wright--Fisher drift)
    -> next-generation allele frequency.

For a diploid effective population size ``N_e`` and post-selection allele
frequency ``p_star``:

    2 N_e p_next | p_star ~ Binomial(2 N_e, p_star)

so

    E[p_next | p_star] = p_star
    Var[p_next | p_star] = p_star (1-p_star) / (2 N_e)
    E[H_next | p_star] = (1 - 1/(2 N_e)) H(p_star),

where H(p)=2p(1-p) is expected heterozygosity.

The last identity makes drift a generational force rather than optional noise:
for every finite N_e and interior p_star, expected heterozygosity decreases in a
single generation when mutation and migration are absent.

To connect ecology to genetics, effective size is closed as

    N_e(A, q) = density_scale * A * [baseline_density + (1-baseline_density) q],

where A is patch size and q is interaction availability. This is a transparent
assumption: high interaction availability supports a larger effective population,
but a baseline density can remain when q is low. The resulting drift erosion rate
is D(A,q)=1/[2N_e(A,q)]. In a bistable interaction patch, the low and high q
branches therefore have distinct genetic-erosion rates at the same environment.

Proofs and scope are stated in ``docs/patch_genetic_drift_theorem.md``.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose

from causal_model.patch_interaction_bifurcation_theory import SaddleNodes, saddle_nodes


@dataclass(frozen=True)
class SelectionDriftStep:
    """Deterministic moments of one selection-plus-drift generation."""

    allele_frequency_before: float
    relative_fitness_high: float
    relative_fitness_low: float
    allele_frequency_after_selection: float
    effective_population_size: float
    expected_allele_frequency_after_drift: float
    allele_frequency_variance_after_drift: float
    heterozygosity_after_selection: float
    expected_heterozygosity_after_drift: float
    expected_heterozygosity_loss: float


@dataclass(frozen=True)
class BranchGeneticErosion:
    """Genetic erosion contrast between low and high interaction branches."""

    patch_size: float
    feedback_strength: float
    barrier: float
    low_interaction_availability: float
    high_interaction_availability: float
    low_effective_population_size: float
    high_effective_population_size: float
    low_drift_erosion_rate: float
    high_drift_erosion_rate: float
    erosion_rate_jump_at_collapse: float


def heterozygosity(p: float) -> float:
    """Expected diploid heterozygosity H(p)=2p(1-p)."""
    if not 0.0 <= p <= 1.0:
        raise ValueError("allele frequency must lie in [0, 1]")
    return 2.0 * p * (1.0 - p)


def selected_allele_frequency(p: float, fitness_high: float, fitness_low: float) -> float:
    """Return allele frequency after viability/fecundity selection.

    The high allele may correspond to an interaction-dependent trait state, but
    the formula itself is agnostic about the trait map. Both relative fitnesses
    must be positive so that selection and the subsequent drift kernel are defined.
    """
    if not 0.0 <= p <= 1.0:
        raise ValueError("allele frequency must lie in [0, 1]")
    if fitness_high <= 0.0 or fitness_low <= 0.0:
        raise ValueError("relative fitnesses must be positive")
    mean_fitness = p * fitness_high + (1.0 - p) * fitness_low
    return p * fitness_high / mean_fitness


def effective_population_size(
    patch_size: float,
    interaction_availability: float,
    *,
    density_scale: float,
    baseline_density: float,
) -> float:
    """Return the positive effective size closure N_e(A,q).

    ``baseline_density`` lies in (0,1]. It prevents a low-interaction patch from
    being silently equated with a zero-population boundary. The theorem is about
    finite positive populations; true extinction is a separate absorbing state.
    """
    if patch_size <= 0.0:
        raise ValueError("patch_size must be positive")
    if not 0.0 <= interaction_availability <= 1.0:
        raise ValueError("interaction_availability must lie in [0, 1]")
    if density_scale <= 0.0:
        raise ValueError("density_scale must be positive")
    if not 0.0 < baseline_density <= 1.0:
        raise ValueError("baseline_density must lie in (0, 1]")
    return density_scale * patch_size * (
        baseline_density + (1.0 - baseline_density) * interaction_availability
    )


def drift_erosion_rate(effective_size: float) -> float:
    """Return the one-generation expected heterozygosity-loss coefficient 1/(2N_e)."""
    if effective_size <= 0.0:
        raise ValueError("effective_size must be positive")
    return 1.0 / (2.0 * effective_size)


def expected_heterozygosity_after_drift(post_selection_frequency: float, effective_size: float) -> float:
    """Return E[H_next | p_star] under diploid Wright--Fisher sampling.

    The formula is exact for an integer diploid N_e. For noninteger effective
    sizes it is the standard moment-equivalent effective-population approximation.
    """
    if effective_size < 0.5:
        raise ValueError("effective_size must be at least 0.5 for a nonnegative drift factor")
    return (1.0 - drift_erosion_rate(effective_size)) * heterozygosity(post_selection_frequency)


def selection_drift_step(
    allele_frequency: float,
    fitness_high: float,
    fitness_low: float,
    effective_size: float,
) -> SelectionDriftStep:
    """Return exact first and second moments after one selected Wright--Fisher generation."""
    p_star = selected_allele_frequency(allele_frequency, fitness_high, fitness_low)
    if effective_size < 0.5:
        raise ValueError("effective_size must be at least 0.5")
    h_star = heterozygosity(p_star)
    h_next = expected_heterozygosity_after_drift(p_star, effective_size)
    variance = p_star * (1.0 - p_star) / (2.0 * effective_size)
    return SelectionDriftStep(
        allele_frequency_before=allele_frequency,
        relative_fitness_high=fitness_high,
        relative_fitness_low=fitness_low,
        allele_frequency_after_selection=p_star,
        effective_population_size=effective_size,
        expected_allele_frequency_after_drift=p_star,
        allele_frequency_variance_after_drift=variance,
        heterozygosity_after_selection=h_star,
        expected_heterozygosity_after_drift=h_next,
        expected_heterozygosity_loss=h_star - h_next,
    )


def branch_genetic_erosion(
    patch_size: float,
    feedback_strength: float,
    *,
    density_scale: float,
    baseline_density: float,
) -> BranchGeneticErosion:
    """Return the exact drift-rate contrast at the two interaction saddle nodes.

    The saddle node availability values are used as the limiting low/high branch
    states at collapse/recovery. Because N_e(A,q) is strictly increasing in q
    whenever baseline_density<1, the low branch has stronger drift erosion than
    the high branch. This is the eco-genetic hysteresis mechanism.
    """
    nodes: SaddleNodes = saddle_nodes(patch_size, feedback_strength)
    n_low = effective_population_size(
        patch_size, nodes.q_low, density_scale=density_scale, baseline_density=baseline_density
    )
    n_high = effective_population_size(
        patch_size, nodes.q_high, density_scale=density_scale, baseline_density=baseline_density
    )
    d_low = drift_erosion_rate(n_low)
    d_high = drift_erosion_rate(n_high)
    if baseline_density < 1.0 and not n_low < n_high:
        raise RuntimeError("interaction-dependent effective size must increase across branches")
    return BranchGeneticErosion(
        patch_size=patch_size,
        feedback_strength=feedback_strength,
        barrier=(nodes.theta_low + nodes.theta_high) / 2.0,
        low_interaction_availability=nodes.q_low,
        high_interaction_availability=nodes.q_high,
        low_effective_population_size=n_low,
        high_effective_population_size=n_high,
        low_drift_erosion_rate=d_low,
        high_drift_erosion_rate=d_high,
        erosion_rate_jump_at_collapse=d_low - d_high,
    )


def drift_is_unavoidable_interior(p: float, effective_size: float, *, tolerance: float = 1e-14) -> bool:
    """Return whether drift strictly lowers expected heterozygosity in one generation.

    This is true exactly for interior allele frequencies and finite effective
    populations with N_e > 1/2, in the mutation- and migration-free model.
    """
    if tolerance < 0.0:
        raise ValueError("tolerance must be non-negative")
    if not 0.0 < p < 1.0 or effective_size <= 0.5:
        return False
    return expected_heterozygosity_after_drift(p, effective_size) < heterozygosity(p) - tolerance


def moment_identity_holds(step: SelectionDriftStep, *, tolerance: float = 1e-12) -> bool:
    """Check the exact Wright--Fisher moment identities for a computed step."""
    if tolerance < 0.0:
        raise ValueError("tolerance must be non-negative")
    p_star = step.allele_frequency_after_selection
    n_e = step.effective_population_size
    return (
        isclose(step.expected_allele_frequency_after_drift, p_star, abs_tol=tolerance)
        and isclose(
            step.allele_frequency_variance_after_drift,
            p_star * (1.0 - p_star) / (2.0 * n_e),
            abs_tol=tolerance,
        )
        and isclose(
            step.expected_heterozygosity_after_drift,
            (1.0 - 1.0 / (2.0 * n_e)) * heterozygosity(p_star),
            abs_tol=tolerance,
        )
    )
