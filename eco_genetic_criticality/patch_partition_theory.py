"""Patch-partition criticality for interaction-supported trait modes.

This module is the theorem layer for a simple but nontrivial spatial ecological
question: when interaction support is nonlinear in patch area, can equal total
habitat area sustain different trait modes depending only on how that area is
partitioned?

Let a landscape have patch areas ``A_1, ..., A_n`` with total area ``A_total``.
The aggregate interaction service is

    I(A) = eta * sum_j A_j ** alpha,

where ``eta > 0`` is interaction yield per area and ``alpha > 0`` is the
aggregation exponent. A high-investment trait mode is viable when

    I(A) >= I_required.

The exact results are:

P1 -- Coarsening theorem.
    For alpha > 1, merging two positive patches strictly increases I; for
    0 < alpha < 1 it strictly decreases I; alpha = 1 is partition neutral.

P2 -- Equal-partition criticality.
    Under n equal patches, I_n = eta * A_total**alpha * n**(1-alpha). For
    alpha > 1 there is an exact maximum number of equal patches compatible with
    the high trait mode. Thus equal total habitat area can lose that mode purely
    by subdivision.

P3 -- Genetic-threshold corollary.
    If a patch has N_e(A)=kappa*A and mutation-drift equilibrium heterozygosity
    H*(A)=4 N_e mu/(1+4 N_e mu), the local patch-area threshold maps exactly to
    an equilibrium heterozygosity threshold. This is a conditional mapping, not
    a universal claim that genetic diversity is always an early-warning signal.

The proofs are in ``docs/eco_genetic_criticality/patch_partition_criticality_theorem.md``.  Functions in
this module are deterministic implementations and regression checks of those
proofs, not their source.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor, isclose
from typing import Iterable, Literal, Sequence


AggregationRegime = Literal["superlinear", "linear", "sublinear"]


@dataclass(frozen=True)
class PatchInteractionSystem:
    """Parameters for nonlinear area-to-interaction service.

    ``interaction_requirement`` is the amount of aggregate service needed for the
    focal high-investment trait mode. It can be derived from a trait-performance
    threshold, for example when ``W_high = W_baseline + s_high * I`` and viability
    requires ``W_high >= tau``.
    """

    total_area: float
    interaction_yield: float
    aggregation_exponent: float
    interaction_requirement: float

    def __post_init__(self) -> None:
        if self.total_area <= 0:
            raise ValueError("total_area must be positive")
        if self.interaction_yield <= 0:
            raise ValueError("interaction_yield must be positive")
        if self.aggregation_exponent <= 0:
            raise ValueError("aggregation_exponent must be positive")
        if self.interaction_requirement <= 0:
            raise ValueError("interaction_requirement must be positive")

    @property
    def regime(self) -> AggregationRegime:
        if isclose(self.aggregation_exponent, 1.0, rel_tol=0.0, abs_tol=1e-12):
            return "linear"
        return "superlinear" if self.aggregation_exponent > 1.0 else "sublinear"

    @property
    def single_patch_critical_area(self) -> float:
        """Smallest local patch area supplying the required interaction service."""
        return (self.interaction_requirement / self.interaction_yield) ** (
            1.0 / self.aggregation_exponent
        )


def _validate_areas(areas: Sequence[float]) -> tuple[float, ...]:
    values = tuple(float(area) for area in areas)
    if not values:
        raise ValueError("at least one patch area is required")
    if any(area <= 0 for area in values):
        raise ValueError("all patch areas must be positive")
    return values


def interaction_service(
    areas: Sequence[float],
    *,
    interaction_yield: float,
    aggregation_exponent: float,
) -> float:
    """Return ``eta * sum(A_j**alpha)`` for a positive patch partition."""
    values = _validate_areas(areas)
    if interaction_yield <= 0 or aggregation_exponent <= 0:
        raise ValueError("interaction_yield and aggregation_exponent must be positive")
    return interaction_yield * sum(area ** aggregation_exponent for area in values)


def equal_partition(total_area: float, n_patches: int) -> tuple[float, ...]:
    """Return ``n_patches`` equal positive patches summing to ``total_area``."""
    if total_area <= 0:
        raise ValueError("total_area must be positive")
    if n_patches < 1:
        raise ValueError("n_patches must be at least one")
    return (total_area / n_patches,) * n_patches


def equal_partition_service(system: PatchInteractionSystem, n_patches: int) -> float:
    """Exact equal-partition service ``eta*A_total**alpha*n**(1-alpha)``."""
    if n_patches < 1:
        raise ValueError("n_patches must be at least one")
    alpha = system.aggregation_exponent
    return (
        system.interaction_yield
        * system.total_area ** alpha
        * n_patches ** (1.0 - alpha)
    )


def high_trait_supported(service: float, interaction_requirement: float, *, tolerance: float = 1e-12) -> bool:
    """Check the declared high-trait viability threshold ``I >= I_required``."""
    if interaction_requirement <= 0:
        raise ValueError("interaction_requirement must be positive")
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    return service > interaction_requirement or isclose(
        service, interaction_requirement, rel_tol=tolerance, abs_tol=tolerance
    )


def merge_service_change(
    left_area: float,
    right_area: float,
    *,
    interaction_yield: float,
    aggregation_exponent: float,
) -> float:
    """Service gain from merging two patches: ``g(a+b)-g(a)-g(b)``."""
    if left_area <= 0 or right_area <= 0:
        raise ValueError("patch areas must be positive")
    if interaction_yield <= 0 or aggregation_exponent <= 0:
        raise ValueError("interaction_yield and aggregation_exponent must be positive")
    alpha = aggregation_exponent
    return interaction_yield * (
        (left_area + right_area) ** alpha - left_area ** alpha - right_area ** alpha
    )


def merge_direction(system: PatchInteractionSystem) -> Literal["increases", "neutral", "decreases"]:
    """Return the P1 direction for merging positive patches in this regime."""
    if system.regime == "superlinear":
        return "increases"
    if system.regime == "sublinear":
        return "decreases"
    return "neutral"


def equal_partition_critical_count(system: PatchInteractionSystem) -> float:
    """Continuous equal-patch critical count where service equals requirement.

    For alpha > 1, high-trait support occurs for ``n <= n_crit``. For alpha < 1,
    it occurs for ``n >= n_crit``. For alpha = 1, partition number is irrelevant
    and this function raises because no count threshold exists.
    """
    alpha = system.aggregation_exponent
    if isclose(alpha, 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("linear area scaling has no partition-count threshold")
    numerator = system.interaction_yield * system.total_area ** alpha
    ratio = numerator / system.interaction_requirement
    return ratio ** (1.0 / (alpha - 1.0))


def admissible_equal_patch_counts(system: PatchInteractionSystem, *, max_count: int) -> tuple[int, ...]:
    """Return equal-patch counts in ``1..max_count`` retaining the high trait mode."""
    if max_count < 1:
        raise ValueError("max_count must be at least one")
    return tuple(
        n for n in range(1, max_count + 1)
        if high_trait_supported(equal_partition_service(system, n), system.interaction_requirement)
    )


def max_equal_patch_count_for_high_trait(system: PatchInteractionSystem) -> int | None:
    """Return the exact integer upper threshold in the superlinear regime.

    ``None`` means no finite upper count exists: either the system is sublinear,
    or linear and already satisfies the trait threshold. ``0`` means even one
    patch cannot support the high trait mode.
    """
    if system.regime == "sublinear":
        return None
    if system.regime == "linear":
        return None if high_trait_supported(
            equal_partition_service(system, 1), system.interaction_requirement
        ) else 0
    continuous = equal_partition_critical_count(system)
    candidate = max(0, floor(continuous + 1e-12))
    while candidate > 0 and not high_trait_supported(
        equal_partition_service(system, candidate), system.interaction_requirement
    ):
        candidate -= 1
    while high_trait_supported(
        equal_partition_service(system, candidate + 1), system.interaction_requirement
    ):
        candidate += 1
    return candidate


def min_equal_patch_count_for_high_trait(system: PatchInteractionSystem) -> int | None:
    """Return the exact integer lower threshold in the sublinear regime.

    ``None`` means no finite lower count is needed: either the system is
    superlinear and one patch is sufficient, or linear and the threshold is met.
    ``0`` means the linear system never reaches the threshold.
    """
    if system.regime == "superlinear":
        return None
    if system.regime == "linear":
        return 1 if high_trait_supported(
            equal_partition_service(system, 1), system.interaction_requirement
        ) else 0
    continuous = equal_partition_critical_count(system)
    candidate = max(1, ceil(continuous - 1e-12))
    while candidate > 1 and high_trait_supported(
        equal_partition_service(system, candidate - 1), system.interaction_requirement
    ):
        candidate -= 1
    while not high_trait_supported(
        equal_partition_service(system, candidate), system.interaction_requirement
    ):
        candidate += 1
    return candidate


def mutation_drift_heterozygosity(
    area: float,
    *,
    effective_density: float,
    mutation_rate: float,
) -> float:
    """Diploid neutral mutation-drift equilibrium heterozygosity for ``N_e=kappa*A``.

    ``H*=4*N_e*mu/(1+4*N_e*mu)``. This is a conditional equilibrium formula,
    deliberately separate from any non-equilibrium or selected genetic process.
    """
    if area <= 0 or effective_density <= 0 or mutation_rate <= 0:
        raise ValueError("area, effective_density, and mutation_rate must be positive")
    theta = 4.0 * effective_density * area * mutation_rate
    return theta / (1.0 + theta)


def area_from_mutation_drift_heterozygosity(
    heterozygosity: float,
    *,
    effective_density: float,
    mutation_rate: float,
) -> float:
    """Invert the positive-area equilibrium heterozygosity formula."""
    if not 0.0 < heterozygosity < 1.0:
        raise ValueError("heterozygosity must lie strictly between zero and one")
    if effective_density <= 0 or mutation_rate <= 0:
        raise ValueError("effective_density and mutation_rate must be positive")
    return heterozygosity / (
        4.0 * effective_density * mutation_rate * (1.0 - heterozygosity)
    )


def critical_heterozygosity_for_local_mode(
    system: PatchInteractionSystem,
    *,
    effective_density: float,
    mutation_rate: float,
) -> float:
    """Map the local single-patch area threshold to equilibrium heterozygosity.

    This is P3's threshold mapping. It is valid only under the stated linear
    ``N_e=kappa*A`` and neutral mutation-drift equilibrium assumptions.
    """
    return mutation_drift_heterozygosity(
        system.single_patch_critical_area,
        effective_density=effective_density,
        mutation_rate=mutation_rate,
    )


def local_mode_supported_by_heterozygosity(
    heterozygosity: float,
    system: PatchInteractionSystem,
    *,
    effective_density: float,
    mutation_rate: float,
    tolerance: float = 1e-12,
) -> bool:
    """Equivalent local-area test expressed on the equilibrium heterozygosity scale."""
    critical = critical_heterozygosity_for_local_mode(
        system,
        effective_density=effective_density,
        mutation_rate=mutation_rate,
    )
    return heterozygosity > critical or isclose(
        heterozygosity, critical, rel_tol=tolerance, abs_tol=tolerance
    )
