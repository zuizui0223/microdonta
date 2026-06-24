"""Demonstrate exact net-performance non-identifiability and resolved-channel identification.

Run with:

    python -m examples.channel_identifiability_demo
"""
from __future__ import annotations

import json
from dataclasses import asdict

from causal_model.channel_identifiability_theory import (
    VitalRateState,
    construct_channel_loss_symmetry,
    identify_from_channel_resolved_rates,
    support_geometry,
)


def main() -> None:
    baseline = VitalRateState(
        grid=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
        fecundity=(1.1, 1.4, 1.9, 2.2, 2.6, 3.0),
        establishment=(1.8, 1.5, 1.2, 0.95, 0.75, 0.55),
    )
    attenuation = (1.0, 0.95, 0.84, 0.72, 0.63, 0.51)
    symmetry = construct_channel_loss_symmetry(
        baseline,
        attenuation,
        thresholds=(0.5, 1.0, 1.5, 2.0, 2.5),
    )
    payload = {
        "theorem_N1": {
            "net_performance_equal": symmetry.net_performance_equal,
            "all_threshold_supports_equal": symmetry.all_threshold_supports_equal,
            "fecundity_loss_geometry_at_1": asdict(
                support_geometry(symmetry.fecundity_loss, 1.0)
            ),
            "establishment_loss_geometry_at_1": asdict(
                support_geometry(symmetry.establishment_loss, 1.0)
            ),
            "note": "The post-change channel states differ, but every net-performance observation agrees.",
        },
        "theorem_N2": {
            "with_fecundity_resolved": asdict(
                identify_from_channel_resolved_rates(baseline, symmetry.fecundity_loss)
            ),
            "with_establishment_resolved": asdict(
                identify_from_channel_resolved_rates(baseline, symmetry.establishment_loss)
            ),
            "note": "Separate vital-rate measurements identify the changed exclusive channel.",
        },
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
