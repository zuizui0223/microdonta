"""Partial identification under bounded regime-specific proxy calibration drift.

This module sits between the stable-calibration result (N3) and the
unconstrained-drift impossibility result (N4).

Let total performance and a proxy of one positive channel be

    W_i = F_i E_i,
    X_i = q_i F_i,

and define ``kappa = q_1 / q_0``.  The stable-proxy estimate of the
complementary-channel ratio is

    rho_E_hat = (W_1/W_0) / (X_1/X_0).

If calibration drift is bounded by

    kappa in [1-delta, 1+delta],  0 <= delta < 1,

then

    rho_E in [rho_E_hat(1-delta), rho_E_hat(1+delta)].

The interval's multiplicative width is ``(1+delta)/(1-delta)``.  The proxied
channel has the reciprocal interval

    rho_F in [rho_X/(1+delta), rho_X/(1-delta)].

The functions below provide deterministic calculations and design diagnostics.
They do not estimate ``delta`` from data and do not turn an assumed bound into
empirical calibration evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Literal


ChannelName = Literal["fecundity", "establishment"]
Direction = Literal["decrease", "increase", "ambiguous"]
DriftPlacement = Literal["multiplicative", "inverse"]


@dataclass(frozen=True)
class IdentifiedRatioInterval:
    """One partially identified before/after channel ratio."""

    point_under_stability: float
    lower: float
    upper: float
    multiplicative_width: float
    direction_at_declared_bound: Direction
    breakdown_delta: float
    breakdown_censored_at_one: bool
    calibration_placement: DriftPlacement

    def contains(self, value: float, *, tolerance: float = 1e-12) -> bool:
        """Return whether a positive latent ratio lies inside the interval."""
        if value <= 0:
            return False
        return self.lower - tolerance <= value <= self.upper + tolerance

    @property
    def excludes_one(self) -> bool:
        """Whether the declared drift bound sign-identifies the change."""
        return self.upper < 1.0 or self.lower > 1.0


@dataclass(frozen=True)
class BoundedProxyDriftResult:
    """Joint identified set for both channels under a bounded calibration ratio."""

    proxy_channel: ChannelName
    delta: float
    calibration_ratio_lower: float
    calibration_ratio_upper: float
    net_ratio: float
    proxy_ratio: float
    fecundity: IdentifiedRatioInterval
    establishment: IdentifiedRatioInterval

    def interval_for(self, channel: ChannelName) -> IdentifiedRatioInterval:
        if channel == "fecundity":
            return self.fecundity
        if channel == "establishment":
            return self.establishment
        raise ValueError(f"unknown channel: {channel}")


@dataclass(frozen=True)
class BoundedDriftDesignRule:
    """Operational interpretation of one identified interval."""

    target_channel: ChannelName
    status: Literal["sign_identified", "partially_identified_sign_ambiguous"]
    report: str
    next_measurement: str


def _positive(value: float, name: str) -> float:
    result = float(value)
    if result <= 0:
        raise ValueError(f"{name} must be strictly positive")
    return result


def _validate_delta(delta: float) -> float:
    result = float(delta)
    if not 0.0 <= result < 1.0:
        raise ValueError("delta must satisfy 0 <= delta < 1")
    return result


def _direction(lower: float, upper: float, *, tolerance: float) -> Direction:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    if upper < 1.0 - tolerance:
        return "decrease"
    if lower > 1.0 + tolerance:
        return "increase"
    return "ambiguous"


def breakdown_point(
    point_under_stability: float,
    *,
    calibration_placement: DriftPlacement = "multiplicative",
    tolerance: float = 1e-12,
) -> tuple[float, bool]:
    """Return the calibration-drift bound at which a sign conclusion breaks.

    ``calibration_placement='multiplicative'`` applies to the complementary
    channel, whose latent ratio equals ``point_under_stability * kappa``.
    ``'inverse'`` applies to the proxied channel, whose latent ratio equals
    ``point_under_stability / kappa``.

    The returned value is capped at one because the declared drift family requires
    ``delta < 1``.  The Boolean is true when the uncapped breakdown lies at or
    beyond that admissible limit, meaning the sign survives every allowed
    ``delta < 1``.
    """
    point = _positive(point_under_stability, "point_under_stability")
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    if isclose(point, 1.0, rel_tol=tolerance, abs_tol=tolerance):
        return 0.0, False

    if calibration_placement == "multiplicative":
        raw = 1.0 / point - 1.0 if point < 1.0 else 1.0 - 1.0 / point
    elif calibration_placement == "inverse":
        raw = 1.0 - point if point < 1.0 else point - 1.0
    else:
        raise ValueError(
            f"unknown calibration_placement: {calibration_placement}"
        )

    raw = max(0.0, raw)
    censored = raw >= 1.0
    return min(raw, 1.0), censored


def identified_ratio_interval(
    point_under_stability: float,
    *,
    delta: float,
    calibration_placement: DriftPlacement = "multiplicative",
    tolerance: float = 1e-12,
) -> IdentifiedRatioInterval:
    """Construct an identified interval from a stable-calibration point ratio."""
    point = _positive(point_under_stability, "point_under_stability")
    bound = _validate_delta(delta)

    if calibration_placement == "multiplicative":
        lower = point * (1.0 - bound)
        upper = point * (1.0 + bound)
    elif calibration_placement == "inverse":
        lower = point / (1.0 + bound)
        upper = point / (1.0 - bound)
    else:
        raise ValueError(
            f"unknown calibration_placement: {calibration_placement}"
        )

    breakdown, censored = breakdown_point(
        point,
        calibration_placement=calibration_placement,
        tolerance=tolerance,
    )
    return IdentifiedRatioInterval(
        point_under_stability=point,
        lower=lower,
        upper=upper,
        multiplicative_width=upper / lower,
        direction_at_declared_bound=_direction(
            lower, upper, tolerance=tolerance
        ),
        breakdown_delta=breakdown,
        breakdown_censored_at_one=censored,
        calibration_placement=calibration_placement,
    )


def identify_under_bounded_proxy_drift(
    *,
    net_ratio: float,
    proxy_ratio: float,
    delta: float,
    proxy_channel: ChannelName = "fecundity",
    tolerance: float = 1e-12,
) -> BoundedProxyDriftResult:
    """Partially identify both channel ratios under ``q_1/q_0`` bounds.

    Parameters are before/after ratios rather than raw observations.  For a proxy
    of fecundity, ``proxy_ratio`` is the stable-calibration point estimate of
    ``rho_F`` and ``net_ratio/proxy_ratio`` is the point estimate of ``rho_E``.
    The establishment-proxy case is symmetric.
    """
    rho_w = _positive(net_ratio, "net_ratio")
    rho_x = _positive(proxy_ratio, "proxy_ratio")
    bound = _validate_delta(delta)

    if proxy_channel == "fecundity":
        fecundity_point = rho_x
        establishment_point = rho_w / rho_x
        fecundity_placement: DriftPlacement = "inverse"
        establishment_placement: DriftPlacement = "multiplicative"
    elif proxy_channel == "establishment":
        establishment_point = rho_x
        fecundity_point = rho_w / rho_x
        establishment_placement = "inverse"
        fecundity_placement = "multiplicative"
    else:
        raise ValueError(f"unknown proxy_channel: {proxy_channel}")

    return BoundedProxyDriftResult(
        proxy_channel=proxy_channel,
        delta=bound,
        calibration_ratio_lower=1.0 - bound,
        calibration_ratio_upper=1.0 + bound,
        net_ratio=rho_w,
        proxy_ratio=rho_x,
        fecundity=identified_ratio_interval(
            fecundity_point,
            delta=bound,
            calibration_placement=fecundity_placement,
            tolerance=tolerance,
        ),
        establishment=identified_ratio_interval(
            establishment_point,
            delta=bound,
            calibration_placement=establishment_placement,
            tolerance=tolerance,
        ),
    )


def design_rule_for_interval(
    interval: IdentifiedRatioInterval,
    *,
    target_channel: ChannelName,
) -> BoundedDriftDesignRule:
    """Translate a bounded identified set into a conservative design rule."""
    if interval.excludes_one:
        direction = interval.direction_at_declared_bound
        return BoundedDriftDesignRule(
            target_channel=target_channel,
            status="sign_identified",
            report=(
                f"Report the {target_channel} ratio interval "
                f"[{interval.lower:.6g}, {interval.upper:.6g}], its "
                f"{direction} sign conclusion, and calibration-drift breakdown "
                f"delta*={interval.breakdown_delta:.6g}."
            ),
            next_measurement=(
                "A direct channel assay or tighter calibration remains useful for "
                "precision, but is not required to retain the sign conclusion under "
                "the declared drift bound."
            ),
        )

    return BoundedDriftDesignRule(
        target_channel=target_channel,
        status="partially_identified_sign_ambiguous",
        report=(
            f"Report the {target_channel} ratio interval "
            f"[{interval.lower:.6g}, {interval.upper:.6g}] and do not claim a "
            "directional change because the set includes one."
        ),
        next_measurement=(
            "Measure the target channel directly, estimate the proxy conversion in "
            "both regimes, or justify a tighter calibration-drift bound before making "
            "a sign claim."
        ),
    )
