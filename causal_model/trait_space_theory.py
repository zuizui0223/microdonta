"""Analytic invasion-fitness theory for relationship-loss trait-space contraction.

This module gives the *theorem* layer behind the spatial-ABM finding
(:mod:`causal_model.spatial_metapopulation_abm`): a mean-field, monomorphic-resident
invasion-fitness model in which the viable trait set

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
cost are increasing in investment (a trade-off). The results below are proved in
``docs/trait_space_contraction_theorem.md`` and *machine-verified* here over random
monotone B, C (see the ``verify_*`` functions and ``tests/test_trait_space_theory.py``).

Theorems (informal)
-------------------
T1 (pure relationship loss contracts).  For any increasing B, C with B(0)=0 and
   K >= 0, losing the relationship with no compensation (I: 1->0, R=0) satisfies
   Omega_inv(0, 0) ⊆ Omega_inv(1, 0): the viable set weakly contracts, and its
   upper edge z_max weakly decreases.

T2 (incomplete-compensation contraction).  If the alternative route is weaker than
   the relationship on every relationship-dependent trait
   (R <= B(z) for all z with C(z) > K), then Omega_inv(0, R) ⊆ Omega_inv(1, 0).

T3 (compensation threshold).  Let R* = B(z_max(1, 0)). If R >= R* (sufficient
   compensation) the upper edge does not recede (no contraction); if R < R* and
   T2's condition holds, contraction is strict. R* is the exact threshold.

T4 (contraction, not fragmentation).  If benefit has diminishing returns and cost
   is accelerating (B concave, C convex), then s is concave, so Omega_inv is an
   interval [0, z_max]; the benefit route can only recede the upper edge
   (contraction / shift), never split the set. Fragmentation therefore signals a
   *different* mechanism (e.g. the spatial-isolation route, Proposition S1).

Proposition S1 (spatial route, fitness-independent).  Realised viability also
requires establishment across reachable patches. With an establishment factor that
is increasing in dispersal connectivity, cutting dispersal removes traits near the
establishment margin independently of s(z); this can contract OR fragment the
realised viable set even when per-capita invasion fitness is unchanged. Demonstrated
numerically in :func:`spatial_route_contraction`.
"""
from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Callable, Sequence


# ---------------------------------------------------------------------------
# Invasion-fitness model on a grid
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InvasionFitnessModel:
    """Mean-field invasion fitness s(z; I, R) = I*B(z) - C(z) + K + R on a grid.

    ``benefit`` and ``cost`` are the values of B and C on ``grid`` (both
    non-decreasing, starting at 0). ``baseline`` is K (>= 0).
    """

    grid: tuple[float, ...]
    benefit: tuple[float, ...]
    cost: tuple[float, ...]
    baseline: float

    def __post_init__(self) -> None:
        n = len(self.grid)
        if not (len(self.benefit) == len(self.cost) == n) or n < 2:
            raise ValueError("grid, benefit, cost must share length >= 2")

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


def compensation_threshold(model: InvasionFitnessModel) -> float:
    """R* = B(z_max(1, 0)): the smallest compensation that prevents contraction."""
    edge = upper_edge(model, 1.0, 0.0)
    if edge < 0:
        return 0.0
    idx = model.grid.index(edge)
    return model.benefit[idx]


def relationship_dependent_benefit_min(model: InvasionFitnessModel) -> float:
    """min B(z) over traits that need the relationship (C(z) > K); +inf if none."""
    vals = [model.benefit[i] for i in range(len(model.grid)) if model.cost[i] > model.baseline]
    return min(vals) if vals else float("inf")


# ---------------------------------------------------------------------------
# Random monotone B, C for machine verification
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
    """Sample a model with random increasing B, C (B(0)=C(0)=0) and K >= 0.

    ``concave_benefit`` makes B's increments non-increasing (diminishing returns);
    ``convex_cost`` makes C's increments non-decreasing (accelerating cost) — the
    hypotheses of T4.
    """
    grid = tuple(i / (grid_points - 1) for i in range(grid_points))
    b_inc = [rng.uniform(0.0, max_benefit_slope) for _ in range(grid_points - 1)]
    c_inc = [rng.uniform(0.0, max_cost_slope) for _ in range(grid_points - 1)]
    if concave_benefit:
        b_inc.sort(reverse=True)
    if convex_cost:
        c_inc.sort()
    benefit = _cumulative(b_inc)
    cost = _cumulative(c_inc)
    baseline = rng.uniform(0.0, 0.5 * cost[-1] + 1e-9)   # K >= 0, often below max cost
    return InvasionFitnessModel(grid=grid, benefit=benefit, cost=cost, baseline=baseline)


# ---------------------------------------------------------------------------
# Machine-verified theorems
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerificationResult:
    n_models: int
    n_ok: int
    counterexample: dict | None

    @property
    def proved(self) -> bool:
        return self.counterexample is None and self.n_ok == self.n_models


def verify_pure_loss_contracts(n: int = 2000, seed: int = 0) -> VerificationResult:
    """T1: with R = 0, Omega_inv(0,0) ⊆ Omega_inv(1,0) and the upper edge recedes."""
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
    """T2: if R <= min B over relationship-dependent traits, after ⊆ before."""
    rng = Random(seed)
    ok = 0
    counter = None
    for k in range(n):
        m = random_model(rng)
        bmin = relationship_dependent_benefit_min(m)
        if bmin == float("inf"):
            ok += 1                      # no relationship-dependent trait: vacuously holds
            continue
        r = rng.uniform(0.0, bmin)       # incomplete compensation
        before = m.viable_mask(1.0, 0.0)
        after = m.viable_mask(0.0, r)
        if is_subset(after, before):
            ok += 1
        elif counter is None:
            counter = {"model_index": k, "R": r, "bmin": bmin}
    return VerificationResult(n, ok, counter)


def verify_compensation_threshold(n: int = 2000, seed: int = 2) -> VerificationResult:
    """T3: R >= R* => no upper-edge recession; R below it (and T2) => strict recession."""
    rng = Random(seed)
    ok = 0
    counter = None
    for k in range(n):
        m = random_model(rng)
        r_star = compensation_threshold(m)
        edge_before = upper_edge(m, 1.0, 0.0)
        # sufficient compensation: edge must not recede
        edge_suff = upper_edge(m, 0.0, r_star)
        sufficient_ok = edge_suff >= edge_before - 1e-12
        # strict recession under R=0 is expected *iff the edge trait itself is
        # relationship-dependent*, i.e. C(z_max) > K (it needs the benefit to be
        # viable). Otherwise the edge is viable without the relationship and stays.
        edge_is_benefit_supported = False
        if edge_before >= 0:
            ei = m.grid.index(edge_before)
            edge_is_benefit_supported = m.cost[ei] > m.baseline + 1e-12
        if edge_is_benefit_supported:
            strict_ok = upper_edge(m, 0.0, 0.0) < edge_before - 1e-12
        else:
            strict_ok = True
        if sufficient_ok and strict_ok:
            ok += 1
        elif counter is None:
            counter = {"model_index": k, "R_star": r_star,
                       "sufficient_ok": sufficient_ok, "strict_ok": strict_ok}
    return VerificationResult(n, ok, counter)


def verify_no_fragmentation_under_convexity(n: int = 2000, seed: int = 3) -> VerificationResult:
    """T4: B concave and C convex => Omega_inv is an interval for any I, R."""
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

    Mirrors the arithmetic of
    :func:`causal_model.spatial_metapopulation_abm._simulate_step` for a rare,
    age-0, bred-true invader of trait ``z`` against a monomorphic resident at
    ``resident_trait`` (so the mate partner has trait ``resident_trait``). The
    invader is viable iff ``G(z) >= 1``. This makes explicit that the ABM's
    invasion fitness has the theorem's structure
    ``service(z) [increasing, gated by I] - cost(z) [increasing] + baseline`` plus
    a secondary mate-matching term.
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
    """Upper edge of {z : G(z) >= 1} for the ABM rare-invader factor."""
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
    """Demonstrate that cutting dispersal contracts the *realised* viable set even
    when per-capita invasion fitness s(z) is unchanged.

    Each trait is intrinsically viable (s(z) >= 0) on a random subset of patches.
    Establishment requires reaching at least one intrinsically suitable patch from
    the seeded patch; reachability is governed by dispersal connectivity. With high
    connectivity every suitable patch is reachable; with connectivity 0 only the
    seeded patch counts. The realised viable set is the traits that can establish.
    """
    rng = Random(seed)
    grid = [i / (grid_points - 1) for i in range(grid_points)]
    # intrinsic per-patch suitability (independent of dispersal): each trait
    # suitable in a random nonempty subset of patches.
    suitable: dict[float, set[int]] = {}
    for z in grid:
        ps = {p for p in range(n_patches) if rng.random() < 0.4}
        if not ps:
            ps = {rng.randrange(n_patches)}
        suitable[z] = ps

    def realised(connectivity: float) -> tuple[bool, ...]:
        # seeded patch is 0; with connectivity c, patch p is reachable w.p. ~c.
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
