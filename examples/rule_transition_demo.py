"""Minimal executable example for ecological rule-transition RACH.

Run from the repository root:
    python examples/rule_transition_demo.py
"""
from causal_model.abm_family_adapter import RobustnessPolicy
from causal_model.ecological_rule_abm import EcologicalRuleParameters, generate_sweep_records
from causal_model.rule_transition_invariants import explain_result
from causal_model.rule_transition_pipeline import analyse_rule_transitions


def main() -> None:
    draws = [
        EcologicalRuleParameters(0.9, 0.6, 0.4, 0.3, 0.5, 0.0),
        EcologicalRuleParameters(0.8, 0.7, 0.5, 0.35, 0.4, 0.0),
        EcologicalRuleParameters(0.9, 0.5, 0.6, 0.25, 0.6, 0.0),
        EcologicalRuleParameters(0.7, 0.8, 0.5, 0.30, 0.5, 0.0),
    ]
    records = (
        generate_sweep_records(
            "pollination",
            ["direct_selection", "reproductive_reconfiguration"],
            draws,
        )
        + generate_sweep_records(
            "predation",
            ["direct_selection", "demographic_reconfiguration"],
            draws,
        )
    )
    analysis = analyse_rule_transitions(
        records,
        policy=RobustnessPolicy(
            min_replicates=4,
            min_match_fraction=0.2,
            fragile_max_fraction=0.05,
        ),
    )
    print(explain_result(analysis.invariant_result))


if __name__ == "__main__":
    main()
