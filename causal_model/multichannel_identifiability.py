"""Identification geometry for positive multiplicative chains.

For a declared k-channel product

    W = prod_j F_j,

net-only observation fixes one scalar product but leaves a (k-1)-dimensional
multiplicative gauge orbit.  In log coordinates the orbit is the affine
hyperplane

    sum_j log(F_j) = log(W).

If r independent channel values (or channel ratios, in a before/after analysis)
are directly anchored, each independent anchor removes one free coordinate.
The residual unidentified dimension is therefore

    k - 1 - r,

until r = k-1, at which point the final channel is recovered from the product.

This is a structural channel-anchor result.  It is distinct from the 0/1/2
*calibration-anchor* ladder in ``calibration_transport_family.py``, which asks
whether a proxy conversion q transports between two regimes.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import prod
from typing import Iterable, Literal, Sequence


IdentificationState = Literal["non_identified", "partially_identified", "point_identified"]


@dataclass(frozen=True)
class ChannelAnchorDimension:
    """Residual equivalence dimension for a k-channel multiplicative chain."""

    channels: int
    independent_anchors: int
    residual_dimension: int
    identification: IdentificationState



def _validate_channels(channels: int) -> int:
    k = int(channels)
    if k < 2:
        raise ValueError("channels must be at least 2")
    return k



def residual_equivalence_dimension(*, channels: int, independent_anchors: int = 0) -> ChannelAnchorDimension:
    """Return the dimension left unidentified by net-only data plus r anchors.

    ``independent_anchors`` counts directly observed channel coordinates beyond
    the single product constraint.  At most ``k-1`` independent anchors are
    needed because the final coordinate is then determined by the product.
    """

    k = _validate_channels(channels)
    r = int(independent_anchors)
    if r < 0 or r > k - 1:
        raise ValueError("independent_anchors must satisfy 0 <= r <= channels-1")
    dimension = k - 1 - r
    if dimension == 0:
        state: IdentificationState = "point_identified"
    elif r == 0:
        state = "non_identified"
    else:
        state = "partially_identified"
    return ChannelAnchorDimension(
        channels=k,
        independent_anchors=r,
        residual_dimension=dimension,
        identification=state,
    )



def log_gauge_basis(channels: int) -> tuple[tuple[float, ...], ...]:
    """Return a basis for multiplicative reallocations preserving the product.

    In log coordinates, product-preserving perturbations satisfy ``sum d_j=0``.
    A convenient basis is ``e_j - e_k`` for j=1,...,k-1.
    """

    k = _validate_channels(channels)
    basis: list[tuple[float, ...]] = []
    for j in range(k - 1):
        row = [0.0] * k
        row[j] = 1.0
        row[-1] = -1.0
        basis.append(tuple(row))
    return tuple(basis)



def residual_product(*, net_product: float, anchored_values: Iterable[float]) -> float:
    """Return the product that must be allocated among unanchored channels."""

    total = float(net_product)
    if total <= 0.0:
        raise ValueError("net_product must be strictly positive")
    anchors = [float(value) for value in anchored_values]
    if any(value <= 0.0 for value in anchors):
        raise ValueError("anchored_values must be strictly positive")
    denominator = prod(anchors) if anchors else 1.0
    return total / denominator



def reconstruct_final_channel(*, net_product: float, anchored_values: Sequence[float], channels: int) -> float:
    """Point-identify the final channel when exactly k-1 channels are anchored."""

    k = _validate_channels(channels)
    if len(anchored_values) != k - 1:
        raise ValueError("exactly channels-1 anchored values are required")
    return residual_product(net_product=net_product, anchored_values=anchored_values)



def channel_ratio_dimension(*, channels: int, observed_channel_ratios: int = 0) -> ChannelAnchorDimension:
    """Before/after corollary for ``rho_W = prod_j rho_j``.

    Each directly observed independent channel ratio removes one degree of
    freedom from the k-1 dimensional ratio-equivalence set.
    """

    return residual_equivalence_dimension(
        channels=channels,
        independent_anchors=observed_channel_ratios,
    )
