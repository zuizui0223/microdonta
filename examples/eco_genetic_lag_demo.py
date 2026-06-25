"""Demonstrate lead and no-lead cases for the same diversity recursion family.

Run:
    python -m examples.eco_genetic_lag_demo
"""
from __future__ import annotations

from dataclasses import asdict
import json

from causal_model.eco_genetic_lag_theory import assess_genetic_lag, uniform_upper_multiplier_bound


def main() -> None:
    initial = 0.8
    warning = 0.5
    collapse_time = 4
    payload = {
        "no_lead_counterexample": asdict(
            assess_genetic_lag(initial, warning, (0.99, 0.99, 0.99, 0.99), collapse_time)
        ),
        "lead_example": asdict(
            assess_genetic_lag(initial, warning, (0.7, 0.7, 0.95, 0.95), collapse_time)
        ),
        "uniform_sufficient_bound": asdict(
            uniform_upper_multiplier_bound(initial, warning, 0.7, collapse_time)
        ),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
