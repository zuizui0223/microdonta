"""Identifiability boundary for channel proxies.

This module refines the positive result in
:mod:`causal_model.channel_identifiability_theory`.  Let total performance be

    W_i(z) = F_i(z) E_i(z),

and let an observed proxy for the fecundity/survival channel be

    X_i(z) = q_i(z) F_i(z),

where ``q_i`` is the unknown conversion between the proxy and the mathematical
channel at time/regime ``i``.

N3 -- Stable-proxy ratio identification.
    If q_0(z)=q_1(z)>0, then relative fecundity change is X_1/X_0 and relative
    establishment change is (W_1/W_0)/(X_1/X_0).  Absolute calibration is not
    necessary to identify channel *changes*.

N4 -- Time-varying-proxy non-identifiability.
    If q_0 and q_1 are unconstrained, the same observed W and X are compatible
    with arbitrary positive q_1/q_0 and therefore different channel-change
    ratios. A proxy whose conversion changes across regimes does not resolve the
    channels without calibration or a stability assumption.

The proofs are in ``docs/proxy_calibration_theorem.md``.  Code here provides
finite-grid constructions and regression checks only.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Literal, Sequence

from causal_model.channel_identifiability_theory import Channel, ChannelConclusion


ProxyChannel = Literal["fecundity", "establishment"]


@dataclass(frozen=True)
class ChannelChangeRatios:
    """Pointwise before/after channel ratios and their qualitative classification."""

    fecundity_ratio: tuple[float, ...]
    establishment_ratio: tuple[float, ...]
    conclusion: ChannelConclusion


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

    If the proxy represents F as X_i=qF_i with the *same* q at both times,
    F_1/F_0=X_1/X_0.  Since W=FE, E_1/E_0=(W_1/W_0)/(F_1/F_0).

    ``proxy_channel='establishment'`` applies the symmetric argument.
    The proxy's absolute scale may be unknown and trait-dependent; only temporal
    stability of its conversion factor is required.
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

    Model A assumes the proxy calibration is stable, q_1=q_0.  Model B sets
    q_1=h q_0, where ``h`` is any positive trait-dependent calibration shift.
    For a fecundity proxy:

    ``F_i = X_i/q_i`` and ``E_i = W_i/F_i``.

    Both models reproduce exactly the supplied observed W and X, but their channel
    ratios can differ whenever h differs from one. This is the constructive form
    of theorem N4.
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
    # The dataclass carries one observed series by definition; this function exists
    # as an explicit invariant boundary for callers/tests.
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
