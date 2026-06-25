"""Print an analytic patch interaction / genetic drift theorem example.

Run with:

    python -m examples.patch_ecogenetic_demo
"""
from __future__ import annotations

import json
from dataclasses import asdict

from causal_model.patch_genetic_drift_theory import (
    branch_genetic_erosion,
    selection_drift_step,
)
from causal_model.patch_interaction_bifurcation_theory import (
    critical_patch_size,
    equilibria,
    partition_capacity,
    saddle_nodes,
    trait_tipping_window,
)
from causal_model.patch_metapopulation_genetics import (
    equal_partition_drift_contrast,
)


def main() -> None:
    patch_size = 3.0
    feedback_strength = 2.0
    nodes = saddle_nodes(patch_size, feedback_strength)
    barrier = (nodes.theta_low + nodes.theta_high) / 2.0
    payload = {
        "patch_theory": {
            "critical_patch_size": critical_patch_size(feedback_strength),
            "saddle_nodes": asdict(nodes),
            "equilibria_inside_hysteresis_window": [
                asdict(item) for item in equilibria(patch_size, feedback_strength, barrier)
            ],
            "high_trait_window": asdict(
                trait_tipping_window(patch_size, feedback_strength, q_required=0.5)
            ),
            "partition_capacity": asdict(
                partition_capacity(total_area=6.0, patch_count=3, feedback_strength=feedback_strength)
            ),
        },
        "genetic_theory": {
            "selection_then_drift": asdict(
                selection_drift_step(0.4, fitness_high=1.5, fitness_low=1.0, effective_size=100.0)
            ),
            "branch_erosion": asdict(
                branch_genetic_erosion(
                    patch_size,
                    feedback_strength,
                    density_scale=30.0,
                    baseline_density=0.2,
                )
            ),
            "equal_partition_drift": asdict(
                equal_partition_drift_contrast(
                    total_area=24.0,
                    patch_count=6,
                    interaction_availability=0.7,
                    density_scale=10.0,
                    baseline_density=0.2,
                )
            ),
        },
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
