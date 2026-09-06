"""Synthetic observation switching; run python -m examples.replication_switch_report."""
from __future__ import annotations

from dataclasses import asdict
import json

from causal_model.empirical_observation_contract import LikelihoodCandidate, condition_on_selected
from causal_model.replication_switch_audit import audit_replication_switch


def three_program_model():
    rows = tuple({"program": label} for label in ("pollination_only", "abiotic_only", "combined"))
    contact = LikelihoodCandidate(
        "contact", ("absent", "present"), ((0.1, 0.9), (0.9, 0.1), (0.1, 0.9)),
        "synthetic contact error=0.1; no field calibration",
    )
    physiology = LikelihoodCandidate(
        "physiology", ("absent", "present"), ((0.9, 0.1), (0.1, 0.9), (0.1, 0.9)),
        "synthetic physiology error=0.1; no field calibration",
    )
    return rows, contact, physiology


def current_weights(history):
    """Condition only the explicitly observed contact history, never future outcomes."""
    rows, contact, _ = three_program_model()
    weights = (1.0, 1.0, 1.0)
    probability = 1.0
    for outcome in history:
        receipt = condition_on_selected(
            rows, contact, outcome, target_columns=["program"], weights=weights,
        )
        weights = receipt.posterior_weights
        probability *= receipt.outcome_probability
    total = sum(weights)
    return tuple(w / total for w in weights), probability


def audit_history(history, *, physiology_error=0.1, include_unmodelled=False):
    rows, contact, physiology = three_program_model()
    if not 0.0 <= physiology_error <= 0.5:
        raise ValueError("physiology_error must be between 0 and 0.5")
    e = physiology_error
    physiology = LikelihoodCandidate(
        physiology.name, physiology.outcomes, ((1-e, e), (e, 1-e), (e, 1-e)),
        f"synthetic physiology error={e}; no field calibration",
    )
    weights, probability = current_weights(history)
    alternatives = [physiology]
    if include_unmodelled:
        alternatives.append(LikelihoodCandidate("unmodelled_followup", ("low", "high"), None))
    audit = audit_replication_switch(
        rows, contact, alternatives, target_columns=["program"], weights=weights,
        support_reference="three synthetic programs; not an exhaustive ecological domain",
        weight_reference=f"equal initial weights updated on contact history {tuple(history)!r}",
        conditional_iid_reference="fresh contact readings iid given the same fixed program",
        future_likelihood_reference="both channels independent of past readings given the full world",
    )
    return {"observed_contact_history": list(history), "history_probability": probability,
            "current_program_weights": list(weights), "audit": asdict(audit)}


def build_report():
    histories = ((), ("present",), ("absent",), ("present", "present"),
                 ("present", "absent"), ("absent", "absent"))
    return {
        "data_kind": "synthetic_current_state_replication_switch_audit",
        "scope": "expected information, not guaranteed realised gain, field proof or cost utility",
        "scenarios": [audit_history(history) for history in histories],
        "incomplete_vocabulary": audit_history(("present",), include_unmodelled=True),
        "physiology_error_sensitivity_after_present": [
            audit_history(("present",), physiology_error=e) for e in (0.05, 0.1, 0.2, 0.3, 0.5)
        ],
        "sensitivity_scope": "sampled synthetic specifications, not an interval robustness certificate",
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, allow_nan=False))
