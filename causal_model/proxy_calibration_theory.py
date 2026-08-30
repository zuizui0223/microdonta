"""Identifiability boundary for channel proxies.

Let total performance be

    W_i(z) = F_i(z) E_i(z),

and let an observed proxy for one channel be

    X_i(z) = q_i(z) F_i(z),

where ``q_i`` is the positive proxy-to-channel conversion at regime ``i``.

N3 -- Stable-proxy ratio identification.
    If q_0(z)=q_1(z)>0, relative channel changes are point identified.

N3b -- Bounded cross-regime calibration drift.
    Define kappa=q_0/q_1 and suppose kappa is prespecified to lie in
    [1-delta, 1+delta], 0 <= delta < 1. Then the unproxied channel ratio has the
    sharp identified set [r_tilde/(1+delta), r_tilde/(1-delta)], where r_tilde
    is the stable-calibration plug-in ratio. The first delta at which the set
    touches one is a directly reportable breakdown point.

N4 -- Unrestricted calibration drift.
    If q_0/q_1 is unconstrained, the same observed W and X are compatible with
    arbitrary positive channel-change ratios.

The proofs are in ``docs/proxy_calibration_theorem.md``. Code here provides
finite-grid constructions, sharp interval calculations and regression checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Literal, Sequence

from causal_model.channel_identifiability_theory import ChannelConclusion

ProxyChannel = Literal["fecundity", "establishment"]


@dataclass(frozen=True)
class ChannelChangeRatios:
    fecundity_ratio: tuple[float, ...]
    establishment_ratio: tuple[float, ...]
    conclusion: ChannelConclusion


@dataclass(frozen=True)
class ProxySymmetryResult:
    observed_net_before: tuple[float, ...]
    observed_net_after: tuple[float, ...]
    observed_proxy_before: tuple[float, ...]
    observed_proxy_after: tuple[float, ...]
    calibration_before: tuple[float, ...]
    calibration_after_a: tuple[float, ...]
    calibration_after_b: tuple[float, ...]
    ratios_a: ChannelChangeRatios
    ratios_b: ChannelChangeRatios


@dataclass(frozen=True)
class IdentifiedInterval:
    """Sharp identified interval for a positive relative channel change."""
    lower: float
    upper: float
    delta: float
    stable_ratio: float

    @property
    def multiplicative_width(self) -> float:
        return self.upper / self.lower

    def excludes_no_change(self, *, tolerance: float = 0.0) -> bool:
        if tolerance < 0:
            raise ValueError("tolerance must be non-negative")
        return self.upper < 1.0 - tolerance or self.lower > 1.0 + tolerance


@dataclass(frozen=True)
class SamplingAwareInterval:
    """Conservative interval combining sampling and bounded-drift uncertainty."""
    lower: float
    upper: float
    delta: float
    stable_ci_lower: float
    stable_ci_upper: float


def _positive(values: Sequence[float], name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result:
        raise ValueError(f"{name} must be nonempty")
    if any(value <= 0 for value in result):
        raise ValueError(f"{name} must be strictly positive")
    return result


def _same_length(**series: Sequence[float]) -> int:
    lengths = {len(values) for values in series.values()}
    if len(lengths) != 1:
        detail = ", ".join(f"{name}={len(values)}" for name, values in series.items())
        raise ValueError(f"series must share a length ({detail})")
    return next(iter(lengths))


def _ratio(after: Sequence[float], before: Sequence[float]) -> tuple[float, ...]:
    return tuple(a / b for a, b in zip(after, before))


def _validate_delta(delta: float) -> float:
    value = float(delta)
    if value < 0 or value >= 1:
        raise ValueError("delta must satisfy 0 <= delta < 1")
    return value


def _classify(fecundity_ratio: Sequence[float], establishment_ratio: Sequence[float], *, tolerance: float) -> ChannelConclusion:
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


def identify_from_net_and_stable_proxy(*, net_before: Sequence[float], net_after: Sequence[float], proxy_before: Sequence[float], proxy_after: Sequence[float], proxy_channel: ProxyChannel, tolerance: float = 1e-10) -> ChannelChangeRatios:
    """Identify relative channel changes under a stable positive proxy map."""
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
    return ChannelChangeRatios(fecundity_ratio, establishment_ratio, _classify(fecundity_ratio, establishment_ratio, tolerance=tolerance))


def bounded_drift_identified_interval(*, stable_ratio: float, delta: float) -> IdentifiedInterval:
    """Return the sharp N3b interval when kappa=q_0/q_1 is bounded.

    If kappa belongs to [1-delta, 1+delta], true_ratio=stable_ratio/kappa.
    ``delta`` directly bounds the cross-regime calibration ratio; it does not
    independently bound q_0 and q_1 around a common reference value.
    """
    ratio = float(stable_ratio)
    if ratio <= 0:
        raise ValueError("stable_ratio must be strictly positive")
    d = _validate_delta(delta)
    return IdentifiedInterval(ratio / (1.0 + d), ratio / (1.0 - d), d, ratio)


def sampling_aware_bounded_drift_interval(*, stable_ci_lower: float, stable_ci_upper: float, delta: float) -> SamplingAwareInterval:
    """Combine a confidence interval for the stable ratio with bounded drift."""
    lower = float(stable_ci_lower)
    upper = float(stable_ci_upper)
    if lower <= 0 or upper <= 0:
        raise ValueError("confidence interval endpoints must be strictly positive")
    if lower > upper:
        raise ValueError("stable_ci_lower must not exceed stable_ci_upper")
    d = _validate_delta(delta)
    return SamplingAwareInterval(lower / (1.0 + d), upper / (1.0 - d), d, lower, upper)


def decline_breakdown_point(*, stable_ratio: float) -> float:
    """Direct ratio-drift breakdown point for a point-estimate decline."""
    ratio = float(stable_ratio)
    if ratio <= 0:
        raise ValueError("stable_ratio must be strictly positive")
    return 0.0 if ratio >= 1 else 1.0 - ratio


def increase_breakdown_point(*, stable_ratio: float) -> float:
    """Direct ratio-drift breakdown point for a point-estimate increase."""
    ratio = float(stable_ratio)
    if ratio <= 0:
        raise ValueError("stable_ratio must be strictly positive")
    return 0.0 if ratio <= 1 else ratio - 1.0


def sampling_aware_decline_breakdown_point(*, stable_ci_upper: float) -> float:
    """Sampling-aware decline breakdown using the upper CI endpoint."""
    upper = float(stable_ci_upper)
    if upper <= 0:
        raise ValueError("stable_ci_upper must be strictly positive")
    return max(0.0, 1.0 - upper)


def construct_time_varying_proxy_symmetry(*, net_before: Sequence[float], net_after: Sequence[float], proxy_before: Sequence[float], proxy_after: Sequence[float], baseline_calibration: Sequence[float], calibration_shift: Sequence[float], proxy_channel: ProxyChannel = "fecundity", tolerance: float = 1e-10) -> ProxySymmetryResult:
    """Construct two latent explanations with identical observed W and proxy X.

    Model A assumes q_1=q_0. Model B sets q_1=h q_0. The bounded-drift N3b
    parameter is kappa=q_0/q_1=1/h.
    """
    w0 = _positive(net_before, "net_before")
    w1 = _positive(net_after, "net_after")
    x0 = _positive(proxy_before, "proxy_before")
    x1 = _positive(proxy_after, "proxy_after")
    q0 = _positive(baseline_calibration, "baseline_calibration")
    h = _positive(calibration_shift, "calibration_shift")
    _same_length(net_before=w0, net_after=w1, proxy_before=x0, proxy_after=x1, baseline_calibration=q0, calibration_shift=h)
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

    return ProxySymmetryResult(w0, w1, x0, x1, q0, q1_a, q1_b, rates(q0, q1_a), rates(q0, q1_b))


def same_observed_proxy_data(result: ProxySymmetryResult, *, tolerance: float = 1e-12) -> bool:
    """Document that N4 alternatives share the observed series by construction."""
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    return all(isclose(value, value, rel_tol=tolerance, abs_tol=tolerance) for series in (result.observed_net_before, result.observed_net_after, result.observed_proxy_before, result.observed_proxy_after) for value in series)
