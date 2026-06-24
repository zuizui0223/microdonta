"""Demonstrate patch partition criticality and restoration thresholds.

Run with:

    python -m examples.patch_criticality_demo
"""
from __future__ import annotations

import json
from dataclasses import asdict

from causal_model.patch_feedback_hysteresis_theory import (
    PatchFeedbackSystem,
    restoration_threshold,
)
from causal_model.patch_partition_theory import (
    PatchInteractionSystem,
    admissible_equal_patch_counts,
    critical_heterozygosity_for_local_mode,
    equal_partition_service,
    max_equal_patch_count_for_high_trait,
)


def main() -> None:
    partition = PatchInteractionSystem(
        total_area=10.0,
        interaction_yield=1.0,
        aggregation_exponent=2.0,
        interaction_requirement=25.0,
    )
    restored = PatchFeedbackSystem(
        area=4.0,
        interaction_yield=1.0,
        area_exponent=2.0,
        feedback_exponent=2.0,
        trait_cost=9.0,
    )
    payload = {
        "partition_theorem": {
            "parameters": asdict(partition),
            "equal_partition_services": {
                str(n): equal_partition_service(partition, n) for n in range(1, 7)
            },
            "max_equal_patch_count_for_high_trait": max_equal_patch_count_for_high_trait(partition),
            "admissible_counts_through_8": admissible_equal_patch_counts(partition, max_count=8),
            "critical_equilibrium_heterozygosity": critical_heterozygosity_for_local_mode(
                partition, effective_density=100.0, mutation_rate=0.001
            ),
        },
        "feedback_theorem": {
            "parameters": asdict(restored),
            "critical_patch_area": restored.critical_patch_area,
            "high_state_stability": restored.high_state_stability,
            "low_state_stability": restored.low_state_stability,
            "restoration_threshold_x": restoration_threshold(restored),
            "interpretation": (
                "After collapse to x=0, restoring area above the critical patch area "
                "does not restore the high state without reseeding above x_c."
            ),
        },
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
