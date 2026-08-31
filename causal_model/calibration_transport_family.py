"""Symmetric calibration-transport family for multiplicative ecological channels.

This module provides a scale-invariant parameterisation of between-regime
proxy calibration drift.  Let ``kappa = q_1 / q_0``.  Rather than bounding
``kappa`` additively around one, define a multiplicative distortion factor
``Gamma >= 1`` such that

    1/Gamma <= kappa <= Gamma.

Equivalently ``eta = log(Gamma)`` and ``|log(kappa)| <= eta``.

This parameterisation closes the stable / bounded / unrestricted calibration
cases into one family:

    Gamma = 1          -> stable calibration (point identification; N3)
    1 < Gamma < inf    -> sharp partial identification
    Gamma -> inf       -> unrestricted calibration drift (N4)

For a stable-calibration complementary-channel ratio ``rho_hat``, the sharp
marginal identified interval is

    [rho_hat / Gamma, rho_hat * Gamma].

The directional breakdown factor is therefore

    Gamma_star = max(rho_hat, 1/rho_hat),

which is invariant to reversing the reference regime.  The corresponding
log-scale breakdown is ``eta_star = |log(rho_hat)|``.

The functions here do not estimate Gamma or eta from the same net/proxy data.
A finite bound must come from external knowledge or calibration anchors.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, isclose, log
from typing import Literal


IdentificationState = Literal["point_identified", "partially_identified", "non_identified"]
AnchorState = Literal["no_transport_calibration", "external_bound", "observed_transport"]


@dataclass(frozen=True)
class SymmetricCalibrationBound:
    """Multiplicatively symmetric bound on ``kappa=q_1/q_0``."""

    gamma: float

    def __post_init__(self) -> None:
        if self.gamma < 1.0:
            raise ValueError("gamma must satisfy gamma >= 1")

    @property
    def eta(self) -> float:
        return log(self.gamma)

    @property
    def kappa_lower(self) -> float:
        return 1.0 / self.gamma

    @property
    def kappa_upper(self) -> float:
        return self.gamma

    @property
    def identification_state(self) -> IdentificationState:
        if isclose(self.gamma, 1.0):
            return "point_identified"
        return "partially_identified"

    @classmethod
    def from_eta(cls, eta: float) -> "SymmetricCalibrationBound":
        value = float(eta)
        if value < 0.0:
            raise ValueError("eta must satisfy eta >= 0")
        return cls(gamma=exp(value))


@dataclass(frozen=True)
class SymmetricIdentifiedInterval:
    """Sharp marginal interval under a symmetric calibration bound."""

    point_under_stability: float
    gamma: float
    eta: float
    lower: float
    upper: float
    multiplicative_width: float
    breakdown_gamma: float
    breakdown_eta: float

    @property
    def excludes_one(self) -> bool:
        return self.upper < 1.0 or self.lower > 1.0


@dataclass(frozen=True)
class AnchorLadderStep:
    """Identification consequence of the number of direct calibration anchors.

    This ladder is about *transport calibration*, not about whether a stable
    proxy ratio can be postulated without anchors.  With zero direct anchors,
    unrestricted transport remains non-identified.  With one anchor, local
    calibration is known but cross-regime transport still requires an external
    bound.  With two anchors, q_0 and q_1 are observed and kappa is measured.
    """

    anchors: int
    state: AnchorState
    identification: IdentificationState
    calibration_object: str
    consequence: str


def symmetric_interval(point_under_stability: float, *, gamma: float) -> SymmetricIdentifiedInterval:
    point = float(point_under_stability)
    if point <= 0.0:
        raise ValueError("point_under_stability must be strictly positive")
    bound = SymmetricCalibrationBound(float(gamma))
    lower = point / bound.gamma
    upper = point * bound.gamma
    breakdown_gamma = max(point, 1.0 / point)
    breakdown_eta = abs(log(point))
    return SymmetricIdentifiedInterval(
        point_under_stability=point,
        gamma=bound.gamma,
        eta=bound.eta,
        lower=lower,
        upper=upper,
        multiplicative_width=bound.gamma**2,
        breakdown_gamma=breakdown_gamma,
        breakdown_eta=breakdown_eta,
    )


def breakdown_factor(point_under_stability: float) -> tuple[float, float]:
    """Return ``(Gamma_star, eta_star)`` for directional robustness."""
    interval = symmetric_interval(point_under_stability, gamma=1.0)
    return interval.breakdown_gamma, interval.breakdown_eta


def observed_kappa(*, proxy_0: float, channel_0: float, proxy_1: float, channel_1: float) -> float:
    """Measure ``kappa=q_1/q_0`` when both regimes have direct anchors."""
    values = {
        "proxy_0": float(proxy_0),
        "channel_0": float(channel_0),
        "proxy_1": float(proxy_1),
        "channel_1": float(channel_1),
    }
    for name, value in values.items():
        if value <= 0.0:
            raise ValueError(f"{name} must be strictly positive")
    q0 = values["proxy_0"] / values["channel_0"]
    q1 = values["proxy_1"] / values["channel_1"]
    return q1 / q0


def identify_with_observed_kappa(
    *,
    net_ratio: float,
    proxy_ratio: float,
    kappa: float,
    proxy_channel: Literal["fecundity", "establishment"] = "fecundity",
) -> tuple[float, float]:
    """Point-identify both channel ratios once transport calibration is observed."""
    rho_w = float(net_ratio)
    rho_x = float(proxy_ratio)
    kap = float(kappa)
    if rho_w <= 0.0 or rho_x <= 0.0 or kap <= 0.0:
        raise ValueError("net_ratio, proxy_ratio and kappa must be strictly positive")

    if proxy_channel == "fecundity":
        rho_f = rho_x / kap
        rho_e = rho_w / rho_f
    elif proxy_channel == "establishment":
        rho_e = rho_x / kap
        rho_f = rho_w / rho_e
    else:
        raise ValueError(f"unknown proxy_channel: {proxy_channel}")
    return rho_f, rho_e


def anchor_ladder(anchors: int) -> AnchorLadderStep:
    """Return the transport-identification consequence for 0, 1 or 2 anchors."""
    count = int(anchors)
    if count == 0:
        return AnchorLadderStep(
            anchors=0,
            state="no_transport_calibration",
            identification="non_identified",
            calibration_object="kappa unrestricted unless supplied by assumption",
            consequence="N4 under unrestricted proxy transport; no directional channel claim is identified from net and proxy observations alone.",
        )
    if count == 1:
        return AnchorLadderStep(
            anchors=1,
            state="external_bound",
            identification="partially_identified",
            calibration_object="local q anchored; cross-regime Gamma or eta remains external",
            consequence="A finite external transport bound gives a sharp identified set and a reportable breakdown factor.",
        )
    if count == 2:
        return AnchorLadderStep(
            anchors=2,
            state="observed_transport",
            identification="point_identified",
            calibration_object="q_0 and q_1 observed, hence kappa=q_1/q_0 measured",
            consequence="Transport calibration is measured directly; Gamma is unnecessary for point identification.",
        )
    raise ValueError("anchors must be one of 0, 1, 2")
