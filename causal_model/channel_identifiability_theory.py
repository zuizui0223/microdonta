"""Exact channel-identifiability results for trait-performance observations.

The central object is a multiplicative decomposition of total trait performance,

    W(z) = F(z) * E(z),

where ``F`` is a local fecundity/survival channel and ``E`` is an
establishment/reachability channel. The module encodes two algebraic results:

N1 -- Net-performance non-identifiability.
    For any trait-dependent attenuation ``a(z)``, applying it to F or to E gives
    the same post-change W. Therefore every observation that is a function only
    of W -- including every thresholded viable set and every geometry derived from
    those sets -- cannot identify which channel changed.

N2 -- One-channel-plus-net identification.
    Given W and either positive factor F or E, the other factor is uniquely
    reconstructed by division. Thus W observed before/after plus one separately
    observed channel before/after identifies both channel changes; mixed and
    unchanged cases remain explicit rather than forced into a single-channel
    explanation.

The proofs are documented in ``docs/channel_identifiability_theorem.md``. The
code and tests are finite-grid regression checks of those algebraic statements.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose
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

    def viable_mask(self, threshold: float = 1.0, *, tolerance: float = 1e-12) -> tuple[bool, ...]:
        """Threshold net performance with a numerical boundary tolerance.

        In exact arithmetic the two channel-loss constructions in theorem N1 are
        identical. Floating point multiplication may differ in the final bit, so
        values numerically indistinguishable from a threshold are treated as lying
        on that threshold.
        """
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        if tolerance < 0:
            raise ValueError("tolerance must be non-negative")
        return tuple(
            value > threshold or isclose(value, threshold, rel_tol=tolerance, abs_tol=tolerance)
            for value in self.net_performance
        )


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
    """Channel-change classification after the two factors have been resolved."""

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


def _positive_values(values: Sequence[float], *, name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result:
        raise ValueError(f"{name} must be nonempty")
    if any(value <= 0 for value in result):
        raise ValueError(f"{name} must be strictly positive")
    return result


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


def net_performance_equal(
    left: VitalRateState,
    right: VitalRateState,
    *,
    tolerance: float = 1e-12,
) -> bool:
    """Numerically compare net performance, respecting the exact algebraic symmetry."""
    if left.grid != right.grid:
        return False
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    return all(
        isclose(a, b, rel_tol=tolerance, abs_tol=tolerance)
        for a, b in zip(left.net_performance, right.net_performance)
    )


def support_geometry(
    state: VitalRateState,
    threshold: float = 1.0,
    *,
    tolerance: float = 1e-12,
) -> SupportGeometry:
    """Return lower edge, upper edge, breadth, and connected components of ``W >= t``."""
    mask = state.viable_mask(threshold, tolerance=tolerance)
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
    *,
    tolerance: float = 1e-12,
) -> bool:
    """Check equality of thresholded support sets for a supplied threshold family."""
    if left.grid != right.grid:
        return False
    return all(
        left.viable_mask(threshold, tolerance=tolerance)
        == right.viable_mask(threshold, tolerance=tolerance)
        for threshold in thresholds
    )


def construct_channel_loss_symmetry(
    baseline: VitalRateState,
    attenuation: Sequence[float],
    *,
    thresholds: Iterable[float] = (0.25, 0.5, 1.0, 1.5, 2.0),
    tolerance: float = 1e-12,
) -> ChannelSymmetryResult:
    """Construct the exact observational equivalence in theorem N1.

    The two post-change states differ in their causal channel:

    ``F_loss = (aF, E)`` and ``E_loss = (F, aE)``.

    Both have net performance ``aFE`` in exact arithmetic. Consequently every
    thresholded viable support is equal, and so is any one-dimensional geometry
    computed from it. The finite-precision comparison uses ``tolerance`` only to
    avoid treating multiplication-order roundoff as a mathematical difference.
    """
    values = _validate_attenuation(baseline, attenuation)
    fecundity_loss = apply_multiplicative_change(baseline, values, channel="fecundity")
    establishment_loss = apply_multiplicative_change(baseline, values, channel="establishment")
    thresholds = tuple(thresholds)
    return ChannelSymmetryResult(
        attenuation=values,
        fecundity_loss=fecundity_loss,
        establishment_loss=establishment_loss,
        net_performance_equal=net_performance_equal(
            fecundity_loss, establishment_loss, tolerance=tolerance
        ),
        all_threshold_supports_equal=all_threshold_supports_equal(
            fecundity_loss, establishment_loss, thresholds, tolerance=tolerance
        ),
    )


def reconstruct_from_net_and_one_channel(
    *,
    grid: Sequence[float],
    net_performance: Sequence[float],
    observed_channel_values: Sequence[float],
    observed_channel: Channel,
) -> VitalRateState:
    """Reconstruct both channels from W and one positive observed factor.

    When F is observed, E is uniquely ``W / F``. When E is observed, F is uniquely
    ``W / E``. This is the constructive content of theorem N2.
    """
    grid_values = tuple(float(value) for value in grid)
    net_values = _positive_values(net_performance, name="net_performance")
    observed = _positive_values(observed_channel_values, name="observed_channel_values")
    if not (len(grid_values) == len(net_values) == len(observed)):
        raise ValueError("grid, net_performance, and observed channel must share a length")
    if observed_channel == "fecundity":
        return VitalRateState(
            grid=grid_values,
            fecundity=observed,
            establishment=tuple(w / f for w, f in zip(net_values, observed)),
        )
    if observed_channel == "establishment":
        return VitalRateState(
            grid=grid_values,
            fecundity=tuple(w / e for w, e in zip(net_values, observed)),
            establishment=observed,
        )
    raise ValueError(f"unknown channel: {observed_channel}")


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
    """Classify channel change after both factors are resolved.

    Mixed and unchanged cases remain explicit rather than being forced into a
    single-channel explanation.
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


def identify_from_net_and_one_channel(
    *,
    grid: Sequence[float],
    net_before: Sequence[float],
    net_after: Sequence[float],
    observed_before: Sequence[float],
    observed_after: Sequence[float],
    observed_channel: Channel,
    tolerance: float = 1e-10,
) -> ChannelResolvedResult:
    """Identify channel change from net performance plus one observed channel.

    This is equivalent to separately observing both channels in the positive
    two-factor model, because the missing factor is reconstructed by division.
    No exclusive-change assumption is needed to detect a mixed change; the
    exclusive labels merely describe the reconstructed result.
    """
    before = reconstruct_from_net_and_one_channel(
        grid=grid,
        net_performance=net_before,
        observed_channel_values=observed_before,
        observed_channel=observed_channel,
    )
    after = reconstruct_from_net_and_one_channel(
        grid=grid,
        net_performance=net_after,
        observed_channel_values=observed_after,
        observed_channel=observed_channel,
    )
    return identify_from_channel_resolved_rates(before, after, tolerance=tolerance)
