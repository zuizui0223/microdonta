"""Compare equal-total-area patch configurations in the declared simulator.

Run:
    python -m examples.multipatch_criticality_demo
"""
from __future__ import annotations

from dataclasses import asdict
import json

from causal_model.multipatch_criticality_dynamics import (
    DynamicsParameters,
    first_alpha_warning,
    first_high_trait_absence,
    simulate,
)


def summarize(result):
    final = result.snapshots[-1]
    return {
        "first_high_trait_absence": first_high_trait_absence(result),
        "first_alpha_warning_at_0_2": first_alpha_warning(result, 0.2),
        "final": asdict(final),
    }


def main() -> None:
    common = dict(
        generations=25,
        density_capacity=40.0,
        interaction_feedback=8.0,
        interaction_barrier=0.45,
        initial_interaction=(),
        initial_high_allele_frequency=(),
        random_seed=17,
    )
    one_large = simulate(DynamicsParameters(patch_areas=(3.0,), **common))
    isolated_small = simulate(DynamicsParameters(patch_areas=(1.0, 1.0, 1.0), **common))
    connected_small = simulate(
        DynamicsParameters(patch_areas=(1.0, 1.0, 1.0), migration_rate=0.1, **common)
    )
    print(
        json.dumps(
            {
                "one_large": summarize(one_large),
                "isolated_small": summarize(isolated_small),
                "connected_small": summarize(connected_small),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
