"""Minimal executable example for ecological rule-transition RACH.

The demo writes ``rule_transition_benchmark_report.json`` with separated
assumptions, simulated outcomes, conditional necessity, counterexamples,
region/seed uncertainty, and declared limitations.

Run from the repository root:
    python examples/rule_transition_demo.py
"""
from __future__ import annotations

import json
from pathlib import Path

from causal_model.abm_family_adapter import RobustnessPolicy, summarise_sweep
from causal_model.ecological_rule_abm import EcologicalRuleParameters, generate_sweep_records
from causal_model.rule_transition_diagnostics import build_benchmark_report
from causal_model.rule_transition_invariants import explain_result
from causal_model.rule_transition_pipeline import analyse_rule_transitions


def build_records():
    draws = [
        EcologicalRuleParameters(0.9, 0.6, 0.4, 0.30, 0.5, 0.0),
        EcologicalRuleParameters(0.8, 0.7, 0.5, 0.35, 0.4, 0.0),
        EcologicalRuleParameters(0.9, 0.5, 0.6, 0.25, 0.6, 0.0),
        EcologicalRuleParameters(0.7, 0.8, 0.5, 0.30, 0.5, 0.0),
    ]
    return (
        generate_sweep_records(
            "pollination",
            ["direct_selection", "reproductive_reconfiguration", "knife_edge_cancellation"],
            draws,
        )
        + generate_sweep_records(
            "predation",
            ["direct_selection", "demographic_reconfiguration"],
            draws,
        )
        + generate_sweep_records(
            "dispersal_loss",
            ["direct_selection", "demographic_reconfiguration"],
            draws,
        )
    )


def main() -> None:
    records = build_records()
    policy = RobustnessPolicy(min_replicates=4, min_match_fraction=0.2, fragile_max_fraction=0.05)

    print("=== POM acceptance per run: d(P_sim, P_obs) <= epsilon  (A_epsilon) ===")
    seen: set[tuple[str, str]] = set()
    for record in records:
        key = (record.scenario, record.program_id)
        if key in seen:
            continue
        seen.add(key)
        metadata = record.metadata
        print(
            f"  {record.scenario:14s} {record.program_id:26s} "
            f"d={metadata['abc_distance']:.2f} eps={metadata['epsilon']:.2f} "
            f"accepted={metadata['accepted']}  P_sim={metadata['P_sim']}"
        )

    print("\n=== sweep classification (robust / fragile / rejected / insufficient) ===")
    for summary in summarise_sweep(records, policy):
        reasons = ", ".join(sorted(summary.fragility_reasons)) or "-"
        print(
            f"  {summary.scenario:14s} {summary.program_id:26s} "
            f"{summary.classification:11s} match={summary.match_fraction:.2f} "
            f"fragility=[{reasons}]"
        )

    analysis = analyse_rule_transitions(records, policy=policy)
    print("\n=== necessary rule transitions across robust ABM families ===")
    print(json.dumps(explain_result(analysis.invariant_result), indent=2, ensure_ascii=False))

    report = build_benchmark_report(
        records,
        policy=policy,
        unresolved_limitations=(
            "The abstract demo is not a substitute for independent empirical calibration.",
            "Endpoint sensitivity must be run separately for every concrete ABM family.",
        ),
    )
    output = Path("rule_transition_benchmark_report.json")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote benchmark diagnostics: {output.resolve()}")


if __name__ == "__main__":
    main()
