"""Demonstrate stable versus time-varying channel proxy calibration.

Run with:

    python -m examples.proxy_calibration_demo
"""
from __future__ import annotations

import json
from dataclasses import asdict

from causal_model.proxy_calibration_theory import (
    construct_time_varying_proxy_symmetry,
    identify_from_net_and_stable_proxy,
)


def main() -> None:
    # Identical observed W and proxy X can encode distinct latent changes when the
    # proxy-to-channel calibration is allowed to drift.
    ambiguity = construct_time_varying_proxy_symmetry(
        net_before=(1.0, 1.0, 1.0, 1.0),
        net_after=(1.0, 1.0, 1.0, 1.0),
        proxy_before=(1.0, 1.0, 1.0, 1.0),
        proxy_after=(1.0, 1.0, 1.0, 1.0),
        baseline_calibration=(1.0, 1.0, 1.0, 1.0),
        calibration_shift=(0.5, 0.75, 1.25, 2.0),
    )

    # Under the declared stability assumption, the same formula identifies ratios.
    stable = identify_from_net_and_stable_proxy(
        net_before=(0.8, 1.0, 1.2),
        net_after=(0.72, 0.8, 0.9),
        proxy_before=(0.4, 0.5, 0.6),
        proxy_after=(0.36, 0.4, 0.45),
        proxy_channel="fecundity",
    )
    print(json.dumps({
        "N3_stable_proxy": asdict(stable),
        "N4_time_varying_proxy": {
            "stable_calibration_explanation": asdict(ambiguity.ratios_a),
            "drifting_calibration_explanation": asdict(ambiguity.ratios_b),
            "note": "Both explanations have the same supplied net-performance and proxy observations.",
        },
    }, indent=2))


if __name__ == "__main__":
    main()
