"""Controlled observation-repetition witnesses, not empirical field findings.

Run from the repository root: python -m examples.replication_limit_report
"""
from __future__ import annotations

from dataclasses import asdict
import json

from causal_model.empirical_observation_contract import LikelihoodCandidate
from causal_model.replication_information_audit import replication_information_profile


def build_replication_examples() -> dict:
    cases = {
        "different_laws_noise_only": (
            [{"target": "A"}, {"target": "B"}],
            ((0.9, 0.1), (0.1, 0.9)),
        ),
        "contact_cannot_separate_pollination_only_from_combined": (
            [{"target": "pollination_only"}, {"target": "abiotic_only"}, {"target": "combined"}],
            ((0.1, 0.9), (0.9, 0.1), (0.1, 0.9)),
        ),
        "persistent_nuisance_singleton_zero_replicates_positive": (
            [{"target": "heterogeneous", "nuisance": "low"},
             {"target": "heterogeneous", "nuisance": "high"},
             {"target": "homogeneous", "nuisance": "low"},
             {"target": "homogeneous", "nuisance": "high"}],
            ((0.8, 0.2), (0.2, 0.8), (0.5, 0.5), (0.5, 0.5)),
        ),
        "nuisance_redrawn_each_repeat_same_target_law": (
            [{"target": "heterogeneous"}, {"target": "homogeneous"}],
            ((0.5, 0.5), (0.5, 0.5)),
        ),
    }
    reports = {}
    for name, (rows, probabilities) in cases.items():
        candidate = LikelihoodCandidate(
            name, ("absent", "present"), probabilities,
            "synthetic declared probabilities, not empirical calibration",
        )
        reports[name] = asdict(replication_information_profile(
            rows, candidate, target_columns=["target"], weights=[1.0] * len(rows),
            support_reference="finite synthetic worlds; natural-system exhaustiveness not certified",
            weight_reference="uniform positive mass over the listed worlds",
            conditional_iid_reference=(
                "Fresh binary readings conditional on a fixed full row. The redrawn-nuisance "
                "case explicitly uses a different target-level generative protocol."
            ), horizons=(0, 1, 2, 5, 10, 20, 50),
        ))
    return {
        "data_kind": "synthetic_replication_limit_witnesses",
        "scope": "conditional_iid_finite_bernoulli_audit_not_cost_optimization_or_adaptation_evidence",
        "reports": reports,
    }


if __name__ == "__main__":
    print(json.dumps(build_replication_examples(), indent=2, allow_nan=False))
