"""Demonstrate stable, bounded-drift, and unconstrained proxy calibration.

Run with:

    python -m examples.proxy_calibration_demo
"""
from __future__ import annotations

import json
from dataclasses import asdict

from causal_model.proxy_calibration_theory import (
    construct_time_varying_proxy_symmetry,
    identify_from_net_and_bounded_proxy_drift,
    identify_from_net_and_stable_proxy,
)


def main() -> None:
    # Identical observed W and proxy X can encode distinct latent changes when the
    # proxy-to-channel calibration is allowed to drift without a bound.
    ambiguity = construct_time_varying_proxy_symmetry(
        net_before=(1.0, 1.0, 1.0, 1.0),
        net_after=(1.0, 1.0, 1.0, 1.0),
        proxy_before=(1.0, 1.0, 1.0, 1.0),
        proxy_after=(1.0, 1.0, 1.0, 1.0),
        baseline_calibration=(1.0, 1.0, 1.0, 1.0),
        calibration_shift=(0.5, 0.75, 1.25, 2.0),
    )

    # Under the declared stability assumption, relative channel changes are point
    # identified even when the absolute proxy conversion is unknown.
    stable = identify_from_net_and_stable_proxy(
        net_before=(0.8, 1.0, 1.2),
        net_after=(0.72, 0.8, 0.9),
        proxy_before=(0.4, 0.5, 0.6),
        proxy_after=(0.36, 0.4, 0.45),
        proxy_channel="fecundity",
    )

    # Worked sensitivity example. The stable-calibration estimate is rho_E=0.745.
    # With |q_1/q_0 - 1| <= 0.34, the upper bound is 0.745*1.34=0.9983,
    # so the establishment-decrease conclusion still excludes one. The exact
    # breakpoint is 1/0.745-1 = 0.34228... .
    bounded = identify_from_net_and_bounded_proxy_drift(
        net_before=(1.0,),
        net_after=(0.745,),
        proxy_before=(1.0,),
        proxy_after=(1.0,),
        proxy_channel="fecundity",
        delta=0.34,
    )
    breakpoint = bounded.establishment_breakdown[0].delta_star

    print(json.dumps({
        "N3_stable_proxy": asdict(stable),
        "N3_N4_bounded_drift": {
            **asdict(bounded),
            "reportable_sentence": (
                "The conclusion that establishment decreased is retained for "
                "calibration drift up to 34%; the interval first reaches one at "
                f"{breakpoint:.2%}."
            ),
            "status": "illustrative sensitivity calculation, not an empirical estimate",
        },
        "N4_time_varying_proxy": {
            "stable_calibration_explanation": asdict(ambiguity.ratios_a),
            "drifting_calibration_explanation": asdict(ambiguity.ratios_b),
            "note": "Both explanations have the same supplied net-performance and proxy observations.",
        },
    }, indent=2))


if __name__ == "__main__":
    main()
