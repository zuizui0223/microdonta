"""Generic null and negative-control scenarios for CAPOM.

These null models test whether pattern-reproducing mechanisms are necessary
by disabling specific processes. They are system-agnostic; system-specific
parameter values should be provided by the caller via base_parameters.
"""

from __future__ import annotations

from .scenarios import Scenario


def null_scenarios() -> list[Scenario]:
    """Return four minimal null models for mechanistic control comparisons.

    N1_drift_only
        Trait change is driven by drift. Pollinator and selfing effects are
        suppressed by setting their contributions to zero.

    N2_pollinator_loss_only
        Pollinator environment is reduced but selfing and inbreeding feedback
        are disabled. Tests whether pollinator loss alone is sufficient.

    N3_selfing_only
        Selfing ability is elevated but guide-mediated pollinator selection is
        disabled. Tests whether selfing pressure alone drives guide loss.

    N4_random_trait_loss
        Nectar-guide maintenance cost is set to zero and mutation rate is
        elevated, simulating neutral trait loss without selection.
    """

    return [
        Scenario(
            name="N1_drift_only",
            parameter_overrides={
                "pollinator_environment": 0.0,
                "bombus_frequency": 0.0,
                "selfing_ability": 0.0,
                "inbreeding_load": 0.0,
                "guide_cost": 0.0,
            },
            enabled_processes=("drift", "mutation"),
            description="Trait change from drift alone; no directional selection.",
        ),
        Scenario(
            name="N2_pollinator_loss_only",
            parameter_overrides={
                "selfing_ability": 0.0,
                "inbreeding_load": 0.0,
            },
            enabled_processes=("pollinator", "drift", "mutation"),
            description="Pollinator-environment decline without selfing or inbreeding feedback.",
        ),
        Scenario(
            name="N3_selfing_only",
            parameter_overrides={
                "bombus_guide_dependence": 0.0,
                "other_pollinator_guide_use": 0.0,
            },
            enabled_processes=("selfing", "drift", "mutation"),
            description="Selfing pressure without guide-mediated pollinator selection.",
        ),
        Scenario(
            name="N4_random_trait_loss",
            parameter_overrides={
                "guide_cost": 0.0,
                "mutation_sd": 0.12,
            },
            enabled_processes=("drift", "mutation"),
            description="Neutral trait drift with elevated mutation; no guide maintenance cost.",
        ),
    ]
