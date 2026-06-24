"""Exact channel-identifiability results for trait-performance observations.

The central object is a multiplicative decomposition of total trait performance,

    W(z) = F(z) * E(z),

where ``F`` is a local fecundity/survival channel and ``E`` is an
establishment/reachability channel.  The module encodes two algebraic results:

N1 -- Net-performance non-identifiability.
    For any trait-dependent attenuation ``a(z)``, applying it to F or to E gives
    the same post-change W.  Therefore every observation that is a function only
    of W -- including every thresholded viable set and every geometry derived from
    those sets -- cannot identify which channel changed.

N2 -- Conditional channel identification.
    If F and E are separately observed before and after, and the model class
    restricts change to exactly one channel, the pointwise ratios identify the
    changed channel.  Mixed and unchanged cases are explicitly retained rather
    than forced into a single-channel explanation.

The proofs are documented in ``docs/channel_identifiability_theorem.md``.  The
code and tests are finite-grid regression checks of those algebraic statements.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Sequence


Channel = Literal["fecundity", "establishment"]
ChannelConclusion = Literal[
    "fecundity_only",
    "establishment_only",
    "mixed_or_unidentified",
    "unchanged",
]


@dataclass(frozen=True)
class VitalRateState:
    """Positive local fecundity/survival and establishment channels on one trait grid."""

    grid: tuple[float, ...]
    fecundity: tuple[float, ...]
    establishment: tuple[float, ...]

    def __post_init__(self) -> None:
        n = len(self.grid)
        if n < 1 or len(self.fecundity) != n or len(self.establishment) != n:
            raise ValueError("grid, fecundity, and establishment must share a nonzero length")
        if any(right <= left for left, right in zip(self.grid, self.grid[1:])):
            raise ValueError("grid must be strictly increasing")
        if any(value <= 0 for value in self.fecundity + self.establishment):
            raise ValueError("vital-rate channels must be strictly positive")

    @property
    def net_performance(self) -> tuple[float, ...]:
        return tuple(f * e for f, e in zip(self.fecundity, self.establishment))

    def viable_mask(self, threshold: float = 1.0) -> tuple[bool, ...]:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        return tuple(value >= threshold for value in self.net_performance)


@dataclass(frozen=True)
class SupportGeometry:
    """Geometry of a thresholded viable set on an ordered one-dimensional grid."""

    lower_edge: float | None
    upper_edge: float | None
    breadth: float
    n_components: int


@dataclass(frozen=True)
class ChannelSymmetryResult:
    """Two physically distinct changes with identical net-performance observations."""

    attenuation: tuple[float, ...]
    fecundity_loss: VitalRateState
    establishment_loss: VitalRateState
    net_performance_equal: bool
    all_threshold_supports_equal: bool


@dataclass(frozen=True)
class ChannelResolvedResult:
    """Result of the conditional single-channel identification rule."""

    conclusion: ChannelConclusion
    fecundity_ratio: tuple[float, ...]
    establishment_ratio: tuple[float, ...]


def _validate_attenuation(state: VitalRateState, attenuation: Sequence[float]) -> tuple[float, ...]:
    values = tuple(float(value) for value in attenuation)
    if len(values) != len(state.grid):
        raise ValueError("attenuation must share the trait-grid length")
    if any(value <= 0 for value in values):
        raise ValueError("attenuation must be strictly positive")
    return values


def apply_multiplicative_change(
    state: VitalRateState,
    attenuation: Sequence[float],
    *,
    channel: Channel,
) -> VitalRateState:
    """Apply a trait-dependent multiplicative change to exactly one channel.

    Values in ``attenuation`` may be below one (loss), equal to one (no change),
    or above one (gain). The non-identifiability theorem requires only positivity;
    an ecological loss is the special case ``0 < a(z) <= 1``.
    """
    values = _validate_attenuation(state, attenuation)
    if channel == "fecundity":
        return VitalRateState(
            grid=state.grid,
            fecundity=tuple(a * f for a, f in zip(values, state.fecundity)),
            establishment=state.establishment,
        )
    if channel == "establishment":
        return VitalRateState(
            grid=state.grid,
            fecundity=state.fecundity,
            establishment=tuple(a * e for a, e in zip(values, state.establishment)),
        )
    raise ValueError(f"unknown channel: {channel}")


def support_geometry(state: VitalRateState, threshold: float = 1.0) -> SupportGeometry:
    """Return lower edge, upper edge, breadth, and connected components of ``W >= t``."""
    mask = state.viable_mask(threshold)
    values = [z for z, viable in zip(state.grid, mask) if viable]
    components = 0
    previous = False
    for viable in mask:
        if viable and not previous:
            components += 1
        previous = viable
    if not values:
        return SupportGeometry(None, None, 0.0, 0)
    return SupportGeometry(
        lower_edge=min(values),
        upper_edge=max(values),
        breadth=max(values) - min(values),
        n_components=components,
    )


def all_threshold_supports_equal(
    left: VitalRateState,
    right: VitalRateState,
    thresholds: Iterable[float],
) -> bool:
    """Check equality of thresholded support sets for a supplied threshold family."""
    if left.grid != right.grid:
        return False
    return all(left.viable_mask(threshold) == right.viable_mask(threshold) for threshold in thresholds)


def construct_channel_loss_symmetry(
    baseline: VitalRateState,
    attenuation: Sequence[float],
    *,
    thresholds: Iterable[float] = (0.25, 0.5, 1.0, 1.5, 2.0),
) -> ChannelSymmetryResult:
    """Construct the exact observational equivalence in theorem N1.

    The two post-change states differ in their causal channel:

    ``F_loss = (aF, E)`` and ``E_loss = (F, aE)``.

    Both have net performance ``aFE``. Consequently every thresholded viable
    support is equal, and so is any one-dimensional geometry computed from it.
    """
    values = _validate_attenuation(baseline, attenuation)
    fecundity_loss = apply_multiplicative_change(baseline, values, channel="fecundity")
    establishment_loss = apply_multiplicative_change(baseline, values, channel="establishment")
    net_equal = fecundity_loss.net_performance == establishment_loss.net_performance
    thresholds = tuple(thresholds)
    supports_equal = all_threshold_supports_equal(fecundity_loss, establishment_loss, thresholds)
    return ChannelSymmetryResult(
        attenuation=values,
        fecundity_loss=fecundity_loss,
        establishment_loss=establishment_loss,
        net_performance_equal=net_equal,
        all_threshold_supports_equal=supports_equal,
    )


def _ratio(after: Sequence[float], before: Sequence[float]) -> tuple[float, ...]:
    return tuple(a / b for a, b in zip(after, before))


def _changed(ratios: Sequence[float], tolerance: float) -> bool:
    return any(abs(value - 1.0) > tolerance for value in ratios)


def identify_from_channel_resolved_rates(
    before: VitalRateState,
    after: VitalRateState,
    *,
    tolerance: float = 1e-10,
) -> ChannelResolvedResult:
    """Identify an exclusive changed channel from separately observed vital rates.

    This is the positive theorem's decision rule. It is conditional on comparing
    the same trait grid and on a model class where an exclusive-channel conclusion
    is scientifically meaningful. When both channels changed, the result remains
    ``mixed_or_unidentified`` rather than inventing an exclusive cause.
    """
    if before.grid != after.grid:
        raise ValueError("before and after states must share the same trait grid")
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    fecundity_ratio = _ratio(after.fecundity, before.fecundity)
    establishment_ratio = _ratio(after.establishment, before.establishment)
    fecundity_changed = _changed(fecundity_ratio, tolerance)
    establishment_changed = _changed(establishment_ratio, tolerance)
    if fecundity_changed and not establishment_changed:
        conclusion: ChannelConclusion = "fecundity_only"
    elif establishment_changed and not fecundity_changed:
        conclusion = "establishment_only"
    elif fecundity_changed and establishment_changed:
        conclusion = "mixed_or_unidentified"
    else:
        conclusion = "unchanged"
    return ChannelResolvedResult(
        conclusion=conclusion,
        fecundity_ratio=fecundity_ratio,
        establishment_ratio=establishment_ratio,
    )
