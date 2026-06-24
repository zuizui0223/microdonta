"""Run reproducible endpoint sensitivity reports for the current RACH ABMs.

The report keeps spatial pollination and defense endpoint analyses separate. Each
cell uses a before resident and a post-intervention re-equilibrated resident, then
records region- and seed-level Wilson intervals. Complete-corridor colonization is
not pooled here because its strict endpoint can be undefined after loss.

Examples
--------
    python -m examples.endpoint_sensitivity_report --profile quick
    python -m examples.endpoint_sensitivity_report --profile standard \
        --output outputs/endpoint_sensitivity_standard.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from causal_model.abm_family_adapter import RobustnessPolicy, SweepRecord
from causal_model.defense_metapopulation_abm import (
    defense_observed_pattern,
    defense_program_motifs,
    make_defense_intervention,
    sample_constrained_defense,
)
from causal_model.endpoint_sensitivity_backends import run_defense_endpoint_sensitivity
from causal_model.rule_transition_diagnostics import (
    build_benchmark_report,
    endpoint_sensitivity_grid,
    run_spatial_endpoint_sensitivity,
)
from causal_model.spatial_metapopulation_abm import (
    constraint_program_motifs,
    default_observed_pattern,
    make_interventions,
    sample_constrained_ecosystem,
)


_PROFILES: dict[str, dict[str, object]] = {
    "quick": {
        "grid_points": (7,),
        "invasion_steps": (4,),
        "invasion_replicates": (1,),
        "invasion_thresholds": (0.0,),
        "stationarity_windows": (8,),
        "n_regions": 2,
        "seeds": (0, 1),
    },
    "standard": {
        "grid_points": (7, 9),
        "invasion_steps": (4, 6),
        "invasion_replicates": (1, 2),
        "invasion_thresholds": (-0.02, 0.0, 0.02),
        "stationarity_windows": (8, 12),
        "n_regions": 4,
        "seeds": (0, 1),
    },
    "full": {
        "grid_points": (7, 9, 13),
        "invasion_steps": (4, 6, 10),
        "invasion_replicates": (1, 2, 4),
        "invasion_thresholds": (-0.02, 0.0, 0.02),
        "stationarity_windows": (8, 12),
        "n_regions": 6,
        "seeds": (0, 1),
    },
}


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, (frozenset, set)):
        return sorted(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _cell_summary(cell: object) -> dict[str, object]:
    return {
        "settings": asdict(cell.settings),
        "n_records": len(cell.records),
        "uncertainty": cell.uncertainty,
    }


def _policy(n_replicates: int) -> RobustnessPolicy:
    return RobustnessPolicy(
        min_replicates=max(4, min(n_replicates, 12)),
        min_match_fraction=0.35,
        fragile_max_fraction=0.15,
    )


def _reference_benchmark(
    records: tuple[SweepRecord, ...],
    policy: RobustnessPolicy,
) -> dict[str, object]:
    """Build a benchmark if the reference cell supports any admissible program.

    Sensitivity cells with no accepted endpoint are informative counterexamples;
    they should be reported rather than crashing the report generator.
    """
    try:
        return build_benchmark_report(
            records,
            policy=policy,
            unresolved_limitations=(
                "Reference benchmark uses only the first declared sensitivity cell; other cells are reported separately.",
            ),
        )
    except ValueError as error:
        return {
            "status": "no_admissible_program_at_reference_setting",
            "reason": str(error),
            "n_records": len(records),
            "n_matches": sum(record.pattern_matched for record in records),
        }


def run(profile: str, backend: str, *, base_seed: int) -> dict[str, object]:
    config = _PROFILES[profile]
    settings = endpoint_sensitivity_grid(
        grid_points=config["grid_points"],
        invasion_steps=config["invasion_steps"],
        invasion_replicates=config["invasion_replicates"],
        invasion_thresholds=config["invasion_thresholds"],
        stationarity_windows=config["stationarity_windows"],
    )
    n_regions = int(config["n_regions"])
    seeds = tuple(config["seeds"])
    policy = _policy(n_regions * len(seeds))
    report: dict[str, object] = {
        "report_type": "RACH endpoint sensitivity",
        "profile": profile,
        "base_seed": base_seed,
        "n_sensitivity_settings": len(settings),
        "endpoint_protocol": "before resident and post-intervention re-equilibrated resident",
        "backends": {},
        "unresolved_limitations": [
            "This is conditional model sensitivity, not empirical validation of a natural population mechanism.",
            "Complete-corridor colonization is excluded because it can lack a stationary post-loss resident, so Omega_inv(after) is undefined under the strict endpoint protocol.",
        ],
    }

    if backend in {"all", "spatial"}:
        intervention = make_interventions(compensation=0.08)["pollination_loss"]
        cells = run_spatial_endpoint_sensitivity(
            intervention,
            program_id="fecundity_reward",
            program_motifs=constraint_program_motifs(intervention),
            ecosystem_sampler=sample_constrained_ecosystem,
            settings=settings,
            observed_pattern=default_observed_pattern(),
            n_regions=n_regions,
            seeds=seeds,
            base_seed=base_seed,
        )
        reference = cells[0]
        report["backends"]["spatial_pollination"] = {
            "intervention": intervention.name,
            "reference_setting": asdict(reference.settings),
            "reference_benchmark": _reference_benchmark(reference.records, policy),
            "sensitivity_cells": [_cell_summary(cell) for cell in cells],
        }

    if backend in {"all", "defense"}:
        intervention = make_defense_intervention(compensation=0.08)
        cells = run_defense_endpoint_sensitivity(
            intervention,
            program_id="survival_reward",
            program_motifs=defense_program_motifs(intervention),
            ecosystem_sampler=sample_constrained_defense,
            settings=settings,
            observed_pattern=defense_observed_pattern(),
            n_regions=n_regions,
            seeds=seeds,
            base_seed=base_seed,
        )
        reference = cells[0]
        report["backends"]["defense_predator_loss"] = {
            "intervention": intervention.name,
            "reference_setting": asdict(reference.settings),
            "reference_benchmark": _reference_benchmark(reference.records, policy),
            "sensitivity_cells": [_cell_summary(cell) for cell in cells],
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=tuple(_PROFILES), default="quick")
    parser.add_argument("--backend", choices=("all", "spatial", "defense"), default="all")
    parser.add_argument("--base-seed", type=int, default=20260624)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/endpoint_sensitivity_quick.json"),
    )
    args = parser.parse_args()
    report = run(args.profile, args.backend, base_seed=args.base_seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    print(f"Wrote {args.output} with {report['n_sensitivity_settings']} sensitivity settings.")


if __name__ == "__main__":
    main()
