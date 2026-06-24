"""Demonstrate net-only non-identifiability and one-channel-plus-net recovery.

Run with:

    python -m examples.channel_identifiability_demo
"""
from __future__ import annotations

import json
from dataclasses import asdict

from causal_model.channel_identifiability_theory import (
    VitalRateState,
    construct_channel_loss_symmetry,
    identify_from_net_and_one_channel,
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

    def infer(post_state: VitalRateState) -> dict:
        return asdict(
            identify_from_net_and_one_channel(
                grid=baseline.grid,
                net_before=baseline.net_performance,
                net_after=post_state.net_performance,
                observed_before=baseline.fecundity,
                observed_after=post_state.fecundity,
                observed_channel="fecundity",
            )
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
            "note": "The post-change channel states differ, but every net-only observation agrees.",
        },
        "theorem_N2": {
            "observe_W_and_F_for_fecundity_loss": infer(symmetry.fecundity_loss),
            "observe_W_and_F_for_establishment_loss": infer(symmetry.establishment_loss),
            "note": "Total performance plus one positive channel reconstructs the other channel.",
        },
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
