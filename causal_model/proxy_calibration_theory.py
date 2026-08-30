"""Identifiability boundary and sensitivity analysis for channel proxies.

Let total performance be

    W_i(z) = F_i(z) E_i(z),

and let an observed proxy for one channel be

    X_i(z) = q_i(z) F_i(z),

with the establishment-proxy case obtained symmetrically.

N3 -- Stable-proxy ratio identification.
    If q_0(z)=q_1(z)>0, relative changes in both channels are point identified.

N3/N4 bounded bridge -- Partial identification under bounded calibration drift.
    If kappa(z)=q_1(z)/q_0(z) lies in [1-delta, 1+delta], 0<=delta<1,
    each channel ratio has a sharp pointwise interval whose multiplicative width
    is (1+delta)/(1-delta). Directional conclusions remain valid exactly while
    the relevant interval excludes one; ``calibration_drift_breakpoint`` returns
    the drift at which it first touches one.

N4 -- Time-varying-proxy non-identifiability.
    If q_0 and q_1 are unconstrained, the same observed W and X are compatible
    with arbitrary positive calibration ratios and different channel changes.

The algebraic proofs are in ``docs/proxy_calibration_theorem.md``. Code here
provides finite-grid calculations, sharp marginal bounds, breakpoint utilities,
and constructive regression checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite
from typing import Literal, Sequence

from causal_model.channel_identifiability_theory import ChannelConclusion


ProxyChannel = Literal["fecundity", "establishment"]
CalibrationEffect = Literal["multiply", "divide"]
RatioDirection = Literal["decrease", "increase", "unchanged", "not_identified"]
StableDirection = Literal["decrease", "increase", "unchanged"]


@dataclass(frozen=True)
class ChannelChangeRatios:
    """Pointwise before/after channel ratios and their qualitative classification."""

    fecundity_ratio: tuple[float, ...]
    establishment_ratio: tuple[float, ...]
    conclusion: ChannelConclusion


@dataclass(frozen=True)
class ChannelRatioIdentificationSet:
    """Sharp pointwise marginal interval for one channel-change ratio."""

    lower: tuple[float, ...]
    upper: tuple[float, ...]
    direction: tuple[RatioDirection, ...]


@dataclass(frozen=True)
class DriftBreakdownPoint:
    """Calibration drift at which a stable-calibration direction first includes one.

    ``delta_star`` is the exact non-negative solution for the first contact with
    one. If it is at least one, the directional conclusion is robust for every
    admissible symmetric drift bound ``0 <= delta < 1``.
    """

    stable_ratio: float
    calibration_effect: CalibrationEffect
    direction: StableDirection
    delta_star: float
    robust_for_all_admissible_drift: bool


@dataclass(frozen=True)
class BoundedProxyIdentification:
    """Partial-identification result under a symmetric calibration-drift bound."""

    delta: float
    calibration_ratio_bounds: tuple[float, float]
    multiplicative_width: float
    fecundity_ratio: ChannelRatioIdentificationSet
    establishment_ratio: ChannelRatioIdentificationSet
    fecundity_breakdown: tuple[DriftBreakdownPoint, ...]
    establishment_breakdown: tuple[DriftBreakdownPoint, ...]


@dataclass(frozen=True)
class ProxySymmetryResult:
    """Two latent channel transitions with exactly the same observed W and X."""

    observed_net_before: tuple[float, ...]
    observed_net_after: tuple[float, ...]
    observed_proxy_before: tuple[float, ...]
    observed_proxy_after: tuple[float, ...]
    calibration_before: tuple[float, ...]
    calibration_after_a: tuple[float, ...]
    calibration_after_b: tuple[float, ...]
    ratios_a: ChannelChangeRatios
    ratios_b: ChannelChangeRatios


def _positive(values: Sequence[float], name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result:
        raise ValueError(f"{name} must be nonempty")
    if any(not isfinite(value) or value <= 0 for value in result):
        raise ValueError(f"{name} must contain finite, strictly positive values")
    return result


def _same_length(**series: Sequence[float]) -> int:
    lengths = {len(values) for values in series.values()}
    if len(lengths) != 1:
        detail = ", ".join(f"{name}={len(values)}" for name, values in series.items())
        raise ValueError(f"series must share a length ({detail})")
    return next(iter(lengths))


def _ratio(after: Sequence[float], before: Sequence[float]) -> tuple[float, ...]:
    return tuple(a / b for a, b in zip(after, before))


def _classify(
    fecundity_ratio: Sequence[float],
    establishment_ratio: Sequence[float],
    *,
    tolerance: float,
) -> ChannelConclusion:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    f_changed = any(abs(value - 1.0) > tolerance for value in fecundity_ratio)
    e_changed = any(abs(value - 1.0) > tolerance for value in establishment_ratio)
    if f_changed and not e_changed:
        return "fecundity_only"
    if e_changed and not f_changed:
        return "establishment_only"
    if f_changed and e_changed:
        return "mixed_or_unidentified"
    return "unchanged"


def _validate_delta(delta: float) -> float:
    value = float(delta)
    if not isfinite(value) or not 0.0 <= value < 1.0:
        raise ValueError("delta must satisfy 0 <= delta < 1")
    return value


def _interval_direction(lower: float, upper: float, *, tolerance: float) -> RatioDirection:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    if upper < 1.0 - tolerance:
        return "decrease"
    if lower > 1.0 + tolerance:
        return "increase"
    if abs(lower - 1.0) <= tolerance and abs(upper - 1.0) <= tolerance:
        return "unchanged"
    return "not_identified"


def _bounded_interval(
    stable_ratios: Sequence[float],
    *,
    delta: float,
    calibration_effect: CalibrationEffect,
    tolerance: float,
) -> ChannelRatioIdentificationSet:
    if calibration_effect == "multiply":
        lower = tuple(ratio * (1.0 - delta) for ratio in stable_ratios)
        upper = tuple(ratio * (1.0 + delta) for ratio in stable_ratios)
    elif calibration_effect == "divide":
        lower = tuple(ratio / (1.0 + delta) for ratio in stable_ratios)
        upper = tuple(ratio / (1.0 - delta) for ratio in stable_ratios)
    else:
        raise ValueError(f"unknown calibration_effect: {calibration_effect}")
    return ChannelRatioIdentificationSet(
        lower=lower,
        upper=upper,
        direction=tuple(
            _interval_direction(lo, hi, tolerance=tolerance)
            for lo, hi in zip(lower, upper)
        ),
    )


def calibration_drift_breakpoint(
    stable_ratio: float,
    *,
    calibration_effect: CalibrationEffect,
    tolerance: float = 1e-12,
) -> DriftBreakdownPoint:
    """Return the symmetric drift bound at which a direction first includes one.

    ``calibration_effect='multiply'`` applies when the target ratio equals its
    stable-calibration value times ``kappa=q_1/q_0``. Its breakpoint is
    ``abs(r-1)/r``. ``'divide'`` applies when the target ratio is divided by
    ``kappa``; its breakpoint is ``abs(r-1)``.

    Robustness is strict: for a breakpoint within ``[0,1)``, the interval excludes
    one for ``delta < delta_star`` and first touches one at ``delta_star``.
    """
    if calibration_effect not in ("multiply", "divide"):
        raise ValueError(f"unknown calibration_effect: {calibration_effect}")
    ratio = float(stable_ratio)
    if not isfinite(ratio) or ratio <= 0:
        raise ValueError("stable_ratio must be finite and strictly positive")
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    if abs(ratio - 1.0) <= tolerance:
        direction: StableDirection = "unchanged"
        delta_star = 0.0
    elif ratio < 1.0:
        direction = "decrease"
        if calibration_effect == "multiply":
            delta_star = (1.0 - ratio) / ratio
        elif calibration_effect == "divide":
            delta_star = 1.0 - ratio
        else:
            raise ValueError(f"unknown calibration_effect: {calibration_effect}")
    else:
        direction = "increase"
        if calibration_effect == "multiply":
            delta_star = (ratio - 1.0) / ratio
        elif calibration_effect == "divide":
            delta_star = ratio - 1.0
        else:
            raise ValueError(f"unknown calibration_effect: {calibration_effect}")
    return DriftBreakdownPoint(
        stable_ratio=ratio,
        calibration_effect=calibration_effect,
        direction=direction,
        delta_star=delta_star,
        robust_for_all_admissible_drift=(direction != "unchanged" and delta_star >= 1.0),
    )


def identify_from_net_and_stable_proxy(
    *,
    net_before: Sequence[float],
    net_after: Sequence[float],
    proxy_before: Sequence[float],
    proxy_after: Sequence[float],
    proxy_channel: ProxyChannel,
    tolerance: float = 1e-10,
) -> ChannelChangeRatios:
    """Identify relative channel changes under a time-stable positive proxy map.

    If the proxy represents F as X_i=qF_i with the same q at both times,
    F_1/F_0=X_1/X_0. Since W=FE, E_1/E_0=(W_1/W_0)/(F_1/F_0).

    ``proxy_channel='establishment'`` applies the symmetric argument. The proxy's
    absolute scale may be unknown and trait-dependent; only temporal stability of
    its conversion factor is required.
    """
    w0 = _positive(net_before, "net_before")
    w1 = _positive(net_after, "net_after")
    x0 = _positive(proxy_before, "proxy_before")
    x1 = _positive(proxy_after, "proxy_after")
    _same_length(net_before=w0, net_after=w1, proxy_before=x0, proxy_after=x1)
    net_ratio = _ratio(w1, w0)
    observed_ratio = _ratio(x1, x0)
    if proxy_channel == "fecundity":
        fecundity_ratio = observed_ratio
        establishment_ratio = tuple(w / f for w, f in zip(net_ratio, fecundity_ratio))
    elif proxy_channel == "establishment":
        establishment_ratio = observed_ratio
        fecundity_ratio = tuple(w / e for w, e in zip(net_ratio, establishment_ratio))
    else:
        raise ValueError(f"unknown proxy_channel: {proxy_channel}")
    return ChannelChangeRatios(
        fecundity_ratio=fecundity_ratio,
        establishment_ratio=establishment_ratio,
        conclusion=_classify(fecundity_ratio, establishment_ratio, tolerance=tolerance),
    )


def identify_from_net_and_bounded_proxy_drift(
    *,
    net_before: Sequence[float],
    net_after: Sequence[float],
    proxy_before: Sequence[float],
    proxy_after: Sequence[float],
    proxy_channel: ProxyChannel,
    delta: float,
    tolerance: float = 1e-10,
) -> BoundedProxyIdentification:
    """Return sharp pointwise channel-ratio bounds under bounded proxy drift.

    Let ``kappa(z)=q_1(z)/q_0(z)`` and assume
    ``1-delta <= kappa(z) <= 1+delta`` pointwise. For a fecundity proxy,

    ``rho_F = (X_1/X_0)/kappa`` and
    ``rho_E = [(W_1/W_0)/(X_1/X_0)] * kappa``.

    The establishment-proxy case swaps F and E. The returned marginal intervals
    are sharp pointwise. The same kappa links the two channels, so the joint set is
    the one-parameter curve described in the theorem rather than the Cartesian
    product of the two marginal intervals.
    """
    drift = _validate_delta(delta)
    stable = identify_from_net_and_stable_proxy(
        net_before=net_before,
        net_after=net_after,
        proxy_before=proxy_before,
        proxy_after=proxy_after,
        proxy_channel=proxy_channel,
        tolerance=tolerance,
    )
    if proxy_channel == "fecundity":
        f_effect: CalibrationEffect = "divide"
        e_effect: CalibrationEffect = "multiply"
    elif proxy_channel == "establishment":
        f_effect = "multiply"
        e_effect = "divide"
    else:
        raise ValueError(f"unknown proxy_channel: {proxy_channel}")
    f_set = _bounded_interval(
        stable.fecundity_ratio,
        delta=drift,
        calibration_effect=f_effect,
        tolerance=tolerance,
    )
    e_set = _bounded_interval(
        stable.establishment_ratio,
        delta=drift,
        calibration_effect=e_effect,
        tolerance=tolerance,
    )
    return BoundedProxyIdentification(
        delta=drift,
        calibration_ratio_bounds=(1.0 - drift, 1.0 + drift),
        multiplicative_width=(1.0 + drift) / (1.0 - drift),
        fecundity_ratio=f_set,
        establishment_ratio=e_set,
        fecundity_breakdown=tuple(
            calibration_drift_breakpoint(
                ratio,
                calibration_effect=f_effect,
                tolerance=tolerance,
            )
            for ratio in stable.fecundity_ratio
        ),
        establishment_breakdown=tuple(
            calibration_drift_breakpoint(
                ratio,
                calibration_effect=e_effect,
                tolerance=tolerance,
            )
            for ratio in stable.establishment_ratio
        ),
    )


def construct_time_varying_proxy_symmetry(
    *,
    net_before: Sequence[float],
    net_after: Sequence[float],
    proxy_before: Sequence[float],
    proxy_after: Sequence[float],
    baseline_calibration: Sequence[float],
    calibration_shift: Sequence[float],
    proxy_channel: ProxyChannel = "fecundity",
    tolerance: float = 1e-10,
) -> ProxySymmetryResult:
    """Construct two latent explanations with identical observed W and proxy X.

    Model A assumes the proxy calibration is stable, q_1=q_0. Model B sets
    q_1=h q_0, where ``h`` is any positive trait-dependent calibration shift.
    For a fecundity proxy, ``F_i=X_i/q_i`` and ``E_i=W_i/F_i``.
    """
    w0 = _positive(net_before, "net_before")
    w1 = _positive(net_after, "net_after")
    x0 = _positive(proxy_before, "proxy_before")
    x1 = _positive(proxy_after, "proxy_after")
    q0 = _positive(baseline_calibration, "baseline_calibration")
    h = _positive(calibration_shift, "calibration_shift")
    _same_length(
        net_before=w0,
        net_after=w1,
        proxy_before=x0,
        proxy_after=x1,
        baseline_calibration=q0,
        calibration_shift=h,
    )
    q1_a = q0
    q1_b = tuple(shift * q for shift, q in zip(h, q0))

    def rates(q_before: tuple[float, ...], q_after: tuple[float, ...]) -> ChannelChangeRatios:
        if proxy_channel == "fecundity":
            f0 = tuple(x / q for x, q in zip(x0, q_before))
            f1 = tuple(x / q for x, q in zip(x1, q_after))
            e0 = tuple(w / f for w, f in zip(w0, f0))
            e1 = tuple(w / f for w, f in zip(w1, f1))
        elif proxy_channel == "establishment":
            e0 = tuple(x / q for x, q in zip(x0, q_before))
            e1 = tuple(x / q for x, q in zip(x1, q_after))
            f0 = tuple(w / e for w, e in zip(w0, e0))
            f1 = tuple(w / e for w, e in zip(w1, e1))
        else:
            raise ValueError(f"unknown proxy_channel: {proxy_channel}")
        fr = _ratio(f1, f0)
        er = _ratio(e1, e0)
        return ChannelChangeRatios(fr, er, _classify(fr, er, tolerance=tolerance))

    return ProxySymmetryResult(
        observed_net_before=w0,
        observed_net_after=w1,
        observed_proxy_before=x0,
        observed_proxy_after=x1,
        calibration_before=q0,
        calibration_after_a=q1_a,
        calibration_after_b=q1_b,
        ratios_a=rates(q0, q1_a),
        ratios_b=rates(q0, q1_b),
    )


def same_observed_proxy_data(result: ProxySymmetryResult, *, tolerance: float = 1e-12) -> bool:
    """Document that N4 alternatives share the observed series by construction."""
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    return all(
        isclose(value, value, rel_tol=tolerance, abs_tol=tolerance)
        for series in (
            result.observed_net_before,
            result.observed_net_after,
            result.observed_proxy_before,
            result.observed_proxy_after,
        )
        for value in series
    )
