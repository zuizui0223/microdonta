"""Run the adversarial coarse-POM / trait-geometry mechanism comparison.

Examples
--------
    python -m examples.geometry_discrimination_demo
    python -m examples.geometry_discrimination_demo --output outputs/geometry_discrimination.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from causal_model.geometry_mechanism_discrimination import (
    run_geometry_mechanism_discrimination,
)


def _summary(report: object) -> dict[str, object]:
    return {
        "target": asdict(report.target),
        "robustness_policy": asdict(report.policy),
        "n_trials": len(report.trials),
        "coarse_survivors": list(report.coarse_survivors),
        "coarse_summaries": [
            {
                "program_id": item.program_id,
                "classification": item.classification,
                "n_replicates": item.n_replicates,
                "n_matches": item.n_matches,
                "match_fraction": item.match_fraction,
            }
            for item in report.coarse_summaries
        ],
        "geometry_resolutions": [asdict(item) for item in report.resolutions],
        "geometry_summaries": {
            label: [
                {
                    "program_id": item.program_id,
                    "classification": item.classification,
                    "n_replicates": item.n_replicates,
                    "n_matches": item.n_matches,
                    "match_fraction": item.match_fraction,
                }
                for item in summaries
            ]
            for label, summaries in report.geometry_summaries.items()
        },
        "interpretation": {
            "coarse_pom": "Mean-trait decline plus persistence retains all candidate mechanisms.",
            "upper_edge_contraction": "Ambiguous: relationship-benefit loss and directional connectivity pruning remain.",
            "shift": "Unique within this declared theory family: optimum displacement.",
            "fragmentation": "Unique within this declared theory family: connectivity fragmentation.",
            "conserved": "Unique within this declared theory family: compensated frequency reweighting.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-regions", type=int, default=12)
    parser.add_argument("--base-seed", type=int, default=20260624)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/geometry_discrimination.json"),
    )
    args = parser.parse_args()
    report = run_geometry_mechanism_discrimination(
        n_regions=args.n_regions,
        base_seed=args.base_seed,
    )
    payload = _summary(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["geometry_resolutions"], indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
