"""Analytic invasion-fitness theory for relationship-loss trait-space contraction.

This module gives the theorem layer behind the spatial-ABM finding
(:mod:`causal_model.spatial_metapopulation_abm`): a mean-field,
monomorphic-resident invasion-fitness model in which the viable trait set

    Omega_inv(I, R) = { z in [0, 1] : s(z; I, R) >= 0 },
    s(z; I, R)      = I * B(z) - C(z) + K + R,

with

    B(z)  relationship benefit, increasing, B(0) = 0   (e.g. pollinator service)
    C(z)  trait cost,           increasing, C(0) = 0   (the allocation trade-off)
    K     relationship-independent baseline net fitness, K >= 0
          (a zero-investment phenotype persists without the relationship)
    R     alternative-route compensation after the loss (R >= 0)
    I     relationship state in {1 (intact), 0 (lost)}.

The qualitative direction of the trait is never assumed; only that benefit and
cost are increasing in investment (a trade-off). The algebraic proofs are in
``docs/trait_space_contraction_theorem.md``. The ``verify_*`` functions and
``tests/test_trait_space_theory.py`` are regression checks over random monotone
instances; they are not substitutes for those proofs.

Theorems (informal)
-------------------
T1 (pure relationship loss contracts). For any increasing B, C with B(0)=0 and
    K >= 0, losing the relationship with no compensation (I: 1->0, R=0)
    satisfies Omega_inv(0, 0) subseteq Omega_inv(1, 0): the viable set weakly
    contracts, and its upper edge weakly decreases.

T2 (incomplete-compensation contraction). If the alternative route is weaker
    than the relationship on every relationship-dependent trait
    (R <= B(z) for all z with C(z) > K), then Omega_inv(0, R) subseteq
    Omega_inv(1, 0).

T3 (edge-retention threshold). Let z* = z_max(1, 0). The exact minimum
    compensation that retains that existing edge trait after loss is
    R_keep = max(0, C(z*) - K). On an ordered grid with non-decreasing cost,
    R >= R_keep iff the upper edge does not recede. B(z*) is a sufficient
    replacement bound, not generally the exact threshold.

T4 (contraction, not fragmentation). If benefit has diminishing returns and
    cost is accelerating (B concave, C convex), then s is concave, so Omega_inv
    is an interval [0, z_max]; the benefit route can only recede the upper edge
    (contraction / shift), never split the set. Fragmentation therefore requires
    a different mechanism within this model family (e.g. spatial isolation,
    Proposition S1).

Proposition S1 (spatial route, fitness-independent). Realised viability also
requires establishment across reachable patches. With an establishment factor
increasing in dispersal connectivity, cutting dispersal removes traits near the
establishment margin independently of s(z); this can contract OR fragment the
realised viable set even when per-capita invasion fitness is unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Sequence


# ---------------------------------------------------------------------------
# Invasion-fitness model on a grid
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InvasionFitnessModel:
    """Mean-field invasion fitness ``s = I*B - C + K + R`` on an ordered grid.

    ``benefit`` and ``cost`` are values of B and C on ``grid``; theorem callers
    must supply non-decreasing sequences starting at zero. ``baseline`` is K.
    """

    grid: tuple[float, ...]
    benefit: tuple[float, ...]
    cost: tuple[float, ...]
    baseline: float

    def __post_init__(self) -> None:
        n = len(self.grid)
        if not (len(self.benefit) == len(self.cost) == n) or n < 2:
            raise ValueError("grid, benefit, cost must share length >= 2")
        if any(right < left for left, right in zip(self.grid, self.grid[1:])):
            raise ValueError("grid must be ordered")
        if self.baseline < 0:
            raise ValueError("baseline must be non-negative")

    def s(self, i: int, interaction: float, compensation: float) -> float:
        return interaction * self.benefit[i] - self.cost[i] + self.baseline + compensation

    def viable_mask(self, interaction: float, compensation: float) -> tuple[bool, ...]:
        return tuple(self.s(i, interaction, compensation) >= -1e-12 for i in range(len(self.grid)))


# ---------------------------------------------------------------------------
# Viable-set geometry
# ---------------------------------------------------------------------------

def viable_values(model: InvasionFitnessModel, interaction: float, compensation: float) -> tuple[float, ...]:
    mask = model.viable_mask(interaction, compensation)
    return tuple(z for z, m in zip(model.grid, mask) if m)


def measure(model: InvasionFitnessModel, interaction: float, compensation: float) -> float:
    mask = model.viable_mask(interaction, compensation)
    return sum(1 for m in mask if m) / len(mask)


def upper_edge(model: InvasionFitnessModel, interaction: float, compensation: float) -> float:
    vals = viable_values(model, interaction, compensation)
    return max(vals) if vals else -1.0


def n_components(mask: Sequence[bool]) -> int:
    count = 0
    prev = False
    for m in mask:
        if m and not prev:
            count += 1
        prev = m
    return count


def is_interval(mask: Sequence[bool]) -> bool:
    return n_components(mask) <= 1


def is_subset(small: Sequence[bool], big: Sequence[bool]) -> bool:
    return all((not s) or b for s, b in zip(small, big))


def _before_edge_index(model: InvasionFitnessModel) -> int | None:
    edge = upper_edge(model, 1.0, 0.0)
    return None if edge < 0 else model.grid.index(edge)


def edge_retention_threshold(model: InvasionFitnessModel) -> float:
    """Exact minimum R that retains the pre-loss upper-edge trait after loss.

    Let z* be the largest trait viable under the intact relationship. After loss,
    z* is viable exactly when ``R >= C(z*) - K``. Because R is constrained to be
    non-negative, the threshold is ``max(0, C(z*) - K)``. With an ordered grid and
    non-decreasing cost, this is also the exact threshold at which the upper edge
    stops receding: below it no trait at or above z* is viable; at or above it z*
    is viable.
    """
    idx = _before_edge_index(model)
    if idx is None:
        return 0.0
    return max(0.0, model.cost[idx] - model.baseline)


def benefit_replacement_bound(model: InvasionFitnessModel) -> float:
    """Sufficient compensation bound ``B(z*)`` for retaining the old upper edge.

    This is not generally minimal. Prior viability of z* gives
    ``C(z*) - K <= B(z*)``, so this bound is at least the exact edge-retention
    threshold. The two agree only when z* lies on the pre-loss invasion boundary.
    """
    idx = _before_edge_index(model)
    return 0.0 if idx is None else model.benefit[idx]


def compensation_threshold(model: InvasionFitnessModel) -> float:
    """Backward-compatible name for :func:`edge_retention_threshold`.

    Earlier versions incorrectly returned ``B(z*)`` and described it as exact.
    """
    return edge_retention_threshold(model)


def relationship_dependent_benefit_min(model: InvasionFitnessModel) -> float:
    """Minimum B(z) over traits that need the relationship; +inf if none."""
    vals = [model.benefit[i] for i in range(len(model.grid)) if model.cost[i] > model.baseline]
    return min(vals) if vals else float("inf")


# ---------------------------------------------------------------------------
# Random monotone B, C for regression checks
# ---------------------------------------------------------------------------

def _cumulative(increments: list[float]) -> tuple[float, ...]:
    out = [0.0]
    for inc in increments:
        out.append(out[-1] + inc)
    return tuple(out)


def random_model(
    rng: Random,
    *,
    grid_points: int = 21,
    max_benefit_slope: float = 0.12,
    max_cost_slope: float = 0.12,
    concave_benefit: bool = False,
    convex_cost: bool = False,
) -> InvasionFitnessModel:
    """Sample increasing B, C with B(0)=C(0)=0 and K >= 0."""
    grid = tuple(i / (grid_points - 1) for i in range(grid_points))
    b_inc = [rng.uniform(0.0, max_benefit_slope) for _ in range(grid_points - 1)]
    c_inc = [rng.uniform(0.0, max_cost_slope) for _ in range(grid_points - 1)]
    if concave_benefit:
        b_inc.sort(reverse=True)
    if convex_cost:
        c_inc.sort()
    benefit = _cumulative(b_inc)
    cost = _cumulative(c_inc)
    baseline = rng.uniform(0.0, 0.5 * cost[-1] + 1e-9)
    return InvasionFitnessModel(grid=grid, benefit=benefit, cost=cost, baseline=baseline)


# ---------------------------------------------------------------------------
# Algebraic-theorem regression checks
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerificationResult:
    n_models: int
    n_ok: int
    counterexample: dict | None

    @property
    def proved(self) -> bool:
        """Compatibility flag: all sampled regression instances passed.

        The actual proofs are algebraic and stated in the accompanying document.
        """
        return self.counterexample is None and self.n_ok == self.n_models


def verify_pure_loss_contracts(n: int = 2000, seed: int = 0) -> VerificationResult:
    """Regression check for T1 with R = 0."""
    rng = Random(seed)
    ok = 0
    counter = None
    for k in range(n):
        m = random_model(rng)
        before = m.viable_mask(1.0, 0.0)
        after = m.viable_mask(0.0, 0.0)
        subset = is_subset(after, before)
        edge = upper_edge(m, 0.0, 0.0) <= upper_edge(m, 1.0, 0.0) + 1e-12
        if subset and edge:
            ok += 1
        elif counter is None:
            counter = {"model_index": k, "subset": subset, "edge": edge}
    return VerificationResult(n, ok, counter)


def verify_incomplete_compensation_contracts(n: int = 2000, seed: int = 1) -> VerificationResult:
    """Regression check for T2 under R <= min B on dependent traits."""
    rng = Random(seed)
    ok = 0
    counter = None
    for k in range(n):
        m = random_model(rng)
        bmin = relationship_dependent_benefit_min(m)
        if bmin == float("inf"):
            ok += 1
            continue
        r = rng.uniform(0.0, bmin)
        before = m.viable_mask(1.0, 0.0)
        after = m.viable_mask(0.0, r)
        if is_subset(after, before):
            ok += 1
        elif counter is None:
            counter = {"model_index": k, "R": r, "bmin": bmin}
    return VerificationResult(n, ok, counter)


def verify_compensation_threshold(n: int = 2000, seed: int = 2) -> VerificationResult:
    """Regression check for exact edge retention and sufficient B(z*) replacement."""
    rng = Random(seed)
    ok = 0
    counter = None
    for k in range(n):
        m = random_model(rng)
        edge_before = upper_edge(m, 1.0, 0.0)
        r_keep = edge_retention_threshold(m)
        r_replace = benefit_replacement_bound(m)
        retained_at_threshold = upper_edge(m, 0.0, r_keep) >= edge_before - 1e-12
        retained_at_replacement = upper_edge(m, 0.0, r_replace) >= edge_before - 1e-12
        strict_below = True
        if r_keep > 1e-8:
            below = max(0.0, r_keep - max(1e-7, r_keep * 0.25))
            strict_below = upper_edge(m, 0.0, below) < edge_before - 1e-12
        if retained_at_threshold and retained_at_replacement and strict_below:
            ok += 1
        elif counter is None:
            counter = {
                "model_index": k,
                "R_keep": r_keep,
                "R_replace": r_replace,
                "retained_at_threshold": retained_at_threshold,
                "retained_at_replacement": retained_at_replacement,
                "strict_below": strict_below,
            }
    return VerificationResult(n, ok, counter)


def verify_no_fragmentation_under_convexity(n: int = 2000, seed: int = 3) -> VerificationResult:
    """Regression check for T4: B concave and C convex imply an interval."""
    rng = Random(seed)
    ok = 0
    counter = None
    for k in range(n):
        m = random_model(rng, concave_benefit=True, convex_cost=True)
        bad = False
        for i_state in (1.0, 0.0):
            for r in (0.0, 0.5 * m.benefit[-1], m.benefit[-1]):
                if not is_interval(m.viable_mask(i_state, r)):
                    bad = True
                    break
            if bad:
                break
        if not bad:
            ok += 1
        elif counter is None:
            counter = {"model_index": k}
    return VerificationResult(n, ok, counter)


# ---------------------------------------------------------------------------
# Bridge: the spatial-ABM rare-invader fitness reduces to this structure
# ---------------------------------------------------------------------------

def abm_invasion_factor(
    z: float,
    *,
    interaction_benefit: float,
    investment_reward: float,
    trait_cost: float,
    survival_tradeoff: float,
    base_survival: float,
    predation_pressure: float,
    interaction_scale: float,
    predation_scale: float,
    repro_baseline: float,
    resident_trait: float,
    density: float = 0.6,
    resource: float = 0.5,
    distance_factor: float = 0.55,
    density_threshold: float = 0.8,
) -> float:
    """Deterministic rare-invader one-step growth factor G(z) of the spatial ABM.

    Mirrors the arithmetic of :func:`causal_model.spatial_metapopulation_abm._simulate_step`
    for a rare, age-0, bred-true invader of trait ``z`` against a monomorphic resident
    at ``resident_trait``. The invader is viable iff ``G(z) >= 1``. This makes explicit
    that the ABM's invasion fitness has the theorem's structure ``service(z) - cost(z)
    + baseline`` plus a secondary mate-matching term.
    """
    availability = max(0.55, 1.0 - 0.5 * density / max(density_threshold, 1e-6))
    service = interaction_scale * interaction_benefit * z * availability
    mate = (1.0 - abs(z - resident_trait)) * distance_factor
    logistic = max(0.0, 1.0 - density)
    repro = max(0.0, min(1.0,
        0.22
        + investment_reward * service
        + 0.20 * mate
        + 0.30 * resource
        + repro_baseline
        - trait_cost * z
    )) * logistic
    predation = predation_pressure * predation_scale * density
    survival = max(0.0, min(1.0, base_survival - survival_tradeoff * z - predation))
    return survival * (1.0 + repro)


def abm_viable_upper_edge(
    *,
    interaction_scale: float,
    repro_baseline: float,
    resident_trait: float,
    grid_points: int = 41,
    **params,
) -> float:
    """Upper edge of ``{z : G(z) >= 1}`` for the ABM rare-invader factor."""
    grid = [i / (grid_points - 1) for i in range(grid_points)]
    edge = -1.0
    for z in grid:
        g = abm_invasion_factor(
            z, interaction_scale=interaction_scale, repro_baseline=repro_baseline,
            resident_trait=resident_trait, **params,
        )
        if g >= 1.0:
            edge = z
    return edge


# ---------------------------------------------------------------------------
# Proposition S1: the spatial (dispersal) route, fitness-independent
# ---------------------------------------------------------------------------

def spatial_route_contraction(
    n_patches: int = 6,
    *,
    grid_points: int = 21,
    connectivity_before: float = 0.9,
    connectivity_after: float = 0.0,
    seed: int = 0,
) -> dict:
    """Demonstrate a spatial route to realised trait-set loss.

    Each trait is intrinsically viable on a random nonempty subset of patches.
    Establishment requires reaching at least one suitable patch from the seeded
    patch. With high connectivity every suitable patch is reachable; with zero
    connectivity only the seeded patch counts. This numerical construction is a
    model example, not a universal fragmentation theorem.
    """
    rng = Random(seed)
    grid = [i / (grid_points - 1) for i in range(grid_points)]
    suitable: dict[float, set[int]] = {}
    for z in grid:
        ps = {p for p in range(n_patches) if rng.random() < 0.4}
        if not ps:
            ps = {rng.randrange(n_patches)}
        suitable[z] = ps

    def realised(connectivity: float) -> tuple[bool, ...]:
        reachable = {0} | {p for p in range(n_patches) if rng.random() < connectivity}
        return tuple(bool(suitable[z] & reachable) for z in grid)

    before = realised(connectivity_before)
    after = realised(connectivity_after)
    m_before = sum(before) / len(before)
    m_after = sum(after) / len(after)
    return {
        "measure_before": m_before,
        "measure_after": m_after,
        "components_before": n_components(before),
        "components_after": n_components(after),
        "contracted": m_after < m_before,
        "fragmented_or_contracted": (m_after < m_before) or (n_components(after) > n_components(before)),
    }
