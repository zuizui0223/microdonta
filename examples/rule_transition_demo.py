"""Minimal executable example for ecological rule-transition RACH.

Runs three independent ecological scenarios — pollination loss, predation loss,
and dispersal loss — each as a *family* of admissible causal programs evaluated
over a parameter sweep. RACH does NOT pick a single best model: it keeps every
robustly-admissible program, discards the fragile ones, and reports the rule
transitions (motifs and OR-clauses) that are necessary across ALL robust
programs in every scenario.

Run from the repository root:
    python examples/rule_transition_demo.py
"""
from causal_model.abm_family_adapter import RobustnessPolicy, summarise_sweep
from causal_model.ecological_rule_abm import EcologicalRuleParameters, generate_sweep_records
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
        # pollination loss: direct vs reproductive reconfiguration, plus a
        # deliberately fragile cancellation-dependent rival.
        generate_sweep_records(
            "pollination",
            ["direct_selection", "reproductive_reconfiguration", "knife_edge_cancellation"],
            draws,
        )
        # predation loss: direct vs demographic reconfiguration.
        + generate_sweep_records(
            "predation",
            ["direct_selection", "demographic_reconfiguration"],
            draws,
        )
        # dispersal loss: direct vs demographic reconfiguration.
        + generate_sweep_records(
            "dispersal_loss",
            ["direct_selection", "demographic_reconfiguration"],
            draws,
        )
    )


def main() -> None:
    records = build_records()
    policy = RobustnessPolicy(min_replicates=4, min_match_fraction=0.2, fragile_max_fraction=0.05)

    print("=== sweep classification (robust / fragile / rejected / insufficient) ===")
    for summary in summarise_sweep(records, policy):
        reasons = ", ".join(sorted(summary.fragility_reasons)) or "-"
        print(
            f"  {summary.scenario:14s} {summary.program_id:26s} "
            f"{summary.classification:11s} match={summary.match_fraction:.2f} "
            f"fragility=[{reasons}]"
        )

    analysis = analyse_rule_transitions(records, policy=policy)
    print("\n=== necessary rule transitions across robust ABM families ===")
    import json
    print(json.dumps(explain_result(analysis.invariant_result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
