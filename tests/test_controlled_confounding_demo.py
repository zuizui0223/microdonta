"""Behaviour tests for the controlled confounding demonstration."""
from __future__ import annotations

import sys
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from causal_model.controlled_confounding_demo import run_controlled_confounding_demo


def test_controlled_confounding_story_holds():
    """The example must preserve ambiguity, value measurements, then resolve it."""
    result = run_controlled_confounding_demo(
        backend="proxy", n_attempts=400, seed=7
    )

    assert result.n_accepted > 0
    assert result.modal_probability < 0.5

    s2 = result.mechanism_admissibility["selfing_syndrome_active"]
    s3 = result.mechanism_admissibility["island_isolation_common_cause"]
    assert abs(s2 - s3) < 0.2

    values = {label: value for label, value, _ in result.information_value_ranking}
    assert values
    assert all(value >= 0.0 for value in values.values())
    assert values["nectar guide at Hachijo"] > 0.0
    assert values["mechanism-independent nuisance"] < values["nectar guide at Hachijo"]

    assert result.resolving_measurement is not None
    assert result.resolvability_after > result.mechanism_resolvability
    assert result.entropy_after < result.mechanism_entropy
    assert (
        result.mechanism_admissibility_after["island_isolation_common_cause"]
        > s3
    )
    assert result.mechanism_admissibility_after["selfing_syndrome_active"] < s2
